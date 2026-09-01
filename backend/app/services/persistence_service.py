from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.repositories.analysis_repository import AnalysisRepository

class PersistenceService:
    @staticmethod
    def get_repo(db: Optional[Session] = None) -> AnalysisRepository:
        """Returns repo instance; opens fresh session if not provided."""
        if db is not None:
            return AnalysisRepository(db)
        return AnalysisRepository(SessionLocal())

    @classmethod
    def create_analysis(cls, analysis_id: str, question: str, filename: str = "dataset.csv", dataset_id: str = None):
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            return repo.create_analysis(analysis_id, question, filename, dataset_id)
        finally:
            db.close()

    @classmethod
    def save_investigation(cls, analysis_id: str, results_data: Dict[str, Any]):
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            return repo.save_investigation_results(analysis_id, results_data)
        finally:
            db.close()

    @classmethod
    def get_analysis(cls, analysis_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            model = repo.get_analysis(analysis_id)
            if not model:
                return None
            return {
                "id": model.id,
                "analysis_id": model.id,
                "dataset_id": model.dataset_id or model.id,
                "datasetName": model.filename or "dataset.csv",
                "question": model.question,
                "user_question": model.question,
                "status": model.status,
                "datasetProfile": model.dataset_profile,
                "investigationPlan": model.investigation_plan,
                "hypotheses": model.hypotheses or [],
                "executed_analyses": model.executed_analyses or [],
                "evidence": model.evidence or [],
                "alternative_explanations": model.alternative_explanations or [],
                "validation": model.validation or {"isVerified": True, "metrics": {}, "rationale": ""},
                "confidence": model.confidence or "HIGH",
                "conclusion": model.conclusion or "",
                "recommendations": model.recommendations or [],
                "limitations": model.limitations or [],
                "evidenceGraph": model.evidence_graph,
                "auditTrail": model.audit_trail or [],
                "whatIfAnalysis": model.what_if_analysis,
                "predictions": model.predictions,
                "contradictions": model.contradictions or [],
                "createdAt": model.created_at.strftime("%Y-%m-%d %H:%M") if model.created_at else "Recent"
            }
        finally:
            db.close()

    @classmethod
    def list_analyses(cls) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            models = repo.list_analyses()
            return [
                {
                    "id": m.id,
                    "analysis_id": m.id,
                    "dataset_id": m.dataset_id or m.id,
                    "datasetName": m.filename or "dataset.csv",
                    "question": m.question,
                    "status": m.status,
                    "conclusion": m.conclusion or "",
                    "confidence": m.confidence or "HIGH",
                    "createdAt": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else "Recent"
                }
                for m in models
            ]
        finally:
            db.close()

    @classmethod
    def update_status(cls, analysis_id: str, status: str, error_summary: Optional[str] = None):
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            return repo.update_status(analysis_id, status, error_summary)
        finally:
            db.close()

    @classmethod
    def save_chat_message(cls, analysis_id: str, role: str, text: str, confidence: str = None, msg_id: str = None):
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            return repo.add_chat_message(analysis_id, role, text, confidence, msg_id)
        finally:
            db.close()

    @classmethod
    def get_chat_history(cls, analysis_id: str) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            messages = repo.get_chat_history(analysis_id)
            return [
                {
                    "id": m.id,
                    "analysisId": m.analysis_id,
                    "sender": "ai" if m.role in ("ASSISTANT", "ai") else "user",
                    "text": m.text,
                    "confidence": m.confidence,
                    "timestamp": m.created_at.strftime("%I:%M %p") if m.created_at else "Recent"
                }
                for m in messages
            ]
        finally:
            db.close()

    @classmethod
    def delete_analysis(cls, analysis_id: str) -> bool:
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            return repo.delete_analysis(analysis_id)
        finally:
            db.close()

    @classmethod
    def save_dataset(cls, dataset_id: str, filename: str, rows: int, cols: int, column_names: list = None, file_path: str = None):
        db = SessionLocal()
        try:
            repo = AnalysisRepository(db)
            return repo.save_dataset_metadata(dataset_id, filename, rows, cols, column_names, file_path)
        finally:
            db.close()
