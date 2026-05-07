"""Professional PDF audit report generation via ReportLab.

Output: a multi-page PDF following the FairLens spec — cover, executive summary,
dataset overview, fairness metrics per attribute, SHAP analysis, regulatory
compliance, mitigation recommendations, appendix.
"""
from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

from app.utils import chart_generator as charts

NAVY = colors.HexColor("#1a2744")
ACCENT = colors.HexColor("#2563eb")
PASS = colors.HexColor("#16a34a")
WARN = colors.HexColor("#d97706")
FAIL = colors.HexColor("#dc2626")
MUTED = colors.HexColor("#64748b")
LIGHT = colors.HexColor("#f1f5f9")
WHITE = colors.white


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontSize=28, textColor=NAVY, alignment=TA_CENTER, spaceAfter=18, fontName="Helvetica-Bold"),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=18, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=10, spaceBefore=4),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=13, textColor=NAVY, fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=10),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=11, textColor=ACCENT, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=6),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=10, textColor=colors.black, leading=14, alignment=TA_LEFT, spaceAfter=6),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontSize=8, textColor=MUTED, leading=10),
        "code": ParagraphStyle("code", parent=base["Code"], fontSize=8, textColor=colors.black, leading=10, fontName="Courier"),
        "cover_meta": ParagraphStyle("cover_meta", parent=base["BodyText"], fontSize=12, textColor=MUTED, alignment=TA_CENTER, spaceAfter=4),
        "badge": ParagraphStyle("badge", parent=base["BodyText"], fontSize=14, textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica-Bold"),
    }


def _severity_color(sev: str) -> colors.Color:
    return {"pass": PASS, "warning": WARN, "fail": FAIL}.get(sev, MUTED)


def _page_decoration(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    # header strip
    canvas.setFillColor(NAVY)
    canvas.rect(0, LETTER[1] - 0.4 * inch, LETTER[0], 0.4 * inch, stroke=0, fill=1)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(0.5 * inch, LETTER[1] - 0.27 * inch, "FairLens — AI Fairness Audit")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(LETTER[0] - 0.5 * inch, LETTER[1] - 0.27 * inch,
                           datetime.now(UTC).strftime("%Y-%m-%d"))
    # footer
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.5 * inch, 0.4 * inch,
                      "FairLens — Confidential audit artefact. Generated automatically.")
    canvas.drawRightString(LETTER[0] - 0.5 * inch, 0.4 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _cover_decoration(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    # Full-page navy band top + accent strip
    canvas.setFillColor(NAVY)
    canvas.rect(0, LETTER[1] - 2.5 * inch, LETTER[0], 2.5 * inch, stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, LETTER[1] - 2.6 * inch, LETTER[0], 0.1 * inch, stroke=0, fill=1)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(LETTER[0] / 2, 0.4 * inch,
                             "FairLens — AI Fairness Audit Report — Confidential")
    canvas.restoreState()


def _kv_table(rows: list[tuple[str, str]], col_widths: tuple[float, float] = (1.8 * inch, 4.5 * inch)) -> Table:
    t = Table(rows, colWidths=list(col_widths), hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.25, MUTED),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, MUTED),
    ]))
    return t


def _metrics_table(metrics: dict[str, dict[str, Any]]) -> Table:
    header = ["Metric", "Value", "Threshold", "Pass", "Severity"]
    data: list[list[Any]] = [header]
    severity_rows: list[tuple[int, str]] = []
    for i, (name, m) in enumerate(metrics.items(), start=1):
        data.append([
            name.replace("_", " "),
            f"{m['value']:.4f}",
            f"{m['threshold']:.2f}",
            "✓" if m["passes"] else "✗",
            m["severity"].upper(),
        ])
        severity_rows.append((i, m["severity"]))
    t = Table(data, colWidths=[2.4 * inch, 0.9 * inch, 0.9 * inch, 0.6 * inch, 1.0 * inch], hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("BOX", (0, 0), (-1, -1), 0.25, MUTED),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, MUTED),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]
    for row, sev in severity_rows:
        c = _severity_color(sev)
        style.append(("TEXTCOLOR", (4, row), (4, row), c))
        style.append(("FONTNAME", (4, row), (4, row), "Helvetica-Bold"))
    t.setStyle(TableStyle(style))
    return t


def _png_image(png: bytes, width: float, height: float | None = None) -> Image:
    img = Image(io.BytesIO(png), width=width, height=height) if height else Image(io.BytesIO(png), width=width, height=width * 0.5)
    img.hAlign = "CENTER"
    return img


