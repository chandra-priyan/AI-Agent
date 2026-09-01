import os
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

from app.db.database import Base, engine
import app.db.models  # Ensure models registered

# Initialize database schema
Base.metadata.create_all(bind=engine)

# Run safe programmatic table migrations for LLM failover metadata
def run_migrations():
    from sqlalchemy import text
    with engine.begin() as conn:
        for col_name, col_type in [
            ("provider_used", "VARCHAR(32)"),
            ("fallback_used", "BOOLEAN DEFAULT 0"),
            ("fallback_reason", "TEXT")
        ]:
            try:
                conn.execute(text(f"ALTER TABLE analyses ADD COLUMN {col_name} {col_type}"))
            except Exception:
                # Column likely already exists
                pass

run_migrations()

app = FastAPI(
    title="Autonomous Data Scientist Backend API",
    description="FastAPI Backend powered by Python Data Science Engine & Groq AI Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Top-level endpoint for Dashboard analysis history."""
    return await agent.get_analyses_history()



llm_service = LLMService()


def generate_synthetic_dataset(name: str) -> pd.DataFrame:
    """Generate representative dataframe for calculation engine."""
    np.random.seed(42)
    n = 1000
    regions = np.random.choice(["North", "South", "East", "West"], size=n, p=[0.25, 0.35, 0.20, 0.20])
    sales = np.where(regions == "North", np.random.normal(120, 30, n), np.random.normal(180, 40, n))
    discounts = np.random.uniform(0.05, 0.25, n)

    return pd.DataFrame({
        "Region": regions,
        "SalesAmount": np.round(sales, 2),
        "DiscountRate": np.round(discounts, 2),
        "CustomerID": np.random.randint(10000, 99999, size=n)
    })


class CreateAnalysisRequest(BaseModel):
    datasetName: str
    question: str
    rowCount: Optional[int] = 48230
    colCount: Optional[int] = 14


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
    ollama_running = models_dict.get("ollama", {}).get("running", False)
    groq_running = models_dict.get("groq", {}).get("running", False)
    
    return {
        "status": "healthy",
        "running": True,
        "ollama_running": ollama_running,
        "groq_running": groq_running,
        "active_model": status["active_model"],
        "available_models": list(models_dict.keys())
    }



@app.post("/api/v1/analysis/create")
def create_analysis(req: CreateAnalysisRequest):
    """Run Python Data Science calculations and invoke Groq AI Agent."""
    status = llm_service.get_status()
    if not status["running"]:
        raise HTTPException(
            status_code=503,
            detail="Groq API is not ready. Please check your GROQ_API_KEY environment variable."
        )

    # 1. Run Python Data Science Engine Calculations
    df = generate_synthetic_dataset(req.datasetName)
    audit_results = EDAEngine.audit_dataset(df)
    correlations = EDAEngine.calculate_correlations(df)
    hypothesis_results = HypothesisEngine.evaluate_business_question(df, req.question)
    feature_importance = AutoMLEngine.calculate_feature_importance(df, "SalesAmount")

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
