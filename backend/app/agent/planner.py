import json
import logging
from typing import Dict, Any, Tuple, List, Optional
from app.llm.service import LLMService
from app.agent.state import InvestigationGoal, InvestigationStep
from app.agent.prompts import GOAL_UNDERSTANDING_PROMPT, PLANNER_PROMPT

logger = logging.getLogger(__name__)

class AgentPlanner:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    async def understand_goal_and_dataset(
        self,
        question: str,
        dataset_profile: Dict[str, Any],
        data_quality: Dict[str, Any]
    ) -> InvestigationGoal:
        """Determines if the question is answerable and maps relevant metrics/columns."""
        prompt = GOAL_UNDERSTANDING_PROMPT.format(
            question=question,
            dataset_profile_json=json.dumps(dataset_profile, default=str),
            data_quality_json=json.dumps(data_quality, default=str)
        )

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.1)
            parsed = self._extract_json(raw_response)

            is_answerable = parsed.get("is_answerable", True)
            target_metric = parsed.get("target_metric")
            unsupported_reason = parsed.get("unsupported_reason")

            # Double-check answerability against profile columns
            num_cols = dataset_profile.get("numerical_columns", [])
            cat_cols = dataset_profile.get("categorical_columns", [])
            all_cols = num_cols + cat_cols

            if target_metric and target_metric not in all_cols:
                # Fallback to first numerical metric if available
                if num_cols:
                    target_metric = num_cols[0]
                else:
                    target_metric = None

            if not is_answerable or (not num_cols and not cat_cols):
                return InvestigationGoal(
                    intent=question,
                    is_answerable=False,
                    unsupported_reason=unsupported_reason or "Dataset lacks sufficient columns or numerical metrics to answer this question."
                )

            return InvestigationGoal(
                intent=parsed.get("intent", question),
                target_metric=target_metric,
                question_type=parsed.get("question_type", "exploratory"),
                relevant_dimensions=parsed.get("relevant_dimensions", cat_cols[:3]),
                date_column=parsed.get("date_column") or dataset_profile.get("date_column"),
                is_answerable=True
            )

        except Exception as e:
            logger.warning(f"Fallback in goal understanding due to LLM error: {e}")
            # Deterministic fallback logic
            num_cols = dataset_profile.get("numerical_columns", [])
            cat_cols = dataset_profile.get("categorical_columns", [])
            date_col = dataset_profile.get("date_column")

            q_lower = question.lower()
            numeric_keywords = ["stock", "price", "revenue", "sales", "churn", "profit", "plummet", "cost", "salary", "decrease", "increase"]
            asking_numeric = any(k in q_lower for k in numeric_keywords)

            if asking_numeric and not num_cols:
                return InvestigationGoal(
                    intent=question,
                    target_metric=None,
                    question_type="unsupported",
                    relevant_dimensions=cat_cols[:3],
                    date_column=date_col,
                    is_answerable=False,
                    unsupported_reason="Dataset contains no numerical columns or financial metrics to evaluate this question."
                )

            target_metric = num_cols[0] if num_cols else None
            is_ans = len(num_cols) > 0 or len(cat_cols) > 0

            return InvestigationGoal(
                intent=question,
                target_metric=target_metric,
                question_type="comparative",
                relevant_dimensions=cat_cols[:3],
                date_column=date_col,
                is_answerable=is_ans,
                unsupported_reason=None if is_ans else "Insufficient columns available in dataset."
            )

    async def create_plan(
        self,
        question: str,
        goal: InvestigationGoal,
        dataset_profile: Dict[str, Any]
    ) -> List[InvestigationStep]:
        """Creates a dynamic step-by-step investigation plan."""
        num_cols = dataset_profile.get("numerical_columns", [])
        cat_cols = dataset_profile.get("categorical_columns", [])
        all_cols = num_cols + cat_cols

        prompt = PLANNER_PROMPT.format(
            question=question,
            goal_json=goal.model_dump_json(),
            columns_json=json.dumps(all_cols)
        )

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.1)
            parsed = self._extract_json(raw_response)
            raw_steps = parsed.get("steps", [])

            steps = []
            for idx, s in enumerate(raw_steps):
                steps.append(
                    InvestigationStep(
                        id=s.get("id", f"step_{idx+1}"),
                        label=s.get("label", f"Investigation Step {idx+1}"),
                        status="completed" if idx == 0 else "pending",
                        phase=s.get("phase", "Exploration"),
                        details=s.get("details")
                    )
                )

            if steps:
                return steps

        except Exception as e:
            logger.warning(f"Fallback in planner due to LLM error: {e}")

        # Deterministic Plan Fallback
        steps = [
            InvestigationStep(id="step_1", label="Assess baseline metrics & distribution", status="completed", phase="Baseline Exploration"),
            InvestigationStep(id="step_2", label="Analyze group performance across categorical dimensions", status="pending", phase="Group Comparative Analysis"),
            InvestigationStep(id="step_3", label="Investigate correlations & secondary factors", status="pending", phase="Correlation & Drivers"),
            InvestigationStep(id="step_4", label="Run statistical hypothesis tests & regression validation", status="pending", phase="Statistical Verification"),
            InvestigationStep(id="step_5", label="Evaluate alternative explanations & synthesize findings", status="pending", phase="Final Synthesis")
        ]
        return steps

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
