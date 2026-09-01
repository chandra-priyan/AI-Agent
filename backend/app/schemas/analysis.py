from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DescriptiveAnalysisRequest(BaseModel):
    column_name: Optional[str] = None

class DescriptiveMetric(BaseModel):
    metric: str
    count: int
    mean: float
    std: float
    min: float
    q25: float
    median: float
    q75: float
    max: float
    pct_change_mean_median: Optional[float] = None

class GroupAnalysisRequest(BaseModel):
    group_by_column: Optional[str] = None
    target_column: Optional[str] = None
    agg_funcs: List[str] = Field(default_factory=lambda: ["mean", "sum", "count"])

class GroupAnalysisResult(BaseModel):
    group_by_column: str
    target_column: str
    groups: List[Dict[str, Any]]

class TrendAnalysisRequest(BaseModel):
    date_column: Optional[str] = None
    value_column: Optional[str] = None
    freq: str = Field(default="monthly", description="daily, weekly, monthly, quarterly, yearly")

class TrendPoint(BaseModel):
    period: str
    value: float
    count: int
    pop_change: Optional[float] = None

class TrendAnalysisResult(BaseModel):
    date_column: str
    value_column: str
    freq: str
    trends: List[TrendPoint]
    overall_direction: str

class CorrelationRequest(BaseModel):
    method: str = Field(default="pearson", description="pearson or spearman")
    columns: Optional[List[str]] = None

class CorrelationPair(BaseModel):
    variable_a: str
    variable_b: str
    method: str
    correlation: float
    strength: str
    disclaimer: str = "Correlation does NOT imply causation."

class StatisticalTestRequest(BaseModel):
    test_type: str = Field(..., description="ttest_ind, anova, chi2, confidence_interval")
    group_column: Optional[str] = None
    value_column: Optional[str] = None
    categorical_col1: Optional[str] = None
    categorical_col2: Optional[str] = None
    confidence_level: float = 0.95

class StatisticalTestResult(BaseModel):
    test_name: str
    statistic: float
    p_value: float
    is_significant: bool
    confidence_level: float
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)

class RegressionRequest(BaseModel):
    target_column: str
    feature_columns: List[str]

class RegressionResult(BaseModel):
    target_column: str
    feature_columns: List[str]
    r_squared: float
    adjusted_r_squared: float
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    std_errors: Dict[str, float]
    confidence_intervals: Dict[str, List[float]]
    residual_summary: Dict[str, float]

class ChartData(BaseModel):
    chart_type: str = Field(..., description="line, bar, scatter, pie, boxplot")
    title: str
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x: List[Any]
    y: List[Any]
    series: Optional[List[Dict[str, Any]]] = None
