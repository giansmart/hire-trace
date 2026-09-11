from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from hire_trace.extraction.models import JobPostORM
from hire_trace.schemas import Company, JobPost


async def save_job_post(
    session: AsyncSession, job: JobPost, raw_post_id: UUID, extractor: str
) -> JobPost:
    row = JobPostORM(
        raw_post_id=raw_post_id,
        extractor=extractor,
        title=job.title,
        description=job.description,
        url=job.url,
        source=job.source,
        application_url=job.application_url,
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


async def set_job_post_company(session: AsyncSession, job_post_id: UUID, company: Company) -> None:
    await session.execute(
        update(JobPostORM)
        .where(JobPostORM.id == job_post_id)
        .values(company=company.model_dump(mode="json"))
    )
    await session.commit()