def _risk_badge_color(risk_level: str) -> colors.Color:
    if "Low" in risk_level:
        return PASS
    if "Medium" in risk_level:
        return WARN
    return FAIL


def _build_cover(story: list, st: dict, summary: dict, audit_name: str, dataset_name: str, prepared_by: str) -> None:
    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph("AI Fairness Audit Report", ParagraphStyle(
        "cover_title", fontSize=32, textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(audit_name, ParagraphStyle(
        "cover_sub", fontSize=16, textColor=WHITE, alignment=TA_CENTER, fontName="Helvetica")))
    story.append(Spacer(1, 1.6 * inch))

    score = summary.get("overall_fairness_score", 0)
    risk = summary.get("risk_level", "Unknown")
    badge_color = _risk_badge_color(risk)
    badge = Table([[Paragraph(f"<b>{risk}</b>", st["badge"])]], colWidths=[3.0 * inch], rowHeights=[0.5 * inch])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), badge_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(badge)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(f"Overall Fairness Score: <b>{score:.0f} / 100</b>", st["cover_meta"]))
    story.append(Spacer(1, 0.6 * inch))
    story.append(Paragraph(f"Dataset: {dataset_name}", st["cover_meta"]))
    story.append(Paragraph(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}", st["cover_meta"]))
    story.append(Paragraph(f"Prepared by: {prepared_by}", st["cover_meta"]))
    story.append(PageBreak())


def _build_executive_summary(story: list, st: dict, results: dict) -> None:
    summary = results["summary"]
    story.append(Paragraph("Executive Summary", st["h1"]))

    score = summary["overall_fairness_score"]
    risk = summary["risk_level"]
    story.append(Spacer(1, 0.1 * inch))
    story.append(_png_image(charts.fairness_score_gauge(score, risk), width=3.5 * inch, height=2.0 * inch))
    story.append(Spacer(1, 0.1 * inch))

    rows = [
        ("Overall fairness score", f"{score:.0f} / 100"),
        ("Risk level", risk),
        ("Metrics passing", f"{summary['metrics_passing']} / {summary['metrics_total']}"),
        ("Pass / Warning / Fail", f"{summary['severities']['pass']} / {summary['severities']['warning']} / {summary['severities']['fail']}"),
        ("Sensitive attributes evaluated", ", ".join(results["sensitive_attributes"].keys())),
    ]
    story.append(_kv_table(rows))
    story.append(Spacer(1, 0.2 * inch))

    findings: list[str] = []
    for attr_name, attr_block in results["sensitive_attributes"].items():
        for m_name, m in attr_block["metrics"].items():
            if not m["passes"]:
                findings.append(
                    f"<b>{attr_name}</b>: <font color='#dc2626'>{m_name.replace('_', ' ')}</font> "
                    f"failed at value <b>{m['value']:.4f}</b> (threshold {m['threshold']:.2f})."
                )
    if not findings:
        findings = ["All evaluated metrics pass at the configured thresholds."]
    story.append(Paragraph("Key findings", st["h2"]))
    for f in findings[:6]:
        story.append(Paragraph(f"• {f}", st["body"]))

    story.append(PageBreak())


def _build_dataset_overview(story: list, st: dict, results: dict, dataset_name: str) -> None:
    story.append(Paragraph("Dataset Overview", st["h1"]))
    ds = results.get("dataset", {})
    story.append(_kv_table([
        ("Dataset name", dataset_name),
        ("Row count", str(ds.get("row_count", "—"))),
        ("Sensitive attributes", ", ".join(results["sensitive_attributes"].keys())),
    ]))
    story.append(Spacer(1, 0.2 * inch))

    # Per-attribute group sizes
    for attr_name, attr_block in results["sensitive_attributes"].items():
        story.append(Paragraph(f"Group composition — {attr_name}", st["h2"]))
        rows = [["Group", "n", "Selection rate"]]
        for g, perf in attr_block["per_group_performance"].items():
            rows.append([g, str(perf["n"]), f"{perf['selection_rate']:.4f}"])
        t = Table(rows, colWidths=[2.5 * inch, 1.0 * inch, 1.5 * inch], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("BOX", (0, 0), (-1, -1), 0.25, MUTED),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, MUTED),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15 * inch))
    story.append(PageBreak())


