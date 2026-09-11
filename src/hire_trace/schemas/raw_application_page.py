from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RawApplicationPage(BaseModel):
    id: UUID | None = None
    job_post_id: UUID
    url: str
    final_url: str | None = None
    html: str
    status_code: int | None = None
    fetched_at: datetime
