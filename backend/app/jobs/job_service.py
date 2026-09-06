import datetime
import logging
from typing import Optional, Dict, Any
from app.repositories.mongo_repository import MongoRepository

logger = logging.getLogger(__name__)

STAGES = [
    "UNDERSTANDING_QUESTION",
    "PROFILING_DATA",
    "PLANNING",
    "GENERATING_HYPOTHESES",
    "ANALYZING",
    "EVALUATING",
    "VALIDATING",
    "SYNTHESIZING",
    "COMPLETED",
    "FAILED"
]

STAGE_MESSAGES = {
    "UNDERSTANDING_QUESTION": "Analyzing business question intent and scope",
    "PROFILING_DATA": "Profiling dataset structure, metrics, and quality health",
    "PLANNING": "Constructing autonomous investigation plan",
    "GENERATING_HYPOTHESES": "Formulating data science hypotheses",
    "ANALYZING": "Executing Python statistical calculations and data transformations",
    "EVALUATING": "Evaluating statistical evidence against hypotheses",
    "VALIDATING": "Validating findings and checking alternative explanations",
    "SYNTHESIZING": "Synthesizing executive conclusions and recommendations",
    "COMPLETED": "Investigation completed successfully",
    "FAILED": "Investigation could not be completed"
}


class JobService:
    """Manages background investigation job states stored in MongoDB Atlas."""

    @staticmethod
    def create_job(analysis_id: str, question: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Creates or initializes a background job record in QUEUED state in MongoDB Atlas."""
        analysis = MongoRepository.get_analysis(analysis_id, user_id)
        if not analysis:
            analysis = MongoRepository.create_analysis(
                analysis_id=analysis_id,
                question=question,
                filename="dataset.csv",
                dataset_id=analysis_id,
                user_id=user_id
            )
        
        MongoRepository.get_analyses_collection().update_one(
            {"_id": analysis_id},
            {"$set": {
                "question": question,
                "status": "QUEUED",
                "job_stage": "UNDERSTANDING_QUESTION",
                "job_progress": 5,
                "user_id": user_id or analysis.get("user_id", "system"),
                "updated_at": datetime.datetime.utcnow().isoformat()
            }}
        )
        return MongoRepository.get_analysis(analysis_id, user_id)

    @staticmethod
    def update_job_status(
        analysis_id: str,
        status: str,
        stage: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error_summary: Optional[str] = None,
        db: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Persists job status, stage, progress (0-100), and error summary in MongoDB Atlas."""
        try:
            update_fields: Dict[str, Any] = {
                "status": status,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }
            if stage:
                update_fields["job_stage"] = stage
            if progress is not None:
                update_fields["job_progress"] = min(100, max(0, progress))
            if error_summary:
                update_fields["error_summary"] = error_summary

            if status == "RUNNING":
                update_fields["started_at"] = datetime.datetime.utcnow().isoformat()
            elif status in ("COMPLETED", "FAILED", "CANCELLED"):
                update_fields["completed_at"] = datetime.datetime.utcnow().isoformat()

            MongoRepository.get_analyses_collection().update_one(
                {"_id": analysis_id},
                {"$set": update_fields}
            )
            return MongoRepository.get_analysis(analysis_id)
        except Exception as e:
            logger.error(f"Failed to update job status in MongoDB Atlas for {analysis_id}: {e}")
            return None

    @staticmethod
    def get_job_status(analysis_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetches job status, progress, stage, and user message from MongoDB Atlas."""
        analysis = MongoRepository.get_analysis(analysis_id, user_id)
        if not analysis:
            return None

        stage = analysis.get("job_stage") or "UNDERSTANDING_QUESTION"
        msg = STAGE_MESSAGES.get(stage, "Processing investigation...")

        if analysis.get("status") == "FAILED":
            msg = "Investigation could not be completed."

        started_at = analysis.get("started_at")
        completed_at = analysis.get("completed_at")

        return {
            "analysis_id": analysis_id,
            "dataset_id": analysis.get("dataset_id", analysis_id),
            "status": analysis.get("status", "QUEUED"),
            "stage": stage,
            "progress": analysis.get("job_progress", 0),
            "message": msg,
            "user_question": analysis.get("question", ""),
            "started_at": started_at[:16].replace("T", " ") if started_at else None,
            "completed_at": completed_at[:16].replace("T", " ") if completed_at else None,
            "error_summary": analysis.get("error_summary") if analysis.get("status") == "FAILED" else None
        }

    @staticmethod
    def retry_job(analysis_id: str, user_id: Optional[str] = None) -> bool:
        """Resets a FAILED or CANCELLED job back to QUEUED for worker execution in MongoDB Atlas."""
        analysis = MongoRepository.get_analysis(analysis_id, user_id)
        if not analysis:
            return False

        if analysis.get("status") not in ("FAILED", "CANCELLED", "COMPLETED"):
            return False

        MongoRepository.get_analyses_collection().update_one(
            {"_id": analysis_id},
            {"$set": {
                "status": "QUEUED",
                "job_stage": "UNDERSTANDING_QUESTION",
                "job_progress": 0,
                "error_summary": None,
                "started_at": None,
                "completed_at": None,
                "updated_at": datetime.datetime.utcnow().isoformat()
            }}
        )
        return True

    @staticmethod
    def cancel_job(analysis_id: str, user_id: Optional[str] = None) -> bool:
        """Cancels a QUEUED or RUNNING job safely in MongoDB Atlas."""
        analysis = MongoRepository.get_analysis(analysis_id, user_id)
        if not analysis:
            return False

        if analysis.get("status") in ("COMPLETED", "CANCELLED"):
            return False

        MongoRepository.get_analyses_collection().update_one(
            {"_id": analysis_id},
            {"$set": {
                "status": "CANCELLED",
                "job_stage": "FAILED",
                "completed_at": datetime.datetime.utcnow().isoformat(),
                "updated_at": datetime.datetime.utcnow().isoformat()
            }}
        )
        return True
