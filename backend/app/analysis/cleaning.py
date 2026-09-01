import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

class DataCleaner:
    @staticmethod
    def generate_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate explainable data quality score and audit metrics."""
        total_rows = int(len(df))
        total_cols = int(len(df.columns))

        if total_rows == 0 or total_cols == 0:
            return {
                "quality_score": 0.0,
                "total_rows": total_rows,
                "total_columns": total_cols,
                "missing_values": {},
                "duplicates": 0,
                "outliers": {},
                "constant_columns": list(df.columns),
                "unusable_columns": list(df.columns),
                "warnings": ["Dataset is empty"]
            }

        missing_map: Dict[str, int] = {}
        total_missing = 0
        total_cells = total_rows * total_cols
        constant_cols: List[str] = []
        unusable_cols: List[str] = []
        outlier_map: Dict[str, int] = {}
        warnings: List[str] = []

        # Outliers & Missingness
        for col in df.columns:
            missing_cnt = int(df[col].isna().sum())
            missing_map[col] = missing_cnt
            total_missing += missing_cnt

            if missing_cnt / total_rows > 0.5:
                warnings.append(f"Column '{col}' has >50% missing values ({missing_cnt}/{total_rows}).")

            if df[col].nunique(dropna=True) <= 1:
                constant_cols.append(col)
                warnings.append(f"Column '{col}' is constant (zero variance).")

            if missing_cnt == total_rows:
                unusable_cols.append(col)
                warnings.append(f"Column '{col}' is completely empty.")

            # IQR Outlier Detection on numerical columns
            if pd.api.types.is_numeric_dtype(df[col]):
                series = df[col].dropna()
                if len(series) > 10:
                    q25, q75 = series.quantile(0.25), series.quantile(0.75)
                    iqr = q75 - q25
                    if iqr > 0:
                        lower_bound = q25 - 1.5 * iqr
                        upper_bound = q75 + 1.5 * iqr
                        outliers_cnt = int(((series < lower_bound) | (series > upper_bound)).sum())
                        if outliers_cnt > 0:
                            outlier_map[col] = outliers_cnt

        duplicates_cnt = int(df.duplicated().sum())
        if duplicates_cnt > 0:
            warnings.append(f"Dataset contains {duplicates_cnt} duplicate rows.")

        # Explainable score calculation (0.0 to 1.0)
        # Deductions:
        # Missing cell ratio: up to -0.30
        # Duplicate row ratio: up to -0.20
        # Constant/unusable column ratio: up to -0.20
        # Outlier ratio: up to -0.10
        missing_penalty = min(0.30, (total_missing / total_cells) * 0.6)
        duplicate_penalty = min(0.20, (duplicates_cnt / total_rows) * 0.5)
        constant_penalty = min(0.20, (len(constant_cols) / total_cols) * 0.4)
        outlier_penalty = min(0.10, (sum(outlier_map.values()) / total_cells) * 0.5)

        quality_score = float(max(0.0, 1.0 - (missing_penalty + duplicate_penalty + constant_penalty + outlier_penalty)))

        return {
            "quality_score": np.round(quality_score, 4),
            "total_rows": total_rows,
            "total_columns": total_cols,
            "missing_values": missing_map,
            "duplicates": duplicates_cnt,
            "outliers": outlier_map,
            "constant_columns": constant_cols,
            "unusable_columns": unusable_cols,
            "warnings": warnings
        }

    @staticmethod
    def clean_dataset(df: pd.DataFrame, drop_duplicates: bool = True, drop_empty_rows: bool = True) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Perform safe, audited transformations on a DataFrame."""
        cleaned_df = df.copy()
        transformations: List[Dict[str, Any]] = []

        # 1. Strip string whitespace
        string_cols = cleaned_df.select_dtypes(include=["object", "string"]).columns
        for col in string_cols:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
            cleaned_df[col] = cleaned_df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})

        # 2. Drop completely empty rows
        if drop_empty_rows:
            before_cnt = len(cleaned_df)
            cleaned_df = cleaned_df.dropna(how="all")
            after_cnt = len(cleaned_df)
            removed = before_cnt - after_cnt
            if removed > 0:
                transformations.append({
                    "operation": "remove_empty_rows",
                    "details": {"rows_before": before_cnt, "rows_after": after_cnt},
                    "rows_affected": removed
                })

        # 3. Handle duplicates
        if drop_duplicates:
            before_cnt = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            after_cnt = len(cleaned_df)
            removed = before_cnt - after_cnt
            if removed > 0:
                transformations.append({
                    "operation": "remove_duplicates",
                    "details": {"rows_before": before_cnt, "rows_after": after_cnt},
                    "rows_affected": removed
                })

        # 4. Auto-convert recognizable numeric values
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == "object":
                # Check if values look like numbers (e.g. "$1,200" or " 12.5 ")
                sample = cleaned_df[col].dropna().head(20)
                if len(sample) > 0:
                    cleaned_sample = sample.astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False)
                    converted = pd.to_numeric(cleaned_sample, errors="coerce")
                    if converted.notna().sum() >= len(sample) * 0.8:
                        cleaned_df[col] = pd.to_numeric(
                            cleaned_df[col].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False),
                            errors="coerce"
                        )
                        transformations.append({
                            "operation": "convert_numeric_column",
                            "details": {"column": col, "new_dtype": str(cleaned_df[col].dtype)},
                            "rows_affected": len(cleaned_df)
                        })

        # 5. Auto-convert recognizable dates
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == "object" and "date" in col.lower() or "time" in col.lower():
                try:
                    parsed = pd.to_datetime(cleaned_df[col], errors="coerce")
                    if parsed.notna().sum() > 0:
                        cleaned_df[col] = parsed
                        transformations.append({
                            "operation": "convert_date_column",
                            "details": {"column": col, "new_dtype": "datetime64[ns]"},
                            "rows_affected": int(parsed.notna().sum())
                        })
                except Exception:
                    pass

        return cleaned_df, transformations
