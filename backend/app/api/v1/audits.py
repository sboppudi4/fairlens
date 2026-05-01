from uuid import UUID

from fastapi import APIRouter, status

from app.core.exceptions import http_404
from app.core.redis import get_async_redis
from app.dependencies import CurrentUser, DBSession
from app.schemas.audit import AuditCreate, AuditDetail, AuditOut, AuditStatus
from app.services.audit_service import create_audit, get_audit, list_audits
from app.tasks.audit_tasks import run_audit

router = APIRouter(prefix="/audits", tags=["audits"])


@router.post("", response_model=AuditOut, status_code=status.HTTP_201_CREATED)
async def create_audit_endpoint(payload: AuditCreate, user: CurrentUser, db: DBSession) -> AuditOut:
    """Create an audit and queue it for background processing."""
    audit = await create_audit(db, user.id, payload)
    task = run_audit.delay(str(audit.id))
    audit.task_id = task.id
    await db.commit()
    await db.refresh(audit)
    return AuditOut.model_validate(audit)


@router.get("", response_model=list[AuditOut])
async def list_my_audits(
    user: CurrentUser, db: DBSession, status_filter: str | None = None, limit: int = 50, offset: int = 0
) -> list[AuditOut]:
    items = await list_audits(db, user.id, status=status_filter, limit=limit, offset=offset)
    return [AuditOut.model_validate(a) for a in items]


@router.get("/{audit_id}", response_model=AuditDetail)
async def get_audit_detail(audit_id: UUID, user: CurrentUser, db: DBSession) -> AuditDetail:
    audit = await get_audit(db, audit_id, user.id)
    return AuditDetail.model_validate(audit)


@router.get("/{audit_id}/status", response_model=AuditStatus)
async def get_audit_status(audit_id: UUID, user: CurrentUser, db: DBSession) -> AuditStatus:
    audit = await get_audit(db, audit_id, user.id)
    r = get_async_redis()
    progress_data = await r.hgetall(f"audit:{audit.id}:progress")
    progress = int(progress_data.get("progress", 0)) if progress_data else (
        100 if audit.status == "completed" else 0
    )
    stage = progress_data.get("stage") if progress_data else None
    return AuditStatus(
        id=audit.id,
        status=audit.status,
        progress=progress,
        stage=stage,
        error_message=audit.error_message,
    )


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(audit_id: UUID, user: CurrentUser, db: DBSession) -> None:
    audit = await get_audit(db, audit_id, user.id)
    await db.delete(audit)
    await db.commit()
