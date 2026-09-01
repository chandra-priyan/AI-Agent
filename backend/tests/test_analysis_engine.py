import os
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.analysis.loader import CSVLoader
from app.analysis.profiler import DatasetProfiler
from app.analysis.cleaning import DataCleaner
from app.analysis.descriptive import DescriptiveAnalysisEngine
from app.analysis.grouping import GroupAnalysisEngine
from app.analysis.trends import TrendAnalysisEngine
from app.analysis.correlation import CorrelationAnalysisEngine
from app.analysis.statistics import StatisticalTestEngine
from app.analysis.regression import RegressionEngine
from app.analysis.visualization import VisualizationEngine
from app.services.analysis_service import AnalysisService

client = TestClient(app)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")
SALES_PATH = os.path.join(SAMPLE_DIR, "demo_sales.csv")
CHURN_PATH = os.path.join(SAMPLE_DIR, "demo_sales.csv")

@pytest.fixture
def sample_sales_df():
    dataset_id, df = CSVLoader.load_from_path(SALES_PATH)
    return dataset_id, df

def test_csv_loader():
    dataset_id, df = CSVLoader.load_from_path(SALES_PATH)
    assert dataset_id.startswith("ds_")
    assert len(df) > 0
    assert "sales_amount" in df.columns

def test_dataset_profiler(sample_sales_df):
    dataset_id, df = sample_sales_df
    profile = DatasetProfiler.profile_dataset(df, dataset_id, "demo_sales.csv")
    assert profile["rows"] == len(df)
    assert profile["columns"] == len(df.columns)
    assert "sales_amount" in profile["numerical_columns"]
    assert "region" in profile["categorical_columns"]
    assert profile["numerical_stats"]["sales_amount"]["mean"] > 0

def test_data_quality_and_cleaning(sample_sales_df):
    dataset_id, df = sample_sales_df
    quality_before = DataCleaner.generate_quality_report(df)
    assert 0.0 <= quality_before["quality_score"] <= 1.0

    cleaned_df, transformations = DataCleaner.clean_dataset(df, drop_duplicates=True)
    assert len(cleaned_df) <= len(df)
    quality_after = DataCleaner.generate_quality_report(cleaned_df)
    assert quality_after["quality_score"] >= quality_before["quality_score"]

def test_descriptive_analysis(sample_sales_df):
    dataset_id, df = sample_sales_df
    stats = DescriptiveAnalysisEngine.calculate_descriptive_stats(df, "sales_amount")
    assert len(stats) == 1
    assert stats[0]["metric"] == "sales_amount"
    assert stats[0]["mean"] > 0
    assert stats[0]["min"] <= stats[0]["median"] <= stats[0]["max"]

def test_group_analysis(sample_sales_df):
    dataset_id, df = sample_sales_df
    group_res = GroupAnalysisEngine.analyze_groups(df, group_by_col="region", target_col="sales_amount")
    assert group_res["group_by_column"] == "region"
    assert group_res["target_column"] == "sales_amount"
    assert len(group_res["groups"]) >= 2

def test_trend_analysis(sample_sales_df):
    dataset_id, df = sample_sales_df
    trend_res = TrendAnalysisEngine.analyze_trends(df, date_col="order_date", value_col="sales_amount", freq="monthly")
    assert trend_res["date_column"] == "order_date"
    assert trend_res["value_column"] == "sales_amount"
    assert len(trend_res["trends"]) > 0

def test_correlation_analysis(sample_sales_df):
    dataset_id, df = sample_sales_df
    corrs = CorrelationAnalysisEngine.calculate_correlations(df, method="pearson")
    assert isinstance(corrs, list)
    for c in corrs:
        assert "disclaimer" in c
        assert "Correlation does NOT imply causation" in c["disclaimer"]

def test_statistical_tests(sample_sales_df):
    dataset_id, df = sample_sales_df
    ttest_res = StatisticalTestEngine.run_test(df, test_type="ttest_ind", group_col="region", val_col="sales_amount")
    assert "test_name" in ttest_res
    assert "p_value" in ttest_res

    anova_res = StatisticalTestEngine.run_test(df, test_type="anova", group_col="category", val_col="sales_amount")
    assert "test_name" in anova_res

    ci_res = StatisticalTestEngine.run_test(df, test_type="confidence_interval", val_col="sales_amount")
    assert ci_res["details"]["lower_bound"] <= ci_res["details"]["upper_bound"]

def test_regression_analysis(sample_sales_df):
    dataset_id, df = sample_sales_df
    clean_df = df.dropna(subset=["sales_amount", "quantity"])
    reg_res = RegressionEngine.run_regression(clean_df, target_col="sales_amount", feature_cols=["quantity"])
    assert 0.0 <= reg_res["r_squared"] <= 1.0
    assert "quantity" in reg_res["coefficients"]

def test_visualization_engine(sample_sales_df):
    dataset_id, df = sample_sales_df
    bar_chart = VisualizationEngine.generate_chart_data(df, chart_type="bar", x_col="region", y_col="sales_amount")
    assert bar_chart["chart_type"] == "bar"
    assert len(bar_chart["x"]) > 0

def test_fastapi_upload_and_analysis_routes():
    reg = client.post("/api/v1/auth/register", json={"email": "eng_test@example.com", "password": "password123"})
    token = reg.json().get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    with open(SALES_PATH, "rb") as f:
        response = client.post("/api/v1/analysis/upload", files={"file": ("sales.csv", f, "text/csv")}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    dataset_id = data["dataset_id"]
    assert dataset_id.startswith("ds_")

    # Profile endpoint
    prof_resp = client.get(f"/api/v1/analysis/{dataset_id}/profile", headers=headers)
    assert prof_resp.status_code == 200
    assert prof_resp.json()["rows"] == data["rows"]

    # Descriptive endpoint
    desc_resp = client.post(f"/api/v1/analysis/{dataset_id}/descriptive")
    assert desc_resp.status_code == 200

    # Evidence endpoint
    ev_resp = client.get(f"/api/v1/analysis/{dataset_id}/evidence")
    assert ev_resp.status_code == 200
    assert "evidence" in ev_resp.json()
