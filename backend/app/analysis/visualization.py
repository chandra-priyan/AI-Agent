import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class VisualizationEngine:
    @staticmethod
    def generate_chart_data(
        df: pd.DataFrame,
        chart_type: str = "bar",
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON chart objects for frontend components."""
        chart_type_clean = chart_type.lower()
        num_cols = df.select_dtypes(include=[np.number]).columns
        cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c]) or "date" in c.lower()]

        if chart_type_clean == "line":
            if not x_col and date_cols:
                x_col = date_cols[0]
            elif not x_col and len(df.columns) > 0:
                x_col = df.columns[0]
            if not y_col and len(num_cols) > 0:
                y_col = num_cols[0]

            if not x_col or not y_col:
                raise ValueError("Line chart requires valid x and y columns.")

            sub_df = df[[x_col, y_col]].dropna().head(100)
            x_vals = sub_df[x_col].astype(str).tolist()
            y_vals = [np.round(float(v), 4) for v in sub_df[y_col].tolist()]

            return {
                "chart_type": "line",
                "title": title or f"{y_col} over {x_col}",
                "x_label": x_col,
                "y_label": y_col,
                "x": x_vals,
                "y": y_vals
            }

        elif chart_type_clean == "bar":
            if not x_col and len(cat_cols) > 0:
                x_col = cat_cols[0]
            elif not x_col:
                x_col = df.columns[0]

            if not y_col and len(num_cols) > 0:
                y_col = num_cols[0]

            if not y_col:
                # Count aggregation if no numeric y column
                counts = df[x_col].value_counts().head(10)
                return {
                    "chart_type": "bar",
                    "title": title or f"Count by {x_col}",
                    "x_label": x_col,
                    "y_label": "Count",
                    "x": [str(k) for k in counts.index],
                    "y": [int(v) for v in counts.values]
                }

            grouped = df.groupby(x_col)[y_col].mean().dropna().head(15)
            return {
                "chart_type": "bar",
                "title": title or f"Mean {y_col} by {x_col}",
                "x_label": x_col,
                "y_label": f"Mean {y_col}",
                "x": [str(k) for k in grouped.index],
                "y": [np.round(float(v), 4) for v in grouped.values]
            }

        elif chart_type_clean == "scatter":
            if not x_col and len(num_cols) > 0:
                x_col = num_cols[0]
            if not y_col and len(num_cols) > 1:
                y_col = num_cols[1]
            elif not y_col and len(num_cols) > 0:
                y_col = num_cols[0]

            if not x_col or not y_col:
                raise ValueError("Scatter chart requires two numerical columns.")

            sub_df = df[[x_col, y_col]].dropna().head(200)
            return {
                "chart_type": "scatter",
                "title": title or f"{y_col} vs {x_col}",
                "x_label": x_col,
                "y_label": y_col,
                "x": [np.round(float(v), 4) for v in sub_df[x_col].tolist()],
                "y": [np.round(float(v), 4) for v in sub_df[y_col].tolist()]
            }

        elif chart_type_clean == "pie":
            if not x_col and len(cat_cols) > 0:
                x_col = cat_cols[0]
            elif not x_col:
                x_col = df.columns[0]

            counts = df[x_col].value_counts().head(8)
            return {
                "chart_type": "pie",
                "title": title or f"Distribution of {x_col}",
                "x_label": x_col,
                "y_label": "Share",
                "x": [str(k) for k in counts.index],
                "y": [int(v) for v in counts.values]
            }

        elif chart_type_clean == "boxplot":
            if not y_col and len(num_cols) > 0:
                y_col = num_cols[0]

            if not y_col:
                raise ValueError("Boxplot requires a numerical y column.")

            series = df[y_col].dropna()
            return {
                "chart_type": "boxplot",
                "title": title or f"Distribution Boxplot for {y_col}",
                "x_label": y_col,
                "y_label": "Value",
                "x": [y_col],
                "y": [
                    float(series.min()),
                    float(series.quantile(0.25)),
                    float(series.median()),
                    float(series.quantile(0.75)),
                    float(series.max())
                ]
            }
        else:
            raise ValueError(f"Unsupported chart type '{chart_type}'. Supported: line, bar, scatter, pie, boxplot.")
