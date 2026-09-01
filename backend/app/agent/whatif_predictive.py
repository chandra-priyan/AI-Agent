import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from sklearn.linear_model import LinearRegression

class WhatIfPredictiveEngine:
    """Provides controlled what-if scenario simulations and machine learning predictive analysis."""

    @staticmethod
    def run_what_if_simulation(
        df: pd.DataFrame,
        metric: str,
        percentage_change: float
    ) -> Dict[str, Any]:
        """Simulates metric change (e.g. churn decreases by 10%) and estimates bottom-line impact."""
        if metric not in df.columns or not pd.api.types.is_numeric_dtype(df[metric]):
            return {
                "status": "error",
                "message": f"Metric '{metric}' not found or not numeric for simulation."
            }

        current_val = float(df[metric].sum())
        simulated_val = current_val * (1.0 + (percentage_change / 100.0))
        absolute_delta = simulated_val - current_val

        return {
            "type": "WHAT_IF_SIMULATION",
            "metric": metric,
            "simulated_change_pct": percentage_change,
            "baseline_value": round(current_val, 2),
            "simulated_value": round(simulated_val, 2),
            "estimated_impact": round(absolute_delta, 2),
            "disclaimer": "Simulated estimates are scenario models, not historical observed facts."
        }

    @staticmethod
    def run_predictive_analysis(
        df: pd.DataFrame,
        target_column: str,
        feature_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Trains linear regression predictive model and forecasts target values."""
        clean_df = df.dropna()
        if target_column not in clean_df.columns or not pd.api.types.is_numeric_dtype(clean_df[target_column]):
            return {"status": "error", "message": f"Target column '{target_column}' is not suitable for prediction."}

        feats = feature_columns or [c for c in clean_df.columns if c != target_column and pd.api.types.is_numeric_dtype(clean_df[c])]
        if not feats:
            return {"status": "error", "message": "No numeric feature columns available for predictive model."}

        X = clean_df[feats]
        y = clean_df[target_column]

        model = LinearRegression()
        model.fit(X, y)

        r2 = float(model.score(X, y))
        preds = model.predict(X)
        mean_forecast = float(np.mean(preds))

        return {
            "type": "PREDICTIVE_ANALYSIS",
            "target_column": target_column,
            "features_used": feats,
            "model_r2_score": round(r2, 4),
            "forecasted_mean": round(mean_forecast, 2),
            "coefficients": {feat: round(float(coef), 4) for feat, coef in zip(feats, model.coef_)},
            "disclaimer": "Predictions are statistical forecasts based on linear modeling assumptions."
        }
