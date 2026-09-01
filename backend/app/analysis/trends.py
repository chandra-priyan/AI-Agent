import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class TrendAnalysisEngine:
    @staticmethod
    def analyze_trends(
        df: pd.DataFrame,
        date_col: Optional[str] = None,
        value_col: Optional[str] = None,
        freq: str = "monthly"
    ) -> Dict[str, Any]:
        """Perform dynamic time-series aggregation and trend detection."""
        num_cols = df.select_dtypes(include=[np.number]).columns
        
        # Detect date column
        if not date_col:
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]) or "date" in col.lower() or "time" in col.lower():
                    try:
                        pd.to_datetime(df[col], errors="raise")
                        date_col = col
                        break
                    except Exception:
                        continue

        if not date_col or date_col not in df.columns:
            raise ValueError("No valid date/time column found in dataset for trend analysis.")

        # Detect value column
        if not value_col:
            if len(num_cols) > 0:
                value_col = list(num_cols)[0]
            else:
                raise ValueError("No numerical value column found for trend analysis.")

        if value_col not in df.columns:
            raise ValueError(f"Value column '{value_col}' not found in dataset.")

        # Parse date column safely
        dt_df = df.copy()
        dt_df["_parsed_date"] = pd.to_datetime(dt_df[date_col], errors="coerce")
        dt_df = dt_df.dropna(subset=["_parsed_date"])

        if len(dt_df) == 0:
            raise ValueError(f"Column '{date_col}' could not be parsed into datetime values.")

        dt_df = dt_df.sort_values("_parsed_date")

        # Map freq string to pandas rule
        freq_map = {
            "daily": "D",
            "weekly": "W",
            "monthly": "ME" if hasattr(pd.offsets, "MonthEnd") else "M",
            "quarterly": "QE" if hasattr(pd.offsets, "QuarterEnd") else "Q",
            "yearly": "YE" if hasattr(pd.offsets, "YearEnd") else "Y"
        }
        pd_freq = freq_map.get(freq.lower(), "ME")

        grouped = dt_df.set_index("_parsed_date").resample(pd_freq)[value_col].agg(["sum", "count"]).reset_index()

        trends_list: List[Dict[str, Any]] = []
        prev_val = None

        for _, row in grouped.iterrows():
            period_str = row["_parsed_date"].strftime("%Y-%m-%d")
            val = float(row["sum"])
            cnt = int(row["count"])

            pop_change = None
            if prev_val is not None and prev_val != 0:
                pop_change = float((val - prev_val) / abs(prev_val))

            trends_list.append({
                "period": period_str,
                "value": np.round(val, 2),
                "count": cnt,
                "pop_change": np.round(pop_change, 4) if pop_change is not None else None
            })
            if cnt > 0:
                prev_val = val

        # Overall trend direction
        direction = "stable"
        if len(trends_list) >= 2:
            first_val = trends_list[0]["value"]
            last_val = trends_list[-1]["value"]
            if first_val != 0:
                total_change = (last_val - first_val) / abs(first_val)
                if total_change > 0.05:
                    direction = "increasing"
                elif total_change < -0.05:
                    direction = "decreasing"

        return {
            "date_column": date_col,
            "value_column": value_col,
            "freq": freq,
            "trends": trends_list,
            "overall_direction": direction
        }
