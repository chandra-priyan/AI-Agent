import logging
import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AnalysisModel, UserModel
from app.core.auth import get_current_user, get_optional_current_user
from app.services.analysis_service import AnalysisService
from app.services.persistence_service import PersistenceService
from app.jobs.job_service import JobService
from app.workers.investigation_worker import run_background_investigation_job
from app.agent.agent import AutonomousDataScientistAgent

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

def verify_analysis_ownership(analysis_id: str, current_user: Optional[UserModel], db: Session) -> AnalysisModel:
    """Verify analysis exists and belongs to user if bound."""
    analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    if analysis.user_id and current_user and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this analysis.")

    return analysis

@router.post("/upload")
async def upload_analysis_dataset(
    file: UploadFile = File(...),
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Upload CSV file, create dataset & analysis records assigned to user."""
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
        
        user_id = current_user.id if current_user else None

        # Save dataset metadata to DB
        PersistenceService.save_dataset(
            dataset_id=analysis_id,
            filename=res["filename"],
            rows=res.get("rows", 0),
            cols=res.get("columns", 0),
            column_names=res.get("column_names", [])
        )

        # Pre-create analysis record bound to user
        analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
        if not analysis:
            analysis = AnalysisModel(
                id=analysis_id,
                user_id=user_id,
                dataset_id=analysis_id,
                filename=res["filename"],
                question="Pending Question",
                status="CREATED",
                job_stage="UNDERSTANDING_QUESTION",
                job_progress=0
            )
            db.add(analysis)
            db.commit()
        else:
            analysis.user_id = user_id
            db.commit()

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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve history of saved analyses filtered for authenticated user."""
    analyses = db.query(AnalysisModel).filter(AnalysisModel.user_id == current_user.id).order_by(AnalysisModel.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "analysis_id": a.id,
            "dataset_id": a.dataset_id or a.id,
            "datasetName": a.filename or "dataset.csv",
            "question": a.question,
            "status": a.status,
            "job_stage": a.job_stage,
            "job_progress": a.job_progress,
            "conclusion": a.conclusion or "",
            "confidence": a.confidence or "HIGH",
            "createdAt": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "Recent"
        }
        for a in analyses
    ]

@router.post("/{analysis_id}/start")
async def start_investigation(
    analysis_id: str,
    req: StartInvestigationRequest,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Asynchronously trigger autonomous agent investigation via background job queue."""
    analysis = verify_analysis_ownership(analysis_id, current_user, db)

    # Check if job is already queued or running to prevent duplicate triggers
    if analysis.status in ("QUEUED", "RUNNING"):
        return {
            "analysis_id": analysis_id,
            "status": analysis.status,
            "stage": analysis.job_stage or "RUNNING",
            "progress": analysis.job_progress or 10,
            "message": f"Investigation is already {analysis.status.lower()}."
        }

    # Queue job in database
    user_id = current_user.id
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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Poll high-level job status, stage, progress (0-100), and stage message."""
    verify_analysis_ownership(analysis_id, current_user, db)

    job_status = JobService.get_job_status(analysis_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Investigation status not found for this analysis ID.")
    return job_status

@router.get("/{analysis_id}/results")
async def get_analysis_results_api(
    analysis_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full persistent investigation results for completed analysis."""
    verify_analysis_ownership(analysis_id, current_user, db)

    result = PersistenceService.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis results not found.")
    return result

@router.post("/{analysis_id}/retry")
async def retry_investigation(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Re-queue failed or cancelled investigation job."""
    analysis = verify_analysis_ownership(analysis_id, current_user, db)

    user_id = current_user.id
    success = JobService.retry_job(analysis_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Analysis job cannot be retried from its current state.")

    # Requeue background worker
    background_tasks.add_task(
        run_background_investigation_job,
        analysis_id=analysis_id,
        user_question=analysis.question or "Perform comprehensive data investigation.",
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
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel running or queued background investigation job."""
    verify_analysis_ownership(analysis_id, current_user, db)

    user_id = current_user.id
    success = JobService.cancel_job(analysis_id, user_id)
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
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Send follow-up question to agent regarding investigation results."""
    analysis = verify_analysis_ownership(analysis_id, current_user, db)

    user_text = req.text
    if not user_text:
        raise HTTPException(status_code=400, detail="User message content cannot be empty.")

    # Save user message
    PersistenceService.save_chat_message(
        analysis_id=analysis_id,
        role="user",
        text=user_text
    )

    # Invoke agent for chat answer
    try:
        agent_instance = AutonomousDataScientistAgent()
        reply_text = await agent_instance.answer_followup_chat(
            analysis_id=analysis_id,
            user_question=analysis.question,
            user_message=user_text
        )

        ai_msg = PersistenceService.save_chat_message(
            analysis_id=analysis_id,
            role="assistant",
            text=reply_text,
            confidence=analysis.confidence or "HIGH"
        )

        return {
            "id": ai_msg.id,
            "analysisId": analysis_id,
            "sender": "ai",
            "text": reply_text,
            "confidence": analysis.confidence or "HIGH",
            "timestamp": "Just now"
        }
    except Exception as e:
        logger.error(f"Error answering chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Agent failed to generate chat response: {str(e)}")

@router.get("/{analysis_id}/chat/history")
async def get_chat_history(
    analysis_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch persistent chat history for analysis session."""
    verify_analysis_ownership(analysis_id, current_user, db)
    return PersistenceService.get_chat_history(analysis_id)

@router.delete("/{analysis_id}")
async def delete_analysis_api(
    analysis_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete analysis and associated persistent data."""
    verify_analysis_ownership(analysis_id, current_user, db)
    success = PersistenceService.delete_analysis(analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis record not found or already deleted.")
    return {"status": "success", "message": "Analysis deleted successfully."}
