import uuid
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from app.analysis.loader import CSVLoader, DatasetLoadError
from app.analysis.profiler import DatasetProfiler
from app.analysis.cleaning import DataCleaner
from app.analysis.descriptive import DescriptiveAnalysisEngine
from app.analysis.grouping import GroupAnalysisEngine
from app.analysis.trends import TrendAnalysisEngine
from app.analysis.correlation import CorrelationAnalysisEngine
from app.analysis.statistics import StatisticalTestEngine
from app.analysis.regression import RegressionEngine
from app.analysis.visualization import VisualizationEngine

class AnalysisService:
    @staticmethod
    def upload_dataset(content: bytes, filename: str) -> Dict[str, Any]:
        """Upload and store dataset, returning summary metadata."""
        dataset_id, df = CSVLoader.load_from_bytes(content, filename)
        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": list(df.columns),
            "status": "ready"
        }

    @staticmethod
    def profile_dataset(dataset_id: str) -> Dict[str, Any]:
        """Retrieve profile report for a dataset."""
        df = CSVLoader.get_dataset(dataset_id)
        meta = CSVLoader.get_metadata(dataset_id)
        return DatasetProfiler.profile_dataset(df, dataset_id, meta.get("filename", "dataset.csv"))

    @staticmethod
    def quality_report(dataset_id: str) -> Dict[str, Any]:
        """Generate data quality report."""
        df = CSVLoader.get_dataset(dataset_id)
        return DataCleaner.generate_quality_report(df)

    @staticmethod
    def clean_dataset(dataset_id: str, drop_duplicates: bool = True, drop_empty_rows: bool = True) -> Dict[str, Any]:
        """Clean dataset safely and store transformed DataFrame back into loader memory."""
        df = CSVLoader.get_dataset(dataset_id)
        meta = CSVLoader.get_metadata(dataset_id)
        rows_before = len(df)
        cols_before = len(df.columns)

        cleaned_df, transformations = DataCleaner.clean_dataset(df, drop_duplicates, drop_empty_rows)
        CSVLoader.store_dataset(dataset_id, cleaned_df, meta.get("filename", "cleaned.csv"))

        rows_after = len(cleaned_df)
        cols_after = len(cleaned_df.columns)
        new_quality = DataCleaner.generate_quality_report(cleaned_df)

        return {
            "dataset_id": dataset_id,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "columns_before": cols_before,
            "columns_after": cols_after,
            "transformations": transformations,
            "quality_score_after": new_quality["quality_score"]
        }

    @staticmethod
    def descriptive_analysis(dataset_id: str, target_column: Optional[str] = None) -> List[Dict[str, Any]]:
        df = CSVLoader.get_dataset(dataset_id)
        return DescriptiveAnalysisEngine.calculate_descriptive_stats(df, target_column)

    @staticmethod
    def group_analysis(
        dataset_id: str,
        group_by_column: Optional[str] = None,
        target_column: Optional[str] = None,
        agg_funcs: List[str] = ["mean", "sum", "count"]
    ) -> Dict[str, Any]:
        df = CSVLoader.get_dataset(dataset_id)
        return GroupAnalysisEngine.analyze_groups(df, group_by_column, target_column, agg_funcs)

    @staticmethod
    def trend_analysis(
        dataset_id: str,
        date_column: Optional[str] = None,
        value_column: Optional[str] = None,
        freq: str = "monthly"
    ) -> Dict[str, Any]:
        df = CSVLoader.get_dataset(dataset_id)
        return TrendAnalysisEngine.analyze_trends(df, date_column, value_column, freq)

    @staticmethod
    def correlation_analysis(
        dataset_id: str,
        method: str = "pearson",
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        df = CSVLoader.get_dataset(dataset_id)
        return CorrelationAnalysisEngine.calculate_correlations(df, method, columns)

    @staticmethod
    def statistical_test(
        dataset_id: str,
        test_type: str,
        group_column: Optional[str] = None,
        value_column: Optional[str] = None,
        categorical_col1: Optional[str] = None,
        categorical_col2: Optional[str] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        df = CSVLoader.get_dataset(dataset_id)
        return StatisticalTestEngine.run_test(
            df, test_type, group_column, value_column, categorical_col1, categorical_col2, confidence_level
        )

    @staticmethod
    def regression_analysis(
        dataset_id: str,
        target_column: str,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        df = CSVLoader.get_dataset(dataset_id)
        return RegressionEngine.run_regression(df, target_column, feature_columns)

    @staticmethod
    def generate_chart(
        dataset_id: str,
        chart_type: str = "bar",
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        df = CSVLoader.get_dataset(dataset_id)
        return VisualizationEngine.generate_chart_data(df, chart_type, x_column, y_column, title)

    @staticmethod
    def get_evidence(dataset_id: str) -> Dict[str, Any]:
        """Automatically synthesize structured evidence objects grounded in dataset math."""
        df = CSVLoader.get_dataset(dataset_id)
        evidence_list: List[Dict[str, Any]] = []

        # 1. Quality evidence
        quality = DataCleaner.generate_quality_report(df)
        if quality["quality_score"] < 0.9:
            evidence_list.append({
                "id": f"ev_{uuid.uuid4().hex[:6]}",
                "finding": f"Dataset quality score is {quality['quality_score']*100:.1f}% due to missing values or duplicates.",
                "metric": "data_quality_score",
                "value": quality["quality_score"],
                "evidence_type": "quality_issue",
                "supporting_analysis": "data_quality_audit",
                "statistical_support": False,
                "details": {"warnings": quality["warnings"]}
            })

        # 2. Strong correlation evidence
        corrs = CorrelationAnalysisEngine.calculate_correlations(df)
        for corr in corrs:
            if corr["strength"] == "strong":
                evidence_list.append({
                    "id": f"ev_{uuid.uuid4().hex[:6]}",
                    "finding": f"Strong correlation ({corr['correlation']:.2f}) observed between '{corr['variable_a']}' and '{corr['variable_b']}'.",
                    "metric": f"corr_{corr['variable_a']}_{corr['variable_b']}",
                    "value": corr["correlation"],
                    "evidence_type": "correlation",
                    "supporting_analysis": "pairwise_correlation",
                    "statistical_support": True,
                    "details": {"disclaimer": corr["disclaimer"]}
                })

        # 3. Group variation evidence
        try:
            grp = GroupAnalysisEngine.analyze_groups(df)
            groups = grp["groups"]
            if len(groups) >= 2 and groups[0].get("mean") is not None and groups[-1].get("mean") is not None:
                max_grp = groups[0]
                min_grp = groups[-1]
                diff_pct = (max_grp["mean"] - min_grp["mean"]) / (abs(min_grp["mean"]) + 1e-9)
                evidence_list.append({
                    "id": f"ev_{uuid.uuid4().hex[:6]}",
                    "finding": f"Group '{max_grp['group']}' has highest mean {grp['target_column']} ({max_grp['mean']:.2f}), compared to '{min_grp['group']}' ({min_grp['mean']:.2f}).",
                    "metric": grp['target_column'],
                    "value": np.round(float(diff_pct), 4),
                    "evidence_type": "group_difference",
                    "supporting_analysis": "group_aggregation",
                    "statistical_support": True,
                    "details": {"group_by": grp["group_by_column"]}
                })
        except Exception:
            pass

        # 4. Trend evidence
        try:
            trd = TrendAnalysisEngine.analyze_trends(df)
            if trd["overall_direction"] != "stable":
                first_val = trd["trends"][0]["value"]
                last_val = trd["trends"][-1]["value"]
                pct_chg = (last_val - first_val) / (abs(first_val) + 1e-9)
                evidence_list.append({
                    "id": f"ev_{uuid.uuid4().hex[:6]}",
                    "finding": f"{trd['value_column']} exhibits an overall {trd['overall_direction']} trend over time ({pct_chg*100:+.1f}% change).",
                    "metric": trd["value_column"],
                    "value": np.round(float(pct_chg), 4),
                    "evidence_type": "trend",
                    "supporting_analysis": "time_series_resample",
                    "statistical_support": True,
                    "details": {"freq": trd["freq"]}
                })
        except Exception:
            pass

        return {
            "dataset_id": dataset_id,
            "total_findings": len(evidence_list),
            "evidence": evidence_list
        }

    # =========================================================================
    # Async / Agent compatibility helpers
    # =========================================================================
    async def run_dataset_profiler(self, dataset_id: str) -> Dict[str, Any]:
        res = self.profile_dataset(dataset_id)
        if hasattr(res, "model_dump"):
            return res
        class ProfilerResult:
            def __init__(self, data): self._data = data
            def model_dump(self): return self._data
        return ProfilerResult(res)

    async def run_data_quality_report(self, dataset_id: str) -> Dict[str, Any]:
        res = self.quality_report(dataset_id)
        class QualityResult:
            def __init__(self, data): self._data = data
            def model_dump(self): return self._data
        return QualityResult(res)

    async def run_descriptive_analysis(self, dataset_id: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        col = columns[0] if columns else None
        res = self.descriptive_analysis(dataset_id, col)
        class DescResult:
            def __init__(self, data): self._data = {"stats": data, "summary": "Descriptive statistics calculated."}
            def model_dump(self): return self._data
        return DescResult(res)

    async def run_group_analysis(self, dataset_id: str, group_by_col: str, target_col: str, agg_func: str = "mean") -> Dict[str, Any]:
        res = self.group_analysis(dataset_id, group_by_col, target_col, [agg_func, "count"])
        class GroupResult:
            def __init__(self, data): self._data = data
            def model_dump(self): return self._data
        return GroupResult(res)

    async def run_trend_analysis(self, dataset_id: str, date_col: str, value_col: str, freq: str = "M") -> Dict[str, Any]:
        res = self.trend_analysis(dataset_id, date_col, value_column=value_col, freq="monthly" if freq == "M" else freq)
        class TrendResult:
            def __init__(self, data): self._data = data
            def model_dump(self): return self._data
        return TrendResult(res)

    async def run_correlation_analysis(self, dataset_id: str, method: str = "pearson") -> Dict[str, Any]:
        res = self.correlation_analysis(dataset_id, method=method)
        class CorrResult:
            def __init__(self, data):
                strong = [{"col1": c["variable_a"], "col2": c["variable_b"], "correlation": c["correlation"]} for c in data if c.get("strength") == "strong"]
                self._data = {"strong_pairs": strong, "correlations": data, "summary": "Correlations calculated."}
            def model_dump(self): return self._data
        return CorrResult(res)

    async def run_statistical_test(self, dataset_id: str, test_type: str = "anova", group_col: Optional[str] = None, val_col: Optional[str] = None, cat_col1: Optional[str] = None, cat_col2: Optional[str] = None) -> Dict[str, Any]:
        res = self.statistical_test(dataset_id, test_type=test_type, group_column=group_col, value_column=val_col, categorical_col1=cat_col1, categorical_col2=cat_col2)
        class StatResult:
            def __init__(self, data): self._data = data
            def model_dump(self): return self._data
        return StatResult(res)

    async def run_regression_analysis(self, dataset_id: str, target_col: str, feature_cols: List[str]) -> Dict[str, Any]:
        res = self.regression_analysis(dataset_id, target_column=target_col, feature_columns=feature_cols)
        class RegResult:
            def __init__(self, data): self._data = data
            def model_dump(self): return self._data
        return RegResult(res)

