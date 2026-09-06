import logging
from typing import Optional, List, Dict, Any
from app.repositories.mongo_repository import MongoRepository

logger = logging.getLogger(__name__)


class PersistenceService:
    """Service layer delegating all application persistence directly to MongoDB Atlas."""

    @classmethod
    def create_analysis(
        cls,
        analysis_id: str,
        question: str,
        filename: str = "dataset.csv",
        dataset_id: str = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates analysis session in MongoDB Atlas analyses collection."""
        return MongoRepository.create_analysis(
            analysis_id=analysis_id,
            question=question,
            filename=filename,
            dataset_id=dataset_id,
            user_id=user_id
        )

    @classmethod
    def save_investigation(cls, analysis_id: str, results_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Persists investigation payload in MongoDB Atlas analyses collection."""
        return MongoRepository.save_investigation_results(
            analysis_id=analysis_id,
            results_data=results_data,
            user_id=user_id
        )

    @classmethod
    def get_analysis(cls, analysis_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves analysis payload by analysis_id from MongoDB Atlas."""
        doc = MongoRepository.get_analysis(analysis_id, user_id)
        if not doc:
            return None
        
        # Ensure standard keys expected by frontend contracts
        return {
            "id": doc.get("id", str(doc.get("_id", analysis_id))),
            "analysis_id": doc.get("analysis_id", analysis_id),
            "dataset_id": doc.get("dataset_id", analysis_id),
            "datasetName": doc.get("datasetName", doc.get("filename", "dataset.csv")),
            "question": doc.get("question", doc.get("user_question", "")),
            "user_question": doc.get("question", doc.get("user_question", "")),
            "status": doc.get("status", "COMPLETED"),
            "job_stage": doc.get("job_stage", "ANALYSIS_COMPLETE"),
            "job_progress": doc.get("job_progress", 100),
            "datasetProfile": doc.get("datasetProfile", doc.get("dataset_profile")),
            "investigationPlan": doc.get("investigationPlan", doc.get("investigation_plan")),
            "hypotheses": doc.get("hypotheses", []),
            "executed_analyses": doc.get("executed_analyses", []),
            "evidence": doc.get("evidence", []),
            "alternative_explanations": doc.get("alternative_explanations", []),
            "validation": doc.get("validation", {"isVerified": True, "metrics": {}, "rationale": ""}),
            "confidence": doc.get("confidence", "HIGH"),
            "conclusion": doc.get("conclusion", ""),
            "recommendations": doc.get("recommendations", []),
            "limitations": doc.get("limitations", []),
            "evidenceGraph": doc.get("evidenceGraph", doc.get("evidence_graph")),
            "auditTrail": doc.get("auditTrail", doc.get("audit_trail", [])),
            "whatIfAnalysis": doc.get("whatIfAnalysis", doc.get("what_if_analysis")),
            "predictions": doc.get("predictions"),
            "contradictions": doc.get("contradictions", []),
            "createdAt": doc.get("createdAt", doc.get("created_at", "Just now"))
        }

    @classmethod
    def list_analyses(cls, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all user analyses from MongoDB Atlas."""
        docs = MongoRepository.list_analyses(user_id=user_id)
        return [
            {
                "id": d.get("id", str(d.get("_id"))),
                "analysis_id": d.get("id", str(d.get("_id"))),
                "dataset_id": d.get("dataset_id", str(d.get("_id"))),
                "datasetName": d.get("datasetName", d.get("filename", "dataset.csv")),
                "question": d.get("question", ""),
                "status": d.get("status", "CREATED"),
                "job_stage": d.get("job_stage", "UNDERSTANDING_QUESTION"),
                "job_progress": d.get("job_progress", 0),
                "conclusion": d.get("conclusion", ""),
                "confidence": d.get("confidence", "HIGH"),
                "createdAt": d.get("createdAt", d.get("created_at", "Recent"))
            }
            for d in docs
        ]

    @classmethod
    def update_status(cls, analysis_id: str, status: str, error_summary: Optional[str] = None, user_id: Optional[str] = None):
        """Updates analysis execution status in MongoDB Atlas."""
        return MongoRepository.update_status(
            analysis_id=analysis_id,
            status=status,
            error_summary=error_summary,
            user_id=user_id
        )

    @classmethod
    def save_chat_message(cls, analysis_id: str, role: str, text: str, confidence: str = None, user_id: Optional[str] = None, msg_id: str = None):
        """Persists chat message in MongoDB Atlas chat_messages collection."""
        return MongoRepository.add_chat_message(
            analysis_id=analysis_id,
            role=role,
            text=text,
            confidence=confidence,
            user_id=user_id,
            msg_id=msg_id
        )

    @classmethod
    def get_chat_history(cls, analysis_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves chat messages for given analysis_id from MongoDB Atlas."""
        docs = MongoRepository.get_chat_history(analysis_id, user_id)
        return [
            {
                "id": doc.get("id", str(doc.get("_id"))),
                "analysisId": doc.get("analysis_id", analysis_id),
                "sender": "ai" if doc.get("role", "").lower() in ("assistant", "ai") else "user",
                "text": doc.get("text", ""),
                "confidence": doc.get("confidence", "HIGH"),
                "timestamp": doc.get("timestamp", doc.get("created_at", "Just now"))
            }
            for doc in docs
        ]

    @classmethod
    def delete_analysis(cls, analysis_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes analysis document and chat messages from MongoDB Atlas."""
        return MongoRepository.delete_analysis(analysis_id, user_id)

    @classmethod
    def save_dataset(cls, dataset_id: str, filename: str, rows: int, cols: int, column_names: list = None, file_path: str = None, user_id: Optional[str] = None):
        """Persists dataset metadata document in MongoDB Atlas datasets collection."""
        return MongoRepository.save_dataset_metadata(
            dataset_id=dataset_id,
            filename=filename,
            rows=rows,
            cols=cols,
            column_names=column_names,
            file_path=file_path,
            user_id=user_id
        )

    @classmethod
    def list_datasets(cls, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists dataset documents from MongoDB Atlas datasets collection."""
        return MongoRepository.list_datasets(user_id=user_id)
