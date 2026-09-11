from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RawDocument(BaseModel):
    id: UUID | None = None
    url: str | None = None
    html: str
    source: str
    status_code: int | None = None
    fetched_at: datetime
