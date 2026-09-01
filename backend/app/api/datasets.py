from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.analysis_service import AnalysisService
from app.schemas.dataset import DatasetUploadResponse, DatasetProfile, DataQualityReport, CleanDatasetResponse
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/datasets", tags=["Datasets"])

@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset_file(file: UploadFile = File(...)):
    """Upload CSV file, load into pandas, assign ID, and return dataset info."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        res = AnalysisService.upload_dataset(content, file.filename)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/profile")
def get_dataset_profile(dataset_id: str):
    """Retrieve full dataset profile."""
    try:
        return AnalysisService.profile_dataset(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{dataset_id}/quality")
def get_data_quality(dataset_id: str):
    """Get data quality report and explainable quality score."""
    try:
        return AnalysisService.quality_report(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{dataset_id}/clean")
def clean_dataset(dataset_id: str, drop_duplicates: bool = True, drop_empty_rows: bool = True):
    """Perform safe data cleaning and return audit log."""
    try:
        return AnalysisService.clean_dataset(dataset_id, drop_duplicates, drop_empty_rows)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
