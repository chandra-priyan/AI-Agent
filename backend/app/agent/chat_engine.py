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
        """Perform comprehensive, dynamic Pandas computations across all CSV columns."""
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'month' in c.lower() or 'year' in c.lower()]

        q_lower = question.lower()

        # Combine with recent history to resolve follow-up context
        prev_user_text = ""
        for item in reversed(history):
            if item.get("role") == "user" or item.get("sender") == "user":
                prev_user_text = item.get("text", "").lower()
                break

        combined_text = f"{prev_user_text} {q_lower}"

        calculations = [
            f"Dataset Overview: {len(df)} rows across {len(df.columns)} columns ({', '.join(df.columns)})."
        ]

        # 1. Provide complete distinct value listing & value counts for ALL categorical columns
        cat_summaries = []
        for col in cat_cols:
            try:
                val_counts = df[col].dropna().value_counts()
                top_vals = val_counts.head(10)
                tot = len(df)
                val_str = ", ".join([f"{idx}: {cnt} ({cnt/tot*100:.1f}%)" for idx, cnt in top_vals.items()])
                cat_summaries.append(f"Categorical attribute '{col}' values (total unique: {len(val_counts)}): {val_str}")
            except Exception as e_cat:
                logger.debug(f"Categorical summary error for {col}: {e_cat}")

        if cat_summaries:
            calculations.extend(cat_summaries)

        # 2. Total & Summary stats for ALL numerical columns
        num_summaries = []
        for col in num_cols:
            try:
                tot_sum = float(df[col].sum())
                mean_val = float(df[col].mean())
                min_val = float(df[col].min())
                max_val = float(df[col].max())
                num_summaries.append(f"Numerical attribute '{col}': Total Sum = {tot_sum:,.2f}, Average = {mean_val:,.2f}, Min = {min_val:,.2f}, Max = {max_val:,.2f}")
            except Exception as e_num:
                logger.debug(f"Numeric summary error for {col}: {e_num}")

        if num_summaries:
            calculations.extend(num_summaries)

        # 3. Dynamic Group Aggregations (Numerical metric grouped by Categorical attribute)
        for cat in cat_cols[:3]: # Top 3 categorical columns
            for num in num_cols[:2]: # Top 2 numeric columns
                try:
                    grp = df.groupby(cat)[num].agg(['sum', 'mean', 'count']).reset_index()
                    tot_s = grp['sum'].sum()
                    grp['pct'] = (grp['sum'] / tot_s * 100).round(1) if tot_s != 0 else 0
                    grp_sorted = grp.sort_values(by='sum', ascending=False).head(5)
                    b_str = ", ".join([f"{r[cat]}: sum={r['sum']:,.2f} ({r['pct']}%, avg={r['mean']:,.2f})" for _, r in grp_sorted.iterrows()])
                    calculations.append(f"Group Aggregation: '{num}' grouped by '{cat}': {b_str}")
                except Exception as e_grp:
                    logger.debug(f"Group aggregation error: {e_grp}")

        # 4. Keyword & Subgroup Search across all string values in dataset
        matched_filters = []
        words = [w.strip() for w in re.split(r'\W+', combined_text) if len(w.strip()) > 2]
        for col in cat_cols:
            unique_vals = df[col].dropna().astype(str).unique()
            for val in unique_vals:
                val_l = val.lower()
                if any(w in val_l for w in words) or val_l in combined_text:
                    sub_df = df[df[col].astype(str).str.lower() == val_l]
                    if len(sub_df) > 0:
                        pct_rows = (len(sub_df) / len(df)) * 100
                        sub_info = f"Specific Subgroup Match '{val}' in column '{col}': {len(sub_df)} rows ({pct_rows:.1f}% of total)"
                        if num_cols:
                            num_sub = []
                            for num_c in num_cols[:2]:
                                s_sum = float(sub_df[num_c].sum())
                                s_avg = float(sub_df[num_c].mean())
                                num_sub.append(f"{num_c} Total={s_sum:,.2f} (Avg={s_avg:,.2f})")
                            sub_info += f" | {', '.join(num_sub)}"
                        matched_filters.append(sub_info)

        if matched_filters:
            calculations.append("SUBGROUP QUERY MATCHES:")
            calculations.extend(matched_filters[:5])

        # 5. Time Series Trend if date column exists
        if date_cols and num_cols:
            date_col = date_cols[0]
            num_col = num_cols[0]
            try:
                df_sorted = df.copy()
                df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors='coerce')
                df_sorted = df_sorted.dropna(subset=[date_col]).sort_values(by=date_col)
                if len(df_sorted) >= 4:
                    half = len(df_sorted) // 2
                    early_sum = float(df_sorted.iloc[:half][num_col].sum())
                    late_sum = float(df_sorted.iloc[half:][num_col].sum())
                    delta = late_sum - early_sum
                    pct_delta = (delta / early_sum * 100) if early_sum != 0 else 0
                    t_dir = "increased" if delta >= 0 else "decreased"
                    calculations.append(f"Time Series Trend ({num_col} over {date_col}): {t_dir} by {abs(delta):,.2f} ({abs(pct_delta):.1f}%) from early ({early_sum:,.2f}) to late ({late_sum:,.2f}).")
            except Exception as e_dt:
                logger.debug(f"Date trend error: {e_dt}")

        evidence = {
            "row_count": len(df),
            "col_count": len(df.columns),
            "calculations": calculations,
            "summary_text": "\n".join(calculations)
        }
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
