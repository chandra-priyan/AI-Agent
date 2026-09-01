import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class DescriptiveAnalysisEngine:
    @staticmethod
    def calculate_descriptive_stats(df: pd.DataFrame, target_column: Optional[str] = None) -> List[Dict[str, Any]]:
        """Calculate structured descriptive metrics (count, mean, std, min, max, percentiles, % change)."""
        num_cols = df.select_dtypes(include=[np.number]).columns
        if target_column:
            if target_column not in df.columns:
                raise ValueError(f"Column '{target_column}' not found in dataset.")
            if target_column in num_cols:
                num_cols = [target_column]
            else:
                num_cols = []

        results: List[Dict[str, Any]] = []

        for col in num_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            count_val = int(len(series))
            mean_val = float(series.mean())
            std_val = float(series.std()) if count_val > 1 else 0.0
            min_val = float(series.min())
            q25 = float(series.quantile(0.25))
            med_val = float(series.median())
            q75 = float(series.quantile(0.75))
            max_val = float(series.max())

            pct_change_mean_med = None
            if med_val != 0:
                pct_change_mean_med = float((mean_val - med_val) / abs(med_val))

            results.append({
                "metric": col,
                "count": count_val,
                "mean": np.round(mean_val, 4),
                "std": np.round(std_val, 4),
                "min": np.round(min_val, 4),
                "q25": np.round(q25, 4),
                "median": np.round(med_val, 4),
                "q75": np.round(q75, 4),
                "max": np.round(max_val, 4),
                "pct_change_mean_median": np.round(pct_change_mean_med, 4) if pct_change_mean_med is not None else None
            })

        return results
