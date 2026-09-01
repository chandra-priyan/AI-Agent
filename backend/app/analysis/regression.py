import pandas as pd
import numpy as np
import statsmodels.api as sm
from typing import Dict, Any, List

class RegressionEngine:
    @staticmethod
    def run_regression(
        df: pd.DataFrame,
        target_col: str,
        feature_cols: List[str]
    ) -> Dict[str, Any]:
        """Perform OLS regression and return structured analytical results."""
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset.")

        valid_features = [c for c in feature_cols if c in df.columns]
        if not valid_features:
            raise ValueError("No valid feature columns provided for regression.")

        clean_cols = [target_col] + valid_features
        clean_df = df[clean_cols].dropna()

        if len(clean_df) < len(valid_features) + 2:
            raise ValueError("Insufficient rows for statistical regression modeling.")

        Y = clean_df[target_col]
        X = clean_df[valid_features]
        X_with_const = sm.add_constant(X)

        model = sm.OLS(Y, X_with_const).fit()

        coeffs: Dict[str, float] = {}
        p_vals: Dict[str, float] = {}
        std_errs: Dict[str, float] = {}
        conf_ints: Dict[str, List[float]] = {}

        for param_name in model.params.index:
            coeffs[param_name] = np.round(float(model.params[param_name]), 4)
            p_vals[param_name] = float(model.pvalues[param_name])
            std_errs[param_name] = np.round(float(model.bse[param_name]), 4)
            ci_lower = float(model.conf_int().loc[param_name, 0])
            ci_upper = float(model.conf_int().loc[param_name, 1])
            conf_ints[param_name] = [np.round(ci_lower, 4), np.round(ci_upper, 4)]

        residuals = model.resid

        return {
            "target_column": target_col,
            "feature_columns": valid_features,
            "r_squared": np.round(float(model.rsquared), 4),
            "adjusted_r_squared": np.round(float(model.rsquared_adj), 4),
            "coefficients": coeffs,
            "p_values": p_vals,
            "std_errors": std_errs,
            "confidence_intervals": conf_ints,
            "residual_summary": {
                "mean": np.round(float(residuals.mean()), 4),
                "std": np.round(float(residuals.std()), 4),
                "min": np.round(float(residuals.min()), 4),
                "max": np.round(float(residuals.max()), 4)
            }
        }
