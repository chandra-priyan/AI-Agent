import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class CorrelationAnalysisEngine:
    @staticmethod
    def calculate_correlations(
        df: pd.DataFrame,
        method: str = "pearson",
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Calculate pairwise correlation with strength rating and strict non-causal disclaimer."""
        num_cols = df.select_dtypes(include=[np.number]).columns
        
        if columns:
            num_cols = [c for c in columns if c in num_cols]

        if len(num_cols) < 2:
            return []

        clean_df = df[num_cols].dropna()
        if len(clean_df) < 3:
            return []

        method_clean = method.lower()
        if method_clean not in ["pearson", "spearman"]:
            method_clean = "pearson"

        corr_matrix = clean_df.corr(method=method_clean)

        pairs: List[Dict[str, Any]] = []
        cols = list(corr_matrix.columns)

        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                var_a = cols[i]
                var_b = cols[j]
                r_val = float(corr_matrix.iloc[i, j])

                if np.isnan(r_val):
                    continue

                abs_r = abs(r_val)
                if abs_r >= 0.7:
                    strength = "strong"
                elif abs_r >= 0.4:
                    strength = "moderate"
                else:
                    strength = "weak"

                pairs.append({
                    "variable_a": var_a,
                    "variable_b": var_b,
                    "method": method_clean,
                    "correlation": np.round(r_val, 4),
                    "strength": strength,
                    "disclaimer": "Correlation does NOT imply causation. Additional domain or experimental validation is required."
                })

        # Sort by absolute correlation strength descending
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return pairs
