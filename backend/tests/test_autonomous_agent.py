import os
import json
import pytest
import pandas as pd
import numpy as np
from typing import Optional
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app.main import app
from app.analysis.loader import DatasetSessionStore
from app.agent.agent import AutonomousDataScientistAgent, AgentSessionStore
from app.agent.state import HypothesisStatus, ConfidenceLevel
from app.db.database import Base, engine

@pytest.fixture(autouse=True)
def init_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture(autouse=True)
def mock_llm_service():
    async def mock_generate(self, prompt: str, system: Optional[str] = None, format_json: bool = False, **kwargs) -> str:
        p_lower = prompt.lower()
        if "unanswerable" in p_lower or "corporate stock price plummet" in p_lower:
            return json.dumps({
                "is_answerable": False,
                "intent": "Why did corporate stock price plummet in 2023?",
                "target_metric": None,
                "question_type": "exploratory",
                "relevant_dimensions": ["employee_name", "role"],
                "date_column": None,
                "unsupported_reason": "Dataset lacks sufficient columns or numerical metrics to answer this question."
            })
        elif "goal_understanding" in p_lower or "is_answerable" in prompt:
            intent = "Explore dataset metrics"
            target_metric = "sales_amount" if "sales" in p_lower or "order_date" in p_lower else "salary"
            if "churn" in p_lower:
                target_metric = "monthly_charges"
            return json.dumps({
                "is_answerable": True,
                "intent": intent,
                "target_metric": target_metric,
                "question_type": "comparative",
                "relevant_dimensions": ["region", "category"] if "sales" in p_lower else ["department"],
                "date_column": "order_date" if "sales" in p_lower else None,
                "unsupported_reason": None
            })
        elif "planner" in p_lower or "steps" in prompt:
            return json.dumps({
                "steps": [
                    {"id": "step_1", "label": "Assess baseline metrics & distribution", "phase": "Baseline Exploration"},
                    {"id": "step_2", "label": "Analyze group performance across categorical dimensions", "phase": "Group Comparative Analysis"},
                    {"id": "step_3", "label": "Investigate correlations & secondary factors", "phase": "Correlation & Drivers"},
                    {"id": "step_4", "label": "Run statistical hypothesis tests & regression validation", "phase": "Statistical Verification"},
                    {"id": "step_5", "label": "Evaluate alternative explanations & synthesize findings", "phase": "Final Synthesis"}
                ]
            })
        elif "hypothesis" in p_lower or "hypotheses" in prompt:
            return json.dumps({
                "hypotheses": [
                    {"id": "H1", "description": "Distribution of metric shows significant baseline variance.", "reason": "Baseline descriptive stats reveal distribution skewness.", "required_analysis": "descriptive_analysis"}
                ]
            })
        elif "analyzer" in p_lower or "action" in p_lower or "execution" in p_lower:
            return json.dumps({
                "action": "execute_analysis",
                "analysis_type": "descriptive_analysis",
                "parameters": {"val_col": "sales_amount" if "sales" in p_lower else "salary"}
            })
        elif "evaluator" in p_lower or "evidence" in p_lower:
            return json.dumps({
                "findings": "Descriptive analysis shows typical ranges.",
                "supported_hypotheses": ["H1"],
                "confidence_level": "MEDIUM",
                "charts": [{"type": "bar", "x": "region", "y": "sales_amount"}]
            })
        elif "alternative" in p_lower:
            return json.dumps({
                "alternative_explanations": ["Observed variation may be due to other segment variations."]
            })
        elif "validator" in p_lower or "validation" in p_lower:
            return json.dumps({
                "is_verified": True,
                "evidence_strength": "MODERATE",
                "consistency_score": 0.85,
                "statistical_support": True,
                "data_quality_ok": True,
                "rationale": "Evidence calculations show support."
            })
        elif "synthesizer" in p_lower or "synthesis" in p_lower:
            return json.dumps({
                "conclusion": "The analysis showed consistent parameters.",
                "recommendations": ["Optimize operations based on segment.", "Monitor performance over the next period."],
                "limitations": ["Dataset representation limit."],
                "next_steps": "Evaluate other parameters."
            })
        
        if format_json:
            return json.dumps({"status": "ok"})
        return "Generic mock LLM response text"

    with patch('app.llm.service.LLMService.generate', mock_generate):
        yield

