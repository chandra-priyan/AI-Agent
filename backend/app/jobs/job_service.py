import datetime
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import AnalysisModel

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
    @staticmethod
    def create_job(analysis_id: str, question: str, user_id: Optional[str] = None) -> Optional[AnalysisModel]:
        """Creates or initializes a background job record in QUEUED state."""
        db = SessionLocal()
        try:
            analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
            if not analysis:
                analysis = AnalysisModel(
                    id=analysis_id,
                    user_id=user_id,
                    dataset_id=analysis_id,
                    question=question,
                    status="QUEUED",
                    job_stage="UNDERSTANDING_QUESTION",
                    job_progress=5
                )
                db.add(analysis)
            else:
                if user_id:
                    analysis.user_id = user_id
                analysis.question = question
                analysis.status = "QUEUED"
                analysis.job_stage = "UNDERSTANDING_QUESTION"
                analysis.job_progress = 5
                analysis.updated_at = datetime.datetime.utcnow()

            db.commit()
            db.refresh(analysis)
            return analysis
        finally:
            db.close()
    @staticmethod
    def update_job_status(
        analysis_id: str,
        status: str,
        stage: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error_summary: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[AnalysisModel]:
        """Persists job status, stage, progress (0-100), and error summary in database."""
        opened = False
        if db is None:
            db = SessionLocal()
            opened = True

        try:
            analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
            if not analysis:
                logger.warning(f"Cannot update status for nonexistent analysis {analysis_id}")
                return None

            analysis.status = status
            if stage:
                analysis.job_stage = stage
            if progress is not None:
                analysis.job_progress = min(100, max(0, progress))

            if status == "RUNNING" and not analysis.started_at:
                analysis.started_at = datetime.datetime.utcnow()
            elif status in ("COMPLETED", "FAILED", "CANCELLED"):
                analysis.completed_at = datetime.datetime.utcnow()

            if error_summary:
                analysis.error_summary = error_summary

            analysis.updated_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(analysis)
            return analysis
        except Exception as e:
            logger.error(f"Failed to update job status for {analysis_id}: {e}")
            db.rollback()
            return None
        finally:
            if opened:
                db.close()

    @staticmethod
    def get_job_status(analysis_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetches job status, progress, stage, and safe user message."""
        db = SessionLocal()
        try:
            query = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id)
            if user_id:
                query = query.filter(AnalysisModel.user_id == user_id)
            analysis = query.first()

            if not analysis:
                return None

            stage = analysis.job_stage or "UNDERSTANDING_QUESTION"
            msg = STAGE_MESSAGES.get(stage, "Processing investigation...")

            if analysis.status == "FAILED":
                msg = "Investigation could not be completed."

            return {
                "analysis_id": analysis.id,
                "dataset_id": analysis.dataset_id or analysis.id,
                "status": analysis.status,
                "stage": stage,
                "progress": analysis.job_progress,
                "message": msg,
                "user_question": analysis.question,
                "started_at": analysis.started_at.strftime("%Y-%m-%d %H:%M") if analysis.started_at else None,
                "completed_at": analysis.completed_at.strftime("%Y-%m-%d %H:%M") if analysis.completed_at else None,
                "error_summary": analysis.error_summary if analysis.status == "FAILED" else None
            }
        finally:
            db.close()

    @staticmethod
    def retry_job(analysis_id: str, user_id: Optional[str] = None) -> bool:
        """Resets a FAILED or CANCELLED job back to QUEUED for worker execution."""
        db = SessionLocal()
        try:
            query = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id)
            if user_id:
                query = query.filter(AnalysisModel.user_id == user_id)
            analysis = query.first()

            if not analysis:
                return False

            if analysis.status not in ("FAILED", "CANCELLED", "COMPLETED"):
                return False

            analysis.status = "QUEUED"
            analysis.job_stage = "UNDERSTANDING_QUESTION"
            analysis.job_progress = 0
            analysis.error_summary = None
            analysis.started_at = None
            analysis.completed_at = None
            analysis.updated_at = datetime.datetime.utcnow()

            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def cancel_job(analysis_id: str, user_id: Optional[str] = None) -> bool:
        """Cancels a QUEUED or RUNNING job safely."""
        db = SessionLocal()
        try:
            query = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id)
            if user_id:
                query = query.filter(AnalysisModel.user_id == user_id)
            analysis = query.first()

            if not analysis:
                return False

            if analysis.status in ("COMPLETED", "CANCELLED"):
                return False

            analysis.status = "CANCELLED"
            analysis.job_stage = "FAILED"
            analysis.completed_at = datetime.datetime.utcnow()
            analysis.updated_at = datetime.datetime.utcnow()

            db.commit()
            return True
        finally:
            db.close()
