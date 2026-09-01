import os
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app
from app.agent.evidence_graph import EvidenceGraph
from app.agent.root_cause import RootCauseEngine
from app.agent.whatif_predictive import WhatIfPredictiveEngine
from app.agent.audit_trail import AuditTrailLogger

client = TestClient(app)
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")

def test_evidence_graph_and_contradiction():
    graph = EvidenceGraph("Why did sales decrease?")
    graph.add_evidence(
        hypothesis_id="h1",
        finding="North region sales dropped by 30%",
        source_analysis="group_analysis",
        supporting_metrics={"change_pct": -30.0}
    )
    graph.add_evidence(
        hypothesis_id="h2",
        finding="North region sales grew by 15%",
        source_analysis="trend_analysis",
        supporting_metrics={"change_pct": 15.0}
    )
    summary = graph.get_quality_summary()
    assert summary["total_nodes"] == 2
    assert summary["contradiction_count"] == 1
    assert summary["contradictions"][0]["status"] == "CONFLICTING_EVIDENCE"

def test_root_cause_engine():
    df = pd.DataFrame({
        "region": ["North", "North", "South", "South"],
        "revenue": [100, 50, 400, 450]
    })
    res = RootCauseEngine.evaluate_root_cause_hierarchy(df, "revenue", ["region"])
    assert res["target_metric"] == "revenue"
    assert res["primary_driver"]["dimension"] == "region"
    assert res["primary_driver"]["top_segment"] == "South"

def test_what_if_and_predictive_engine():
    df = pd.DataFrame({
        "units": [10, 20, 30, 40, 50],
        "sales": [100, 200, 300, 400, 500]
    })
    what_if = WhatIfPredictiveEngine.run_what_if_simulation(df, "sales", -10.0)
    assert what_if["metric"] == "sales"
    assert what_if["simulated_change_pct"] == -10.0
    assert what_if["estimated_impact"] == -150.0

    pred = WhatIfPredictiveEngine.run_predictive_analysis(df, "sales", ["units"])
    assert pred["target_column"] == "sales"
    assert pred["model_r2_score"] == 1.0

def test_audit_trail_logger():
    logger = AuditTrailLogger("test_analysis_id")
    logger.log_event("goal_understood", "Question intent analyzed")
    logger.log_event("hypotheses_generated", "Prioritized 3 hypotheses")
    trail = logger.to_list()
    assert len(trail) == 2
    assert trail[0]["action"] == "goal_understood"
    assert trail[1]["action"] == "hypotheses_generated"

def test_sample_datasets_exist():
    datasets = ["demo_sales.csv"]
    for ds in datasets:
        path = os.path.join(SAMPLE_DIR, ds)
        assert os.path.exists(path), f"Dataset missing: {ds}"
