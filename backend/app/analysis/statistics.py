import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List, Optional

class StatisticalTestEngine:
    @staticmethod
    def run_test(
        df: pd.DataFrame,
        test_type: str,
        group_col: Optional[str] = None,
        val_col: Optional[str] = None,
        cat_col1: Optional[str] = None,
        cat_col2: Optional[str] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Perform statistical hypothesis testing using SciPy."""
        test_clean = test_type.lower()

        if test_clean in ["ttest", "ttest_ind", "t_test"]:
            return StatisticalTestEngine._run_ttest(df, group_col, val_col, confidence_level)
        elif test_clean in ["anova", "f_test"]:
            return StatisticalTestEngine._run_anova(df, group_col, val_col, confidence_level)
        elif test_clean in ["chi2", "chi_square", "chisq"]:
            return StatisticalTestEngine._run_chi2(df, cat_col1, cat_col2, confidence_level)
        elif test_clean in ["ci", "confidence_interval"]:
            return StatisticalTestEngine._run_confidence_interval(df, val_col, confidence_level)
        else:
            raise ValueError(f"Unsupported statistical test type '{test_type}'. Supported: ttest_ind, anova, chi2, confidence_interval.")

    @staticmethod
    def _run_ttest(df: pd.DataFrame, group_col: Optional[str], val_col: Optional[str], alpha_level: float) -> Dict[str, Any]:
        cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns
        num_cols = df.select_dtypes(include=[np.number]).columns

        if not group_col:
            two_val_cats = [c for c in cat_cols if df[c].nunique(dropna=True) == 2]
            if two_val_cats:
                group_col = two_val_cats[0]
            elif len(cat_cols) > 0:
                group_col = list(cat_cols)[0]

        if not group_col or group_col not in df.columns:
            raise ValueError("T-test requires a grouping column with 2 distinct groups.")

        if not val_col:
            if len(num_cols) > 0:
                val_col = list(num_cols)[0]

        if not val_col or val_col not in df.columns:
            raise ValueError("T-test requires a numerical value column.")

        clean_df = df.dropna(subset=[group_col, val_col])
        groups = clean_df[group_col].unique()

        if len(groups) < 2:
            raise ValueError(f"Column '{group_col}' has fewer than 2 distinct non-null groups.")

        g1_data = clean_df[clean_df[group_col] == groups[0]][val_col]
        g2_data = clean_df[clean_df[group_col] == groups[1]][val_col]

        stat, p_val = stats.ttest_ind(g1_data, g2_data, equal_var=False)
        alpha = 1.0 - alpha_level
        is_sig = bool(p_val < alpha)

        summary = f"Independent t-test between '{groups[0]}' (mean={g1_data.mean():.2f}) and '{groups[1]}' (mean={g2_data.mean():.2f}) on '{val_col}'."
        if is_sig:
            summary += f" The difference is statistically SIGNIFICANT (p = {p_val:.4f} < {alpha:.2f})."
        else:
            summary += f" The difference is NOT statistically significant (p = {p_val:.4f} >= {alpha:.2f})."

        return {
            "test_name": "Two-Sample Independent T-Test (Welch's)",
            "statistic": np.round(float(stat), 4),
            "p_value": float(p_val),
            "is_significant": is_sig,
            "confidence_level": alpha_level,
            "summary": summary,
            "details": {
                "group_column": group_col,
                "value_column": val_col,
                "group1": str(groups[0]),
                "group1_mean": np.round(float(g1_data.mean()), 4),
                "group1_n": int(len(g1_data)),
                "group2": str(groups[1]),
                "group2_mean": np.round(float(g2_data.mean()), 4),
                "group2_n": int(len(g2_data))
            }
        }

    @staticmethod
    def _run_anova(df: pd.DataFrame, group_col: Optional[str], val_col: Optional[str], alpha_level: float) -> Dict[str, Any]:
        cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns
        num_cols = df.select_dtypes(include=[np.number]).columns

        if not group_col:
            multi_cats = [c for c in cat_cols if 2 <= df[c].nunique(dropna=True) <= 15]
            if multi_cats:
                group_col = multi_cats[0]

        if not group_col or group_col not in df.columns:
            raise ValueError("ANOVA requires a categorical grouping column.")

        if not val_col:
            if len(num_cols) > 0:
                val_col = list(num_cols)[0]

        if not val_col or val_col not in df.columns:
            raise ValueError("ANOVA requires a numerical value column.")

        clean_df = df.dropna(subset=[group_col, val_col])
        groups = clean_df[group_col].unique()

        if len(groups) < 2:
            raise ValueError("ANOVA requires at least 2 distinct groups.")

        group_series_list = [clean_df[clean_df[group_col] == g][val_col] for g in groups]
        stat, p_val = stats.f_oneway(*group_series_list)

        alpha = 1.0 - alpha_level
        is_sig = bool(p_val < alpha)

        summary = f"One-Way ANOVA across {len(groups)} groups of '{group_col}' for metric '{val_col}'."
        if is_sig:
            summary += f" Significant variation exists across groups (F = {stat:.2f}, p = {p_val:.4f})."
        else:
            summary += f" No significant variation detected across groups (F = {stat:.2f}, p = {p_val:.4f})."

        return {
            "test_name": "One-Way ANOVA",
            "statistic": np.round(float(stat), 4),
            "p_value": float(p_val),
            "is_significant": is_sig,
            "confidence_level": alpha_level,
            "summary": summary,
            "details": {
                "group_column": group_col,
                "value_column": val_col,
                "group_count": len(groups)
            }
        }

    @staticmethod
    def _run_chi2(df: pd.DataFrame, cat_col1: Optional[str], cat_col2: Optional[str], alpha_level: float) -> Dict[str, Any]:
        cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns

        if not cat_col1 or not cat_col2:
            if len(cat_cols) >= 2:
                cat_col1, cat_col2 = cat_cols[0], cat_cols[1]

        if not cat_col1 or not cat_col2 or cat_col1 not in df.columns or cat_col2 not in df.columns:
            raise ValueError("Chi-Square test requires two valid categorical columns.")

        contingency_tab = pd.crosstab(df[cat_col1], df[cat_col2])
        stat, p_val, dof, _ = stats.chi2_contingency(contingency_tab)

        alpha = 1.0 - alpha_level
        is_sig = bool(p_val < alpha)

        summary = f"Chi-Square Test of Independence between '{cat_col1}' and '{cat_col2}'."
        if is_sig:
            summary += f" The variables are SIGNIFICANTLY associated (Chi2 = {stat:.2f}, p = {p_val:.4f})."
        else:
            summary += f" No significant association detected (Chi2 = {stat:.2f}, p = {p_val:.4f})."

        return {
            "test_name": "Chi-Square Test of Independence",
            "statistic": np.round(float(stat), 4),
            "p_value": float(p_val),
            "is_significant": is_sig,
            "confidence_level": alpha_level,
            "summary": summary,
            "details": {
                "categorical_col1": cat_col1,
                "categorical_col2": cat_col2,
                "degrees_of_freedom": int(dof)
            }
        }

    @staticmethod
    def _run_confidence_interval(df: pd.DataFrame, val_col: Optional[str], confidence_level: float) -> Dict[str, Any]:
        num_cols = df.select_dtypes(include=[np.number]).columns
        if not val_col:
            if len(num_cols) > 0:
                val_col = list(num_cols)[0]

        if not val_col or val_col not in df.columns:
            raise ValueError("Confidence interval calculation requires a numerical column.")

        series = df[val_col].dropna()
        n = len(series)
        if n < 2:
            raise ValueError("Insufficient data to compute confidence interval.")

        mean_val = float(series.mean())
        sem = stats.sem(series)
        ci = stats.t.interval(confidence_level, df=n - 1, loc=mean_val, scale=sem)

        summary = f"{int(confidence_level*100)}% Confidence Interval for mean of '{val_col}': [{ci[0]:.4f}, {ci[1]:.4f}] (mean = {mean_val:.4f})."

        return {
            "test_name": f"{int(confidence_level*100)}% Confidence Interval for Mean",
            "statistic": np.round(mean_val, 4),
            "p_value": 0.0,
            "is_significant": True,
            "confidence_level": confidence_level,
            "summary": summary,
            "details": {
                "value_column": val_col,
                "sample_size": n,
                "sample_mean": np.round(mean_val, 4),
                "lower_bound": np.round(float(ci[0]), 4),
                "upper_bound": np.round(float(ci[1]), 4)
            }
        }
