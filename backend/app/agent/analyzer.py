import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from app.llm.service import LLMService
from app.services.analysis_service import AnalysisService
from app.agent.state import Hypothesis, EvidenceItem, AnalysisExecution, InvestigationGoal
from app.agent.prompts import ANALYSIS_SELECTOR_PROMPT

logger = logging.getLogger(__name__)

class AgentAnalyzer:
    def __init__(
        self,
        analysis_service: Optional[AnalysisService] = None,
        llm_service: Optional[LLMService] = None
    ):
        self.analysis_service = analysis_service or AnalysisService()
        self.llm = llm_service or LLMService()

    async def select_and_execute_analysis(
        self,
        analysis_id: str,
        dataset_id: str,
        question: str,
        goal: InvestigationGoal,
        dataset_profile: Dict[str, Any],
        hypotheses: List[Hypothesis],
        executed_analyses: List[AnalysisExecution]
    ) -> Tuple[AnalysisExecution, EvidenceItem]:
        """Selects the next optimal analysis capability and executes it via AnalysisService."""
        num_cols = dataset_profile.get("numerical_columns", [])
        cat_cols = dataset_profile.get("categorical_columns", [])
        date_col = goal.date_column or dataset_profile.get("date_column")
        target_metric = goal.target_metric or (num_cols[0] if num_cols else None)

        executed_summary = [
            {"type": a.analysis_type, "params": a.parameters} for a in executed_analyses
        ]

        prompt = ANALYSIS_SELECTOR_PROMPT.format(
            question=question,
            target_metric=target_metric or "N/A",
            numerical_cols=json.dumps(num_cols),
            categorical_cols=json.dumps(cat_cols),
            date_col=date_col or "None",
            hypotheses_json=json.dumps([h.model_dump() for h in hypotheses]),
            executed_summary_json=json.dumps(executed_summary)
        )

        selected_type = "group_analysis"
        parameters: Dict[str, Any] = {}

        try:
            raw_response = await self.llm.generate(prompt, temperature=0.1)
            parsed = self._extract_json(raw_response)
            selected_type = parsed.get("analysis_type", "group_analysis")
            parameters = parsed.get("parameters", {})
        except Exception as e:
            logger.warning(f"Fallback in analysis selection due to LLM error: {e}")

        # Validate and apply fallbacks to ensure executable parameters
        selected_type, parameters = self._sanitize_analysis_params(
            selected_type, parameters, num_cols, cat_cols, date_col, target_metric, executed_summary
        )

        # Execute via Python Analysis Engine
        result = await self._run_python_engine(dataset_id, selected_type, parameters)

        execution = AnalysisExecution(
            id=str(uuid.uuid4())[:8],
            analysis_type=selected_type,
            parameters=parameters,
            result=result,
            executed_at=str(uuid.uuid4())
        )

        evidence = self._convert_to_evidence(selected_type, parameters, result, dataset_id)
        return execution, evidence

    def _sanitize_analysis_params(
        self,
        selected_type: str,
        params: Dict[str, Any],
        num_cols: List[str],
        cat_cols: List[str],
        date_col: Optional[str],
        target_metric: Optional[str],
        executed_summary: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, Any]]:
        """Sanitizes requested analysis type and parameters against actual schema."""

        # Group Analysis
        if selected_type == "group_analysis":
            group_col = params.get("group_by_col") or params.get("group_by") or (cat_cols[0] if cat_cols else None)
            target = params.get("target_col") or params.get("metric") or target_metric or (num_cols[0] if num_cols else None)

            if group_col and target:
                return "group_analysis", {"group_by_col": group_col, "target_col": target, "agg_func": "mean"}

        # Trend Analysis
        if selected_type == "trend_analysis" and date_col and num_cols:
            val_col = params.get("value_col") or params.get("metric") or target_metric or num_cols[0]
            return "trend_analysis", {"date_col": date_col, "value_col": val_col, "freq": "M"}

        # Correlation Analysis
        if selected_type == "correlation_analysis" and len(num_cols) >= 2:
            return "correlation_analysis", {"method": "pearson"}

        # Statistical Test
        if selected_type == "statistical_test" and cat_cols and num_cols:
            group_col = params.get("group_col") or cat_cols[0]
            val_col = params.get("val_col") or target_metric or num_cols[0]
            return "statistical_test", {
                "test_type": "anova" if len(cat_cols) > 0 else "ttest_ind",
                "group_col": group_col,
                "val_col": val_col
            }

        # Regression Analysis
        if selected_type == "regression" and target_metric and len(num_cols) >= 2:
            features = [c for c in num_cols if c != target_metric][:4]
            if features:
                return "regression", {"target_col": target_metric, "feature_cols": features}

        # Ultimate fallback: Group analysis if categorical columns exist, else descriptive
        if cat_cols and num_cols:
            return "group_analysis", {"group_by_col": cat_cols[0], "target_col": num_cols[0], "agg_func": "mean"}
        elif num_cols:
            return "descriptive_analysis", {"val_col": num_cols[0]}
        else:
            return "descriptive_analysis", {"val_col": cat_cols[0] if cat_cols else "index"}

    async def _run_python_engine(
        self,
        dataset_id: str,
        analysis_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calls backend AnalysisService engine methods."""
        try:
            if analysis_type == "group_analysis":
                res = await self.analysis_service.run_group_analysis(
                    dataset_id=dataset_id,
                    group_by_col=params["group_by_col"],
                    target_col=params["target_col"],
                    agg_func=params.get("agg_func", "mean")
                )
                return res.model_dump()

            elif analysis_type == "trend_analysis":
                res = await self.analysis_service.run_trend_analysis(
                    dataset_id=dataset_id,
                    date_col=params["date_col"],
                    value_col=params["value_col"],
                    freq=params.get("freq", "M")
                )
                return res.model_dump()

            elif analysis_type == "correlation_analysis":
                res = await self.analysis_service.run_correlation_analysis(
                    dataset_id=dataset_id,
                    method=params.get("method", "pearson")
                )
                return res.model_dump()

            elif analysis_type == "statistical_test":
                res = await self.analysis_service.run_statistical_test(
                    dataset_id=dataset_id,
                    test_type=params.get("test_type", "anova"),
                    group_col=params.get("group_col"),
                    val_col=params.get("val_col"),
                    cat_col1=params.get("cat_col1"),
                    cat_col2=params.get("cat_col2")
                )
                return res.model_dump()

            elif analysis_type == "regression":
                res = await self.analysis_service.run_regression_analysis(
                    dataset_id=dataset_id,
                    target_col=params["target_col"],
                    feature_cols=params["feature_cols"]
                )
                return res.model_dump()

            else:
                res = await self.analysis_service.run_descriptive_analysis(
                    dataset_id=dataset_id,
                    columns=[params.get("val_col")] if params.get("val_col") else None
                )
                return res.model_dump()

        except Exception as e:
            logger.error(f"Error executing Python analysis ({analysis_type}): {e}")
            return {"error": str(e), "analysis_type": analysis_type}

    def _convert_to_evidence(
        self,
        analysis_type: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        dataset_id: Optional[str] = None
    ) -> EvidenceItem:
        """Converts raw Python engine output to structured EvidenceItem."""
        evidence_id = str(uuid.uuid4())[:8]

        if analysis_type == "group_analysis":
            groups = result.get("groups", [])
            chart_data = [
                {"group": g.get("group") or g.get("group_value"), "value": g.get("mean", g.get("count", 0))}
                for g in groups
            ]
            group_col = params.get("group_by_col")
            target_col = params.get("target_col")
            return EvidenceItem(
                id=evidence_id,
                title=f"Group Comparison: '{target_col}' by '{group_col}'",
                chart_type="bar",
                data=chart_data,
                explanation=result.get("summary", f"Aggregated {target_col} across {group_col} groups."),
                metric=target_col,
                dimension=group_col
            )

        elif analysis_type == "trend_analysis":
            periods = result.get("trends") or result.get("periods") or []
            chart_data = [
                {"period": p.get("period"), "value": p.get("value")} for p in periods
            ]
            date_col = params.get("date_col")
            val_col = params.get("value_col")
            return EvidenceItem(
                id=evidence_id,
                title=f"Time-Series Trend: '{val_col}' over '{date_col}'",
                chart_type="line",
                data=chart_data,
                explanation=result.get("summary", f"Tracked {val_col} trend over time."),
                metric=val_col,
                dimension=date_col
            )

        elif analysis_type == "correlation_analysis":
            strong_pairs = result.get("strong_pairs", [])
            chart_data = [
                {"pair": f"{p['col1']} vs {p['col2']}", "correlation": p["correlation"]}
                for p in strong_pairs
            ]
            return EvidenceItem(
                id=evidence_id,
                title="Numerical Correlation Matrix & Key Drivers",
                chart_type="bar",
                data=chart_data,
                explanation=result.get("summary", "Identified numerical correlation pairs."),
                metric="correlation"
            )

        elif analysis_type == "statistical_test":
            p_val = result.get("p_value")
            is_sig = result.get("is_statistically_significant", False)
            chart_data = []

            # Populate group comparison values for drawing a chart representing the test
            details = result.get("details", {})
            group_col = details.get("group_column") or params.get("group_col") or params.get("group_by_col")
            val_col = details.get("value_column") or params.get("val_col") or params.get("target_col")

            if group_col and val_col and dataset_id:
                try:
                    import pandas as pd
                    from app.analysis.loader import CSVLoader
                    df = CSVLoader.get_dataset(dataset_id)
                    
                    # Handle high cardinality
                    is_numeric_group = pd.api.types.is_numeric_dtype(df[group_col])
                    num_unique = df[group_col].nunique(dropna=True)
                    if num_unique > 15:
                        df = df.copy()
                        if is_numeric_group:
                            non_nan_mask = df[group_col].notna()
                            if non_nan_mask.sum() > 0:
                                num_bins = min(8, df[group_col].nunique())
                                binned = pd.qcut(df[group_col][non_nan_mask], q=num_bins, duplicates='drop')
                                labels = []
                                for interval in binned:
                                    left = round(float(interval.left), 2)
                                    right = round(float(interval.right), 2)
                                    def format_val(v):
                                        if abs(v) >= 1_000_000:
                                            return f"{v/1_000_000:.1f}M"
                                        elif abs(v) >= 1_000:
                                            return f"{v/1_000:.1f}K"
                                        return str(v)
                                    labels.append(f"{format_val(left)}-{format_val(right)}")
                                df.loc[non_nan_mask, f"{group_col}_binned"] = labels
                                df.loc[~non_nan_mask, f"{group_col}_binned"] = "Missing"
                                group_col = f"{group_col}_binned"
                            else:
                                df[group_col] = "Missing"
                        else:
                            top_cats = df[group_col].value_counts().index[:10]
                            df[group_col] = df[group_col].apply(lambda x: str(x) if x in top_cats else "Other")

                    means = df.groupby(group_col, dropna=False)[val_col].mean().dropna().reset_index()
                    chart_data = [
                        {"group": str(row[group_col]), "value": float(round(row[val_col], 4))}
                        for _, row in means.iterrows()
                    ]
                except Exception as e:
                    logger.warning(f"Could not construct chart data for statistical test: {e}")

            return EvidenceItem(
                id=evidence_id,
                title=f"Hypothesis Test: {result.get('test_name', 'Statistical Test')}",
                chart_type="bar",
                data=chart_data,
                explanation=result.get("summary", "Ran statistical test."),
                p_value=p_val,
                is_statistically_significant=is_sig
            )

        elif analysis_type == "regression":
            coefs = result.get("coefficients", {})
            chart_data = [
                {"feature": k, "coefficient": v} for k, v in coefs.items() if k != "const"
            ]
            return EvidenceItem(
                id=evidence_id,
                title=f"OLS Regression Model (R² = {result.get('r_squared', 0)})",
                chart_type="bar",
                data=chart_data,
                explanation=result.get("summary", "Fitted linear regression model."),
                metric=params.get("target_col")
            )

        else:
            return EvidenceItem(
                id=evidence_id,
                title="Descriptive Statistics Summary",
                chart_type="bar",
                data=[],
                explanation="Calculated baseline descriptive metrics."
            )

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
