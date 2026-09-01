import io
import os
import uuid
import pandas as pd
from typing import Dict, Tuple, Optional, Any

# In-memory storage for datasets in Phase 4 (no DB required)
_DATASETS: Dict[str, pd.DataFrame] = {}
_METADATA: Dict[str, Dict[str, Any]] = {}

class DatasetLoadError(Exception):
    pass

class CSVLoader:
    _sessions = _DATASETS
    @staticmethod
    def load_from_bytes(content: bytes, filename: str) -> Tuple[str, pd.DataFrame]:
        """Read bytes into DataFrame, assign UUID, cache in memory, and persist on disk."""
        if not content:
            raise DatasetLoadError("Uploaded file is empty.")

        # Try multiple encodings
        df = None
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
        for enc in encodings:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=enc)
                break
            except Exception:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=enc, on_bad_lines='skip')
                    break
                except Exception:
                    continue

        if df is None:
            raise DatasetLoadError("Unable to parse CSV file with supported text encodings.")

        if df.empty or len(df.columns) == 0:
            raise DatasetLoadError("Dataset is empty or contains no valid columns.")

        # Clean column names (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]

        dataset_id = f"ds_{uuid.uuid4().hex[:8]}"
        _DATASETS[dataset_id] = df
        _METADATA[dataset_id] = {
            "dataset_id": dataset_id,
            "filename": filename,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "status": "ready"
        }

        # Persist to disk to prevent loss on server reloads
        try:
            os.makedirs(os.path.join("data", "datasets"), exist_ok=True)
            file_path = os.path.join("data", "datasets", f"{dataset_id}.csv")
            df.to_csv(file_path, index=False)
        except Exception:
            pass

        return dataset_id, df

    @staticmethod
    def load_from_path(file_path: str) -> Tuple[str, pd.DataFrame]:
        """Load CSV from local file path."""
        if not os.path.exists(file_path):
            raise DatasetLoadError(f"File not found at path: {file_path}")

        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            return CSVLoader.load_from_bytes(f.read(), filename)

    @staticmethod
    def get_dataset(dataset_id: str) -> pd.DataFrame:
        """Retrieve dataset DataFrame from in-memory cache, or load from disk if missing."""
        if dataset_id not in _DATASETS:
            file_path = os.path.join("data", "datasets", f"{dataset_id}.csv")
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path)
                    _DATASETS[dataset_id] = df
                    _METADATA[dataset_id] = {
                        "dataset_id": dataset_id,
                        "filename": "dataset.csv",
                        "rows": int(len(df)),
                        "columns": int(len(df.columns)),
                        "status": "ready"
                    }
                    return df
                except Exception as e:
                    raise DatasetLoadError(f"Failed to load dataset from disk: {e}")
            raise DatasetLoadError(f"Dataset ID '{dataset_id}' not found.")
        return _DATASETS[dataset_id]

    @staticmethod
    def store_dataset(dataset_id: str, df: pd.DataFrame, filename: str = "dataset.csv") -> None:
        """Store or replace dataset DataFrame."""
        _DATASETS[dataset_id] = df
        _METADATA[dataset_id] = {
            "dataset_id": dataset_id,
            "filename": filename,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "status": "ready"
        }

    @staticmethod
    def save_session(dataset_id: str, df: pd.DataFrame, filename: str = "dataset.csv") -> None:
        """Alias for store_dataset."""
        CSVLoader.store_dataset(dataset_id, df, filename)

    @staticmethod
    def get_metadata(dataset_id: str) -> Dict[str, Any]:
        """Get dataset metadata info."""
        if dataset_id not in _METADATA:
            raise DatasetLoadError(f"Metadata for dataset ID '{dataset_id}' not found.")
        return _METADATA[dataset_id]

    @staticmethod
    def list_datasets() -> Dict[str, Dict[str, Any]]:
        """List all loaded datasets."""
        return _METADATA

DatasetSessionStore = CSVLoader
