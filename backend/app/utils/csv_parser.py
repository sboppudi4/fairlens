"""CSV parsing + column type inference. Used both at upload time and inside Celery."""
from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd

# Heuristics for column type inference
_BOOL_VALUES = {"true", "false", "yes", "no", "0", "1", "t", "f", "y", "n"}


def parse_csv(data: bytes, *, max_rows_for_preview: int = 20) -> dict[str, Any]:
    """Parse CSV bytes and return metadata + preview rows.

    Validates: utf-8, header present, >= 100 rows, <= 500 cols.
    """
    try:
        df = pd.read_csv(BytesIO(data), encoding="utf-8", low_memory=False)
    except UnicodeDecodeError as e:
        raise ValueError("CSV must be UTF-8 encoded") from e
    except pd.errors.EmptyDataError as e:
        raise ValueError("CSV is empty") from e
    except pd.errors.ParserError as e:
        raise ValueError(f"CSV parse error: {e}") from e

    if df.shape[0] < 100:
        raise ValueError(f"CSV must have at least 100 rows (got {df.shape[0]})")
    if df.shape[1] > 500:
        raise ValueError(f"CSV exceeds 500-column limit (got {df.shape[1]})")
    if df.shape[1] < 2:
        raise ValueError("CSV must have at least 2 columns")
    if any(col.startswith("Unnamed:") for col in df.columns):
        raise ValueError("CSV appears to be missing a header row")

    column_types = {col: _infer_dtype(df[col]) for col in df.columns}

    preview_rows = (
        df.head(max_rows_for_preview)
        .astype(object)
        .where(df.head(max_rows_for_preview).notna(), None)
        .to_dict(orient="records")
    )

    return {
        "row_count": int(df.shape[0]),
        "column_names": list(df.columns),
        "column_types": column_types,
        "preview_rows": preview_rows,
    }


def _infer_dtype(series: pd.Series) -> str:
    """Return one of: numeric | boolean | categorical | string."""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    # Try boolean-like strings
    non_null = series.dropna()
    if len(non_null) == 0:
        return "string"
    sample = non_null.astype(str).str.lower().head(200)
    unique = set(sample.unique())
    if unique.issubset(_BOOL_VALUES) and len(unique) <= 2:
        return "boolean"
    # Cardinality heuristic
    nunique = series.nunique(dropna=True)
    if nunique <= max(20, len(series) * 0.05):
        return "categorical"
    return "string"


def column_stats(data: bytes, max_unique_for_samples: int = 10) -> list[dict[str, Any]]:
    """Per-column stats: cardinality, null count, sample values."""
    df = pd.read_csv(BytesIO(data), encoding="utf-8", low_memory=False)
    out = []
    for col in df.columns:
        s = df[col]
        sample_unique = s.dropna().astype(str).unique()[:max_unique_for_samples].tolist()
        out.append({
            "name": col,
            "dtype": _infer_dtype(s),
            "cardinality": int(s.nunique(dropna=True)),
            "null_count": int(s.isna().sum()),
            "sample_values": [str(v) for v in sample_unique],
        })
    return out
