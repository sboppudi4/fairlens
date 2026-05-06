"""Bias mitigation suggestions.

For each FAILING fairness metric, produce a concrete, actionable mitigation
suggestion: technique name, description, complexity, expected improvement,
runnable Python snippet, and a citation.

The snippets favour `fairlearn` (mature, scikit-learn compatible) over the
older aif360, but reference both where appropriate. Snippets are deliberately
self-contained so a reader can copy/paste into a notebook.
"""
from __future__ import annotations

from typing import Any


_SUGGESTIONS: dict[str, list[dict[str, Any]]] = {
    "demographic_parity_difference": [
        {
            "technique": "Reweighing (preprocessing)",
            "description": (
                "Reweighing assigns a sample weight to each (group, label) cell so that group "
                "membership becomes statistically independent of the label in the reweighted training set. "
                "Apply the weights during model training; no model architecture change is needed."
            ),
            "complexity": "low",
            "expected_improvement": "Typically reduces demographic parity gap by 30–60%.",
            "code_snippet": (
                "from fairlearn.preprocessing import CorrelationRemover\n"
                "from sklearn.linear_model import LogisticRegression\n"
                "import pandas as pd, numpy as np\n\n"
                "# X: features (incl. one-hot of sensitive). A: sensitive attribute series.\n"
                "cr = CorrelationRemover(sensitive_feature_ids=['sex'], alpha=1.0)\n"
                "X_decorrelated = cr.fit_transform(X)\n"
                "model = LogisticRegression(max_iter=1000).fit(X_decorrelated, y)\n"
            ),
            "reference": "Kamiran & Calders (2012). Data preprocessing techniques for classification without discrimination.",
        },
        {
            "technique": "Threshold optimisation per group",
            "description": (
                "Calibrate per-group decision thresholds so that selection rates are equalised. "
                "Postprocessing only: original model is unchanged."
            ),
            "complexity": "low",
            "expected_improvement": "Can drive demographic parity gap to ~0; may sacrifice 1-3% accuracy.",
            "code_snippet": (
                "from fairlearn.postprocessing import ThresholdOptimizer\n"
                "from sklearn.ensemble import GradientBoostingClassifier\n\n"
                "base = GradientBoostingClassifier().fit(X_train, y_train)\n"
                "to = ThresholdOptimizer(estimator=base, constraints='demographic_parity',\n"
                "                       prefit=True, predict_method='predict_proba')\n"
                "to.fit(X_train, y_train, sensitive_features=A_train)\n"
                "y_pred = to.predict(X_test, sensitive_features=A_test)\n"
            ),
            "reference": "Hardt, Price, Srebro (2016). Equality of Opportunity in Supervised Learning.",
        },
    ],
    "disparate_impact_ratio": [
        {
            "technique": "Disparate Impact Remover (preprocessing)",
            "description": (
                "Edits feature distributions per group so that the rank within group is preserved but "
                "marginal distributions become aligned across groups, removing the proxy signal that "
                "produces disparate impact."
            ),
            "complexity": "medium",
            "expected_improvement": "Brings DIR > 0.8 in most benchmarks; trade-off ~1% accuracy.",
            "code_snippet": (
                "from aif360.algorithms.preprocessing import DisparateImpactRemover\n"
                "from aif360.datasets import StandardDataset\n\n"
                "dataset = StandardDataset(df, label_name='income', favorable_classes=['>50K'],\n"
                "                          protected_attribute_names=['sex'],\n"
                "                          privileged_classes=[['Male']])\n"
                "dir_remover = DisparateImpactRemover(repair_level=1.0)\n"
                "repaired = dir_remover.fit_transform(dataset)\n"
            ),
            "reference": "Feldman et al. (2015). Certifying and removing disparate impact.",
        },
        {
            "technique": "Adversarial debiasing (in-processing)",
            "description": (
                "Train a classifier with an adversary that tries to predict the sensitive attribute from the "
                "main model's predictions. The classifier learns to satisfy the prediction task while denying "
                "the adversary, removing dependence on the sensitive attribute."
            ),
            "complexity": "high",
            "expected_improvement": "DIR typically rises into the 0.85–0.95 band; requires GPU for large datasets.",
            "code_snippet": (
                "from fairlearn.reductions import ExponentiatedGradient, DemographicParity\n"
                "from sklearn.linear_model import LogisticRegression\n\n"
                "estimator = LogisticRegression(max_iter=1000)\n"
                "expg = ExponentiatedGradient(estimator, constraints=DemographicParity(),\n"
                "                              eps=0.05)\n"
                "expg.fit(X_train, y_train, sensitive_features=A_train)\n"
                "y_pred = expg.predict(X_test)\n"
            ),
            "reference": "Zhang, Lemoine, Mitchell (2018). Mitigating Unwanted Biases with Adversarial Learning.",
        },
    ],
    "equal_opportunity_difference": [
        {
            "technique": "Equalised odds postprocessing",
            "description": (
                "Hardt et al. derive a randomised postprocessing transform that achieves equal TPR (and FPR) "
                "across groups while staying as close as possible to the original classifier."
            ),
            "complexity": "low",
            "expected_improvement": "TPR gap < 0.05 in most cases.",
            "code_snippet": (
                "from fairlearn.postprocessing import ThresholdOptimizer\n"
                "to = ThresholdOptimizer(estimator=base_model, constraints='true_positive_rate_parity',\n"
                "                       prefit=True, predict_method='predict_proba')\n"
                "to.fit(X_train, y_train, sensitive_features=A_train)\n"
                "y_pred = to.predict(X_test, sensitive_features=A_test)\n"
            ),
            "reference": "Hardt, Price, Srebro (2016). Equality of Opportunity in Supervised Learning.",
        },
    ],
    "equalized_odds_difference": [
        {
            "technique": "Equalised odds postprocessing (joint TPR + FPR parity)",
            "description": (
                "Same Hardt-style postprocessing as for equal opportunity, but jointly enforces both TPR "
                "and FPR parity across groups."
            ),
            "complexity": "low",
            "expected_improvement": "Joint gap < 0.05 in most cases.",
            "code_snippet": (
                "from fairlearn.postprocessing import ThresholdOptimizer\n"
                "to = ThresholdOptimizer(estimator=base_model, constraints='equalized_odds',\n"
                "                       prefit=True, predict_method='predict_proba')\n"
                "to.fit(X_train, y_train, sensitive_features=A_train)\n"
                "y_pred = to.predict(X_test, sensitive_features=A_test)\n"
            ),
            "reference": "Hardt et al. (2016); fairlearn user guide §postprocessing.",
        },
    ],
    "predictive_parity_difference": [
        {
            "technique": "Calibration-by-group + threshold tuning",
            "description": (
                "Fit a per-group isotonic calibrator on a held-out validation set; then choose group-specific "
                "thresholds to align precision (PPV) across groups."
            ),
            "complexity": "medium",
            "expected_improvement": "PPV gap typically falls below 0.03.",
            "code_snippet": (
                "from sklearn.isotonic import IsotonicRegression\n"
                "calibrators = {g: IsotonicRegression(out_of_bounds='clip').fit(p_val[A_val==g], y_val[A_val==g])\n"
                "               for g in np.unique(A_val)}\n"
                "p_cal = np.where(A_test=='F', calibrators['F'].transform(p_test),\n"
                "                                calibrators['M'].transform(p_test))\n"
            ),
            "reference": "Pleiss et al. (2017). On Fairness and Calibration.",
        },
    ],
    "calibration_difference": [
        {
            "technique": "Per-group isotonic / Platt calibration",
            "description": (
                "Train one calibrator per group on a held-out set and apply at inference. This is the "
                "standard remedy when PPV / FOR differ across groups."
            ),
            "complexity": "low",
            "expected_improvement": "Calibration error per group brought below 0.02 on most benchmarks.",
            "code_snippet": (
                "from sklearn.calibration import CalibratedClassifierCV\n"
                "models = {g: CalibratedClassifierCV(base_model, method='isotonic', cv='prefit').\n"
                "             fit(X_val[A_val==g], y_val[A_val==g])\n"
                "          for g in np.unique(A_val)}\n"
            ),
            "reference": "Niculescu-Mizil & Caruana (2005). Predicting Good Probabilities with Supervised Learning.",
        },
    ],
    "individual_fairness_consistency": [
        {
            "technique": "Lipschitz-regularised training",
            "description": (
                "Add a regulariser penalising the difference in model output between pairs of similar "
                "training points. Encourages the model to give similar predictions to similar individuals."
            ),
            "complexity": "high",
            "expected_improvement": "Consistency rises by 10–20 percentage points; small accuracy cost.",
            "code_snippet": (
                "# Pseudocode — frameworks differ.\n"
                "for x_i, x_j in similar_pairs:                      # k-NN pairs\n"
                "    consistency_loss += (model(x_i) - model(x_j))**2\n"
                "loss = ce_loss + lambda_consistency * consistency_loss\n"
            ),
            "reference": "Dwork et al. (2012). Fairness Through Awareness.",
        },
    ],
}


