"""Audit creation + retrieval. Validation against the dataset's columns happens here."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import http_404, http_422
from app.models.audit import Audit
from app.models.dataset import Dataset
from app.schemas.audit import AuditConfig, AuditCreate


async def create_audit(db: AsyncSession, user_id: UUID, payload: AuditCreate) -> Audit:
    ds = await db.get(Dataset, payload.dataset_id)
    if ds is None or ds.user_id != user_id:
        raise http_404("dataset not found")

    _validate_config_against_dataset(payload.config, ds)

    audit = Audit(
        user_id=user_id,
        dataset_id=ds.id,
        name=payload.name,
        description=payload.description,
        config=payload.config.model_dump(),
        status="pending",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    return audit


def _validate_config_against_dataset(cfg: AuditConfig, ds: Dataset) -> None:
    cols = set(ds.column_names)
    missing = []
    if cfg.label_column not in cols:
        missing.append(f"label_column '{cfg.label_column}'")
    if cfg.prediction_column not in cols:
        missing.append(f"prediction_column '{cfg.prediction_column}'")
    for s in cfg.sensitive_attributes:
        if s not in cols:
            missing.append(f"sensitive_attribute '{s}'")
    if missing:
        raise http_422(f"columns not found in dataset: {', '.join(missing)}")
    if cfg.label_column == cfg.prediction_column:
        raise http_422("label_column and prediction_column must differ")


async def list_audits(
    db: AsyncSession,
    user_id: UUID,
    *,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Audit]:
    stmt = select(Audit).where(Audit.user_id == user_id)
    if status:
        stmt = stmt.where(Audit.status == status)
    stmt = stmt.order_by(Audit.created_at.desc()).limit(limit).offset(offset)
    return list((await db.scalars(stmt)).all())


async def get_audit(db: AsyncSession, audit_id: UUID, user_id: UUID) -> Audit:
    audit = await db.get(Audit, audit_id)
    if audit is None or audit.user_id != user_id:
        raise http_404("audit not found")
    return audit
