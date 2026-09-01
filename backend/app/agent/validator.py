import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.llm.service import LLMService
from app.agent.state import AgentValidation, AgentConfidence, ConfidenceLevel, Hypothesis, HypothesisStatus, AnalysisExecution
from app.agent.prompts import VALIDATION_PROMPT

logger = logging.getLogger(__name__)

class AgentValidator:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    async def validate_investigation(
        self,
        question: str,
        data_quality: Dict[str, Any],
        hypotheses: List[Hypothesis],
        executed_analyses: List[AnalysisExecution]
    ) -> Tuple[AgentValidation, AgentConfidence]:
        """Validates evidence consistency, statistical support, data quality, and assigns explainable confidence level."""

        supported_hypotheses = [
            h for h in hypotheses
            if h.status in (HypothesisStatus.SUPPORTED, HypothesisStatus.PARTIALLY_SUPPORTED)
        ]

        hyp_evidence_list = [
            {
                "id": h.id,
                "description": h.description,
                "status": h.status.value,
                "reasoning": h.evaluation_reasoning
            }
            for h in hypotheses
        ]

        prompt = VALIDATION_PROMPT.format(
            question=question,
            data_quality_json=json.dumps(data_quality, default=str),
            hypotheses_and_evidence_json=json.dumps(hyp_evidence_list),
            executed_count=len(executed_analyses)
        )

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.1)
            parsed = self._extract_json(raw_response)

            is_verified = parsed.get("is_verified", True)
            ev_strength = parsed.get("evidence_strength", "MODERATE")
            consistency = parsed.get("consistency_score", 0.8)
            stat_support = parsed.get("statistical_support", False)
            quality_ok = parsed.get("data_quality_ok", True)
            rationale = parsed.get("rationale", ["Evidence consistency evaluated."])

            validation = AgentValidation(
                is_verified=is_verified,
                evidence_strength=ev_strength,
                consistency_score=consistency,
                statistical_support=stat_support,
                data_quality_ok=quality_ok,
                rationale=rationale
            )

            confidence = self._compute_explainable_confidence(
                validation=validation,
                supported_count=len(supported_hypotheses),
                total_count=len(hypotheses),
                executed_count=len(executed_analyses),
                data_quality=data_quality
            )

            return validation, confidence

        except Exception as e:
            logger.warning(f"Fallback in validation due to LLM error: {e}")

        # Deterministic Validation & Confidence Fallback
        stat_support = any(
            a.result.get("is_statistically_significant", False)
            for a in executed_analyses
            if a.analysis_type == "statistical_test"
        )
        data_score = data_quality.get("healthScore", 80)
        quality_ok = data_score >= 50

        rationale = []
        if supported_hypotheses:
            rationale.append(f"{len(supported_hypotheses)} hypothesis(es) supported by Python calculated evidence.")
        else:
            rationale.append("No hypotheses received strong supporting evidence.")

        if stat_support:
            rationale.append("Statistically significant test p-value confirmed.")
        if not quality_ok:
            rationale.append(f"Data health score is {data_score}% with missing values/duplicates.")

        validation = AgentValidation(
            is_verified=len(supported_hypotheses) > 0,
            evidence_strength="STRONG" if (supported_hypotheses and stat_support) else ("MODERATE" if supported_hypotheses else "WEAK"),
            consistency_score=0.85 if supported_hypotheses else 0.4,
            statistical_support=stat_support,
            data_quality_ok=quality_ok,
            rationale=rationale
        )

        confidence = self._compute_explainable_confidence(
            validation=validation,
            supported_count=len(supported_hypotheses),
            total_count=len(hypotheses),
            executed_count=len(executed_analyses),
            data_quality=data_quality
        )

        return validation, confidence

    def _compute_explainable_confidence(
        self,
        validation: AgentValidation,
        supported_count: int,
        total_count: int,
        executed_count: int,
        data_quality: Dict[str, Any]
    ) -> AgentConfidence:
        """Assigns explainable confidence score considering evidence, statistical support, and data health."""
        rationale = []

        if supported_count == 0 or executed_count == 0:
            return AgentConfidence(
                level=ConfidenceLevel.INSUFFICIENT,
                rationale=["No hypotheses supported by calculated evidence.", "Insufficient analytical executions."]
            )

        health_score = data_quality.get("healthScore", 80)

        if validation.statistical_support and supported_count >= 1 and health_score >= 70:
            level = ConfidenceLevel.HIGH
            rationale.append("Statistically significant test support (p < 0.05).")
            rationale.append("High dataset health score and consistent group evidence.")
        elif supported_count >= 1 and health_score >= 50:
            level = ConfidenceLevel.MEDIUM
            rationale.append("Hypothesis supported by calculated group/trend metrics.")
            rationale.append("Moderate data health score.")
        else:
            level = ConfidenceLevel.LOW
            rationale.append("Weak evidence or low dataset quality score.")

        return AgentConfidence(level=level, rationale=rationale)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Utility to extract JSON object from markdown blocks or raw strings."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end+1]
        return json.loads(text)