@pytest.fixture
def session_store():
    store = DatasetSessionStore()
    store._sessions.clear()
    return store

@pytest.fixture
def agent_store():
    store = AgentSessionStore()
    store._sessions.clear()
    return store

@pytest.fixture
def sample_sales_df():
    np.random.seed(42)
    rows = 100
    dates = pd.date_range("2024-01-01", periods=rows, freq="D")
    regions = np.random.choice(["North", "South", "East", "West"], rows)
    categories = np.random.choice(["Electronics", "Clothing", "Home"], rows)

    sales = np.random.normal(500, 100, rows)
    # Simulate a drop in North region
    sales[regions == "North"] -= 150

    df = pd.DataFrame({
        "order_date": dates,
        "region": regions,
        "category": categories,
        "sales_amount": sales,
        "quantity": np.random.randint(1, 10, rows)
    })
    return df

@pytest.fixture
def sample_churn_df():
    rows = 100
    contracts = np.random.choice(["Month-to-Month", "One Year", "Two Year"], rows)
    charges = np.random.normal(70, 20, rows)
    churn = np.random.choice(["Yes", "No"], rows)
    dates = pd.date_range("2024-01-01", periods=rows, freq="D")

    return pd.DataFrame({
        "order_date": dates,
        "contract_type": contracts,
        "monthly_charges": charges,
        "tenure_months": np.random.randint(1, 60, rows),
        "churn_status": churn
    })

@pytest.fixture
def sample_missing_df():
    df = pd.DataFrame({
        "department": ["HR", "Engineering", "Sales", "HR", "Sales", None, "Engineering"],
        "salary": [50000, 120000, None, 52000, 85000, 90000, None],
        "performance_score": [3, 5, 4, 3, 2, 4, 5]
    })
    return df

@pytest.fixture
def sample_no_date_df():
    return pd.DataFrame({
        "product_name": ["Widget A", "Widget B", "Widget C", "Widget D"],
        "unit_cost": [10.5, 20.0, 15.0, 5.0],
        "revenue": [1000, 2500, 1800, 600]
    })

@pytest.mark.anyio
async def test_agent_question_1_sales_decrease(session_store, agent_store, sample_sales_df):
    """Test 1: 'Why did sales decrease?'"""
    dataset_id = "test_sales_ds"
    session_store.save_session(dataset_id, sample_sales_df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t1",
        dataset_id=dataset_id,
        user_question="Why did sales decrease?"
    )

    assert state.status == "completed"
    assert state.investigation_goal.is_answerable is True
    assert len(state.hypotheses) > 0
    assert len(state.executed_analyses) > 0
    assert state.conclusion is not None
    assert len(state.recommendations) > 0

@pytest.mark.anyio
async def test_agent_question_2_churn_increase(session_store, agent_store, sample_churn_df):
    """Test 2: 'Why did customer churn increase?'"""
    dataset_id = "test_churn_ds"
    session_store.save_session(dataset_id, sample_churn_df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t2",
        dataset_id=dataset_id,
        user_question="Why did customer churn increase?"
    )

    assert state.status == "completed"
    assert state.investigation_goal.is_answerable is True
    assert len(state.evidence) > 0

@pytest.mark.anyio
async def test_agent_question_3_worst_region(session_store, agent_store, sample_sales_df):
    """Test 3: 'Which region performed worst?'"""
    dataset_id = "test_sales_ds"
    session_store.save_session(dataset_id, sample_sales_df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t3",
        dataset_id=dataset_id,
        user_question="Which region performed worst?"
    )

    assert state.status == "completed"
    assert any(a.analysis_type == "group_analysis" for a in state.executed_analyses)