_PROXY_SUGGESTION = {
    "technique": "Address proxy discrimination",
    "description": (
        "SHAP analysis flagged one or more features whose importance differs materially across "
        "demographic groups. Such features may be acting as proxies for a sensitive attribute. "
        "Investigate by (1) computing the correlation between each flagged feature and the sensitive "
        "attribute, (2) fitting a regression model that predicts the sensitive attribute from the "
        "feature alone, and (3) considering removal, transformation (residualisation against the "
        "sensitive attribute), or fairness-constrained re-training."
    ),
    "complexity": "medium",
    "expected_improvement": (
        "Removing or residualising a high-leakage proxy commonly cuts demographic parity gap by half."
    ),
    "code_snippet": (
        "import statsmodels.api as sm\n"
        "# Residualise feature against sensitive attribute (one-hot encoded):\n"
        "A_oh = pd.get_dummies(A, drop_first=True)\n"
        "model_proxy = sm.OLS(df['proxy_feature'], sm.add_constant(A_oh)).fit()\n"
        "df['proxy_feature_residualised'] = df['proxy_feature'] - model_proxy.predict(sm.add_constant(A_oh))\n"
        "# Refit your classifier with the residualised feature.\n"
    ),
    "reference": "Kilbertus et al. (2017). Avoiding Discrimination through Causal Reasoning.",
}


