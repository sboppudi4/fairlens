"""Dataset upload + retrieval orchestration."""
from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import http_400, http_404, http_413
from app.core.storage import upload_bytes
from app.models.dataset import Dataset
from app.utils.csv_parser import parse_csv


_ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.ms-excel",  # Some browsers tag .csv this way
    "application/octet-stream",  # Fallback when the browser isn't sure
    "",  # When the client doesn't send one at all
    None,
}

# Magic bytes that disqualify a file outright (compressed archives, executables, PDFs).
_BLOCKED_MAGIC_BYTES: tuple[bytes, ...] = (
    b"PK\x03\x04",  # ZIP / docx / xlsx
    b"\x1f\x8b",  # GZIP
    b"BZh",  # BZIP2
    b"\xfd7zXZ\x00",  # XZ
    b"7z\xbc\xaf\x27\x1c",  # 7z
    b"%PDF-",  # PDF
    b"\x7fELF",  # ELF binary
    b"MZ",  # Windows PE
)


async def create_dataset_from_upload(
    db: AsyncSession,
    *,
    user_id: UUID,
    filename: str,
    data: bytes,
    name: str | None,
    description: str | None,
    max_size_bytes: int,
    content_type: str | None = None,
) -> Dataset:
    # ---- Boundary checks (size, extension, MIME, magic bytes) -----------
    if len(data) > max_size_bytes:
        raise http_413(f"file exceeds max size of {max_size_bytes // (1024 * 1024)} MB")
    if not filename.lower().endswith(".csv"):
        raise http_400("only .csv files are supported")
    if content_type is not None and content_type not in _ALLOWED_MIME_TYPES:
        raise http_400(f"unsupported content-type: {content_type}")
    head = data[:8]
    if any(head.startswith(magic) for magic in _BLOCKED_MAGIC_BYTES):
        raise http_400("file does not appear to be a plain-text CSV")
    # Cheap text-content sniff: reject if the first 4 KB contains many NULs
    sample = data[: 4 * 1024]
    if sample.count(b"\x00") > 8:
        raise http_400("CSV must be plain text (binary content detected)")

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
