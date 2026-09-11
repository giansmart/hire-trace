import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from hire_trace.core.db import Base


class JobORM(Base):
    """Persisted output of a JobExtractor run against a RawDocument.

    company/publisher/salary/requested_data are JSONB on purpose: these shapes
    are still evolving while we compare extractors, and there's no entity
    resolution yet to make normalized company/publisher tables meaningful.
    """

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_document_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("raw_documents.id"), nullable=False
    )
    extractor: Mapped[str] = mapped_column(String, nullable=False)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    publisher: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    salary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    requested_data: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
