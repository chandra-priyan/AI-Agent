import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class GroupAnalysisEngine:
    @staticmethod
    def analyze_groups(
        df: pd.DataFrame,
        group_by_col: Optional[str] = None,
        target_col: Optional[str] = None,
        agg_funcs: List[str] = ["mean", "sum", "count"]
    ) -> Dict[str, Any]:
        """Perform dynamic group analysis by detecting available categorical and numerical columns."""
        cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns
        num_cols = df.select_dtypes(include=[np.number]).columns

        # Auto-detect group_by column if not provided
        if not group_by_col:
            # Pick a categorical column with reasonable cardinality (2 <= unique <= 20)
            valid_cats = [c for c in cat_cols if 2 <= df[c].nunique(dropna=True) <= 20]
            if valid_cats:
                group_by_col = valid_cats[0]
            elif len(cat_cols) > 0:
                group_by_col = list(cat_cols)[0]
            else:
                raise ValueError("No categorical column available for grouping.")

        if group_by_col not in df.columns:
            raise ValueError(f"Grouping column '{group_by_col}' not found in dataset.")

        # Auto-detect target column if not provided
        if not target_col:
            if len(num_cols) > 0:
                target_col = list(num_cols)[0]
            else:
                raise ValueError("No numerical target column available for group aggregation.")

        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset.")

        # Handle high cardinality grouping columns to avoid overcrowded charts
        is_numeric_group = pd.api.types.is_numeric_dtype(df[group_by_col])
        num_unique = df[group_by_col].nunique(dropna=True)
        original_group_by_col = group_by_col

        if num_unique > 15:
            df = df.copy()
            if is_numeric_group:
                try:
                    non_nan_mask = df[group_by_col].notna()
                    if non_nan_mask.sum() > 0:
                        num_bins = min(8, df[group_by_col].nunique())
                        binned = pd.qcut(df[group_by_col][non_nan_mask], q=num_bins, duplicates='drop')
                        
                        labels = []
                        for interval in binned:
                            left = round(float(interval.left), 2)
                            right = round(float(interval.right), 2)
                            def format_val(v):
                                if abs(v) >= 1_000_000:
                                    return f"{v/1_000_000:.1f}M"
                                elif abs(v) >= 1_000:
                                    return f"{v/1_000:.1f}K"
                                return str(v)
                            labels.append(f"{format_val(left)}-{format_val(right)}")
                        
                        df.loc[non_nan_mask, f"{group_by_col}_binned"] = labels
                        df.loc[~non_nan_mask, f"{group_by_col}_binned"] = "Missing"
                        group_by_col = f"{group_by_col}_binned"
                    else:
                        df[group_by_col] = "Missing"
                except Exception:
                    # Fallback to Top-10 categorical grouping
                    top_cats = df[group_by_col].value_counts().index[:10]
                    df[group_by_col] = df[group_by_col].apply(lambda x: str(x) if x in top_cats else "Other")
            else:
                top_cats = df[group_by_col].value_counts().index[:10]
                df[group_by_col] = df[group_by_col].apply(lambda x: str(x) if x in top_cats else "Other")

        grouped = df.groupby(group_by_col, dropna=False)[target_col]

        # Valid agg funcs
        valid_aggs = [f for f in agg_funcs if f in ["mean", "sum", "count", "median", "min", "max", "std"]]
        if not valid_aggs:
            valid_aggs = ["mean", "sum", "count"]

        agg_result = grouped.agg(valid_aggs).reset_index()

        groups_list: List[Dict[str, Any]] = []
        for _, row in agg_result.iterrows():
            group_name = str(row[group_by_col])
            group_entry: Dict[str, Any] = {"group": group_name}
            for agg in valid_aggs:
                val = row[agg]
                group_entry[agg] = np.round(float(val), 4) if pd.notna(val) else None
            groups_list.append(group_entry)

        # Sort by mean/sum descending
        primary_sort = valid_aggs[0]
        groups_list.sort(key=lambda x: (x[primary_sort] is not None, x[primary_sort]), reverse=True)

        return {
            "group_by_column": original_group_by_col,
            "target_column": target_col,
            "groups": groups_list
        }
