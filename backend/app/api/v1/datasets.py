from io import BytesIO
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, File, Form, UploadFile, status

from app.config import get_settings
from app.core.exceptions import http_400, http_404
from app.core.storage import download_bytes
from app.dependencies import CurrentUser, DBSession
from app.schemas.dataset import ColumnInfo, DatasetColumns, DatasetOut, DatasetPreview
from app.services.dataset_service import create_dataset_from_upload, get_dataset, list_datasets
from app.utils.csv_parser import column_stats

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    description: str | None = Form(default=None),
) -> DatasetOut:
    """Upload a CSV dataset. Returns the dataset record once parsed and stored."""
    if file.filename is None:
        raise http_400("filename is required")
    data = await file.read()
    settings = get_settings()
    ds = await create_dataset_from_upload(
        db,
        user_id=user.id,
        filename=file.filename,
        data=data,
        name=name,
        description=description,
        max_size_bytes=settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024,
    )
    return DatasetOut.model_validate(ds)


@router.get("", response_model=list[DatasetOut])
async def list_my_datasets(user: CurrentUser, db: DBSession, limit: int = 50, offset: int = 0) -> list[DatasetOut]:
    items = await list_datasets(db, user.id, limit=limit, offset=offset)
    return [DatasetOut.model_validate(d) for d in items]


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset_detail(dataset_id: UUID, user: CurrentUser, db: DBSession) -> DatasetOut:
    ds = await get_dataset(db, dataset_id, user.id)
    return DatasetOut.model_validate(ds)


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
async def preview_dataset(dataset_id: UUID, user: CurrentUser, db: DBSession, n: int = 20) -> DatasetPreview:
    ds = await get_dataset(db, dataset_id, user.id)
    raw = await download_bytes(ds.s3_key)
    df = pd.read_csv(BytesIO(raw), encoding="utf-8", low_memory=False).head(n)
    df = df.astype(object).where(df.notna(), None)
    return DatasetPreview(
        columns=list(df.columns),
        rows=df.to_dict(orient="records"),
        row_count=ds.row_count,
    )


@router.get("/{dataset_id}/columns", response_model=DatasetColumns)
async def dataset_columns(dataset_id: UUID, user: CurrentUser, db: DBSession) -> DatasetColumns:
    ds = await get_dataset(db, dataset_id, user.id)
    raw = await download_bytes(ds.s3_key)
    cols = column_stats(raw)
    return DatasetColumns(columns=[ColumnInfo(**c) for c in cols])


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: UUID, user: CurrentUser, db: DBSession) -> None:
    ds = await get_dataset(db, dataset_id, user.id)
    await db.delete(ds)
    await db.commit()
