from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import UserModel
from app.core.auth import get_optional_current_user

from app.services.analysis_service import AnalysisService
from app.schemas.analysis import (
    DescriptiveAnalysisRequest, GroupAnalysisRequest, TrendAnalysisRequest,
    CorrelationRequest, StatisticalTestRequest, RegressionRequest
)

router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])

@router.post("/upload")
async def upload_csv_endpoint(
    file: UploadFile = File(...),
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """CSV upload endpoint delegating to main agent upload handler."""
    from app.api import agent
    return await agent.upload_analysis_dataset(file=file, current_user=current_user, db=db)

@router.get("/{dataset_id}/profile")
def get_dataset_profile(dataset_id: str):
    try:
        return AnalysisService.profile_dataset(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{dataset_id}/descriptive")
def run_descriptive_analysis(dataset_id: str, req: Optional[DescriptiveAnalysisRequest] = None):
    target_col = req.column_name if req else None
    try:
        return AnalysisService.descriptive_analysis(dataset_id, target_col)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{dataset_id}/group")
def run_group_analysis(dataset_id: str, req: Optional[GroupAnalysisRequest] = None):
    grp_col = req.group_by_column if req else None
    tgt_col = req.target_column if req else None
    aggs = req.agg_funcs if req else ["mean", "sum", "count"]
    try:
        return AnalysisService.group_analysis(dataset_id, grp_col, tgt_col, aggs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{dataset_id}/trend")
def run_trend_analysis(dataset_id: str, req: Optional[TrendAnalysisRequest] = None):
    dt_col = req.date_column if req else None
    val_col = req.value_column if req else None
    freq = req.freq if req else "monthly"
    try:
        return AnalysisService.trend_analysis(dataset_id, dt_col, val_col, freq)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{dataset_id}/correlation")
def run_correlation_analysis(dataset_id: str, req: Optional[CorrelationRequest] = None):
    method = req.method if req else "pearson"
    cols = req.columns if req else None
    try:
        return AnalysisService.correlation_analysis(dataset_id, method, cols)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{dataset_id}/statistical-test")
def run_statistical_test(dataset_id: str, req: StatisticalTestRequest):
    try:
        return AnalysisService.statistical_test(
            dataset_id,
            req.test_type,
            req.group_column,
            req.value_column,
            req.categorical_col1,
            req.categorical_col2,
            req.confidence_level
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{dataset_id}/regression")
def run_regression_analysis(dataset_id: str, req: RegressionRequest):
    try:
        return AnalysisService.regression_analysis(dataset_id, req.target_column, req.feature_columns)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/evidence")
def get_dataset_evidence(dataset_id: str):
    try:
        return AnalysisService.get_evidence(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{dataset_id}/chart")
def get_chart_data(
    dataset_id: str,
    chart_type: str = "bar",
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
    title: Optional[str] = None
):
    try:
        return AnalysisService.generate_chart(dataset_id, chart_type, x_column, y_column, title)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
