"""Report endpoints — trigger PDF generation, poll status, stream the PDF."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update

from app.core.exceptions import http_404, http_409
from app.core.redis import get_async_redis
from app.core.storage import stream_object
from app.dependencies import CurrentUser, DBSession
from app.models.audit import Audit
from app.models.report import Report
from app.schemas.report import ReportOut
from app.tasks.audit_tasks import generate_report

router = APIRouter(prefix="/reports", tags=["reports"])


async def _get_user_audit(db, audit_id: UUID, user_id: UUID) -> Audit:
    result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.user_id == user_id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise http_404("audit not found")
    return audit


async def _get_report_for_audit(db, audit_id: UUID, user_id: UUID) -> Report | None:
    result = await db.execute(
        select(Report).where(Report.audit_id == audit_id, Report.user_id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("/{audit_id}/generate", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def trigger_report_generation(
    audit_id: UUID, user: CurrentUser, db: DBSession
) -> dict[str, str]:
    """Queue a PDF report generation job. Idempotent: re-runs replace the previous report."""
    audit = await _get_user_audit(db, audit_id, user.id)
    if audit.status != "completed":
        raise http_409(
            f"audit must be completed before a report can be generated (current status: {audit.status})"
        )
    task = generate_report.delay(str(audit.id))
    return {"audit_id": str(audit.id), "task_id": task.id, "status": "queued"}


@router.get("/{audit_id}/status", response_model=dict)
async def get_report_status(
    audit_id: UUID, user: CurrentUser, db: DBSession
) -> dict[str, object]:
    await _get_user_audit(db, audit_id, user.id)
    r = get_async_redis()
    progress_data = await r.hgetall(f"report:{audit_id}:progress")
    report = await _get_report_for_audit(db, audit_id, user.id)
    return {
        "audit_id": str(audit_id),
        "ready": report is not None,
        "report": ReportOut.model_validate(report).model_dump(mode="json") if report else None,
        "progress": int(progress_data.get("progress", 0)) if progress_data else (100 if report else 0),
        "stage": progress_data.get("stage") if progress_data else ("completed" if report else None),
    }


@router.get("/{audit_id}/download")
async def download_report(audit_id: UUID, user: CurrentUser, db: DBSession) -> StreamingResponse:
    """Stream the PDF report from object storage."""
    report = await _get_report_for_audit(db, audit_id, user.id)
    if report is None:
        raise http_404("report not yet generated for this audit")

    # Increment download counter (best-effort)
    await db.execute(
        update(Report)
        .where(Report.id == report.id)
        .values(download_count=Report.download_count + 1)
    )
    await db.commit()

    filename = f"fairlens-audit-{audit_id}.pdf"
    return StreamingResponse(
        stream_object(report.s3_key),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
