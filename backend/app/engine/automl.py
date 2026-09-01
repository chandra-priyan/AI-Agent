import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from typing import Dict, Any, List


class AutoMLEngine:
    @staticmethod
    def calculate_feature_importance(
        df: pd.DataFrame,
        target_col: str
    ) -> List[Dict[str, Any]]:
        """Calculate feature importances using RandomForest model."""
        if target_col not in df.columns:
            return []

        clean_df = df.dropna().copy()
        if len(clean_df) < 10:
            return []

        # Encode categorical columns
        encoders = {}
        X = clean_df.drop(columns=[target_col])
        y = clean_df[target_col]

        X_processed = pd.DataFrame()
        for col in X.columns:
            if pd.api.types.is_numeric_dtype(X[col]):
                X_processed[col] = X[col]
            else:
                le = LabelEncoder()
                X_processed[col] = le.fit_transform(X[col].astype(str))

        if X_processed.shape[1] == 0:
            return []

        is_numeric_target = pd.api.types.is_numeric_dtype(y)
        if is_numeric_target and y.nunique() > 10:
            model = RandomForestRegressor(n_estimators=50, random_state=42)
        else:
            if not is_numeric_target:
                le_target = LabelEncoder()
                y = le_target.fit_transform(y.astype(str))
            model = RandomForestClassifier(n_estimators=50, random_state=42)

        model.fit(X_processed, y)

        importances = model.feature_importances_
        feature_scores = []
        for feature_name, score in zip(X_processed.columns, importances):
            feature_scores.append({
                "feature": feature_name,
                "importance": float(round(score, 4)),
                "importancePercentage": float(round(score * 100, 2))
            })

        feature_scores.sort(key=lambda x: x["importance"], reverse=True)
        return feature_scores
