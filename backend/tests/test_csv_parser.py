"""Unit tests for the CSV parser's validation and type-inference paths.

These are pure-function tests (no DB / no app), focused on the corrupted- and
malformed-input rejection paths that guard every upload.
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest

from app.utils.csv_parser import column_stats, parse_csv


def _csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def _valid_df(n: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "age": rng.integers(18, 90, n),
            "score": rng.normal(0.0, 1.0, n),
            "group": rng.choice(["A", "B", "C"], n),
            "flag": rng.choice(["yes", "no"], n),
            "label": rng.integers(0, 2, n),
        }
    )


def test_parse_valid_csv_returns_metadata_and_inferred_types() -> None:
    result = parse_csv(_csv_bytes(_valid_df(120)))
    assert result["row_count"] == 120
    assert result["column_names"] == ["age", "score", "group", "flag", "label"]
    types = result["column_types"]
    assert types["age"] == "numeric"
    assert types["score"] == "numeric"
    assert types["group"] == "categorical"
    assert types["flag"] == "boolean"
    assert len(result["preview_rows"]) == 20  # default max_rows_for_preview


def test_empty_bytes_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_csv(b"")


def test_non_utf8_bytes_rejected() -> None:
    corrupted = b"a,b\n" + b"\xff\xfe,2\n" * 150  # invalid UTF-8 start bytes
    with pytest.raises(ValueError, match="UTF-8"):
        parse_csv(corrupted)


def test_too_few_rows_rejected() -> None:
    with pytest.raises(ValueError, match="100 rows"):
        parse_csv(_csv_bytes(_valid_df(50)))


def test_single_column_rejected() -> None:
    one_col = _csv_bytes(pd.DataFrame({"only": list(range(120))}))
    with pytest.raises(ValueError, match="2 columns"):
        parse_csv(one_col)


def test_missing_header_rejected() -> None:
    # A blank header cell makes pandas synthesize an "Unnamed:" column name.
    raw = ",b,c\n" + "".join(f"{i},2,3\n" for i in range(120))
    with pytest.raises(ValueError, match="header"):
        parse_csv(raw.encode())


def test_too_many_columns_rejected() -> None:
    wide = _csv_bytes(pd.DataFrame(np.zeros((100, 501), dtype=int)))
    with pytest.raises(ValueError, match="500-column"):
        parse_csv(wide)


def test_column_stats_reports_nulls_and_cardinality() -> None:
    df = _valid_df(120)
    df.loc[:9, "score"] = np.nan  # 10 nulls
    stats = {row["name"]: row for row in column_stats(_csv_bytes(df))}
    assert stats["score"]["null_count"] == 10
    assert stats["group"]["cardinality"] == 3
    assert set(stats["group"]["sample_values"]) <= {"A", "B", "C"}