def _build_fairness_section(story: list, st: dict, results: dict) -> None:
    story.append(Paragraph("Fairness Metrics Results", st["h1"]))
    for attr_name, attr_block in results["sensitive_attributes"].items():
        story.append(Paragraph(f"Sensitive attribute: {attr_name}", st["h2"]))
        story.append(_metrics_table(attr_block["metrics"]))
        story.append(Spacer(1, 0.1 * inch))
        story.append(_png_image(charts.metrics_bar(attr_block["metrics"], attr_name), width=6.5 * inch, height=3.4 * inch))
        story.append(Spacer(1, 0.1 * inch))
        story.append(_png_image(
            charts.selection_rate_per_group(attr_block["per_group_performance"], attr_name),
            width=6.5 * inch, height=3.0 * inch,
        ))
        story.append(PageBreak())


def _build_shap_section(story: list, st: dict, shap_block: dict) -> None:
    story.append(Paragraph("SHAP Explainability Analysis", st["h1"]))
    if not shap_block.get("available"):
        story.append(Paragraph(
            f"SHAP analysis was not produced for this audit. Reason: {shap_block.get('reason', 'unknown')}",
            st["body"],
        ))
        story.append(PageBreak())
        return

    story.append(Paragraph(
        f"Explained {shap_block['n_samples_explained']} samples across "
        f"{shap_block['n_features']} engineered features.",
        st["body"],
    ))
    story.append(_png_image(charts.feature_importance_bar(shap_block["feature_importance"]),
                            width=6.5 * inch, height=4.2 * inch))
    story.append(Spacer(1, 0.1 * inch))
    for sens_attr, per_group in shap_block.get("per_group", {}).items():
        if not per_group:
            continue
        story.append(Paragraph(f"Importance by group — {sens_attr}", st["h2"]))
        story.append(_png_image(charts.grouped_feature_importance(per_group, f"{sens_attr}"),
                                width=6.5 * inch, height=3.5 * inch))
        story.append(Spacer(1, 0.1 * inch))

    warnings = shap_block.get("proxy_warnings") or []
    if warnings:
        story.append(Paragraph("Proxy discrimination warnings", st["h2"]))
        rows = [["Sensitive attr", "Feature", "Rel gap", "Interpretation"]]
        for w in warnings[:8]:
            rows.append([
                w["sensitive_attribute"],
                w["feature"][:24],
                f"{w['relative_gap']:.2%}",
                Paragraph(w["interpretation"], st["small"]),
            ])
        t = Table(rows, colWidths=[1.1 * inch, 1.6 * inch, 0.8 * inch, 3.0 * inch], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("BOX", (0, 0), (-1, -1), 0.25, MUTED),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, MUTED),
        ]))
        story.append(t)
    story.append(PageBreak())


def _build_regulatory(story: list, st: dict, regulatory: dict) -> None:
    story.append(Paragraph("Regulatory Compliance Mapping", st["h1"]))
    fw_rows = [["Framework", "Compliant", "Total", "Compliance %", "Status"]]
    for fw in regulatory.get("frameworks", []):
        fw_rows.append([
            fw["framework"],
            str(fw["compliant"]),
            str(fw["total"]),
            f"{fw['compliance_percentage']:.1f}%",
            fw["status"].replace("_", " ").title(),
        ])
    t = Table(fw_rows, colWidths=[1.8 * inch, 0.9 * inch, 0.7 * inch, 1.2 * inch, 1.2 * inch], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.25, MUTED),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, MUTED),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Per-metric compliance detail", st["h2"]))
    items = regulatory.get("per_metric", [])
    if not items:
        story.append(Paragraph("No per-metric mapping was produced.", st["body"]))
    rows = [["Attribute", "Metric", "Framework", "Locator", "Status"]]
    for item in items[:24]:
        rows.append([
            item["sensitive_attribute"],
            item["metric"].replace("_", " "),
            item["framework"],
            item["locator"],
            item["status"].replace("_", " "),
        ])
    if len(rows) > 1:
        rt = Table(rows, colWidths=[1.0 * inch, 1.7 * inch, 1.0 * inch, 1.7 * inch, 1.0 * inch], hAlign="LEFT")
        rt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("BOX", (0, 0), (-1, -1), 0.25, MUTED),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, MUTED),
        ]))
        story.append(rt)
    story.append(PageBreak())


