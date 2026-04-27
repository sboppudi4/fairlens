from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_id: UUID
    file_size_bytes: int
    download_count: int
    generated_at: datetime
