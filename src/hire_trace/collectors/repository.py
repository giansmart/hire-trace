from sqlalchemy.ext.asyncio import AsyncSession

from hire_trace.collectors.models import RawApplicationPageORM, RawPostORM
from hire_trace.schemas import RawApplicationPage, RawPost


async def save_raw_post(session: AsyncSession, raw: RawPost) -> RawPost:
    row = RawPostORM(
        url=raw.url,
        html=raw.html,
        source=raw.source,
        status_code=raw.status_code,
        fetched_at=raw.fetched_at,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return raw.model_copy(update={"id": row.id})


async def save_raw_application_page(
    session: AsyncSession, page: RawApplicationPage
) -> RawApplicationPage:
    row = RawApplicationPageORM(
        job_post_id=page.job_post_id,
        url=page.url,
        final_url=page.final_url,
        html=page.html,
        status_code=page.status_code,
        fetched_at=page.fetched_at,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return page.model_copy(update={"id": row.id})
