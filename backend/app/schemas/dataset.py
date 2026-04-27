from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    filename: str
    row_count: int
    column_names: list[str]
    column_types: dict[str, str]
    file_size_bytes: int
    status: str
    created_at: datetime


class ColumnInfo(BaseModel):
    name: str
    dtype: str  # numeric | categorical | boolean | string
    cardinality: int
    null_count: int
    sample_values: list[str]


class DatasetColumns(BaseModel):
    columns: list[ColumnInfo]


class DatasetPreview(BaseModel):
    columns: list[str]
    rows: list[dict]  # first N rows as dicts
    row_count: int
