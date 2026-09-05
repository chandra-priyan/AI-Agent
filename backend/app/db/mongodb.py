import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)

# Primary connection parameters from backend/.env
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://ch123:Chandra%402708@cluster0.fyjn9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "autonomous_data_scientist")

_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None


def connect_to_mongo() -> Database:
    """
    Initializes and verifies primary MongoDB database connection (MongoDB Atlas).
    """
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db

    # Attempt primary MongoDB connection (Atlas URI)
    try:
        logger.info(f"Connecting to primary MongoDB Atlas database [{MONGODB_DATABASE}]...")
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            tlsAllowInvalidCertificates=True
        )
        client.admin.command('ping')
        _mongo_client = client
        _mongo_db = client[MONGODB_DATABASE]
        logger.info(f"SUCCESS: Connected to MongoDB Atlas [{MONGODB_DATABASE}]!")
        return _mongo_db
    except Exception as primary_err:
        logger.warning(f"MongoDB Atlas primary connection timed out or unreachable: {primary_err}")
        
        # Fallback to local MongoDB engine instance if Atlas IP Whitelist restricts remote access
        local_uri = "mongodb://localhost:27017/autonomous_data_scientist"
        try:
            logger.info("Attempting connection to local MongoDB instance on port 27017...")
            client = MongoClient(local_uri, serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            _mongo_client = client
            _mongo_db = client[MONGODB_DATABASE]
            logger.info(f"SUCCESS: Connected to MongoDB engine [{MONGODB_DATABASE}]!")
            return _mongo_db
        except Exception as local_err:
            logger.error(f"CRITICAL: Failed to connect to any MongoDB instance: {local_err}")
            raise RuntimeError(f"Database service unavailable. MongoDB Atlas and local MongoDB connection failed: {primary_err}")


def get_mongo_db() -> Database:
    """Returns active MongoDB database instance."""
    global _mongo_db
    if _mongo_db is None:
        return connect_to_mongo()
    return _mongo_db


def close_mongo_connection():
    """Closes MongoDB connection cleanly on shutdown."""
    global _mongo_client, _mongo_db
    if _mongo_client:
        logger.info("Closing MongoDB connection...")
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None


# Collection Accessors
def get_users_collection():
    return get_mongo_db()["users"]

def get_datasets_collection():
    return get_mongo_db()["datasets"]

def get_analyses_collection():
    return get_mongo_db()["analyses"]

def get_chat_messages_collection():
    return get_mongo_db()["chat_messages"]

def get_reports_collection():
    return get_mongo_db()["reports"]
