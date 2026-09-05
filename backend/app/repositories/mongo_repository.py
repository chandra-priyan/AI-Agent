import datetime
import uuid
import logging
from typing import List, Optional, Dict, Any

from app.db.mongodb import (
    get_users_collection,
    get_datasets_collection,
    get_analyses_collection,
    get_chat_messages_collection,
    get_reports_collection
)

logger = logging.getLogger(__name__)


class MongoRepository:
    """Centralized repository providing CRUD access to MongoDB Atlas collections."""

    # ----------------------------------------------------
    # USER OPERATIONS
    # ----------------------------------------------------
    @staticmethod
    def create_user(email: str, password_hash: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Registers a new user in MongoDB Atlas users collection."""
        users_col = get_users_collection()
        uid = user_id or f"usr_{uuid.uuid4().hex[:12]}"
        now_str = datetime.datetime.utcnow().isoformat()
        
        user_doc = {
            "_id": uid,
            "id": uid,
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "created_at": now_str,
            "updated_at": now_str
        }
        users_col.replace_one({"_id": uid}, user_doc, upsert=True)
        return user_doc

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Finds user document by unique email address."""
        users_col = get_users_collection()
        return users_col.find_one({"email": email.strip().lower()})

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Finds user document by user_id (_id)."""
        users_col = get_users_collection()
        return users_col.find_one({"_id": user_id})

    # ----------------------------------------------------
    # DATASET OPERATIONS
    # ----------------------------------------------------
    @staticmethod
    def save_dataset_metadata(
        dataset_id: str,
        filename: str,
        rows: int,
        cols: int,
        column_names: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Persists dataset metadata in MongoDB Atlas datasets collection."""
        datasets_col = get_datasets_collection()
        now_str = datetime.datetime.utcnow().isoformat()
        
        existing = datasets_col.find_one({"_id": dataset_id})
        ds_doc = {
            "_id": dataset_id,
            "id": dataset_id,
            "user_id": user_id or (existing.get("user_id") if existing else "system"),
            "filename": filename,
            "rows": rows,
            "columns": cols,
            "column_names": column_names or (existing.get("column_names") if existing else []),
            "file_path": file_path or (existing.get("file_path") if existing else None),
            "uploaded_at": existing.get("uploaded_at") if existing else now_str,
            "created_at": existing.get("created_at") if existing else now_str,
            "status": "READY"
        }
        datasets_col.replace_one({"_id": dataset_id}, ds_doc, upsert=True)
        return ds_doc

    @staticmethod
    def list_datasets(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists dataset documents from MongoDB Atlas, isolated by user_id if provided."""
        datasets_col = get_datasets_collection()
        query = {}
        if user_id:
            query["$or"] = [{"user_id": user_id}, {"user_id": "system"}]
            
        cursor = datasets_col.find(query).sort("created_at", -1)
        results = []
        for doc in cursor:
            doc["id"] = str(doc.get("_id", doc.get("id")))
            results.append(doc)
        return results

    @staticmethod
    def get_dataset(dataset_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves dataset document by dataset_id."""
        datasets_col = get_datasets_collection()
        query = {"_id": dataset_id}
        if user_id:
            query["$or"] = [{"user_id": user_id}, {"user_id": "system"}]
        return datasets_col.find_one(query)

    # ----------------------------------------------------
    # ANALYSIS OPERATIONS
    # ----------------------------------------------------
    @staticmethod
    def create_analysis(
        analysis_id: str,
        question: str,
        filename: Optional[str] = "dataset.csv",
        dataset_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates or initializes analysis session in MongoDB Atlas analyses collection."""
        analyses_col = get_analyses_collection()
        now_str = datetime.datetime.utcnow().isoformat()
        ds_id = dataset_id or analysis_id

        existing = analyses_col.find_one({"_id": analysis_id})
        analysis_doc = {
            "_id": analysis_id,
            "id": analysis_id,
            "analysis_id": analysis_id,
            "user_id": user_id or (existing.get("user_id") if existing else "system"),
            "dataset_id": ds_id,
            "datasetName": filename or "dataset.csv",
            "filename": filename or "dataset.csv",
            "question": question,
            "status": "CREATED",
            "job_stage": "UNDERSTANDING_QUESTION",
            "job_progress": 0,
            "created_at": existing.get("created_at") if existing else now_str,
            "createdAt": existing.get("createdAt") if existing else now_str,
            "updated_at": now_str
        }
        analyses_col.replace_one({"_id": analysis_id}, analysis_doc, upsert=True)
        return analysis_doc

    @staticmethod
    def get_analysis(analysis_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves analysis document by ID from MongoDB Atlas."""
        analyses_col = get_analyses_collection()
        query = {"_id": analysis_id}
        if user_id:
            query["$or"] = [{"user_id": user_id}, {"user_id": "system"}]
        doc = analyses_col.find_one(query)
        if doc:
            doc["id"] = str(doc.get("_id", doc.get("id")))
        return doc

    @staticmethod
    def list_analyses(
        user_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        dataset_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lists analyses from MongoDB Atlas with user isolation and filtering."""
        analyses_col = get_analyses_collection()
        query: Dict[str, Any] = {}

        if user_id:
            query["$or"] = [{"user_id": user_id}, {"user_id": "system"}]

        if status_filter and status_filter.upper() != "ALL":
            query["status"] = status_filter.upper()

        if dataset_filter and dataset_filter.upper() != "ALL":
            query["dataset_id"] = dataset_filter

        if search_query:
            query["$text"] = {"$search": search_query} if False else {
                "$or": [
                    {"question": {"$regex": search_query, "$options": "i"}},
                    {"datasetName": {"$regex": search_query, "$options": "i"}},
                    {"conclusion": {"$regex": search_query, "$options": "i"}}
                ]
            }

        cursor = analyses_col.find(query).sort("created_at", -1)
        results = []
        for doc in cursor:
            doc["id"] = str(doc.get("_id", doc.get("id")))
            results.append(doc)
        return results

    @staticmethod
    def update_status(analysis_id: str, status: str, error_summary: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Updates execution status of analysis in MongoDB Atlas."""
        analyses_col = get_analyses_collection()
        now_str = datetime.datetime.utcnow().isoformat()
        
        update_fields: Dict[str, Any] = {
            "status": status,
            "updated_at": now_str
        }
        if error_summary:
            update_fields["error_summary"] = error_summary
        if status == "COMPLETED":
            update_fields["completed_at"] = now_str
            update_fields["job_progress"] = 100
            update_fields["job_stage"] = "ANALYSIS_COMPLETE"

        analyses_col.update_one({"_id": analysis_id}, {"$set": update_fields})
        return MongoRepository.get_analysis(analysis_id, user_id)

    @staticmethod
    def save_investigation_results(analysis_id: str, results_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Persists full investigation payload into MongoDB Atlas."""
        analyses_col = get_analyses_collection()
        now_str = datetime.datetime.utcnow().isoformat()
        
        existing = analyses_col.find_one({"_id": analysis_id}) or {}
        
        payload = results_data.copy()
        payload["_id"] = analysis_id
        payload["id"] = analysis_id
        payload["analysis_id"] = analysis_id
        payload["user_id"] = user_id or existing.get("user_id", "system")
        payload["status"] = results_data.get("status", "COMPLETED")
        payload["created_at"] = existing.get("created_at", now_str)
        payload["createdAt"] = existing.get("createdAt", now_str)
        payload["updated_at"] = now_str
        payload["completed_at"] = now_str
        payload["job_progress"] = 100
        payload["job_stage"] = "ANALYSIS_COMPLETE"

        analyses_col.replace_one({"_id": analysis_id}, payload, upsert=True)
        return payload

    @staticmethod
    def delete_analysis(analysis_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes analysis document and associated chat messages from MongoDB Atlas."""
        analyses_col = get_analyses_collection()
        chat_col = get_chat_messages_collection()

        query = {"_id": analysis_id}
        if user_id:
            query["user_id"] = user_id

        res = analyses_col.delete_one(query)
        if res.deleted_count > 0:
            chat_col.delete_many({"analysis_id": analysis_id})
            return True
        return False

    # ----------------------------------------------------
    # CHAT MESSAGE OPERATIONS
    # ----------------------------------------------------
    @staticmethod
    def add_chat_message(
        analysis_id: str,
        role: str,
        text: str,
        confidence: Optional[str] = None,
        user_id: Optional[str] = None,
        msg_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Persists a chat message in MongoDB Atlas chat_messages collection."""
        chat_col = get_chat_messages_collection()
        cid = msg_id or f"chat_{uuid.uuid4().hex[:12]}"
        now_str = datetime.datetime.utcnow().isoformat()

        msg_doc = {
            "_id": cid,
            "id": cid,
            "analysis_id": analysis_id,
            "user_id": user_id or "system",
            "role": role,
            "sender": "user" if role.lower() == "user" else "ai",
            "text": text,
            "confidence": confidence or "HIGH",
            "timestamp": "Just now",
            "created_at": now_str
        }
        chat_col.replace_one({"_id": cid}, msg_doc, upsert=True)
        return msg_doc

    @staticmethod
    def get_chat_history(analysis_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves chat messages for analysis_id from MongoDB Atlas."""
        chat_col = get_chat_messages_collection()
        cursor = chat_col.find({"analysis_id": analysis_id}).sort("created_at", 1)
        results = []
        for doc in cursor:
            doc["id"] = str(doc.get("_id", doc.get("id")))
            results.append(doc)
        return results

    # ----------------------------------------------------
    # REPORT OPERATIONS
    # ----------------------------------------------------
    @staticmethod
    def save_report(
        report_id: str,
        analysis_id: str,
        title: str,
        conclusion: str,
        findings: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        status: str = "GENERATED"
    ) -> Dict[str, Any]:
        """Persists report metadata document in MongoDB Atlas reports collection."""
        reports_col = get_reports_collection()
        now_str = datetime.datetime.utcnow().isoformat()

        report_doc = {
            "_id": report_id,
            "id": report_id,
            "analysis_id": analysis_id,
            "user_id": user_id or "system",
            "title": title,
            "conclusion": conclusion,
            "findings": findings,
            "created_at": now_str,
            "status": status
        }
        reports_col.replace_one({"_id": report_id}, report_doc, upsert=True)
        return report_doc

    @staticmethod
    def list_reports(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists reports from MongoDB Atlas."""
        reports_col = get_reports_collection()
        query = {}
        if user_id:
            query["$or"] = [{"user_id": user_id}, {"user_id": "system"}]
        cursor = reports_col.find(query).sort("created_at", -1)
        results = []
        for doc in cursor:
            doc["id"] = str(doc.get("_id", doc.get("id")))
            results.append(doc)
        return results

    @staticmethod
    def get_report(report_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves report by report_id from MongoDB Atlas."""
        reports_col = get_reports_collection()
        query = {"_id": report_id}
        if user_id:
            query["$or"] = [{"user_id": user_id}, {"user_id": "system"}]
        return reports_col.find_one(query)