def _build_mitigations(story: list, st: dict, mitigations: list[dict]) -> None:
    story.append(Paragraph("Mitigation Recommendations", st["h1"]))
    if not mitigations:
        story.append(Paragraph(
            "No failing metrics — no specific mitigations recommended. Continue monitoring "
            "via scheduled FairLens audits as part of your Article 9 risk-management cycle.",
            st["body"],
        ))
        story.append(PageBreak())
        return

    for m in mitigations:
        story.append(Paragraph(
            f"{m['technique']} — <font color='#64748b'>{m['failing_metric'].replace('_', ' ')} ({m['sensitive_attribute']})</font>",
            st["h2"],
        ))
        story.append(_kv_table([
            ("Complexity", m["complexity"]),
            ("Expected improvement", m["expected_improvement"]),
            ("Reference", m["reference"]),
        ], col_widths=(1.6 * inch, 4.7 * inch)))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph(m["description"], st["body"]))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Preformatted(m["code_snippet"], st["code"]))
        story.append(Spacer(1, 0.15 * inch))
    story.append(PageBreak())


def _build_appendix(story: list, st: dict, results: dict, config: dict) -> None:
    story.append(Paragraph("Appendix — Audit Configuration", st["h1"]))
    rows = [(k, ", ".join(v) if isinstance(v, list) else str(v)) for k, v in config.items()]
    story.append(_kv_table(rows))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Per-group confusion matrices", st["h2"]))
    for attr_name, block in results["sensitive_attributes"].items():
        story.append(Paragraph(attr_name, st["h3"]))
        rows = [["Group", "TP", "FP", "TN", "FN", "Accuracy", "Precision", "Recall", "F1"]]
        for g, perf in block["per_group_performance"].items():
            cm = perf["confusion_matrix"]
            rows.append([
                g, str(cm["tp"]), str(cm["fp"]), str(cm["tn"]), str(cm["fn"]),
                f"{perf['accuracy']:.4f}",
                f"{perf['precision']:.4f}" if perf['precision'] is not None else "—",
                f"{perf['recall']:.4f}" if perf['recall'] is not None else "—",
                f"{perf['f1']:.4f}" if perf['f1'] is not None else "—",
            ])
        t = Table(rows, colWidths=[1.2 * inch] + [0.55 * inch] * 4 + [0.7 * inch] * 4, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0.25, MUTED),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, MUTED),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.1 * inch))


def build_pdf(
    audit_name: str,
    dataset_name: str,
    prepared_by: str,
    results: dict[str, Any],
    config: dict[str, Any],
    shap_block: dict[str, Any] | None,
    mitigations: list[dict[str, Any]],
) -> bytes:
    """Assemble the full multi-page PDF and return its bytes.

    Parameters
    ----------
    audit_name : human-readable audit name.
    dataset_name : dataset display name.
    prepared_by : full name of the user.
    results : the persisted audit.results dict (output of compute_all_metrics + regulatory).
    config : the audit's config dict (label_column, sensitive_attributes, etc.).
    shap_block : output of analyze_shap, or {"available": False, ...}.
    mitigations : output of build_mitigations.
    """
    st = _styles()
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.8 * inch, bottomMargin=0.7 * inch,
        title=f"FairLens Audit — {audit_name}",
        author="FairLens",
    )
    cover_frame = Frame(0.7 * inch, 0.7 * inch, LETTER[0] - 1.4 * inch, LETTER[1] - 1.4 * inch, id="cover")
    body_frame = Frame(0.7 * inch, 0.7 * inch, LETTER[0] - 1.4 * inch, LETTER[1] - 1.5 * inch, id="body")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=_cover_decoration),
        PageTemplate(id="body", frames=[body_frame], onPage=_page_decoration),
    ])

    from reportlab.platypus import NextPageTemplate
    story: list = []
    # First page uses the 'cover' template (default = first registered).
    # Switch every subsequent page to the 'body' template.
    story.append(NextPageTemplate("body"))
    _build_cover(story, st, results["summary"], audit_name, dataset_name, prepared_by)
    _build_executive_summary(story, st, results)
    _build_dataset_overview(story, st, results, dataset_name)
    _build_fairness_section(story, st, results)
    _build_shap_section(story, st, shap_block or {"available": False, "reason": "not produced"})
    _build_regulatory(story, st, results.get("regulatory", {"frameworks": [], "per_metric": []}))
    _build_mitigations(story, st, mitigations)
    _build_appendix(story, st, results, config)

    doc.build(story)
    return buf.getvalue()
