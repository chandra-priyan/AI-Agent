from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class HypothesisStatus(str, Enum):
    PENDING = "PENDING"
    TESTING = "TESTING"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"

class Hypothesis(BaseModel):
    id: str
    description: str
    reason: str
    required_analysis: str
    status: HypothesisStatus = HypothesisStatus.PENDING
    evidence: Optional[Dict[str, Any]] = None
    evaluation_reasoning: Optional[str] = None
    tested_at: Optional[str] = None

class InvestigationStep(BaseModel):
    id: str
    label: str
    status: str = "pending"  # "completed" | "active" | "pending"
    phase: str
    details: Optional[str] = None

class AnalysisExecution(BaseModel):
    id: str
    analysis_type: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    executed_at: str

class EvidenceItem(BaseModel):
    id: str
    title: str
    chart_type: str = "bar"
    data: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str
    metric: Optional[str] = None
    dimension: Optional[str] = None
    p_value: Optional[float] = None
    is_statistically_significant: Optional[bool] = None

class InvestigationGoal(BaseModel):
    intent: str
    target_metric: Optional[str] = None
    question_type: str = "exploratory"  # "causal", "comparative", "trend", "correlative", "exploratory"
    relevant_dimensions: List[str] = Field(default_factory=list)
    date_column: Optional[str] = None
    unsupported_reason: Optional[str] = None
    is_answerable: bool = True

class AgentValidation(BaseModel):
    is_verified: bool = False
    evidence_strength: str = "WEAK"
    consistency_score: float = 0.0
    statistical_support: bool = False
    data_quality_ok: bool = True
    rationale: List[str] = Field(default_factory=list)

class AgentConfidence(BaseModel):
    level: ConfidenceLevel = ConfidenceLevel.LOW
    rationale: List[str] = Field(default_factory=list)

class InvestigationState(BaseModel):
    analysis_id: str
    dataset_id: str
    user_question: str
    dataset_profile: Dict[str, Any] = Field(default_factory=dict)
    data_quality: Dict[str, Any] = Field(default_factory=dict)
    investigation_goal: Optional[InvestigationGoal] = None
    investigation_plan: List[InvestigationStep] = Field(default_factory=list)
    current_step_id: Optional[str] = None
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    executed_analyses: List[AnalysisExecution] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    alternative_explanations: List[str] = Field(default_factory=list)
    validation: AgentValidation = Field(default_factory=AgentValidation)
    confidence: AgentConfidence = Field(default_factory=AgentConfidence)
    conclusion: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    next_investigation: Optional[str] = None
    status: str = "idle"  # "idle" | "planning" | "investigating" | "completed" | "failed"
    iteration_count: int = 0
    max_iterations: int = 5
    logs: List[str] = Field(default_factory=list)

    # Phase 9 fields
    audit_trail_data: Optional[List[Dict[str, Any]]] = None
    evidence_graph_data: Optional[Dict[str, Any]] = None
    what_if_data: Optional[Dict[str, Any]] = None
    predictive_data: Optional[Dict[str, Any]] = None
    contradictions_data: Optional[List[Dict[str, Any]]] = None

    # LLM Provider Metadata fields
    provider_used: Optional[str] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
