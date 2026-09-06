import logging
from fastapi import APIRouter
from app.db.mongodb import get_mongo_db
from app.llm.service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Health Checks"])
llm_service = LLMService()


@router.get("")
@router.get("/")
def get_application_health():
    """Health check endpoint verifying FastAPI, MongoDB Atlas connection, LLMs, and Worker status."""
    db_status = "connected"
    try:
        db = get_mongo_db()
        db.command("ping")
    except Exception as e:
        logger.error(f"MongoDB Atlas health check failed: {e}")
        db_status = "disconnected"

    status_info = llm_service.get_status()
    models_status = status_info.get("models", {})

    ollama_status = "healthy" if models_status.get("ollama", {}).get("running") else "unhealthy"
    groq_status = "healthy" if models_status.get("groq", {}).get("running") else "unhealthy"
    gemini_status = "healthy" if models_status.get("gemini", {}).get("running") else "unhealthy"
    openrouter_status = "healthy" if models_status.get("openrouter", {}).get("running") else "unhealthy"

    llm_healthy = (
        ollama_status == "healthy" or
        groq_status == "healthy" or
        gemini_status == "healthy" or
        openrouter_status == "healthy"
    )
    overall = "healthy" if (db_status == "connected" and llm_healthy) else "degraded"

    return {
        "status": overall,
        "services": {
            "backend": "healthy",
            "database": db_status,
            "mongodb_atlas": db_status,
            "ollama": ollama_status,
            "groq": groq_status,
            "gemini": gemini_status,
            "openrouter": openrouter_status,
            "worker": "healthy"
        },
        "active_model": status_info.get("active_model"),
        "error": status_info.get("error") if not llm_healthy else None
    }
