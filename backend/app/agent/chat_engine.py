import logging
import json
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from app.llm.service import LLMService
from app.analysis.loader import CSVLoader
from app.services.persistence_service import PersistenceService
from app.repositories.mongo_repository import MongoRepository

logger = logging.getLogger(__name__)


class AIChatEngine:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    async def process_chat(
        self,
        analysis_id: str,
        user_message: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dataset-grounded AI Chat assistant executing real Pandas calculations."""
        msg_clean = user_message.strip()

        # 1. Out-of-scope question guardrail
        if self._is_out_of_scope(msg_clean):
            return {
                "text": "This question is outside the scope of the current dataset analysis. Ask me a question about the uploaded data.",
                "confidence": "HIGH"
            }

        # 2. Retrieve analysis record & dataset reference
        analysis = None
        if user_id:
            analysis = PersistenceService.get_analysis(analysis_id, user_id=user_id)
        if not analysis:
            analysis = MongoRepository.get_analysis(analysis_id)

        dataset_id = None
        if analysis:
            dataset_id = analysis.get("dataset_id") or analysis.get("datasetId") or analysis_id
        else:
            dataset_id = analysis_id

        # 3. Guardrails for missing dataset / missing analysis
        if not dataset_id:
            return {
                "text": "Please start an analysis before using AI Chat.",
                "confidence": "LOW"
            }

        df = CSVLoader.get_dataset(dataset_id)
        if df is None or df.empty:
            return {
                "text": "Please upload a CSV dataset before asking an analysis question.",
                "confidence": "LOW"
            }

        # 4. Fetch persistent chat history for context awareness
        history = []
        try:
            history = PersistenceService.get_chat_history(analysis_id, user_id=user_id) or []
        except Exception:
            pass

        chat_context_text = self._format_chat_history(history)

        # 5. Execute real Pandas data analysis
        computed_evidence = self._compute_dataset_evidence(df, msg_clean, history, analysis or {})

        # 6. Generate grounded response using LLM
        prompt = self._build_grounded_chat_prompt(
            user_message=msg_clean,
            dataset_name=(analysis.get("filename") if analysis else None) or (analysis.get("datasetName") if analysis else None) or "Uploaded Dataset",
            columns=list(df.columns),
            computed_evidence=computed_evidence,
            existing_conclusion=(analysis.get("conclusion") if analysis else "") or "",
            chat_context=chat_context_text
        )

        try:
            raw_reply = await self.llm.generate(prompt, temperature=0.1)
            formatted_reply = self._format_llm_output(raw_reply, computed_evidence)
            return {
                "text": formatted_reply,
                "confidence": "HIGH"
            }
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            summary = computed_evidence.get("summary_text", "Calculated statistical metrics from dataset.")
            return {
                "text": f"ANSWER\n{summary}\n\nCONFIDENCE\nHigh",
                "confidence": "HIGH"
            }

    def _is_out_of_scope(self, text: str) -> bool:
        t = text.lower().strip()
        out_patterns = [
            r"capital of ", r"who is the president", r"weather in ", r"recipe for",
            r"how to make", r"write a poem", r"tell me a joke", r"who won the",
            r"translate to", r"solve this math", r"meaning of life", r"what is france"
        ]
        if any(re.search(pat, t) for pat in out_patterns):
            data_keywords = ["sales", "data", "row", "column", "dataset", "percent", "revenue", "price", "count", "metric", "region", "product"]
            if not any(k in t for k in data_keywords):
                return True
        return False

    def _format_chat_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "No previous conversation context."
        recent = history[-4:]
        lines = []
        for msg in recent:
            role = "User" if msg.get("role") == "user" or msg.get("sender") == "user" else "Assistant"
            text = msg.get("text") or msg.get("content") or ""
            lines.append(f"{role}: {text}")
        return "\n".join(lines)

    def _compute_dataset_evidence(
        self,
        df: pd.DataFrame,
        question: str,
        history: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform exact Pandas computations based on user query + dataset columns."""
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'month' in c.lower() or 'year' in c.lower()]

        q_lower = question.lower()

        # Combine with recent history to resolve pronouns ("Why?", "What about South region?", etc.)
        prev_user_text = ""
        for item in reversed(history):
            if item.get("role") == "user" or item.get("sender") == "user":
                prev_user_text = item.get("text", "").lower()
                break

        combined_text = f"{prev_user_text} {q_lower}"

        # Determine target metric column
        target_num = None
        for col in num_cols:
            if col.lower() in combined_text:
                target_num = col
                break
        if not target_num:
            metric_synonyms = ["sales", "revenue", "amount", "profit", "price", "cost", "quantity", "val", "score"]
            for syn in metric_synonyms:
                for col in num_cols:
                    if syn in col.lower():
                        target_num = col
                        break
                if target_num:
                    break
        if not target_num and num_cols:
            target_num = num_cols[0]

        # Determine group dimension column
        group_cat = None
        for col in cat_cols:
            if col.lower() in combined_text:
                group_cat = col
                break
        if not group_cat:
            dim_synonyms = ["region", "product", "category", "segment", "country", "state", "store", "customer", "type", "channel"]
            for syn in dim_synonyms:
                for col in cat_cols:
                    if syn in col.lower():
                        group_cat = col
                        break
                if group_cat:
                    break
        if not group_cat and cat_cols:
            group_cat = cat_cols[0]

        evidence: Dict[str, Any] = {
            "target_metric": target_num,
            "group_dimension": group_cat,
            "row_count": len(df),
            "calculations": []
        }

        # 1. Total & Summary stats for target metric
        if target_num and target_num in df.columns:
            tot_sum = float(df[target_num].sum())
            mean_val = float(df[target_num].mean())
            min_val = float(df[target_num].min())
            max_val = float(df[target_num].max())

            evidence["metric_summary"] = {
                "metric": target_num,
                "total_sum": round(tot_sum, 2),
                "mean": round(mean_val, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2)
            }
            evidence["calculations"].append(f"Total {target_num}: {tot_sum:,.2f}, Average: {mean_val:,.2f}, Range: [{min_val:,.2f} to {max_val:,.2f}]")

        # 2. Categorical Group Aggregation & Ranking
        if group_cat and target_num and group_cat in df.columns and target_num in df.columns:
            grp = df.groupby(group_cat)[target_num].agg(['sum', 'mean', 'count']).reset_index()
            total_sum = grp['sum'].sum()
            grp['percentage'] = (grp['sum'] / total_sum * 100).round(2) if total_sum != 0 else 0
            grp_sorted = grp.sort_values(by='sum', ascending=False)

            top_row = grp_sorted.iloc[0]
            bottom_row = grp_sorted.iloc[-1]

            evidence["group_ranking"] = {
                "dimension": group_cat,
                "top_performer": {
                    "category": str(top_row[group_cat]),
                    "sum": round(float(top_row['sum']), 2),
                    "percentage": float(top_row['percentage'])
                },
                "lowest_performer": {
                    "category": str(bottom_row[group_cat]),
                    "sum": round(float(bottom_row['sum']), 2),
                    "percentage": float(bottom_row['percentage'])
                },
                "breakdown": [
                    {
                        "category": str(row[group_cat]),
                        "sum": round(float(row['sum']), 2),
                        "mean": round(float(row['mean']), 2),
                        "percentage": float(row['percentage'])
                    }
                    for _, row in grp_sorted.head(10).iterrows()
                ]
            }

            breakdown_str = ", ".join([f"{r['category']}: {r['sum']:,.2f} ({r['percentage']}%)" for r in evidence["group_ranking"]["breakdown"][:5]])
            evidence["calculations"].append(f"Breakdown of {target_num} by {group_cat}: {breakdown_str}")

        # 3. Check for specific filtering (e.g. "South region", "East vs West")
        if group_cat and group_cat in df.columns:
            unique_vals = df[group_cat].dropna().astype(str).unique()
            matched_vals = [val for val in unique_vals if val.lower() in q_lower]
            if matched_vals:
                filter_evidence = []
                for val in matched_vals:
                    sub_df = df[df[group_cat].astype(str).str.lower() == val.lower()]
                    if target_num and target_num in sub_df.columns:
                        sub_sum = float(sub_df[target_num].sum())
                        sub_mean = float(sub_df[target_num].mean())
                        sub_pct = (sub_sum / evidence["metric_summary"]["total_sum"] * 100) if evidence.get("metric_summary", {}).get("total_sum") else 0
                        filter_evidence.append(f"Segment '{val}': Total {target_num} = {sub_sum:,.2f} ({sub_pct:.1f}% of overall), Average = {sub_mean:,.2f}, Rows = {len(sub_df)}")
                evidence["specific_filter"] = filter_evidence
                evidence["calculations"].extend(filter_evidence)

        # 4. Period-over-Period / Time Series Trend Analysis if Date Column exists
        if date_cols and target_num:
            date_col = date_cols[0]
            try:
                df_sorted = df.copy()
                df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors='coerce')
                df_sorted = df_sorted.dropna(subset=[date_col]).sort_values(by=date_col)
                if len(df_sorted) >= 4:
                    half = len(df_sorted) // 2
                    early_sum = float(df_sorted.iloc[:half][target_num].sum())
                    late_sum = float(df_sorted.iloc[half:][target_num].sum())
                    delta = late_sum - early_sum
                    pct_delta = (delta / early_sum * 100) if early_sum != 0 else 0

                    evidence["period_trend"] = {
                        "early_period_sum": round(early_sum, 2),
                        "late_period_sum": round(late_sum, 2),
                        "delta": round(delta, 2),
                        "pct_delta": round(pct_delta, 2)
                    }
                    trend_dir = "increased" if delta >= 0 else "decreased"
                    evidence["calculations"].append(
                        f"Time series trend for {target_num}: {trend_dir} by {abs(delta):,.2f} ({abs(pct_delta):.1f}%) from early period ({early_sum:,.2f}) to late period ({late_sum:,.2f})."
                    )
            except Exception as e_date:
                logger.debug(f"Date parsing skipped in chat engine: {e_date}")

        # 5. Numerical Correlations
        if len(num_cols) > 1:
            try:
                corr_matrix = df[num_cols].corr()
                top_corrs = []
                for i in range(len(num_cols)):
                    for j in range(i+1, len(num_cols)):
                        c1, c2 = num_cols[i], num_cols[j]
                        val = float(corr_matrix.loc[c1, c2])
                        if not np.isnan(val) and abs(val) > 0.2:
                            top_corrs.append(f"Correlation ({c1} vs {c2}) = {val:+.2f}")
                if top_corrs:
                    evidence["correlations"] = top_corrs[:4]
                    evidence["calculations"].append("Key correlations: " + "; ".join(top_corrs[:4]))
            except Exception as e_corr:
                logger.debug(f"Correlation calculation skipped: {e_corr}")

        evidence["summary_text"] = "\n".join(evidence["calculations"])
        return evidence

    def _build_grounded_chat_prompt(
        self,
        user_message: str,
        dataset_name: str,
        columns: List[str],
        computed_evidence: Dict[str, Any],
        existing_conclusion: str,
        chat_context: str
    ) -> str:
        calc_str = computed_evidence.get("summary_text") or "Dataset loaded successfully."

        return f"""
You are an expert Autonomous Data Scientist Agent. Answer the user's question using ONLY the provided real Pandas calculation evidence from the uploaded dataset.

CRITICAL RULES:
1. Every number, percentage, delta, and ranking MUST come directly from the CALCULATED EVIDENCE below.
2. NEVER invent fake numbers, dates, percentages, or hypothetical facts.
3. Be concise, direct, professional, and data-grounded.
4. Do NOT give generic ChatGPT advice ("Sales can decrease due to many factors..."). State what the data actually shows.

DATASET CONTEXT:
- File: {dataset_name}
- Columns: {', '.join(columns)}
- Prior Investigation Conclusion: {existing_conclusion or 'None'}

CONVERSATION HISTORY:
{chat_context}

CALCULATED PANDAS EVIDENCE FROM CSV DATASET:
{calc_str}

USER QUESTION:
"{user_message}"

RESPONSE FORMAT (Use exact header titles if relevant):

ANSWER
[Direct, precise answer to the user question using exact numbers.]

EVIDENCE
[Specific calculated metrics, totals, percentages, or group breakdowns.]

ANALYSIS
[Short 1-2 sentence explanation of how the evidence supports the conclusion.]

CONFIDENCE
High
"""

    def _format_llm_output(self, raw_text: str, computed_evidence: Dict[str, Any]) -> str:
        text = raw_text.strip()
        # Clean markdown code blocks if wrapped
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Ensure Confidence line is present
        if "CONFIDENCE" not in text:
            text += "\n\nCONFIDENCE\nHigh"

        return text
