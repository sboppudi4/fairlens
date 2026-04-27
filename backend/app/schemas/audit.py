from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuditConfig(BaseModel):
    """User-supplied audit configuration. Validated against the dataset columns at request time."""

    label_column: str = Field(min_length=1, description="Column name of the ground-truth label")
    prediction_column: str = Field(min_length=1, description="Column name of the model prediction")
    sensitive_attributes: list[str] = Field(min_length=1, max_length=5)
    positive_label: str = Field(description="Value of label_column representing the positive outcome")
    favorable_prediction: str = Field(
        description="Value of prediction_column representing the favorable outcome"
    )
    model_type: str = Field(default="binary_classification")

    @field_validator("sensitive_attributes")
    @classmethod
    def _no_dupes(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("sensitive_attributes must be unique")
        return v


class AuditCreate(BaseModel):
    dataset_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    config: AuditConfig


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    name: str
    description: str | None
    config: dict[str, Any]
    status: str
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AuditDetail(AuditOut):
    results: dict[str, Any] | None = None


class AuditStatus(BaseModel):
    id: UUID
    status: str
    progress: int = 0  # 0-100
    stage: str | None = None
    error_message: str | None = None
