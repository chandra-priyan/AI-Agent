from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DatasetUnderstandingSchema(BaseModel):
    summary: str
    key_observations: List[str] = Field(default_factory=list)


class InvestigationStepSchema(BaseModel):
    id: str
    label: str
    status: str = "completed"
    phase: str


class HypothesisSchema(BaseModel):
    id: str
    title: str
    evidence_level: str
    is_supported: bool
    details: str


class EvidenceSchema(BaseModel):
    id: str
    title: str
    chart_type: str = "bar"
    data: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str


class ValidationSchema(BaseModel):
    is_verified: bool = True
    metrics: Dict[str, float] = Field(default_factory=dict)
    rationale: str


class ConfidenceSchema(BaseModel):
    level: str = "HIGH"
    rationale: List[str] = Field(default_factory=list)


class RecommendationSchema(BaseModel):
    id: str
    text: str
    action_type: Optional[str] = "investigate_further"


class StructuredAgentResult(BaseModel):
    goal: str
    dataset_understanding: DatasetUnderstandingSchema
    investigation_plan: List[InvestigationStepSchema]
    hypotheses: List[HypothesisSchema]
    evidence: List[EvidenceSchema]
    alternative_explanations: List[str]
    validation: ValidationSchema
    confidence: ConfidenceSchema
    conclusion: str
    recommendations: List[RecommendationSchema]
    next_investigation: str
