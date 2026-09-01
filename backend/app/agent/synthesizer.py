import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.llm.service import LLMService
from app.agent.state import Hypothesis, HypothesisStatus, EvidenceItem, AgentValidation, AgentConfidence, InvestigationGoal
from app.agent.prompts import SYNTHESIZER_PROMPT

logger = logging.getLogger(__name__)

class AgentSynthesizer:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    async def synthesize_results(
        self,
        question: str,
        goal: InvestigationGoal,
        hypotheses: List[Hypothesis],
        evidence: List[EvidenceItem],
        validation: AgentValidation,
        confidence: AgentConfidence
    ) -> Tuple[str, List[str], Optional[str]]:
        """Produces primary conclusion, recommendations, and next investigation steps."""

        supported_hyp = [
            h for h in hypotheses
            if h.status in (HypothesisStatus.SUPPORTED, HypothesisStatus.PARTIALLY_SUPPORTED)
        ]

        if not supported_hyp:
            conclusion = f"Insufficient evidence in the dataset to conclusively answer: '{question}'."
            recs = [
                "Collect additional data features or granular time-series records.",
                "Review data quality and missing value distribution."
            ]
            next_inv = "Re-evaluate dataset schema with expanded data columns."
            return conclusion, recs, next_inv

        supported_evidence_list = [
            {
                "hypothesis": h.description,
                "reasoning": h.evaluation_reasoning,
                "evidence": h.evidence
            }
            for h in supported_hyp
        ]

        prompt = SYNTHESIZER_PROMPT.format(
            question=question,
            goal_json=goal.model_dump_json(),
            supported_evidence_json=json.dumps(supported_evidence_list),
            validation_json=validation.model_dump_json()
        )

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.2)
            parsed = self._extract_json(raw_response)

            conclusion = parsed.get("conclusion")
            recs = parsed.get("recommendations", [])
            next_inv = parsed.get("next_investigation")

            if conclusion and recs:
                return conclusion, recs, next_inv

        except Exception as e:
            logger.warning(f"Fallback in synthesis due to LLM error: {e}")

        # Deterministic Synthesis Fallback
        primary_h = supported_hyp[0]
        conclusion = f"Primary conclusion: {primary_h.description} {primary_h.evaluation_reasoning or ''}"
        recs = [
            f"Focus intervention strategies on key drivers identified in {primary_h.description}.",
            "Monitor period-over-period metric performance to validate ongoing trends."
        ]
        if len(supported_hyp) > 1:
            next_inv = f"Investigate secondary supported factor: '{supported_hyp[1].description}'."
        else:
            next_inv = "Conduct deep-dive segmentation analysis across secondary demographic or operational dimensions."

        return conclusion, recs, next_inv

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
