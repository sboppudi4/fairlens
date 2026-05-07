"""Celery audit task — runs end-to-end: download CSV, compute metrics, persist results.

This task is intentionally synchronous (no asyncio inside Celery worker) because
mixing event loops with prefork workers is fragile. We use the sync SQLAlchemy
URL by swapping the asyncpg driver for psycopg2-style sync access via a separate
sync engine. To keep dependencies minimal, we instead use the sync boto3 client
and sync DB operations through the engine's connect() with text SQL where needed.

For Phase 1 simplicity, we use a sync SQLAlchemy engine here that talks to the
same Postgres DB as the API. The DB URL is converted from asyncpg -> psycopg.
"""
from __future__ import annotations

import io
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from celery import Task
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_settings
from app.core.redis import get_sync_redis
from app.core.storage import download_bytes_sync, upload_bytes_sync
from app.services.fairness.metrics import compute_all_metrics
from app.services.fairness.mitigation import build_mitigations
from app.services.fairness.regulatory import build_regulatory_mapping
from app.services.fairness.shap_analyzer import analyze_shap
from app.services.report_service import build_pdf
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _sync_db_url() -> str:
    """Convert async DB URL to sync. asyncpg -> psycopg2."""
    url = get_settings().DATABASE_URL
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


_engine: Engine | None = None


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(_sync_db_url(), pool_pre_ping=True)
    return _engine


def _set_progress(audit_id: str, progress: int, stage: str) -> None:
    r = get_sync_redis()
    r.hset(f"audit:{audit_id}:progress", mapping={"progress": progress, "stage": stage})
    r.expire(f"audit:{audit_id}:progress", 3600)


def _update_audit_status(
    audit_id: str,
    *,
    status: str | None = None,
    results: dict | None = None,
    error: str | None = None,
    started: bool = False,
    completed: bool = False,
) -> None:
    fields = []
    params: dict[str, Any] = {"id": uuid.UUID(audit_id)}
    if status is not None:
        fields.append("status = :status")
        params["status"] = status
    if results is not None:
        fields.append("results = :results")
        params["results"] = json.dumps(results)
    if error is not None:
        fields.append("error_message = :error")
        params["error"] = error
    if started:
        fields.append("started_at = :started_at")
        params["started_at"] = datetime.now(UTC)
    if completed:
        fields.append("completed_at = :completed_at")
        params["completed_at"] = datetime.now(UTC)
    if not fields:
        return
    sql = f"UPDATE audits SET {', '.join(fields)}, updated_at = NOW() WHERE id = :id"
    with _get_engine().begin() as conn:
        conn.execute(text(sql), params)


def _load_audit_and_dataset(audit_id: str) -> tuple[dict, dict]:
    with _get_engine().connect() as conn:
        audit = conn.execute(
            text("SELECT id, dataset_id, config FROM audits WHERE id = :id"),
            {"id": uuid.UUID(audit_id)},
        ).mappings().first()
        if audit is None:
            raise RuntimeError(f"audit {audit_id} not found")
        ds = conn.execute(
            text("SELECT id, s3_key, row_count, column_names FROM datasets WHERE id = :id"),
            {"id": audit["dataset_id"]},
        ).mappings().first()
        if ds is None:
            raise RuntimeError(f"dataset {audit['dataset_id']} not found")
    return dict(audit), dict(ds)


