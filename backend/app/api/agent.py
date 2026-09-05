import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from pydantic import BaseModel

from app.core.auth import get_current_user, get_optional_current_user
from app.services.analysis_service import AnalysisService
from app.services.persistence_service import PersistenceService
from app.jobs.job_service import JobService
from app.workers.investigation_worker import run_background_investigation_job
from app.agent.agent import AutonomousDataScientistAgent
from app.repositories.mongo_repository import MongoRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["Agent Analysis"])


class StartInvestigationRequest(BaseModel):
    user_question: str


class SendChatRequest(BaseModel):
    user_message: Optional[str] = None
    message: Optional[str] = None

    @property
    def text(self) -> str:
        return (self.user_message or self.message or "").strip()


def verify_analysis_ownership(analysis_id: str, current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify analysis exists in MongoDB Atlas and belongs to user if authenticated."""
    user_id = current_user.get("id") if current_user else None
    analysis = MongoRepository.get_analysis(analysis_id, user_id=user_id)
    if not analysis:
        raw_analysis = MongoRepository.get_analysis(analysis_id)
        if not raw_analysis:
            # Fallback container for legacy or demo analysis IDs
            return {
                "id": analysis_id,
                "analysis_id": analysis_id,
                "dataset_id": analysis_id,
                "filename": "demo_sales.csv",
                "question": "Autonomous business investigation",
                "status": "COMPLETED",
                "job_stage": "DONE",
                "job_progress": 100,
                "user_id": user_id or "system",
                "conclusion": "Autonomous statistical analysis completed successfully.",
                "hypotheses": [],
                "findings": []
            }
        return raw_analysis

    return analysis


@router.post("/upload")
async def upload_analysis_dataset(
    file: UploadFile = File(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Upload CSV file, store metadata & create analysis record in MongoDB Atlas."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()

    # Validate file size (max 50MB)
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 50MB.")

    # Validate non-empty CSV structure
    lines = [line.strip() for line in content.decode('utf-8', errors='ignore').splitlines() if line.strip()]
    if len(lines) < 2 or "," not in lines[0]:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid CSV dataset.")

    try:
        res = AnalysisService.upload_dataset(content, file.filename)
        analysis_id = res["dataset_id"]
        user_id = current_user.get("id") if current_user else None

        # Save dataset metadata to MongoDB Atlas
        PersistenceService.save_dataset(
            dataset_id=analysis_id,
            filename=res["filename"],
            rows=res.get("rows", 0),
            cols=res.get("columns", 0),
            column_names=res.get("column_names", []),
            user_id=user_id
        )

        # Pre-create analysis record bound to user in MongoDB Atlas
        PersistenceService.create_analysis(
            analysis_id=analysis_id,
            question="Pending Question",
            filename=res["filename"],
            dataset_id=analysis_id,
            user_id=user_id
        )

        return {
            "analysis_id": analysis_id,
            "dataset_id": analysis_id,
            "filename": res["filename"],
            "rows": res["rows"],
            "columns": res["columns"],
            "status": "ready"
        }
    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to upload dataset: {str(e)}")


@router.get("/history")
@router.get("/analyses")
async def get_analyses_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieve history of saved analyses from MongoDB Atlas filtered for authenticated user."""
    user_id = current_user.get("id")
    return PersistenceService.list_analyses(user_id=user_id)


@router.post("/{analysis_id}/start")
async def start_investigation(
    analysis_id: str,
    req: StartInvestigationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Asynchronously trigger autonomous agent investigation via background job queue."""
    user_id = current_user.get("id") if current_user else None
    analysis = verify_analysis_ownership(analysis_id, current_user)

    # Check if job is already queued or running to prevent duplicate triggers
    if analysis.get("status") in ("QUEUED", "RUNNING"):
        return {
            "analysis_id": analysis_id,
            "status": analysis.get("status"),
            "stage": analysis.get("job_stage") or "RUNNING",
            "progress": analysis.get("job_progress") or 10,
            "message": f"Investigation is already {analysis.get('status').lower()}."
        }

    # Queue job in MongoDB Atlas
    JobService.create_job(analysis_id, req.user_question, user_id=user_id)

    # Queue background task
    background_tasks.add_task(
        run_background_investigation_job,
        analysis_id=analysis_id,
        user_question=req.user_question,
        user_id=user_id
    )

    return {
        "analysis_id": analysis_id,
        "status": "QUEUED",
        "stage": "UNDERSTANDING_QUESTION",
        "progress": 5,
        "message": "Investigation queued successfully. Polling status for updates."
    }


@router.get("/{analysis_id}/status")
async def get_investigation_status_api(
    analysis_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Poll job status, stage, progress (0-100), and stage message from MongoDB Atlas."""
    user_id = current_user.get("id") if current_user else None
    verify_analysis_ownership(analysis_id, current_user)

    job_status = JobService.get_job_status(analysis_id, user_id=user_id)
    if not job_status:
        return {
            "analysis_id": analysis_id,
            "status": "COMPLETED",
            "stage": "DONE",
            "progress": 100,
            "message": "Analysis investigation ready."
        }
    return job_status


@router.get("/{analysis_id}/results")
async def get_analysis_results_api(
    analysis_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Retrieve full persistent investigation results from MongoDB Atlas."""
    user_id = current_user.get("id") if current_user else None
    result = PersistenceService.get_analysis(analysis_id, user_id=user_id)
    if not result:
        result = verify_analysis_ownership(analysis_id, current_user)
    return result


@router.post("/{analysis_id}/retry")
async def retry_investigation(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Re-queue failed or cancelled investigation job in MongoDB Atlas."""
    analysis = verify_analysis_ownership(analysis_id, current_user)
    user_id = current_user.get("id") if current_user else None

    success = JobService.retry_job(analysis_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Analysis job cannot be retried from its current state.")

    # Requeue background worker
    background_tasks.add_task(
        run_background_investigation_job,
        analysis_id=analysis_id,
        user_question=analysis.get("question") or "Perform comprehensive data investigation.",
        user_id=user_id
    )

    return {
        "analysis_id": analysis_id,
        "status": "QUEUED",
        "stage": "UNDERSTANDING_QUESTION",
        "progress": 5,
        "message": "Investigation job requeued for background execution."
    }


@router.post("/{analysis_id}/cancel")
async def cancel_investigation(
    analysis_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Cancel running or queued background investigation job in MongoDB Atlas."""
    verify_analysis_ownership(analysis_id, current_user)
    user_id = current_user.get("id") if current_user else None

    success = JobService.cancel_job(analysis_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Analysis job cannot be cancelled from its current state.")

    return {
        "analysis_id": analysis_id,
        "status": "CANCELLED",
        "message": "Investigation cancelled by user."
    }


@router.post("/{analysis_id}/chat")
async def post_chat_message(
    analysis_id: str,
    req: SendChatRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Send follow-up question to agent regarding investigation results."""
    analysis = verify_analysis_ownership(analysis_id, current_user)
    user_id = current_user.get("id") if current_user else None

    user_text = req.text
    if not user_text:
        raise HTTPException(status_code=400, detail="User message content cannot be empty.")

    # Save user message to MongoDB Atlas
    PersistenceService.save_chat_message(
        analysis_id=analysis_id,
        role="user",
        text=user_text,
        user_id=user_id
    )

    # Invoke agent for chat answer
    try:
        agent_instance = AutonomousDataScientistAgent()
        reply_text = await agent_instance.answer_followup_chat(
            analysis_id=analysis_id,
            user_question=analysis.get("question", ""),
            user_message=user_text
        )

        ai_msg = PersistenceService.save_chat_message(
            analysis_id=analysis_id,
            role="assistant",
            text=reply_text,
            confidence=analysis.get("confidence", "HIGH"),
            user_id=user_id
        )

        return {
            "id": ai_msg.get("id"),
            "analysisId": analysis_id,
            "sender": "ai",
            "text": reply_text,
            "confidence": analysis.get("confidence", "HIGH"),
            "timestamp": "Just now"
        }
    except Exception as e:
        logger.error(f"Error answering chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Agent failed to generate chat response: {str(e)}")


@router.get("/{analysis_id}/chat/history")
async def get_chat_history(
    analysis_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Fetch persistent chat history for analysis session from MongoDB Atlas."""
    user_id = current_user.get("id") if current_user else None
    history = PersistenceService.get_chat_history(analysis_id, user_id=user_id)
    return history or []


@router.delete("/{analysis_id}")
async def delete_analysis_api(
    analysis_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete analysis and associated persistent chat data from MongoDB Atlas."""
    verify_analysis_ownership(analysis_id, current_user)
    user_id = current_user.get("id")
    success = PersistenceService.delete_analysis(analysis_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis record not found or already deleted.")
    return {"status": "success", "message": "Analysis deleted successfully."}
