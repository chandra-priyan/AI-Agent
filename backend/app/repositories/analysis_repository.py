import datetime
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import AnalysisModel, ChatMessageModel, DatasetModel
from app.db.mongo import save_to_mongo, find_from_mongo, find_all_from_mongo

class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_analysis(
        self,
        analysis_id: str,
        question: str,
        filename: Optional[str] = "dataset.csv",
        dataset_id: Optional[str] = None
    ) -> AnalysisModel:
        """Create new analysis record in database."""
        analysis = self.db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
        if not analysis:
            analysis = AnalysisModel(
                id=analysis_id,
                dataset_id=dataset_id or analysis_id,
                filename=filename or "dataset.csv",
                question=question,
                status="CREATED",
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            self.db.add(analysis)
        else:
            analysis.question = question
            analysis.filename = filename or analysis.filename
            analysis.status = "CREATED"
            analysis.updated_at = datetime.datetime.utcnow()

        self.db.commit()
        self.db.refresh(analysis)

        # Mirror to MongoDB
        save_to_mongo("analyses", analysis_id, {
            "id": analysis_id,
            "dataset_id": dataset_id or analysis_id,
            "filename": filename or "dataset.csv",
            "question": question,
            "status": "CREATED",
            "created_at": datetime.datetime.utcnow().isoformat()
        })

        return analysis

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisModel]:
        """Fetch analysis record by ID."""
        return self.db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()

    def list_analyses(self) -> List[AnalysisModel]:
        """Fetch all analyses ordered by created_at descending."""
        return self.db.query(AnalysisModel).order_by(AnalysisModel.created_at.desc()).all()

    def update_status(self, analysis_id: str, status: str, error_summary: Optional[str] = None) -> Optional[AnalysisModel]:
        """Update analysis execution status."""
        analysis = self.get_analysis(analysis_id)
        if analysis:
            analysis.status = status
            analysis.updated_at = datetime.datetime.utcnow()
            if error_summary:
                analysis.error_summary = error_summary
            if status == "COMPLETED":
                analysis.completed_at = datetime.datetime.utcnow()
            self.db.commit()
            self.db.refresh(analysis)

            # Update in MongoDB
            save_to_mongo("analyses", analysis_id, {
                "id": analysis_id,
                "status": status,
                "error_summary": error_summary,
                "updated_at": datetime.datetime.utcnow().isoformat()
            })

        return analysis

    def save_investigation_results(self, analysis_id: str, results_data: Dict[str, Any]) -> Optional[AnalysisModel]:
        """Persist full investigation results, evidence, and conclusions."""
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            analysis = self.create_analysis(
                analysis_id=analysis_id,
                question=results_data.get("user_question") or results_data.get("question") or "Analysis Question",
                filename=results_data.get("datasetName") or "dataset.csv",
                dataset_id=results_data.get("dataset_id") or analysis_id
            )

        analysis.status = results_data.get("status") or "COMPLETED"
        analysis.dataset_profile = results_data.get("datasetProfile") or results_data.get("dataset_profile")
        analysis.investigation_plan = results_data.get("investigationPlan") or results_data.get("investigation_plan")
        analysis.hypotheses = results_data.get("hypotheses")
        analysis.executed_analyses = results_data.get("executed_analyses")
        analysis.evidence = results_data.get("evidence")
        analysis.alternative_explanations = results_data.get("alternative_explanations")
        analysis.validation = results_data.get("validation")
        analysis.confidence = results_data.get("confidence")
        analysis.conclusion = results_data.get("conclusion")
        analysis.recommendations = results_data.get("recommendations")
        analysis.limitations = results_data.get("limitations")

        # Provider metadata fields
        analysis.provider_used = results_data.get("provider_used")
        analysis.fallback_used = results_data.get("fallback_used", False)
        analysis.fallback_reason = results_data.get("fallback_reason")

        # Phase 9 fields
        analysis.evidence_graph = results_data.get("evidenceGraph") or results_data.get("evidence_graph")
        analysis.audit_trail = results_data.get("auditTrail") or results_data.get("audit_trail")
        analysis.what_if_analysis = results_data.get("whatIfAnalysis") or results_data.get("what_if_analysis")
        analysis.predictions = results_data.get("predictions")
        analysis.contradictions = results_data.get("contradictions")

        analysis.completed_at = datetime.datetime.utcnow()
        analysis.updated_at = datetime.datetime.utcnow()

        self.db.commit()
        self.db.refresh(analysis)

        # Mirror full results payload to MongoDB
        mongo_doc = results_data.copy()
        mongo_doc["id"] = analysis_id
        mongo_doc["updated_at"] = datetime.datetime.utcnow().isoformat()
        save_to_mongo("analyses", analysis_id, mongo_doc)

        return analysis

    def add_chat_message(
        self,
        analysis_id: str,
        role: str,
        text: str,
        confidence: Optional[str] = None,
        msg_id: Optional[str] = None
    ) -> ChatMessageModel:
        """Persist user or assistant chat message."""
        msg_id_val = msg_id or f"chat_{uuid.uuid4().hex[:8]}"
        msg = ChatMessageModel(
            id=msg_id_val,
            analysis_id=analysis_id,
            role=role,
            text=text,
            confidence=confidence,
            created_at=datetime.datetime.utcnow()
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        # Mirror chat message to MongoDB
        save_to_mongo("chat_messages", msg_id_val, {
            "id": msg_id_val,
            "analysis_id": analysis_id,
            "role": role,
            "text": text,
            "confidence": confidence,
            "created_at": datetime.datetime.utcnow().isoformat()
        })

        return msg

    def get_chat_history(self, analysis_id: str) -> List[ChatMessageModel]:
        """Fetch chat history for given analysis ordered by created_at."""
        return self.db.query(ChatMessageModel).filter(ChatMessageModel.analysis_id == analysis_id).order_by(ChatMessageModel.created_at.asc()).all()

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete analysis and associated chat records."""
        analysis = self.get_analysis(analysis_id)
        if analysis:
            self.db.delete(analysis)
            self.db.commit()
            return True
        return False

    def save_dataset_metadata(
        self,
        dataset_id: str,
        filename: str,
        rows: int,
        cols: int,
        column_names: Optional[List[str]] = None,
        file_path: Optional[str] = None
    ) -> DatasetModel:
        """Persist dataset upload metadata."""
        ds = self.db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if not ds:
            ds = DatasetModel(
                id=dataset_id,
                filename=filename,
                rows=rows,
                columns=cols,
                column_names=column_names or [],
                file_path=file_path,
                created_at=datetime.datetime.utcnow()
            )
            self.db.add(ds)
        else:
            ds.rows = rows
            ds.columns = cols
            ds.column_names = column_names or ds.column_names
        self.db.commit()
        self.db.refresh(ds)

        # Mirror dataset to MongoDB
        save_to_mongo("datasets", dataset_id, {
            "id": dataset_id,
            "filename": filename,
            "rows": rows,
            "columns": cols,
            "column_names": column_names or [],
            "file_path": file_path,
            "created_at": datetime.datetime.utcnow().isoformat()
        })

        return ds
