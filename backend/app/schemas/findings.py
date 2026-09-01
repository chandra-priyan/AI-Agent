from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EvidenceObject(BaseModel):
    id: str
    finding: str
    metric: str
    value: float
    evidence_type: str = Field(..., description="trend, group_difference, correlation, anomaly, quality_issue")
    supporting_analysis: str
    statistical_support: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)

class FindingsBundle(BaseModel):
    dataset_id: str
    total_findings: int
    evidence: List[EvidenceObject]
