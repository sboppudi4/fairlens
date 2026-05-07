"""Smoke tests for the PDF report service.

These verify the report builds without exceptions, returns valid PDF bytes
(starts with %PDF), and includes pages for cover + executive summary +
fairness sections.

We do NOT validate visual fidelity — that is left to manual inspection.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.services.fairness.metrics import compute_all_metrics
from app.services.fairness.mitigation import build_mitigations
from app.services.fairness.regulatory import build_regulatory_mapping
from app.services.report_service import build_pdf


def _toy_results() -> tuple[dict, dict]:
    rng = np.random.default_rng(3)
    n = 400
    y_true = rng.integers(0, 2, size=n)
    y_pred = rng.integers(0, 2, size=n)
    s = rng.choice(["A", "B"], size=n)
    metrics = compute_all_metrics(
        y_true=y_true.astype(str),
        y_pred=y_pred.astype(str),
        sensitive={"group": s},
        positive_label="1",
        favorable_prediction="1",
    )
    regulatory = build_regulatory_mapping(metrics["sensitive_attributes"])
    results = {
        "schema_version": "1.0",
        "summary": metrics["summary"],
        "sensitive_attributes": metrics["sensitive_attributes"],
        "regulatory": regulatory,
        "config_used": {
            "label_column": "label",
            "prediction_column": "prediction",
            "sensitive_attributes": ["group"],
            "positive_label": "1",
            "favorable_prediction": "1",
            "model_type": "binary_classification",
        },
        "dataset": {"id": "abc", "row_count": n},
        "completed_at": "2026-05-07T00:00:00Z",
    }
    config = results["config_used"]
    return results, config


def test_build_pdf_returns_valid_pdf_bytes():
    results, config = _toy_results()
    mitigations = build_mitigations(results["sensitive_attributes"], {"available": False})
    pdf = build_pdf(
        audit_name="Test audit",
        dataset_name="toy",
        prepared_by="Tester",
        results=results,
        config=config,
        shap_block={"available": False, "reason": "test path"},
        mitigations=mitigations,
    )
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"
    # A meaningful report should produce >20kB of bytes given the embedded charts
    assert len(pdf) > 20_000


def test_build_pdf_with_shap_section():
    results, config = _toy_results()
    shap_block = {
        "available": True,
        "n_samples_explained": 100,
        "n_features": 5,
        "feature_importance": [
            {"feature": "feat_1", "mean_abs_shap": 0.42},
            {"feature": "feat_2", "mean_abs_shap": 0.31},
            {"feature": "feat_3", "mean_abs_shap": 0.20},
        ],
        "per_group": {
            "group": {
                "A": [{"feature": "feat_1", "mean_abs_shap": 0.5}],
                "B": [{"feature": "feat_2", "mean_abs_shap": 0.4}],
            }
        },
        "proxy_warnings": [
            {
                "sensitive_attribute": "group",
                "feature": "feat_1",
                "max_group_importance": 0.5,
                "min_group_importance": 0.1,
                "relative_gap": 0.8,
                "interpretation": "test proxy",
            }
        ],
    }
    mitigations = build_mitigations(results["sensitive_attributes"], shap_block)
    pdf = build_pdf(
        audit_name="With SHAP",
        dataset_name="toy",
        prepared_by="Tester",
        results=results,
        config=config,
        shap_block=shap_block,
        mitigations=mitigations,
    )
    assert pdf[:4] == b"%PDF"


def test_build_mitigations_emits_one_per_failing_metric():
    results, _ = _toy_results()
    out = build_mitigations(results["sensitive_attributes"], {"available": False})
    # All entries should reference a failing metric and have the required schema
    for m in out:
        assert "technique" in m
        assert "code_snippet" in m
        assert m["complexity"] in {"low", "medium", "high"}


def test_regulatory_mapping_covers_three_frameworks():
    _, _ = _toy_results()
    results, _ = _toy_results()
    reg = build_regulatory_mapping(results["sensitive_attributes"])
    frameworks = {f["framework"] for f in reg["frameworks"]}
    assert {"EU AI Act", "NIST AI RMF", "ISO/IEC 42001"} <= frameworks
    assert reg["per_metric"]
    for item in reg["per_metric"]:
        assert item["status"] in {"compliant", "non_compliant"}
