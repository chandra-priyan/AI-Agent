import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DatasetProfiler:
    @staticmethod
    def profile_dataset(df: pd.DataFrame, dataset_id: str = "ds_default", filename: str = "dataset.csv") -> Dict[str, Any]:
        """Perform dynamic profiling on a Pandas DataFrame without assuming hardcoded column names."""
        total_rows = int(len(df))
        total_cols = int(len(df.columns))

        num_cols: List[str] = []
        cat_cols: List[str] = []
        date_cols: List[str] = []
        constant_cols: List[str] = []
        potential_id_cols: List[str] = []

        dtypes_map: Dict[str, str] = {}
        missing_map: Dict[str, int] = {}
        
        num_stats: Dict[str, Dict[str, Any]] = {}
        cat_stats: Dict[str, Dict[str, Any]] = {}
        date_stats: Dict[str, Dict[str, Any]] = {}

        # 1. Inspect each column
        for col in df.columns:
            series = df[col]
            missing_cnt = int(series.isna().sum())
            missing_pct = float(missing_cnt / total_rows) if total_rows > 0 else 0.0
            missing_map[col] = missing_cnt

            unique_cnt = int(series.nunique(dropna=True))

            # Constant column
            if unique_cnt <= 1:
                constant_cols.append(col)

            # Potential ID column
            if unique_cnt == total_rows and total_rows > 5:
                potential_id_cols.append(col)

            # Check if column is datetime
            is_date = False
            if pd.api.types.is_datetime64_any_dtype(series):
                is_date = True
            elif series.dtype == "object":
                # Try parsing sample values as dates
                sample = series.dropna().head(20)
                if len(sample) > 0:
                    try:
                        parsed = pd.to_datetime(sample, errors="coerce")
                        if parsed.notna().sum() > len(sample) * 0.8:
                            is_date = True
                    except Exception:
                        is_date = False

            if is_date:
                date_cols.append(col)
                dtypes_map[col] = "datetime64"
                dt_series = pd.to_datetime(series, errors="coerce")
                valid_dt = dt_series.dropna()
                if len(valid_dt) > 0:
                    min_d = valid_dt.min().strftime("%Y-%m-%d")
                    max_d = valid_dt.max().strftime("%Y-%m-%d")
                    span = (valid_dt.max() - valid_dt.min()).days
                else:
                    min_d, max_d, span = "", "", 0

                date_stats[col] = {
                    "name": col,
                    "count": int(valid_dt.count()),
                    "min_date": min_d,
                    "max_date": max_d,
                    "time_span_days": int(span),
                    "missing_count": missing_cnt
                }
            elif pd.api.types.is_numeric_dtype(series) and not (col in potential_id_cols and "id" in col.lower()):
                num_cols.append(col)
                dtypes_map[col] = str(series.dtype)
                valid_num = series.dropna()

                if len(valid_num) > 0:
                    mean_val = float(valid_num.mean())
                    std_val = float(valid_num.std()) if len(valid_num) > 1 else 0.0
                    min_val = float(valid_num.min())
                    max_val = float(valid_num.max())
                    q25 = float(valid_num.quantile(0.25))
                    med = float(valid_num.median())
                    q75 = float(valid_num.quantile(0.75))
                else:
                    mean_val = std_val = min_val = max_val = q25 = med = q75 = 0.0

                num_stats[col] = {
                    "name": col,
                    "count": int(valid_num.count()),
                    "mean": np.round(mean_val, 4),
                    "std": np.round(std_val, 4),
                    "min": np.round(min_val, 4),
                    "q25": np.round(q25, 4),
                    "median": np.round(med, 4),
                    "q75": np.round(q75, 4),
                    "max": np.round(max_val, 4),
                    "missing_count": missing_cnt,
                    "missing_pct": np.round(missing_pct, 4)
                }
            else:
                cat_cols.append(col)
                dtypes_map[col] = "string/categorical"
                valid_cat = series.dropna()

                most_freq = None
                freq_dist: Dict[str, int] = {}
                if len(valid_cat) > 0:
                    val_counts = valid_cat.value_counts()
                    most_freq = str(val_counts.index[0])
                    # Top 10 frequencies
                    freq_dist = {str(k): int(v) for k, v in val_counts.head(10).items()}

                cat_stats[col] = {
                    "name": col,
                    "count": int(valid_cat.count()),
                    "unique_count": unique_cnt,
                    "most_frequent": most_freq,
                    "frequency_distribution": freq_dist,
                    "missing_count": missing_cnt,
                    "missing_pct": np.round(missing_pct, 4)
                }

        dup_rows = int(df.duplicated().sum())

        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "rows": total_rows,
            "columns": total_cols,
            "column_names": list(df.columns),
            "dtypes": dtypes_map,
            "numerical_columns": num_cols,
            "categorical_columns": cat_cols,
            "date_columns": date_cols,
            "missing_values": missing_map,
            "duplicate_rows": dup_rows,
            "constant_columns": constant_cols,
            "potential_id_columns": potential_id_cols,
            "numerical_stats": num_stats,
            "categorical_stats": cat_stats,
            "date_stats": date_stats
        }
