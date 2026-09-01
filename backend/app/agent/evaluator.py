import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.llm.service import LLMService
from app.agent.state import Hypothesis, HypothesisStatus, EvidenceItem, AnalysisExecution
from app.agent.prompts import EVIDENCE_EVALUATOR_PROMPT, ALTERNATIVE_EXPLANATIONS_PROMPT

logger = logging.getLogger(__name__)

class AgentEvaluator:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    async def evaluate_evidence(
        self,
        hypothesis: Hypothesis,
        execution: AnalysisExecution
    ) -> Hypothesis:
        """Evaluates latest Python analysis result against active hypothesis."""
        prompt = EVIDENCE_EVALUATOR_PROMPT.format(
            hypothesis_json=hypothesis.model_dump_json(),
            analysis_type=execution.analysis_type,
            result_json=json.dumps(execution.result, default=str)
        )

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.1)
            parsed = self._extract_json(raw_response)

            status_str = parsed.get("status", "TESTING").upper()
            try:
                new_status = HypothesisStatus(status_str)
            except ValueError:
                new_status = HypothesisStatus.SUPPORTED

            reasoning = parsed.get("reasoning", "Evidence evaluated against Python calculations.")
            evidence_exp = parsed.get("evidence_explanation")

            hypothesis.status = new_status
            hypothesis.evaluation_reasoning = reasoning
            hypothesis.evidence = {
                "execution_id": execution.id,
                "analysis_type": execution.analysis_type,
                "explanation": evidence_exp,
                "result_summary": execution.result.get("summary")
            }
            return hypothesis

        except Exception as e:
            logger.warning(f"Fallback in evidence evaluation due to LLM error: {e}")

        # Deterministic evaluation fallback
        res = execution.result
        if "error" in res:
            hypothesis.status = HypothesisStatus.INSUFFICIENT_EVIDENCE
            hypothesis.evaluation_reasoning = f"Analysis failed with error: {res['error']}"
        elif execution.analysis_type == "statistical_test":
            is_sig = res.get("is_statistically_significant", False)
            p_val = res.get("p_value")
            if is_sig:
                hypothesis.status = HypothesisStatus.SUPPORTED
                hypothesis.evaluation_reasoning = f"Statistically significant result confirmed with p-value = {p_val}."
            else:
                hypothesis.status = HypothesisStatus.NOT_SUPPORTED
                hypothesis.evaluation_reasoning = f"Result was not statistically significant (p-value = {p_val})."
        elif execution.analysis_type == "group_analysis" and res.get("groups"):
            hypothesis.status = HypothesisStatus.SUPPORTED
            hypothesis.evaluation_reasoning = f"Group differences calculated across {len(res['groups'])} categories."
        else:
            hypothesis.status = HypothesisStatus.SUPPORTED
            hypothesis.evaluation_reasoning = "Analysis executed successfully with structured evidence."

        return hypothesis

    async def generate_alternative_explanations(
        self,
        supported_hypotheses: List[Hypothesis],
        dataset_profile: Dict[str, Any]
    ) -> List[str]:
        """Generates alternative explanations to ensure the agent does not stop at first finding."""
        num_cols = dataset_profile.get("numerical_columns", [])
        cat_cols = dataset_profile.get("categorical_columns", [])
        all_cols = num_cols + cat_cols

        findings = [
            {"hypothesis": h.description, "reasoning": h.evaluation_reasoning}
            for h in supported_hypotheses
        ]

        prompt = ALTERNATIVE_EXPLANATIONS_PROMPT.format(
            findings_json=json.dumps(findings),
            columns_json=json.dumps(all_cols)
        )

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.2)
            parsed = self._extract_json(raw_response)
            alts = parsed.get("alternative_explanations", [])
            if alts:
                return alts
        except Exception as e:
            logger.warning(f"Fallback in alternative explanations generation: {e}")

        # Deterministic alternatives fallback
        alts = []
        if len(cat_cols) > 1:
            alts.append(f"Observed variation may be confounded by secondary category '{cat_cols[1]}'.")
        if dataset_profile.get("date_column"):
            alts.append(f"Temporal seasonality along date column '{dataset_profile['date_column']}' could explain part of the change.")
        if not alts:
            alts.append("Unobserved external market factors or data collection noise might contribute.")

        return alts

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
