import os
import logging
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.llm.service import LLMService
from app.engine.eda import EDAEngine
from app.engine.hypothesis import HypothesisEngine
from app.engine.automl import AutoMLEngine

from app.api import datasets, analysis, agent, auth, health, report
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services.persistence_service import PersistenceService
from app.analysis.loader import CSVLoader

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autonomous Data Scientist Backend API",
    description="FastAPI Backend powered by Python Data Science Engine, Groq AI Agent & MongoDB Atlas",
    version="1.0.0"
)

# Startup & Shutdown event handlers for MongoDB Atlas lifecycle
@app.on_event("startup")
def startup_db_client():
    """Initializes and verifies primary MongoDB Atlas connection on server startup."""
    try:
        connect_to_mongo()
        logger.info("MongoDB Atlas startup verification complete.")
    except Exception as e:
        logger.error(f"CRITICAL: Application failed to start due to MongoDB Atlas connection error: {e}")

@app.on_event("shutdown")
def shutdown_db_client():
    """Closes MongoDB Atlas connections cleanly on application shutdown."""
    close_mongo_connection()

allowed_origins = [
    "https://ai-agent-omega-eight.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(analysis.router)
app.include_router(agent.router)
app.include_router(report.router)


@app.get("/api/analyses")
async def get_all_analyses():
    """Top-level endpoint for Dashboard analysis history from MongoDB Atlas."""
    return PersistenceService.list_analyses()


llm_service = LLMService()


class CreateAnalysisRequest(BaseModel):
    datasetName: str
    question: str
    datasetId: Optional[str] = None
    rowCount: Optional[int] = None
    colCount: Optional[int] = None


class ChatRequest(BaseModel):
    analysisId: str
    userMessage: str
    context: Optional[Dict[str, Any]] = None


@app.get("/api/v1/health")
def health_check():
    """Health check verifying AI runtime availability and active model."""
    status = llm_service.get_status()
    if not status["running"]:
        return {
            "status": "unhealthy",
            "running": False,
            "error": status["error"] or "All AI providers are currently unavailable.",
            "message": "AI services are not ready. Please verify your provider endpoints and api keys."
        }
    
    models_dict = status.get("models", {})
    groq_running = models_dict.get("groq", {}).get("running", False)
    openrouter_running = models_dict.get("openrouter", {}).get("running", False)
    
    return {
        "status": "healthy",
        "running": True,
        "groq_running": groq_running,
        "openrouter_running": openrouter_running,
        "active_model": status["active_model"],
        "available_models": list(models_dict.keys())
    }


@app.post("/api/v1/analysis/create")
def create_analysis(req: CreateAnalysisRequest):
    """Run Python Data Science calculations on real CSV and invoke AI Agent."""
    status = llm_service.get_status()
    if not status["running"]:
        raise HTTPException(
            status_code=503,
            detail="AI services are unavailable. Please verify API keys and network connectivity."
        )

    # 1. Load real CSV dataset
    dataset_id = req.datasetId or req.datasetName
    try:
        df = CSVLoader.get_dataset(dataset_id)
    except Exception as err:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset '{dataset_id}' could not be loaded. Please upload a CSV dataset first."
        )

    # 2. Run Python Data Science Engine Calculations
    audit_results = EDAEngine.audit_dataset(df)
    correlations = EDAEngine.calculate_correlations(df)
    hypothesis_results = HypothesisEngine.evaluate_business_question(df, req.question)

    # Find numeric target column for feature importance
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    target_col = numeric_cols[-1] if numeric_cols else (df.columns[0] if len(df.columns) > 0 else "target")
    feature_importance = AutoMLEngine.calculate_feature_importance(df, target_col) if numeric_cols else []

    computed_metrics = {
        "audit": audit_results,
        "correlations": correlations,
        "hypothesisTests": hypothesis_results,
        "featureImportance": feature_importance
    }

    # 2. Feed calculated metrics to LLM Service
    try:
        agent_result = llm_service.generate_investigation_result(
            question=req.question,
            dataset_name=req.datasetName,
            row_count=audit_results.get("rowCount", 1000),
            col_count=audit_results.get("colCount", 4),
            computed_metrics=computed_metrics
        )

        return {
            "id": f"session_{os.urandom(4).hex()}",
            "datasetName": req.datasetName,
            "question": req.question,
            "status": "completed",
            "confidence": agent_result.get("confidence", {}).get("level", "HIGH"),
            "conclusion": agent_result.get("conclusion"),
            "datasetProfile": audit_results,
            "computedMetrics": computed_metrics,
            "findings": [
                {
                    "id": "f1",
                    "title": "Primary Variance Finding",
                    "summary": agent_result.get("conclusion"),
                    "confidence": agent_result.get("confidence", {}).get("level", "HIGH"),
                    "evidenceIds": ["e1"]
                }
            ],
            "hypotheses": agent_result.get("hypotheses", []),
            "evidence": agent_result.get("evidence", []),
            "recommendations": agent_result.get("recommendations", []),
            "agentResult": agent_result,
            "createdAt": "Just now"
        }
    except Exception as err:
        raise HTTPException(status_code=503, detail=str(err))


@app.post("/api/v1/chat/send")
def chat_send(req: ChatRequest):
    """Send follow-up chat message to Groq AI Agent."""
    status = llm_service.get_status()
    if not status["running"]:
        raise HTTPException(
            status_code=503,
            detail="Groq API is not ready. Please check your GROQ_API_KEY environment variable."
        )

    ctx = req.context or {}
    reply = llm_service.answer_chat_message(
        question=ctx.get("question", "General Analysis"),
        dataset_name=ctx.get("datasetName", "Dataset"),
        conclusion=ctx.get("conclusion", ""),
        user_message=req.userMessage
    )

    return {
        "id": f"ai_{os.urandom(4).hex()}",
        "analysisId": req.analysisId,
        "sender": "ai",
        "text": reply,
        "timestamp": "Just now",
        "confidence": "HIGH"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
