import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

class RootCauseEngine:
    """Executes progressive hierarchical narrowing: Segment -> Dimension -> Sub-Segment -> Key Driver."""

    @staticmethod
    def discover_segments(df: pd.DataFrame) -> List[str]:
        """Identifies categorical and discrete dimensions suitable for segment analysis."""
        valid_dims = []
        for col in df.columns:
            if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                num_unique = df[col].nunique()
                if 2 <= num_unique <= 20:
                    valid_dims.append(col)
            elif pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() <= 10:
                valid_dims.append(col)
        return valid_dims

    @staticmethod
    def evaluate_root_cause_hierarchy(
        df: pd.DataFrame,
        target_metric: str,
        possible_dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Progressively drills down across dimensions to find the primary driver of metric variance."""
        if target_metric not in df.columns or not pd.api.types.is_numeric_dtype(df[target_metric]):
            return {"status": "error", "message": f"Target metric '{target_metric}' is not numeric or not found."}

        dims = possible_dimensions or RootCauseEngine.discover_segments(df)
        if not dims:
            return {"status": "insufficient_dimensions", "message": "No categorical dimensions found for drill-down."}

        hierarchy_steps = []
        total_target_val = df[target_metric].sum()

        for dim in dims:
            grouped = df.groupby(dim)[target_metric].agg(['sum', 'mean', 'count']).reset_index()
            grouped['contribution_pct'] = (grouped['sum'] / total_target_val) * 100
            sorted_groups = grouped.sort_values(by='sum', ascending=False)
            
            top_row = sorted_groups.iloc[0]
            hierarchy_steps.append({
                "dimension": dim,
                "top_segment": str(top_row[dim]),
                "segment_sum": float(top_row['sum']),
                "segment_mean": float(top_row['mean']),
                "contribution_pct": round(float(top_row['contribution_pct']), 2)
            })

        # Select primary driver dimension (highest concentration of contribution)
        primary_step = max(hierarchy_steps, key=lambda x: x["contribution_pct"]) if hierarchy_steps else None

        return {
            "target_metric": target_metric,
            "evaluated_dimensions": dims,
            "hierarchy_steps": hierarchy_steps,
            "primary_driver": primary_step,
            "explanation": f"Metric '{target_metric}' is most heavily concentrated in '{primary_step['dimension']}' = '{primary_step['top_segment']}' ({primary_step['contribution_pct']}% of total)." if primary_step else "No clear segment driver found."
        }
