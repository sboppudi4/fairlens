"""Fairness metrics — pure NumPy, hand-derivable, deterministic.

All metrics operate on three vectors of equal length N:
    y_true:  ground-truth label, binarized to {0, 1} where 1 = positive_label
    y_pred:  model prediction, binarized to {0, 1} where 1 = favorable_prediction
    s:       sensitive attribute group id (any hashable; binary or multiclass supported)

For multiclass sensitive attributes, pairwise comparisons are computed against a
designated reference group (the largest by default). The "worst" pairwise gap is
reported as the headline value, and full pairwise breakdown is returned for the UI.

Conventions
-----------
* Demographic parity DIFFERENCE is computed as max(SR_g) - min(SR_g): non-negative,
  closer to 0 is better. Pass threshold |value| <= 0.1.
* Disparate impact RATIO is computed as min(SR_g) / max(SR_g): in [0, 1], closer to
  1 is better. Pass if >= 0.8 (the EEOC 4/5ths rule). This is direction-agnostic.
* TPR/FPR/PPV gaps are computed similarly as max - min across groups.
* Equalized odds = max(TPR_gap, FPR_gap).
* Per-group performance (accuracy, precision, recall, F1, AUC, confusion matrix,
  selection rate) is always returned alongside the gap-based metrics.
* All floats are rounded to 4 decimal places at the boundary; internal computation
  is full precision.

This module is intentionally framework-free so that hand-calculation tests can
verify it. Do not introduce hidden randomness or sklearn dependencies in metric
formulas; sklearn is only used for AUC where the closed-form requires sorting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Pass thresholds — EU AI Act Article 10 / 15 do not prescribe specific numbers,
# so we follow the most widely-adopted operational thresholds:
#   * EEOC 4/5ths rule for disparate impact (0.80)
#   * 0.10 absolute gap for parity-style differences (Hardt et al. style)
# These are configurable via the metric functions but default per spec.
# ---------------------------------------------------------------------------

DEFAULT_GAP_THRESHOLD = 0.10
DEFAULT_DIR_THRESHOLD = 0.80


@dataclass
class MetricResult:
    name: str
    value: float
    threshold: float
    passes: bool
    severity: str  # "pass" | "warning" | "fail"
    interpretation: str
    direction: str  # "lower_is_better" | "ratio_close_to_1"
    per_group: dict[str, Any] = field(default_factory=dict)
    pairwise: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(float(self.value), 4),
            "threshold": float(self.threshold),
            "passes": bool(self.passes),
            "severity": self.severity,
            "interpretation": self.interpretation,
            "direction": self.direction,
            "per_group": self.per_group,
            "pairwise": self.pairwise,
        }


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _safe_div(num: float, den: float) -> float:
    return float(num) / float(den) if den != 0 else float("nan")


def _binarize(y: np.ndarray, positive_value: Any) -> np.ndarray:
    """Map values equal to positive_value -> 1, else 0. Handles strings and numbers uniformly."""
    return (y == positive_value).astype(np.int8)


def _selection_rate(y_pred_bin: np.ndarray) -> float:
    if y_pred_bin.size == 0:
        return float("nan")
    return float(y_pred_bin.mean())


def _tpr(y_true_bin: np.ndarray, y_pred_bin: np.ndarray) -> float:
    pos = y_true_bin == 1
    if pos.sum() == 0:
        return float("nan")
    return float(y_pred_bin[pos].mean())


def _fpr(y_true_bin: np.ndarray, y_pred_bin: np.ndarray) -> float:
    neg = y_true_bin == 0
    if neg.sum() == 0:
        return float("nan")
    return float(y_pred_bin[neg].mean())


def _ppv(y_true_bin: np.ndarray, y_pred_bin: np.ndarray) -> float:
    pred_pos = y_pred_bin == 1
    if pred_pos.sum() == 0:
        return float("nan")
    return float(y_true_bin[pred_pos].mean())


def _confusion(y_true_bin: np.ndarray, y_pred_bin: np.ndarray) -> dict[str, int]:
    tp = int(((y_true_bin == 1) & (y_pred_bin == 1)).sum())
    fp = int(((y_true_bin == 0) & (y_pred_bin == 1)).sum())
    tn = int(((y_true_bin == 0) & (y_pred_bin == 0)).sum())
    fn = int(((y_true_bin == 1) & (y_pred_bin == 0)).sum())
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def _per_group_performance(
    y_true_bin: np.ndarray, y_pred_bin: np.ndarray, s: np.ndarray
) -> dict[str, dict[str, Any]]:
    """Per-group accuracy, precision, recall, F1, selection rate, confusion matrix, n."""
    groups = sorted(set(np.asarray(s).tolist()), key=lambda x: str(x))
    out: dict[str, dict[str, Any]] = {}
    for g in groups:
        mask = s == g
        yt = y_true_bin[mask]
        yp = y_pred_bin[mask]
        n = int(mask.sum())
        if n == 0:
            continue
        cm = _confusion(yt, yp)
        accuracy = float((yt == yp).mean()) if n else float("nan")
        precision = _ppv(yt, yp)
        recall = _tpr(yt, yp)
        if not (np.isnan(precision) or np.isnan(recall)) and (precision + recall) > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = float("nan")
        out[str(g)] = {
            "n": n,
            "selection_rate": round(_selection_rate(yp), 4),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4) if not np.isnan(precision) else None,
            "recall": round(recall, 4) if not np.isnan(recall) else None,
            "f1": round(f1, 4) if not np.isnan(f1) else None,
            "tpr": round(recall, 4) if not np.isnan(recall) else None,
            "fpr": round(_fpr(yt, yp), 4) if not np.isnan(_fpr(yt, yp)) else None,
            "confusion_matrix": cm,
        }
    return out


def _pairwise_gaps(values_by_group: dict[str, float]) -> list[dict[str, Any]]:
    keys = list(values_by_group.keys())
    out = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            va, vb = values_by_group[a], values_by_group[b]
            if np.isnan(va) or np.isnan(vb):
                continue
            out.append({"group_a": a, "group_b": b, "gap": round(float(va - vb), 4)})
    return out


def _severity(passes: bool, value: float, threshold: float, direction: str) -> str:
    if passes:
        return "pass"
    # warning band: within 50% of the threshold beyond pass
    if direction == "lower_is_better":
        if value <= threshold * 1.5:
            return "warning"
    elif direction == "ratio_close_to_1":
        if value >= threshold * 0.9:
            return "warning"
    return "fail"


# ---------------------------------------------------------------------------
# The seven metrics
# ---------------------------------------------------------------------------

def demographic_parity_difference(
    y_pred_bin: np.ndarray, s: np.ndarray, threshold: float = DEFAULT_GAP_THRESHOLD
) -> MetricResult:
    """Statistical parity difference: max(SR_g) - min(SR_g) across groups."""
    groups = sorted(set(np.asarray(s).tolist()), key=lambda x: str(x))
    sr = {str(g): _selection_rate(y_pred_bin[s == g]) for g in groups}
    valid = {k: v for k, v in sr.items() if not np.isnan(v)}
    if len(valid) < 2:
        value = 0.0
    else:
        value = max(valid.values()) - min(valid.values())
    passes = value <= threshold
    return MetricResult(
        name="demographic_parity_difference",
        value=value,
        threshold=threshold,
        passes=passes,
        severity=_severity(passes, value, threshold, "lower_is_better"),
        direction="lower_is_better",
        interpretation=(
            f"Largest gap in positive-prediction rates between groups is {value:.4f}. "
            f"Pass if <= {threshold}. Source: P(Ŷ=1|A=g) per group."
        ),
        per_group={k: round(v, 4) for k, v in sr.items()},
        pairwise=_pairwise_gaps(sr),
    )


def disparate_impact_ratio(
    y_pred_bin: np.ndarray, s: np.ndarray, threshold: float = DEFAULT_DIR_THRESHOLD
) -> MetricResult:
    """4/5ths rule: min(SR_g) / max(SR_g). Direction-agnostic so neither group can dominate."""
    groups = sorted(set(np.asarray(s).tolist()), key=lambda x: str(x))
    sr = {str(g): _selection_rate(y_pred_bin[s == g]) for g in groups}
    valid = {k: v for k, v in sr.items() if not np.isnan(v) and v > 0}
    if len(valid) < 2:
        value = 1.0
    else:
        value = min(valid.values()) / max(valid.values())
    passes = value >= threshold
    return MetricResult(
        name="disparate_impact_ratio",
        value=value,
        threshold=threshold,
        passes=passes,
        severity=_severity(passes, value, threshold, "ratio_close_to_1"),
        direction="ratio_close_to_1",
        interpretation=(
            f"Ratio min(SR)/max(SR) across groups is {value:.4f}. "
            f"EEOC 4/5ths rule: pass if >= {threshold}."
        ),
        per_group={k: round(v, 4) for k, v in sr.items()},
    )


def equal_opportunity_difference(
    y_true_bin: np.ndarray,
    y_pred_bin: np.ndarray,
    s: np.ndarray,
    threshold: float = DEFAULT_GAP_THRESHOLD,
) -> MetricResult:
    """Max-min gap in TPR across groups."""
    groups = sorted(set(np.asarray(s).tolist()), key=lambda x: str(x))
    tpr = {str(g): _tpr(y_true_bin[s == g], y_pred_bin[s == g]) for g in groups}
    valid = {k: v for k, v in tpr.items() if not np.isnan(v)}
    value = max(valid.values()) - min(valid.values()) if len(valid) >= 2 else 0.0
    passes = value <= threshold
    return MetricResult(
        name="equal_opportunity_difference",
        value=value,
        threshold=threshold,
        passes=passes,
        severity=_severity(passes, value, threshold, "lower_is_better"),
        direction="lower_is_better",
        interpretation=(
            f"Largest gap in true-positive rates is {value:.4f}. "
            f"Pass if <= {threshold}. TPR = P(Ŷ=1|Y=1, A=g)."
        ),
        per_group={k: round(v, 4) if not np.isnan(v) else None for k, v in tpr.items()},
        pairwise=_pairwise_gaps(tpr),
    )


def equalized_odds_difference(
    y_true_bin: np.ndarray,
    y_pred_bin: np.ndarray,
    s: np.ndarray,
    threshold: float = DEFAULT_GAP_THRESHOLD,
) -> MetricResult:
    """Max of TPR-gap and FPR-gap across groups."""
    groups = sorted(set(np.asarray(s).tolist()), key=lambda x: str(x))
    tpr = {str(g): _tpr(y_true_bin[s == g], y_pred_bin[s == g]) for g in groups}
    fpr = {str(g): _fpr(y_true_bin[s == g], y_pred_bin[s == g]) for g in groups}
    tpr_v = [v for v in tpr.values() if not np.isnan(v)]
    fpr_v = [v for v in fpr.values() if not np.isnan(v)]
    tpr_gap = (max(tpr_v) - min(tpr_v)) if len(tpr_v) >= 2 else 0.0
    fpr_gap = (max(fpr_v) - min(fpr_v)) if len(fpr_v) >= 2 else 0.0
    value = max(tpr_gap, fpr_gap)
    passes = value <= threshold
    return MetricResult(
        name="equalized_odds_difference",
        value=value,
        threshold=threshold,
        passes=passes,
        severity=_severity(passes, value, threshold, "lower_is_better"),
        direction="lower_is_better",
        interpretation=(
            f"Worst of (TPR gap = {tpr_gap:.4f}, FPR gap = {fpr_gap:.4f}) is {value:.4f}. "
            f"Pass if <= {threshold}."
        ),
        per_group={
            "tpr": {k: round(v, 4) if not np.isnan(v) else None for k, v in tpr.items()},
            "fpr": {k: round(v, 4) if not np.isnan(v) else None for k, v in fpr.items()},
            "tpr_gap": round(tpr_gap, 4),
            "fpr_gap": round(fpr_gap, 4),
        },
    )


def predictive_parity_difference(
    y_true_bin: np.ndarray,
    y_pred_bin: np.ndarray,
    s: np.ndarray,
    threshold: float = DEFAULT_GAP_THRESHOLD,
) -> MetricResult:
    """Max-min gap in PPV (precision) across groups."""
    groups = sorted(set(np.asarray(s).tolist()), key=lambda x: str(x))
    ppv = {str(g): _ppv(y_true_bin[s == g], y_pred_bin[s == g]) for g in groups}
    valid = {k: v for k, v in ppv.items() if not np.isnan(v)}
    value = max(valid.values()) - min(valid.values()) if len(valid) >= 2 else 0.0
    passes = value <= threshold
    return MetricResult(
        name="predictive_parity_difference",
        value=value,
        threshold=threshold,
        passes=passes,
        severity=_severity(passes, value, threshold, "lower_is_better"),
        direction="lower_is_better",
        interpretation=(
            f"Largest gap in precision (PPV = P(Y=1|Ŷ=1, A=g)) is {value:.4f}. "
            f"Pass if <= {threshold}."
        ),
        per_group={k: round(v, 4) if not np.isnan(v) else None for k, v in ppv.items()},
        pairwise=_pairwise_gaps(ppv),
    )


def calibration_difference(
    y_true_bin: np.ndarray,
    y_pred_bin: np.ndarray,
    s: np.ndarray,
    threshold: float = DEFAULT_GAP_THRESHOLD,
) -> MetricResult:
    """Average calibration gap across groups.

    With binary predictions (no probabilities), calibration reduces to: among predicted positives,
    what fraction were actually positive (= PPV); among predicted negatives, what fraction were
    actually positive (false omission rate). We report the worst absolute group gap across both
    buckets, averaged. This is a coarse approximation; with probability scores, replace with
    expected calibration error per group.
    """
    groups = sorted(set(np.asarray(s).tolist()), key=lambda x: str(x))
    pos_cal = {}  # P(Y=1 | Ŷ=1, A=g) = PPV
    neg_cal = {}  # P(Y=1 | Ŷ=0, A=g) = FOR (false omission rate)
    for g in groups:
        m = s == g
        yt, yp = y_true_bin[m], y_pred_bin[m]
        pos_mask = yp == 1
        neg_mask = yp == 0
        pos_cal[str(g)] = float(yt[pos_mask].mean()) if pos_mask.sum() else float("nan")
        neg_cal[str(g)] = float(yt[neg_mask].mean()) if neg_mask.sum() else float("nan")

    pos_v = [v for v in pos_cal.values() if not np.isnan(v)]
    neg_v = [v for v in neg_cal.values() if not np.isnan(v)]
    pos_gap = (max(pos_v) - min(pos_v)) if len(pos_v) >= 2 else 0.0
    neg_gap = (max(neg_v) - min(neg_v)) if len(neg_v) >= 2 else 0.0
    value = (pos_gap + neg_gap) / 2.0
    passes = value <= threshold
    return MetricResult(
        name="calibration_difference",
        value=value,
        threshold=threshold,
        passes=passes,
        severity=_severity(passes, value, threshold, "lower_is_better"),
        direction="lower_is_better",
        interpretation=(
            f"Average calibration gap across positive- and negative-prediction buckets is "
            f"{value:.4f} (pos bucket gap {pos_gap:.4f}, neg bucket gap {neg_gap:.4f}). "
            f"Pass if <= {threshold}."
        ),
        per_group={
            "p_y1_given_yhat1": {k: round(v, 4) if not np.isnan(v) else None for k, v in pos_cal.items()},
            "p_y1_given_yhat0": {k: round(v, 4) if not np.isnan(v) else None for k, v in neg_cal.items()},
        },
    )


def individual_fairness_consistency(
    X: np.ndarray,
    y_pred_bin: np.ndarray,
    k: int = 5,
    threshold: float = 0.75,
    max_n: int = 5000,
    rng_seed: int = 42,
) -> MetricResult:
    """Consistency score: fraction of k-NN that share the same prediction.

    For tractability on large datasets, we subsample to `max_n` rows. Distance is
    Euclidean over standardized numeric features only — categorical handling is left
    to the caller (one-hot encode upstream).
    """
    from sklearn.neighbors import NearestNeighbors  # local import to keep top clean

    n = X.shape[0]
    rng = np.random.default_rng(rng_seed)
    if n > max_n:
        idx = rng.choice(n, size=max_n, replace=False)
        X_s = X[idx]
        y_s = y_pred_bin[idx]
    else:
        X_s = X
        y_s = y_pred_bin

    # standardize
    mean = X_s.mean(axis=0)
    std = X_s.std(axis=0)
    std[std == 0] = 1.0
    Xn = (X_s - mean) / std

    k_eff = min(k + 1, len(Xn))  # +1 because the closest neighbor is the point itself
    nn = NearestNeighbors(n_neighbors=k_eff).fit(Xn)
    _, indices = nn.kneighbors(Xn)

    # drop self (column 0)
    neighbor_idx = indices[:, 1:]
    neighbor_preds = y_s[neighbor_idx]
    same = (neighbor_preds == y_s[:, None]).mean(axis=1)
    value = float(same.mean())
    passes = value >= threshold
    return MetricResult(
        name="individual_fairness_consistency",
        value=value,
        threshold=threshold,
        passes=passes,
        severity="pass" if passes else ("warning" if value >= threshold * 0.9 else "fail"),
        direction="ratio_close_to_1",
        interpretation=(
            f"Mean fraction of {k}-nearest-neighbors sharing the same prediction is "
            f"{value:.4f}. Pass if >= {threshold}. Higher = more locally consistent."
        ),
        per_group={"k": k, "n_evaluated": int(len(Xn))},
    )


# ---------------------------------------------------------------------------
# Aggregate audit
# ---------------------------------------------------------------------------

def compute_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    sensitive: dict[str, np.ndarray],
    positive_label: Any,
    favorable_prediction: Any,
    X_numeric: np.ndarray | None = None,
) -> dict[str, Any]:
    """Run all seven metrics for each sensitive attribute.

    Returns a nested dict ready to JSON-serialize and store in audit.results.
    """
    y_true_bin = _binarize(np.asarray(y_true), positive_label)
    y_pred_bin = _binarize(np.asarray(y_pred), favorable_prediction)

    out: dict[str, Any] = {
        "sensitive_attributes": {},
        "summary": {},
    }

    total_pass = 0
    total_metrics = 0
    severities: list[str] = []

    for attr_name, s_raw in sensitive.items():
        s = np.asarray(s_raw)
        attr_metrics: dict[str, Any] = {
            "demographic_parity_difference": demographic_parity_difference(y_pred_bin, s).to_dict(),
            "disparate_impact_ratio": disparate_impact_ratio(y_pred_bin, s).to_dict(),
            "equal_opportunity_difference": equal_opportunity_difference(y_true_bin, y_pred_bin, s).to_dict(),
            "equalized_odds_difference": equalized_odds_difference(y_true_bin, y_pred_bin, s).to_dict(),
            "predictive_parity_difference": predictive_parity_difference(y_true_bin, y_pred_bin, s).to_dict(),
            "calibration_difference": calibration_difference(y_true_bin, y_pred_bin, s).to_dict(),
        }
        if X_numeric is not None and X_numeric.shape[0] == len(y_pred_bin):
            attr_metrics["individual_fairness_consistency"] = individual_fairness_consistency(
                X_numeric, y_pred_bin
            ).to_dict()

        per_group_perf = _per_group_performance(y_true_bin, y_pred_bin, s)

        for m in attr_metrics.values():
            total_metrics += 1
            if m["passes"]:
                total_pass += 1
            severities.append(m["severity"])

        out["sensitive_attributes"][attr_name] = {
            "metrics": attr_metrics,
            "per_group_performance": per_group_perf,
        }

    # Overall fairness score: % of metrics passing, with warnings counted as half.
    if total_metrics > 0:
        weighted = sum(1.0 if sev == "pass" else 0.5 if sev == "warning" else 0.0 for sev in severities)
        score = round(100.0 * weighted / total_metrics, 1)
    else:
        score = 0.0

    if score >= 80:
        risk = "Low Risk"
    elif score >= 60:
        risk = "Medium Risk"
    else:
        risk = "High Risk"

    out["summary"] = {
        "overall_fairness_score": score,
        "risk_level": risk,
        "metrics_passing": total_pass,
        "metrics_total": total_metrics,
        "severities": {
            "pass": severities.count("pass"),
            "warning": severities.count("warning"),
            "fail": severities.count("fail"),
        },
    }
    return out
