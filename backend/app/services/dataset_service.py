"""Dataset upload + retrieval orchestration."""
from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import http_400, http_404, http_413
from app.core.storage import upload_bytes
from app.models.dataset import Dataset
from app.utils.csv_parser import parse_csv


async def create_dataset_from_upload(
    db: AsyncSession,
    *,
    user_id: UUID,
    filename: str,
    data: bytes,
    name: str | None,
    description: str | None,
    max_size_bytes: int,
) -> Dataset:
    if len(data) > max_size_bytes:
        raise http_413(f"file exceeds max size of {max_size_bytes // (1024 * 1024)} MB")
    if not filename.lower().endswith(".csv"):
        raise http_400("only .csv files are supported")

    try:
        meta = parse_csv(data)
    except ValueError as e:
        raise http_400(str(e)) from e

    dataset_id = uuid4()
    s3_key = f"datasets/{user_id}/{dataset_id}/{filename}"
    await upload_bytes(s3_key, data, content_type="text/csv")

    ds = Dataset(
        id=dataset_id,
        user_id=user_id,
        name=name or filename,
        description=description,
        filename=filename,
        s3_key=s3_key,
        row_count=meta["row_count"],
        column_names=meta["column_names"],
        column_types=meta["column_types"],
        file_size_bytes=len(data),
        status="ready",
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return ds


async def list_datasets(db: AsyncSession, user_id: UUID, limit: int = 50, offset: int = 0) -> list[Dataset]:
    stmt = (
        select(Dataset)
        .where(Dataset.user_id == user_id)
        .order_by(Dataset.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await db.scalars(stmt)).all())


async def get_dataset(db: AsyncSession, dataset_id: UUID, user_id: UUID) -> Dataset:
    ds = await db.get(Dataset, dataset_id)
    if ds is None or ds.user_id != user_id:
        raise http_404("dataset not found")
    return ds