@celery_app.task(
    bind=True,
    name="app.tasks.audit_tasks.run_audit",
    autoretry_for=(IOError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def run_audit(self: Task, audit_id: str) -> dict[str, Any]:
    """Run a fairness audit end-to-end."""
    logger.info("audit.start", extra={"audit_id": audit_id})
    _update_audit_status(audit_id, status="running", started=True)
    _set_progress(audit_id, 5, "loading dataset")

    try:
        audit, dataset = _load_audit_and_dataset(audit_id)
        cfg = audit["config"] if isinstance(audit["config"], dict) else json.loads(audit["config"])

        # 1. Download CSV from object storage
        _set_progress(audit_id, 15, "downloading dataset from storage")
        raw = download_bytes_sync(dataset["s3_key"])

        # 2. Parse
        _set_progress(audit_id, 30, "parsing CSV")
        df = pd.read_csv(io.BytesIO(raw), encoding="utf-8", low_memory=False)

        label_col = cfg["label_column"]
        pred_col = cfg["prediction_column"]
        sensitive_cols: list[str] = cfg["sensitive_attributes"]
        positive_label = cfg["positive_label"]
        favorable_prediction = cfg["favorable_prediction"]

        for col in [label_col, pred_col, *sensitive_cols]:
            if col not in df.columns:
                raise RuntimeError(f"column not found in dataset at run time: {col}")

        # Coerce to comparable types: cast to string for the binarization (handles ints + strings uniformly)
        y_true = df[label_col].astype(str).to_numpy()
        y_pred = df[pred_col].astype(str).to_numpy()
        sensitive = {c: df[c].astype(str).to_numpy() for c in sensitive_cols}
        positive_label = str(positive_label)
        favorable_prediction = str(favorable_prediction)

        # 3. Compute metrics
        _set_progress(audit_id, 50, "computing fairness metrics")
        metrics = compute_all_metrics(
            y_true=y_true,
            y_pred=y_pred,
            sensitive=sensitive,
            positive_label=positive_label,
            favorable_prediction=favorable_prediction,
            X_numeric=None,
        )

        # 4. SHAP explainability — non-fatal if it fails
        _set_progress(audit_id, 70, "running SHAP explainability analysis")
        shap_block = analyze_shap(
            df=df,
            label_column=label_col,
            prediction_column=pred_col,
            sensitive_columns=sensitive_cols,
            positive_label=positive_label,
        )

        # 5. Regulatory mapping
        _set_progress(audit_id, 82, "mapping to EU AI Act / NIST RMF / ISO 42001")
        regulatory = build_regulatory_mapping(metrics["sensitive_attributes"])

        # 6. Mitigation suggestions
        _set_progress(audit_id, 88, "generating mitigation recommendations")
        mitigations = build_mitigations(metrics["sensitive_attributes"], shap_block)

        # 7. Assemble final results
        _set_progress(audit_id, 95, "finalizing results")
        results = {
            "schema_version": "1.0",
            "summary": metrics["summary"],
            "sensitive_attributes": metrics["sensitive_attributes"],
            "shap": shap_block,
            "regulatory": regulatory,
            "mitigations": mitigations,
            "config_used": cfg,
            "dataset": {
                "id": str(dataset["id"]),
                "row_count": dataset["row_count"],
            },
            "completed_at": datetime.now(UTC).isoformat(),
        }

        _update_audit_status(audit_id, status="completed", results=results, completed=True)
        _set_progress(audit_id, 100, "completed")
        logger.info("audit.complete", extra={"audit_id": audit_id, "score": results["summary"]["overall_fairness_score"]})

        # 8. Auto-trigger PDF generation
        try:
            generate_report.delay(audit_id)
        except Exception:  # noqa: BLE001
            logger.exception("audit.report_dispatch_failed", extra={"audit_id": audit_id})

        return {"audit_id": audit_id, "status": "completed"}

    except Exception as exc:  # noqa: BLE001
        logger.exception("audit.failed", extra={"audit_id": audit_id})
        _update_audit_status(audit_id, status="failed", error=str(exc), completed=True)
        _set_progress(audit_id, 0, f"failed: {exc}")
        raise


def _load_report_inputs(audit_id: str) -> dict[str, Any]:
    with _get_engine().connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT a.id, a.name, a.user_id, a.results, a.config,
                       d.name AS dataset_name,
                       u.full_name AS user_full_name, u.email AS user_email
                FROM audits a
                JOIN datasets d ON d.id = a.dataset_id
                JOIN users u ON u.id = a.user_id
                WHERE a.id = :id
                """
            ),
            {"id": uuid.UUID(audit_id)},
        ).mappings().first()
    if row is None:
        raise RuntimeError(f"audit {audit_id} not found for report generation")
    return dict(row)


def _upsert_report(audit_id: str, user_id: uuid.UUID, s3_key: str, size: int) -> None:
    with _get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO reports (id, audit_id, user_id, s3_key, file_size_bytes, generated_at)
                VALUES (:id, :audit_id, :user_id, :s3_key, :size, NOW())
                ON CONFLICT (audit_id) DO UPDATE
                SET s3_key = EXCLUDED.s3_key,
                    file_size_bytes = EXCLUDED.file_size_bytes,
                    generated_at = NOW()
                """
            ),
            {
                "id": uuid.uuid4(),
                "audit_id": uuid.UUID(audit_id),
                "user_id": user_id,
                "s3_key": s3_key,
                "size": size,
            },
        )


@celery_app.task(
    bind=True,
    name="app.tasks.audit_tasks.generate_report",
    autoretry_for=(IOError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def generate_report(self: Task, audit_id: str) -> dict[str, Any]:
    """Build the PDF report for a completed audit and persist it to object storage."""
    logger.info("report.start", extra={"audit_id": audit_id})
    r = get_sync_redis()
    r.hset(f"report:{audit_id}:progress", mapping={"progress": 5, "stage": "loading audit"})
    r.expire(f"report:{audit_id}:progress", 3600)

    try:
        row = _load_report_inputs(audit_id)
        results = row["results"] if isinstance(row["results"], dict) else json.loads(row["results"])
        config = row["config"] if isinstance(row["config"], dict) else json.loads(row["config"])

        r.hset(f"report:{audit_id}:progress", mapping={"progress": 35, "stage": "rendering charts and pdf"})
        pdf_bytes = build_pdf(
            audit_name=row["name"],
            dataset_name=row["dataset_name"],
            prepared_by=row["user_full_name"] or row["user_email"],
            results=results,
            config=config,
            shap_block=results.get("shap"),
            mitigations=results.get("mitigations", []),
        )

        r.hset(f"report:{audit_id}:progress", mapping={"progress": 80, "stage": "uploading"})
        s3_key = f"reports/{audit_id}.pdf"
        upload_bytes_sync(s3_key, pdf_bytes, content_type="application/pdf")

        _upsert_report(audit_id, row["user_id"], s3_key, len(pdf_bytes))
        r.hset(f"report:{audit_id}:progress", mapping={"progress": 100, "stage": "completed"})
        logger.info("report.complete", extra={"audit_id": audit_id, "size": len(pdf_bytes)})
        return {"audit_id": audit_id, "s3_key": s3_key, "size": len(pdf_bytes)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("report.failed", extra={"audit_id": audit_id})
        r.hset(f"report:{audit_id}:progress", mapping={"progress": 0, "stage": f"failed: {exc}"})
        raise
