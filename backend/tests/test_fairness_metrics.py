"""Hand-calculated correctness tests for fairness metrics.

Each test constructs a tiny dataset where every metric value can be derived by
hand and compared to the function output. If any of these tests start to fail,
the math has regressed.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.services.fairness.metrics import (
    calibration_difference,
    compute_all_metrics,
    demographic_parity_difference,
    disparate_impact_ratio,
    equal_opportunity_difference,
    equalized_odds_difference,
    individual_fairness_consistency,
    predictive_parity_difference,
)


# ---------------------------------------------------------------------------
# Fixture: a 10-row toy dataset with two groups (A=0 unprivileged, A=1 privileged).
# Group A=0: 5 rows. Truths [1,1,0,0,0]. Preds [1,0,0,0,0].  -> SR=1/5=0.2, TPR=1/2=0.5, FPR=0/3=0
# Group A=1: 5 rows. Truths [1,1,1,0,0]. Preds [1,1,1,1,0].  -> SR=4/5=0.8, TPR=3/3=1.0, FPR=1/2=0.5
# ---------------------------------------------------------------------------

Y_TRUE = np.array([1, 1, 0, 0, 0, 1, 1, 1, 0, 0], dtype=np.int8)
Y_PRED = np.array([1, 0, 0, 0, 0, 1, 1, 1, 1, 0], dtype=np.int8)
S = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])


def test_demographic_parity_difference_hand_calculated():
    # SR(A=0) = 1/5 = 0.2 ; SR(A=1) = 4/5 = 0.8 ; gap = 0.6
    r = demographic_parity_difference(Y_PRED, S)
    assert r.value == pytest.approx(0.6, abs=1e-9)
    assert r.passes is False  # 0.6 > 0.10
    assert r.severity == "fail"
    assert r.per_group["0"] == pytest.approx(0.2, abs=1e-9)
    assert r.per_group["1"] == pytest.approx(0.8, abs=1e-9)


def test_disparate_impact_ratio_hand_calculated():
    # min(SR)/max(SR) = 0.2 / 0.8 = 0.25 ; pass threshold 0.80
    r = disparate_impact_ratio(Y_PRED, S)
    assert r.value == pytest.approx(0.25, abs=1e-9)
    assert r.passes is False
    assert r.severity == "fail"


def test_equal_opportunity_difference_hand_calculated():
    # TPR(A=0) = P(Yhat=1 | Y=1, A=0): truths==1 are positions 0,1 -> preds [1,0] -> mean=0.5
    # TPR(A=1) = positions 5,6,7 -> preds [1,1,1] -> mean=1.0
    # gap = 0.5
    r = equal_opportunity_difference(Y_TRUE, Y_PRED, S)
    assert r.value == pytest.approx(0.5, abs=1e-9)
    assert r.passes is False


def test_equalized_odds_difference_hand_calculated():
    # TPR gap = 0.5 (above)
    # FPR(A=0): truths==0 are positions 2,3,4 -> preds [0,0,0] -> 0.0
    # FPR(A=1): truths==0 are positions 8,9 -> preds [1,0] -> 0.5
    # FPR gap = 0.5 ; equalized odds = max(0.5, 0.5) = 0.5
    r = equalized_odds_difference(Y_TRUE, Y_PRED, S)
    assert r.value == pytest.approx(0.5, abs=1e-9)
    assert r.per_group["tpr_gap"] == pytest.approx(0.5, abs=1e-9)
    assert r.per_group["fpr_gap"] == pytest.approx(0.5, abs=1e-9)


def test_predictive_parity_difference_hand_calculated():
    # PPV(A=0): preds==1 at position 0 -> truth [1] -> 1.0
    # PPV(A=1): preds==1 at positions 5,6,7,8 -> truths [1,1,1,0] -> 0.75
    # gap = 0.25
    r = predictive_parity_difference(Y_TRUE, Y_PRED, S)
    assert r.value == pytest.approx(0.25, abs=1e-9)
    assert r.passes is False


def test_calibration_difference_hand_calculated():
    # Positive bucket: P(Y=1|Yhat=1, A=0) = 1.0 ; A=1 = 0.75 ; gap = 0.25
    # Negative bucket: P(Y=1|Yhat=0, A=0): preds==0 at 1,2,3,4 -> truths [1,0,0,0] -> 0.25
    #                  A=1: preds==0 at 9 -> truth [0] -> 0.0 ; gap = 0.25
    # avg = 0.25
    r = calibration_difference(Y_TRUE, Y_PRED, S)
    assert r.value == pytest.approx(0.25, abs=1e-9)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_perfect_fairness_returns_zero_gaps():
    # Both groups identical: SR=0.5, TPR=1.0, FPR=0
    y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 0, 1, 0, 1, 0])
    s = np.array([0, 0, 0, 0, 1, 1, 1, 1])

    assert demographic_parity_difference(y_pred, s).value == pytest.approx(0.0)
    assert disparate_impact_ratio(y_pred, s).value == pytest.approx(1.0)
    assert equal_opportunity_difference(y_true, y_pred, s).value == pytest.approx(0.0)
    assert equalized_odds_difference(y_true, y_pred, s).value == pytest.approx(0.0)
    assert predictive_parity_difference(y_true, y_pred, s).value == pytest.approx(0.0)


def test_single_group_returns_zero_gap():
    y_true = np.array([1, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 1])
    s = np.array([0, 0, 0, 0])
    assert demographic_parity_difference(y_pred, s).value == pytest.approx(0.0)


def test_three_group_pairwise_breakdown():
    # SR by group: 0=0.0, 1=0.5, 2=1.0 ; max-min = 1.0
    y_pred = np.array([0, 0, 1, 1, 1, 1])
    s = np.array(["a", "a", "b", "b", "c", "c"])
    r = demographic_parity_difference(y_pred, s)
    assert r.value == pytest.approx(1.0)
    assert r.per_group["a"] == pytest.approx(0.0)
    assert r.per_group["b"] == pytest.approx(0.5)
    assert r.per_group["c"] == pytest.approx(1.0)
    # 3 pairwise gaps: a-b, a-c, b-c
    assert len(r.pairwise) == 3


def test_string_labels_binarize_correctly():
    # positive_label = ">50K", favorable_prediction = ">50K"
    y_true = np.array([">50K", "<=50K", ">50K", "<=50K"])
    y_pred = np.array([">50K", "<=50K", "<=50K", "<=50K"])
    s = np.array(["F", "F", "M", "M"])
    out = compute_all_metrics(
        y_true=y_true,
        y_pred=y_pred,
        sensitive={"sex": s},
        positive_label=">50K",
        favorable_prediction=">50K",
    )
    assert "sex" in out["sensitive_attributes"]
    assert out["summary"]["metrics_total"] >= 6


def test_individual_fairness_perfect_consistency():
    # Two clusters in feature space, each with identical predictions -> consistency = 1.0
    rng = np.random.default_rng(0)
    cluster_a = rng.normal(loc=0, scale=0.01, size=(50, 3))
    cluster_b = rng.normal(loc=10, scale=0.01, size=(50, 3))
    X = np.vstack([cluster_a, cluster_b])
    y_pred = np.array([0] * 50 + [1] * 50, dtype=np.int8)
    r = individual_fairness_consistency(X, y_pred, k=5)
    assert r.value == pytest.approx(1.0, abs=1e-6)
    assert r.passes is True


def test_compute_all_metrics_summary_shape():
    out = compute_all_metrics(
        y_true=Y_TRUE,
        y_pred=Y_PRED,
        sensitive={"group": S},
        positive_label=1,
        favorable_prediction=1,
    )
    assert out["summary"]["metrics_total"] == 6  # no IF since no X_numeric
    assert out["summary"]["risk_level"] in ("Low Risk", "Medium Risk", "High Risk")
    assert "demographic_parity_difference" in out["sensitive_attributes"]["group"]["metrics"]
    assert "per_group_performance" in out["sensitive_attributes"]["group"]


def test_zero_positive_predictions_does_not_crash():
    y_true = np.array([1, 1, 0, 0])
    y_pred = np.array([0, 0, 0, 0])
    s = np.array([0, 0, 1, 1])
    # Should not raise; value should be 0 (no gap when both groups predict all-negative).
    r = demographic_parity_difference(y_pred, s)
    assert r.value == pytest.approx(0.0)
    # PPV is undefined for both groups -> per_group has Nones, value falls back to 0.
    r2 = predictive_parity_difference(y_true, y_pred, s)
    assert r2.value == pytest.approx(0.0)