@pytest.mark.anyio
async def test_agent_question_4_factors_associated_revenue(session_store, agent_store, sample_sales_df):
    """Test 4: 'What factors are associated with revenue?'"""
    dataset_id = "test_sales_ds"
    session_store.save_session(dataset_id, sample_sales_df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t4",
        dataset_id=dataset_id,
        user_question="What factors are associated with revenue?"
    )

    assert state.status == "completed"
    assert len(state.evidence) > 0

@pytest.mark.anyio
async def test_agent_question_5_unanswerable_question(session_store, agent_store):
    """Test 5: A question that cannot be answered from the dataset."""
    df = pd.DataFrame({"employee_name": ["Alice", "Bob"], "role": ["Dev", "QA"]})
    dataset_id = "test_unanswerable_ds"
    session_store.save_session(dataset_id, df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t5",
        dataset_id=dataset_id,
        user_question="Why did corporate stock price plummet in 2023?"
    )

    assert state.status == "completed"
    assert state.investigation_goal.is_answerable is False
    assert state.confidence.level == ConfidenceLevel.INSUFFICIENT

@pytest.mark.anyio
async def test_agent_question_6_missing_values(session_store, agent_store, sample_missing_df):
    """Test 6: A dataset with missing values."""
    dataset_id = "test_missing_ds"
    session_store.save_session(dataset_id, sample_missing_df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t6",
        dataset_id=dataset_id,
        user_question="What is the average salary by department?"
    )

    assert state.status == "completed"
    assert sum(state.data_quality.get("missing_values", {}).values()) > 0 or state.data_quality.get("missingCells", 0) > 0

@pytest.mark.anyio
async def test_agent_question_7_no_date_column(session_store, agent_store, sample_no_date_df):
    """Test 7: A dataset without a date column."""
    dataset_id = "test_no_date_ds"
    session_store.save_session(dataset_id, sample_no_date_df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t7",
        dataset_id=dataset_id,
        user_question="Which product drives highest revenue?"
    )

    assert state.status == "completed"
    assert state.dataset_profile.get("date_column") is None

@pytest.mark.anyio
async def test_agent_question_8_insufficient_evidence(session_store, agent_store):
    """Test 8: A dataset with insufficient evidence or empty numbers."""
    df = pd.DataFrame({
        "item": ["A", "B"],
        "val": [10, 10]
    })
    dataset_id = "test_flat_ds"
    session_store.save_session(dataset_id, df)

    agent = AutonomousDataScientistAgent()
    state = await agent.run_investigation(
        analysis_id="analysis_t8",
        dataset_id=dataset_id,
        user_question="Why did val fluctuate wildly?"
    )

    assert state.status == "completed"
    assert state.confidence.level in (ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT, ConfidenceLevel.MEDIUM)

@pytest.mark.anyio
async def test_agent_fastapi_endpoints(session_store, sample_sales_df):
    """Integration Test for FastAPI agent endpoints (/start, /status, /results)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Register user for auth token
        reg = await client.post("/api/v1/auth/register", json={"email": "agent_test@example.com", "password": "password123"})
        assert reg.status_code == 200
        token = reg.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload dataset
        csv_bytes = b"Region,Sales\nNorth,100\nSouth,200\n"
        up_res = await client.post("/api/v1/analysis/upload", files={"file": ("data.csv", csv_bytes, "text/csv")}, headers=headers)
        assert up_res.status_code == 200
        analysis_id = up_res.json()["analysis_id"]

        # 1. Start investigation
        start_res = await client.post(
            f"/api/v1/analysis/{analysis_id}/start",
            json={"user_question": "Why did sales decrease in North?"},
            headers=headers
        )
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "QUEUED"

        # 2. Get status
        status_res = await client.get(f"/api/v1/analysis/{analysis_id}/status", headers=headers)
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["analysis_id"] == analysis_id
        assert status_data["status"] in ("QUEUED", "RUNNING", "COMPLETED")
