"""Matplotlib chart generation for the PDF report.

Each function returns PNG bytes ready to embed in ReportLab. Charts use the
FairLens palette (deep navy headers, accent blue, traffic-light pass/fail).

The module is import-safe: on first call it forces the non-interactive 'Agg'
backend so it works in Celery workers without a display.
"""
from __future__ import annotations

import io
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# FairLens palette
NAVY = "#1a2744"
ACCENT = "#2563eb"
PASS = "#16a34a"
WARN = "#d97706"
FAIL = "#dc2626"
MUTED = "#64748b"
BG = "#ffffff"


def _style() -> None:
    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "axes.edgecolor": "#cbd5e1",
        "axes.labelcolor": NAVY,
        "axes.titlecolor": NAVY,
        "axes.titleweight": "bold",
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "savefig.bbox": "tight",
        "savefig.dpi": 150,
    })


def _save(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


def _severity_color(severity: str) -> str:
    return {"pass": PASS, "warning": WARN, "fail": FAIL}.get(severity, MUTED)


def fairness_score_gauge(score: float, risk_level: str) -> bytes:
    """Half-circle gauge with the overall fairness score in the middle."""
    _style()
    fig, ax = plt.subplots(figsize=(5, 3), subplot_kw={"projection": "polar"})
    ax.set_theta_zero_location("W")
    ax.set_theta_direction(-1)

    score = max(0.0, min(100.0, float(score)))
    # background arc
    theta_full = np.linspace(0, np.pi, 200)
    ax.bar(x=theta_full, height=1.0, width=np.pi / 200, color="#e5e7eb", edgecolor="none")
    # filled arc proportional to score
    fill_theta = np.linspace(0, np.pi * (score / 100.0), max(2, int(score * 2)))
    color = PASS if score >= 80 else (WARN if score >= 60 else FAIL)
    ax.bar(x=fill_theta, height=1.0, width=np.pi / 200, color=color, edgecolor="none")

    ax.set_ylim(0, 1.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)

    fig.text(0.5, 0.40, f"{score:.0f}", ha="center", va="center",
             fontsize=42, fontweight="bold", color=NAVY)
    fig.text(0.5, 0.22, "Fairness Score", ha="center", va="center", fontsize=11, color=MUTED)
    fig.text(0.5, 0.10, risk_level, ha="center", va="center", fontsize=12, fontweight="bold", color=color)
    return _save(fig)


def selection_rate_per_group(per_group: dict[str, dict[str, Any]], title: str) -> bytes:
    _style()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    groups = list(per_group.keys())
    rates = [per_group[g].get("selection_rate", 0) or 0 for g in groups]
    bars = ax.bar(groups, rates, color=ACCENT, edgecolor=NAVY)
    for bar, val in zip(bars, rates, strict=False):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", fontsize=9, color=NAVY)
    ax.set_ylim(0, max(1.0, max(rates) * 1.2 if rates else 1.0))
    ax.set_ylabel("Positive prediction rate")
    ax.set_title(f"Selection rate by group — {title}")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return _save(fig)


def metrics_bar(metrics: dict[str, dict[str, Any]], title: str) -> bytes:
    """Bar chart of metric values, color-coded by severity."""
    _style()
    fig, ax = plt.subplots(figsize=(7.5, 4))
    names = list(metrics.keys())
    short = [n.replace("_", "\n") for n in names]
    values = [metrics[n]["value"] for n in names]
    colors = [_severity_color(metrics[n]["severity"]) for n in names]
    ax.barh(short, values, color=colors, edgecolor=NAVY)
    ax.set_xlabel("Value")
    ax.set_title(f"Fairness metrics — {title}")
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return _save(fig)


def feature_importance_bar(items: list[dict[str, Any]], title: str = "Global feature importance") -> bytes:
    _style()
    fig, ax = plt.subplots(figsize=(7.5, 5))
    items = sorted(items, key=lambda x: x["mean_abs_shap"])
    names = [i["feature"][:30] for i in items]
    vals = [i["mean_abs_shap"] for i in items]
    ax.barh(names, vals, color=ACCENT, edgecolor=NAVY)
    ax.set_xlabel("Mean |SHAP|")
    ax.set_title(title)
    fig.tight_layout()
    return _save(fig)


def grouped_feature_importance(per_group: dict[str, list[dict[str, Any]]], title: str) -> bytes:
    """Grouped bar chart: top 10 features × demographic groups."""
    _style()
    if not per_group:
        return b""
    # union of top features across groups, capped at 10
    feature_set: list[str] = []
    for top in per_group.values():
        for entry in top:
            if entry["feature"] not in feature_set:
                feature_set.append(entry["feature"])
            if len(feature_set) >= 10:
                break
        if len(feature_set) >= 10:
            break

    groups = list(per_group.keys())
    n_groups = len(groups)
    x = np.arange(len(feature_set))
    width = 0.8 / max(n_groups, 1)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cmap = plt.get_cmap("tab10")
    for i, g in enumerate(groups):
        lookup = {e["feature"]: e["mean_abs_shap"] for e in per_group[g]}
        vals = [lookup.get(f, 0) for f in feature_set]
        ax.bar(x + i * width, vals, width, label=str(g), color=cmap(i))
    ax.set_xticks(x + width * (n_groups - 1) / 2)
    ax.set_xticklabels([f[:18] for f in feature_set], rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Mean |SHAP|")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig)


def label_distribution(labels: list[Any], counts: list[int], title: str = "Label distribution") -> bytes:
    _style()
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar([str(label) for label in labels], counts, color=ACCENT, edgecolor=NAVY)
    ax.set_title(title)
    ax.set_ylabel("Count")
    fig.tight_layout()
    return _save(fig)
