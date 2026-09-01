import pandas as pd
import numpy as np
from typing import Dict, Any, List


class EDAEngine:
    @staticmethod
    def audit_dataset(df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive data health audit on a DataFrame."""
        row_count, col_count = df.shape
        missing_total = int(df.isnull().sum().sum())
        total_cells = row_count * col_count
        missing_pct = float(round((missing_total / total_cells) * 100, 2)) if total_cells > 0 else 0.0

        duplicate_rows = int(df.duplicated().sum())
        quality_score = max(0, min(100, int(100 - (missing_pct * 2) - (duplicate_rows / row_count * 10))))

        columns_audit = []
        for col in df.columns:
            dtype_name = str(df[col].dtype)
            missing_cnt = int(df[col].isnull().sum())
            missing_col_pct = float(round((missing_cnt / row_count) * 100, 2)) if row_count > 0 else 0.0

            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            col_info: Dict[str, Any] = {
                "name": col,
                "type": "numeric" if is_numeric else "categorical",
                "dtype": dtype_name,
                "missingCount": missing_cnt,
                "missingPercentage": missing_col_pct,
                "uniqueValues": int(df[col].nunique())
            }

            if is_numeric:
                non_nulls = df[col].dropna()
                if len(non_nulls) > 0:
                    col_info["mean"] = float(round(non_nulls.mean(), 2))
                    col_info["std"] = float(round(non_nulls.std(), 2))
                    col_info["min"] = float(round(non_nulls.min(), 2))
                    col_info["max"] = float(round(non_nulls.max(), 2))
                    col_info["median"] = float(round(non_nulls.median(), 2))

            columns_audit.append(col_info)

        return {
            "rowCount": row_count,
            "colCount": col_count,
            "qualityScore": quality_score,
            "qualityRating": "Good" if quality_score >= 80 else ("Fair" if quality_score >= 60 else "Poor"),
            "missingPercentage": missing_pct,
            "duplicateRows": duplicate_rows,
            "columns": columns_audit
        }

    @staticmethod
    def calculate_correlations(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate numerical pairwise correlations."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return []

        corr_matrix = numeric_df.corr().round(3)
        pairs = []
        cols = corr_matrix.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr_matrix.iloc[i, j]
                if not np.isnan(val):
                    pairs.append({
                        "featureA": cols[i],
                        "featureB": cols[j],
                        "correlation": float(val),
                        "absCorrelation": float(abs(val))
                    })

        pairs.sort(key=lambda x: x["absCorrelation"], reverse=True)
        return pairs[:10]
