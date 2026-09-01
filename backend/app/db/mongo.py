import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/autonomous_ds")

_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None

def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        try:
            logger.info(f"Connecting to MongoDB at {MONGODB_URL}")
            _mongo_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=2000)
            # Test connection
            _mongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")
        except Exception as e:
            logger.warning(f"MongoDB connection warning: {e}. SQLite/Local fallback active.")
            _mongo_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=2000)
    return _mongo_client

def get_mongo_db() -> Database:
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        # Parse database name from URI or default to 'autonomous_ds'
        db_name = "autonomous_ds"
        if "/" in MONGODB_URL.split("://")[-1]:
            uri_db = MONGODB_URL.split("/")[-1].split("?")[0]
            if uri_db:
                db_name = uri_db
        _mongo_db = client[db_name]
    return _mongo_db

def save_to_mongo(collection_name: str, doc_id: str, data: dict):
    """Save or update a document in MongoDB."""
    try:
        db = get_mongo_db()
        data["_id"] = doc_id
        db[collection_name].replace_one({"_id": doc_id}, data, upsert=True)
    except Exception as e:
        logger.warning(f"Failed to write to MongoDB collection {collection_name}: {e}")

def find_from_mongo(collection_name: str, doc_id: str) -> Optional[dict]:
    """Retrieve a document by ID from MongoDB."""
    try:
        db = get_mongo_db()
        return db[collection_name].find_one({"_id": doc_id})
    except Exception as e:
        logger.warning(f"Failed to read from MongoDB collection {collection_name}: {e}")
        return None

def find_all_from_mongo(collection_name: str, filter_query: dict = None, limit: int = 50) -> list:
    """Find documents from MongoDB collection."""
    try:
        db = get_mongo_db()
        query = filter_query or {}
        cursor = db[collection_name].find(query).limit(limit)
        results = list(cursor)
        for r in results:
            if "_id" in r:
                r["id"] = str(r["_id"])
        return results
    except Exception as e:
        logger.warning(f"Failed to query MongoDB collection {collection_name}: {e}")
        return []
