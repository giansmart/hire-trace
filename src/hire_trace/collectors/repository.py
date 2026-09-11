from sqlalchemy.ext.asyncio import AsyncSession

from hire_trace.collectors.models import RawPostORM
from hire_trace.schemas import RawPost


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
