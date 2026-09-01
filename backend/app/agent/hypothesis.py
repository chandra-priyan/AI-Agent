import json
import logging
from typing import Dict, Any, List, Optional
from app.llm.service import LLMService
from app.agent.state import Hypothesis, HypothesisStatus, InvestigationGoal
from app.agent.prompts import HYPOTHESIS_GENERATOR_PROMPT

logger = logging.getLogger(__name__)

class HypothesisEngine:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    async def generate_hypotheses(
        self,
        question: str,
        goal: InvestigationGoal,
        dataset_profile: Dict[str, Any]
    ) -> List[Hypothesis]:
        """Generates 3 to 5 distinct hypotheses grounded in actual dataset columns."""
        num_cols = dataset_profile.get("numerical_columns", [])
        cat_cols = dataset_profile.get("categorical_columns", [])
        target_metric = goal.target_metric or (num_cols[0] if num_cols else "metric")

        prompt = HYPOTHESIS_GENERATOR_PROMPT.format(
            question=question,
            numerical_cols=json.dumps(num_cols),
            categorical_cols=json.dumps(cat_cols),
            target_metric=target_metric
        )

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.2)
            parsed = self._extract_json(raw_response)
            raw_hyp = parsed.get("hypotheses", [])

            hypotheses = []
            for idx, h in enumerate(raw_hyp):
                hypotheses.append(
                    Hypothesis(
                        id=h.get("id", f"H{idx+1}"),
                        description=h.get("description", f"Hypothesis {idx+1}"),
                        reason=h.get("reason", "Based on column relationships"),
                        required_analysis=h.get("required_analysis", "group_analysis"),
                        status=HypothesisStatus.PENDING
                    )
                )

            if hypotheses:
                return hypotheses

        except Exception as e:
            logger.warning(f"Fallback in hypothesis generation due to LLM error: {e}")

        # Fallback deterministic hypotheses generator
        hypotheses = []
        if cat_cols and num_cols:
            hypotheses.append(
                Hypothesis(
                    id="H1",
                    description=f"Performance variation in {target_metric} is primarily driven by categorical grouping in '{cat_cols[0]}'.",
                    reason=f"Categorical groupings in {cat_cols[0]} often account for regional or structural variance.",
                    required_analysis="group_analysis",
                    status=HypothesisStatus.PENDING
                )
            )

        if len(num_cols) > 1:
            other_num = num_cols[1] if num_cols[0] == target_metric else num_cols[0]
            hypotheses.append(
                Hypothesis(
                    id="H2",
                    description=f"Changes in '{target_metric}' are strongly correlated with numerical shifts in '{other_num}'.",
                    reason=f"Numerical correlation between {target_metric} and {other_num} indicates a direct metric relationship.",
                    required_analysis="correlation_analysis",
                    status=HypothesisStatus.PENDING
                )
            )

        if dataset_profile.get("date_column"):
            date_col = dataset_profile.get("date_column")
            hypotheses.append(
                Hypothesis(
                    id="H3",
                    description=f"Trend shifts over time along date column '{date_col}' explain metric changes.",
                    reason=f"Time-series analysis along {date_col} captures temporal shifts.",
                    required_analysis="trend_analysis",
                    status=HypothesisStatus.PENDING
                )
            )

        if not hypotheses:
            hypotheses.append(
                Hypothesis(
                    id="H1",
                    description=f"Distribution of {target_metric} shows significant baseline variance.",
                    reason="Baseline descriptive stats reveal distribution skewness.",
                    required_analysis="descriptive_analysis",
                    status=HypothesisStatus.PENDING
                )
            )

        return hypotheses

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