def build_mitigations(metrics_block: dict[str, Any], shap_block: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a flat list of mitigation suggestions for the audit report.

    Parameters
    ----------
    metrics_block : output['sensitive_attributes'] from compute_all_metrics.
    shap_block : output of analyze_shap (may have available=False).

    Returns
    -------
    list of suggestion dicts, one per (sensitive_attribute, failing_metric) pair,
    plus one global proxy-discrimination suggestion if SHAP flagged any.
    """
    out: list[dict[str, Any]] = []

    for attr_name, attr_block in metrics_block.items():
        for metric_name, metric in attr_block.get("metrics", {}).items():
            if metric.get("passes"):
                continue
            for s in _SUGGESTIONS.get(metric_name, []):
                out.append({
                    "sensitive_attribute": attr_name,
                    "failing_metric": metric_name,
                    "metric_value": metric.get("value"),
                    "metric_severity": metric.get("severity"),
                    **s,
                })

    if shap_block.get("available") and shap_block.get("proxy_warnings"):
        # one consolidated proxy suggestion, with the flagged features attached
        flagged = [
            f"{w['feature']} (rel gap {w['relative_gap']:.2%}, attribute '{w['sensitive_attribute']}')"
            for w in shap_block["proxy_warnings"][:5]
        ]
        out.append({
            "sensitive_attribute": "(multiple)",
            "failing_metric": "shap_proxy_discrimination",
            "metric_value": None,
            "metric_severity": "warning",
            **_PROXY_SUGGESTION,
            "flagged_features": flagged,
        })

    return out
