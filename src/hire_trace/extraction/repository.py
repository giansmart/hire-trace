from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from hire_trace.extraction.models import JobORM
from hire_trace.schemas import Job


async def save_job(session: AsyncSession, job: Job, raw_document_id: UUID, extractor: str) -> Job:
    row = JobORM(
        raw_document_id=raw_document_id,
        extractor=extractor,
        title=job.title,
        description=job.description,
        url=job.url,
        source=job.source,
        posted_at=job.posted_at,
        company=job.company.model_dump(mode="json") if job.company else None,
        publisher=job.publisher.model_dump(mode="json") if job.publisher else None,
        salary=job.salary.model_dump(mode="json") if job.salary else None,
        requested_data=[value.value for value in job.requested_data],
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return job.model_copy(update={"id": row.id})
