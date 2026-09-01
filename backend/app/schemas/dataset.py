from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    status: str = "ready"
    created_at: Optional[str] = None

class NumericalColumnProfile(BaseModel):
    name: str
    count: int
    mean: float
    std: float
    min: float
    q25: float
    median: float
    q75: float
    max: float
    missing_count: int
    missing_pct: float

class CategoricalColumnProfile(BaseModel):
    name: str
    count: int
    unique_count: int
    most_frequent: Optional[Any] = None
    frequency_distribution: Dict[str, int] = Field(default_factory=dict)
    missing_count: int
    missing_pct: float

class DateColumnProfile(BaseModel):
    name: str
    count: int
    min_date: str
    max_date: str
    time_span_days: int
    missing_count: int

class DatasetProfile(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    dtypes: Dict[str, str]
    numerical_columns: List[str]
    categorical_columns: List[str]
    date_columns: List[str]
    missing_values: Dict[str, int]
    duplicate_rows: int
    constant_columns: List[str]
    potential_id_columns: List[str]
    numerical_stats: Dict[str, NumericalColumnProfile] = Field(default_factory=dict)
    categorical_stats: Dict[str, CategoricalColumnProfile] = Field(default_factory=dict)
    date_stats: Dict[str, DateColumnProfile] = Field(default_factory=dict)

class CleaningTransformation(BaseModel):
    operation: str
    details: Dict[str, Any]
    rows_affected: int

class DataQualityReport(BaseModel):
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Explainable data quality score between 0 and 1")
    total_rows: int
    total_columns: int
    missing_values: Dict[str, int]
    duplicates: int
    outliers: Dict[str, int] = Field(default_factory=dict)
    constant_columns: List[str] = Field(default_factory=list)
    unusable_columns: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class CleanDatasetResponse(BaseModel):
    dataset_id: str
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    transformations: List[CleaningTransformation]
    quality_score_after: float
