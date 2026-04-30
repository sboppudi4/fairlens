"""Regulatory mapping for fairness metrics.

Each fairness metric is mapped to specific clauses in the three frameworks
that govern AI fairness in the Union and adjacent jurisdictions:

  * EU AI Act — Regulation (EU) 2024/1689
  * NIST AI Risk Management Framework — NIST AI 100-1 (Jan 2023)
  * ISO/IEC 42001:2023 — AI Management System

Citations are verbatim where space permits. Article/control numbers refer to
the published texts uploaded as the authoritative source for FairLens.

The output of build_regulatory_mapping() is a list of compliance items
suitable for the audit results JSON and the PDF Regulatory Compliance page.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Per-metric mapping table. Keys match metric names emitted by metrics.py.
# Each entry contains tuples of (framework, locator, title, quoted_text, why_it_applies).
# ---------------------------------------------------------------------------

_METRIC_MAPPING: dict[str, list[dict[str, str]]] = {
    "demographic_parity_difference": [
        {
            "framework": "EU AI Act",
            "locator": "Article 10(2)(f)–(g)",
            "title": "Data and data governance — bias examination and mitigation",
            "quote": (
                "examination in view of possible biases that are likely to affect the health "
                "and safety of persons, have a negative impact on fundamental rights or lead "
                "to discrimination prohibited under Union law … appropriate measures to "
                "detect, prevent and mitigate possible biases identified."
            ),
            "rationale": (
                "Demographic parity differences are the most direct quantitative evidence of "
                "the kind of disparity that Article 10 obliges providers to detect and mitigate."
            ),
        },
        {
            "framework": "NIST AI RMF",
            "locator": "MEASURE 2.11",
            "title": "Fairness and bias evaluated and results documented",
            "quote": "Fairness and bias — as identified in the MAP function — are evaluated and results are documented.",
            "rationale": (
                "Statistical parity is one of the canonical fairness metrics that this "
                "subcategory expects to be measured and recorded."
            ),
        },
        {
            "framework": "ISO/IEC 42001",
            "locator": "Annex A — A.7.4 Quality of data",
            "title": "Quality of data for AI systems",
            "quote": (
                "The organization shall consider the impact of bias on system performance and "
                "system fairness and make such adjustments as necessary to the model and data "
                "used to improve performance and fairness so they are acceptable for the use case."
            ),
            "rationale": (
                "Selection-rate disparities indicate the data/model bias that A.7.4 requires the "
                "organization to detect and adjust for."
            ),
        },
    ],
    "disparate_impact_ratio": [
        {
            "framework": "EU AI Act",
            "locator": "Article 10(2)(f)",
            "title": "Examination for biases leading to prohibited discrimination",
            "quote": (
                "examination in view of possible biases … that are likely to … lead to "
                "discrimination prohibited under Union law."
            ),
            "rationale": (
                "The 4/5ths rule originates in US EEOC enforcement of disparate-impact "
                "discrimination; the same practical test is used in EU compliance audits as a "
                "screen for prohibited indirect discrimination."
            ),
        },
        {
            "framework": "NIST AI RMF",
            "locator": "MAP 5.1",
            "title": "Likelihood and magnitude of impacts identified",
            "quote": (
                "Likelihood and magnitude of each identified impact (both potentially beneficial "
                "and harmful) … are identified and documented."
            ),
            "rationale": (
                "DIR < 0.8 is a documented signal that adverse impact is likely on the affected "
                "group, satisfying the magnitude-of-impact identification requirement."
            ),
        },
        {
            "framework": "ISO/IEC 42001",
            "locator": "Annex A — A.5.4 Assessing AI system impact on individuals or groups",
            "title": "Assessment of impact on individuals or groups of individuals",
            "quote": (
                "The organization shall assess and document the potential impacts of AI systems "
                "to individuals or groups of individuals throughout the system's life cycle."
            ),
            "rationale": "The ratio quantifies the disparate impact on a protected group.",
        },
    ],
    "equal_opportunity_difference": [
        {
            "framework": "EU AI Act",
            "locator": "Article 15(1)",
            "title": "Accuracy, robustness and cybersecurity",
            "quote": (
                "High-risk AI systems shall be designed and developed in such a way that they "
                "achieve an appropriate level of accuracy, robustness, and cybersecurity, and "
                "that they perform consistently in those respects throughout their lifecycle."
            ),
            "rationale": (
                "TPR gaps demonstrate that the system does NOT perform consistently across "
                "demographic groups — directly within Article 15's scope."
            ),
        },
        {
            "framework": "NIST AI RMF",
            "locator": "MEASURE 2.3",
            "title": "Performance demonstrated for deployment conditions",
            "quote": (
                "AI system performance or assurance criteria are measured qualitatively or "
                "quantitatively and demonstrated for conditions similar to deployment setting(s)."
            ),
            "rationale": "Group-disaggregated TPR is the deployment-condition performance breakdown.",
        },
        {
            "framework": "ISO/IEC 42001",
            "locator": "Annex A — A.6.2.4 AI system verification and validation",
            "title": "Verification and validation measures",
            "quote": (
                "The organization shall define and document verification and validation measures "
                "for the AI system and specify criteria for their use."
            ),
            "rationale": "Equal opportunity is a per-group V&V criterion.",
        },
    ],
    "equalized_odds_difference": [
        {
            "framework": "EU AI Act",
            "locator": "Article 9(1)–(2)",
            "title": "Risk management system",
            "quote": (
                "A risk management system shall be established, implemented, documented and "
                "maintained in relation to high-risk AI systems."
            ),
            "rationale": (
                "Equalized odds combines TPR and FPR gaps; both are risks the Article 9 RMS "
                "must identify, estimate, and treat."
            ),
        },
        {
            "framework": "NIST AI RMF",
            "locator": "MEASURE 2.11 + GOVERN 1.2",
            "title": "Trustworthy-AI characteristics integrated into policy and measured",
            "quote": (
                "The characteristics of trustworthy AI are integrated into organizational "
                "policies, processes, procedures, and practices."
            ),
            "rationale": (
                "Equalized odds is the standard joint check for the Fair-with-Harmful-Bias-Managed "
                "characteristic."
            ),
        },
        {
            "framework": "ISO/IEC 42001",
            "locator": "Clause 6.1.2 / Clause 9.1",
            "title": "Risk assessment and monitoring of AI performance",
            "quote": (
                "The organization shall determine: what needs to be monitored and measured; the "
                "methods … to ensure valid results; when the monitoring and measuring shall be "
                "performed."
            ),
            "rationale": "TPR/FPR gaps are exactly the kind of result Clause 9.1 expects to be monitored.",
        },
    ],
    "predictive_parity_difference": [
        {
            "framework": "EU AI Act",
            "locator": "Article 13(3)(b)(ii)",
            "title": "Transparency — accuracy metrics in instructions for use",
            "quote": (
                "the level of accuracy, including its metrics, robustness and cybersecurity … "
                "and any known and foreseeable circumstances that may have an impact on that "
                "expected level of accuracy, robustness and cybersecurity."
            ),
            "rationale": (
                "Per-group precision (PPV) is a primary disaggregated accuracy metric that must "
                "be disclosed to deployers."
            ),
        },
        {
            "framework": "NIST AI RMF",
            "locator": "MEASURE 2.11",
            "title": "Fairness and bias evaluated and documented",
            "quote": "Fairness and bias — as identified in the MAP function — are evaluated and results are documented.",
            "rationale": "Predictive parity is one of three canonical group-fairness criteria.",
        },
        {
            "framework": "ISO/IEC 42001",
            "locator": "Annex A — A.6.2.6 AI system operation and monitoring",
            "title": "Performance monitoring with disaggregated metrics",
            "quote": (
                "system and performance monitoring … to ensure that the AI system continues to "
                "meet its design goals and operates on production data as intended."
            ),
            "rationale": "Per-group PPV monitoring is required to detect drift in calibration on subpopulations.",
        },
    ],
    "calibration_difference": [
        {
            "framework": "EU AI Act",
            "locator": "Article 15(1) + Recital 67",
            "title": "Consistent performance across the lifecycle",
            "quote": (
                "perform consistently in those respects throughout their lifecycle … data sets "
                "for training, validation and testing … shall have the appropriate statistical "
                "properties, including, where applicable, as regards the persons or groups of "
                "persons in relation to whom the high-risk AI system is intended to be used."
            ),
            "rationale": (
                "Calibration gaps signal that statistical properties differ across groups in a way "
                "that Article 15 / Recital 67 requires to be addressed."
            ),
        },
        {
            "framework": "NIST AI RMF",
            "locator": "MEASURE 2.5 + MEASURE 2.11",
            "title": "Validity, reliability, and bias evaluation",
            "quote": (
                "The AI system to be deployed is demonstrated to be valid and reliable. "
                "Limitations of the generalizability beyond the conditions under which the "
                "technology was developed are documented."
            ),
            "rationale": "Calibration is the classical test of validity per group.",
        },
        {
            "framework": "ISO/IEC 42001",
            "locator": "Annex A — A.6.2.4",
            "title": "Verification and validation",
            "quote": (
                "The organization shall define and document verification and validation measures "
                "for the AI system and specify criteria for their use."
            ),
            "rationale": "Per-group calibration is a required V&V criterion.",
        },
    ],
    "individual_fairness_consistency": [
        {
            "framework": "EU AI Act",
            "locator": "Article 15(4)",
            "title": "Robustness — consistent behaviour under perturbations",
            "quote": (
                "High-risk AI systems shall be as resilient as possible regarding errors, faults "
                "or inconsistencies that may occur within the system or the environment in which "
                "the system operates."
            ),
            "rationale": (
                "Local consistency (similar inputs → similar outputs) is the operational test of "
                "Article 15(4) at the individual level."
            ),
        },
        {
            "framework": "NIST AI RMF",
            "locator": "MEASURE 2.7",
            "title": "Security and resilience evaluated",
            "quote": "AI system security and resilience — as identified in the MAP function — are evaluated and documented.",
            "rationale": "Individual fairness is the resilience-to-perturbation test on demographically similar inputs.",
        },
        {
            "framework": "ISO/IEC 42001",
            "locator": "Annex C — C.2.8 Robustness",
            "title": "Robustness as an organizational objective",
            "quote": (
                "robustness properties demonstrate the ability (or inability) of the system to "
                "have comparable performance on new data as on the data on which it was trained "
                "or the data of typical operations."
            ),
            "rationale": "Consistency across nearest neighbours is a direct measure of this property.",
        },
    ],
}


# ---------------------------------------------------------------------------
# Cross-cutting clauses that always apply to a fairness audit run as a whole.
# ---------------------------------------------------------------------------

_CROSS_CUTTING: list[dict[str, str]] = [
    {
        "framework": "EU AI Act",
        "locator": "Article 9 — Risk management system",
        "title": "Establishing the risk management process",
        "quote": (
            "A risk management system shall be established, implemented, documented and "
            "maintained in relation to high-risk AI systems. The risk management system shall be "
            "understood as a continuous iterative process planned and run throughout the entire "
            "lifecycle of a high-risk AI system."
        ),
        "rationale": "A FairLens audit is one execution of this iterative process.",
    },
    {
        "framework": "EU AI Act",
        "locator": "Article 27 — Fundamental rights impact assessment",
        "title": "FRIA for deployers of certain high-risk AI systems",
        "quote": (
            "deployers … shall perform an assessment of the impact on fundamental rights that "
            "the use of such system may produce."
        ),
        "rationale": "The audit report is a structured input to the deployer's FRIA.",
    },
    {
        "framework": "NIST AI RMF",
        "locator": "GOVERN 1.2 + MAP 5.1",
        "title": "Trustworthiness characteristics and impact identification",
        "quote": (
            "The characteristics of trustworthy AI are integrated into organizational policies … "
            "Likelihood and magnitude of each identified impact … are identified and documented."
        ),
        "rationale": "The audit operationalizes both subcategories.",
    },
    {
        "framework": "ISO/IEC 42001",
        "locator": "Clause 6.1.4 — AI system impact assessment",
        "title": "Assessing potential consequences for individuals, groups, and societies",
        "quote": (
            "The organization shall define a process for assessing the potential consequences for "
            "individuals or groups of individuals, or both, and societies that can result from the "
            "development, provision or use of AI systems."
        ),
        "rationale": "A FairLens audit is one such assessment.",
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_regulatory_mapping(metric_results: dict[str, Any]) -> dict[str, Any]:
    """Build the regulatory compliance section of an audit result.

    Parameters
    ----------
    metric_results : dict
        The 'sensitive_attributes' subtree of the metrics output. Each attribute key
        maps to {'metrics': {metric_name: {..., 'passes': bool}}}.

    Returns
    -------
    dict with keys:
        - frameworks: per-framework summary {compliant, total, items}
        - cross_cutting: list of always-applicable items
        - per_metric: list per metric, with status per framework
    """
    per_metric: list[dict[str, Any]] = []
    framework_totals: dict[str, dict[str, int]] = {}

    for attr_name, attr_block in metric_results.items():
        for metric_name, metric in attr_block.get("metrics", {}).items():
            mapping_entries = _METRIC_MAPPING.get(metric_name, [])
            passes = bool(metric.get("passes", False))
            for entry in mapping_entries:
                fw = entry["framework"]
                t = framework_totals.setdefault(fw, {"compliant": 0, "non_compliant": 0, "total": 0})
                t["total"] += 1
                if passes:
                    t["compliant"] += 1
                    status = "compliant"
                else:
                    t["non_compliant"] += 1
                    status = "non_compliant"
                per_metric.append({
                    "sensitive_attribute": attr_name,
                    "metric": metric_name,
                    "metric_value": metric.get("value"),
                    "metric_passes": passes,
                    "framework": fw,
                    "locator": entry["locator"],
                    "title": entry["title"],
                    "quote": entry["quote"],
                    "rationale": entry["rationale"],
                    "status": status,
                    "action_required": (
                        None if passes
                        else f"Mitigate the bias surfaced by {metric_name} on attribute '{attr_name}' "
                             f"before deployment, and document the mitigation in the {fw} compliance file."
                    ),
                })

    # Per-framework summary with compliance percentage
    frameworks = []
    for fw, t in framework_totals.items():
        pct = round(100.0 * t["compliant"] / t["total"], 1) if t["total"] > 0 else 0.0
        frameworks.append({
            "framework": fw,
            "compliant": t["compliant"],
            "non_compliant": t["non_compliant"],
            "total": t["total"],
            "compliance_percentage": pct,
            "status": (
                "compliant" if t["non_compliant"] == 0
                else "partial" if t["compliant"] > 0
                else "non_compliant"
            ),
        })

    return {
        "frameworks": frameworks,
        "cross_cutting": _CROSS_CUTTING,
        "per_metric": per_metric,
    }
