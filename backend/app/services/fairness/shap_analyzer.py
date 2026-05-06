"""SHAP explainability analysis.

Given a dataset with a label column, this module trains a default XGBoost
classifier (if no model is supplied), computes SHAP values, and surfaces:

  * Global feature importance (mean |SHAP|).
  * Per-demographic-group feature importance (so the UI/PDF can compare
    which features drive predictions for each group).
  * "Proxy discrimination" warnings — features whose importance differs by
    more than 20% between any two groups, indicating the model may be
    indirectly using a sensitive attribute through a correlated proxy.

The output is JSON-serializable and bounded in size: the per-row SHAP matrix
is NOT returned, only aggregate statistics. This keeps audit.results compact.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

# Top features kept in summaries
_TOP_K = 15
# Threshold for proxy-discrimination flag (relative difference in mean |SHAP|)
_PROXY_THRESHOLD = 0.20


def _train_default_model(X: pd.DataFrame, y: np.ndarray) -> Any:
    import xgboost as xgb  # local import to keep top clean

    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        n_jobs=1,
        eval_metric="logloss",
        tree_method="hist",
        verbosity=0,
        random_state=42,
    )
    model.fit(X, y)
    return model


def _encode_features(df: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """One-hot encode categoricals, leave numerics alone. Returns (X, feature_names)."""
    X = df[feature_cols].copy()
    cat_cols = [c for c in X.columns if X[c].dtype == "object" or str(X[c].dtype).startswith("category")]
    if cat_cols:
        X = pd.get_dummies(X, columns=cat_cols, drop_first=False, dummy_na=False)
    # Coerce remaining to float; non-convertible -> NaN -> fill 0
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    X = X.fillna(0.0).astype(np.float32)
    return X, list(X.columns)


def analyze_shap(
    df: pd.DataFrame,
    label_column: str,
    prediction_column: str,
    sensitive_columns: list[str],
    positive_label: str,
    max_rows: int = 5000,
    rng_seed: int = 42,
) -> dict[str, Any]:
    """Run SHAP analysis end-to-end.

    Parameters
    ----------
    df : DataFrame containing all columns (label, prediction, sensitive, features).
    label_column : ground-truth label column.
    prediction_column : column with the model's prediction (excluded from features).
    sensitive_columns : columns to break SHAP importance down by (also excluded from features).
    positive_label : value of label_column treated as the positive class.
    max_rows : subsample for tractability.

    Returns dict with: feature_importance (global), per_group, proxy_warnings, top_features.
    Returns {"available": False, "reason": "..."} on failure.
    """
    try:
        import shap  # local import, heavy dependency
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": f"shap import failed: {e}"}

    try:
        # Subsample for tractable SHAP runtime
        rng = np.random.default_rng(rng_seed)
        if len(df) > max_rows:
            idx = rng.choice(len(df), size=max_rows, replace=False)
            df_s = df.iloc[idx].reset_index(drop=True)
        else:
            df_s = df.reset_index(drop=True)

        # Build label vector
        y = (df_s[label_column].astype(str) == str(positive_label)).astype(np.int8).to_numpy()
        if y.sum() == 0 or y.sum() == len(y):
            return {
                "available": False,
                "reason": "Label column is constant; cannot fit explainability model.",
            }

        feature_cols = [
            c for c in df_s.columns
            if c not in {label_column, prediction_column, *sensitive_columns}
        ]
        if not feature_cols:
            return {"available": False, "reason": "No feature columns available for SHAP analysis."}

        X, feature_names = _encode_features(df_s, feature_cols)

        model = _train_default_model(X, y)

        # TreeExplainer is fast and exact for tree models
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        # XGBoost binary → 2D array (rows x features)
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        shap_values = np.asarray(shap_values)
        if shap_values.ndim == 3:
            shap_values = shap_values[:, :, 1] if shap_values.shape[2] > 1 else shap_values[:, :, 0]

        abs_shap = np.abs(shap_values)
        global_importance = abs_shap.mean(axis=0)
        order = np.argsort(-global_importance)
        top_idx = order[:_TOP_K]
        feature_importance = [
            {"feature": feature_names[i], "mean_abs_shap": round(float(global_importance[i]), 6)}
            for i in top_idx
        ]

        # Per-group importance
        per_group: dict[str, dict[str, list[dict[str, Any]]]] = {}
        proxy_warnings: list[dict[str, Any]] = []
        for sens_col in sensitive_columns:
            s = df_s[sens_col].astype(str).to_numpy()
            groups = sorted(set(s.tolist()))
            group_importance_map: dict[str, np.ndarray] = {}
            group_top: dict[str, list[dict[str, Any]]] = {}
            for g in groups:
                mask = s == g
                if mask.sum() < 5:
                    continue
                gi = np.abs(shap_values[mask]).mean(axis=0)
                group_importance_map[g] = gi
                top_g_idx = np.argsort(-gi)[:_TOP_K]
                group_top[g] = [
                    {"feature": feature_names[i], "mean_abs_shap": round(float(gi[i]), 6)}
                    for i in top_g_idx
                ]
            per_group[sens_col] = group_top

            # Proxy discrimination: for each feature, max gap in mean |SHAP| across groups
            # Flag if relative gap > _PROXY_THRESHOLD AND absolute importance is meaningful.
            if len(group_importance_map) >= 2:
                imps = np.stack(list(group_importance_map.values()), axis=0)  # (n_groups, n_features)
                f_max = imps.max(axis=0)
                f_min = imps.min(axis=0)
                significant = f_max > (global_importance.mean())  # ignore noise floor
                rel = np.where(f_max > 0, (f_max - f_min) / f_max, 0.0)
                for i, feat in enumerate(feature_names):
                    if significant[i] and rel[i] >= _PROXY_THRESHOLD:
                        proxy_warnings.append({
                            "sensitive_attribute": sens_col,
                            "feature": feat,
                            "max_group_importance": round(float(f_max[i]), 6),
                            "min_group_importance": round(float(f_min[i]), 6),
                            "relative_gap": round(float(rel[i]), 4),
                            "interpretation": (
                                f"Feature '{feat}' has materially different SHAP importance "
                                f"across groups of '{sens_col}' (relative gap {rel[i]:.2%}). "
                                f"Investigate as a possible proxy for the sensitive attribute."
                            ),
                        })

        # Sort proxy warnings by severity, cap to top 20
        proxy_warnings.sort(key=lambda x: -x["relative_gap"])
        proxy_warnings = proxy_warnings[:20]

        return {
            "available": True,
            "n_samples_explained": int(len(df_s)),
            "n_features": len(feature_names),
            "feature_importance": feature_importance,
            "per_group": per_group,
            "proxy_warnings": proxy_warnings,
        }
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": f"SHAP analysis failed: {e}"}
