import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List


class HypothesisEngine:
    @staticmethod
    def test_group_difference(
        df: pd.DataFrame,
        group_col: str,
        value_col: str
    ) -> Dict[str, Any]:
        """Perform statistical test comparing value distribution across groups."""
        if group_col not in df.columns or value_col not in df.columns:
            return {"isSignificant": False, "pvalue": 1.0, "details": "Columns not found"}

        clean_df = df[[group_col, value_col]].dropna()
        groups = [group[value_col].values for _, group in clean_df.groupby(group_col)]

        if len(groups) < 2:
            return {"isSignificant": False, "pvalue": 1.0, "details": "Insufficient group categories"}

        if len(groups) == 2:
            # Two-sample t-test / Mann-Whitney
            stat_val, p_val = stats.ttest_ind(groups[0], groups[1], equal_var=False)
            test_type = "Welch's T-Test"
        else:
            # One-way ANOVA
            stat_val, p_val = stats.f_oneway(*groups)
            test_type = "One-Way ANOVA"

        # Calculate group means & relative variance
        group_means = clean_df.groupby(group_col)[value_col].agg(["mean", "count"]).round(2).to_dict(orient="index")

        is_sig = bool(p_val < 0.05)
        return {
            "testType": test_type,
            "statistic": float(round(stat_val, 4)) if not np.isnan(stat_val) else 0.0,
            "pvalue": float(round(p_val, 6)) if not np.isnan(p_val) else 1.0,
            "isSignificant": is_sig,
            "confidenceLevel": "HIGH" if p_val < 0.01 else ("MEDIUM" if p_val < 0.05 else "LOW"),
            "groupMeans": group_means,
            "details": f"{test_type} p-value: {round(p_val, 6)} ({'Statistically significant' if is_sig else 'Not significant'})."
        }

    @staticmethod
    def evaluate_business_question(
        df: pd.DataFrame,
        question: str
    ) -> List[Dict[str, Any]]:
        """Automatically identify key grouping variables and run statistical tests."""
        results = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        if not numeric_cols or not categorical_cols:
            return results

        target_num = numeric_cols[0]  # Primary numeric target (e.g. Sales, Valuation, Churn score)

        for cat_col in categorical_cols[:3]:  # Top categorical candidates
            if df[cat_col].nunique() <= 10:
                test_res = HypothesisEngine.test_group_difference(df, cat_col, target_num)
                results.append({
                    "groupingFeature": cat_col,
                    "targetMetric": target_num,
                    **test_res
                })

        return results
