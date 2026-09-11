from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from hire_trace.collectors import (
    FallbackFetcher,
    fetch_application_page,
    save_raw_application_page,
    save_raw_post,
)
from hire_trace.core.db import get_session
from hire_trace.extraction import HeuristicExtractor, save_job_post, set_job_post_company
from hire_trace.schemas import JobPost

router = APIRouter(prefix="/jobs", tags=["jobs"])


class AnalyzeJobRequest(BaseModel):
    url: str


@router.post("/analyze", response_model=JobPost)
async def analyze_job(
    payload: AnalyzeJobRequest,
    session: AsyncSession = Depends(get_session),
) -> JobPost:
    """Fetches the URL, persists the raw HTML, runs the heuristic extractor, and
    (if an application_url was found) follows it, captures that page too, and
    fills in `company` from its schema.org Organization block when present.

    Placeholder wiring to prove the pipeline end to end — no enrichment,
    resolution, or trust scoring yet.
    """
    fetcher = FallbackFetcher()
    raw = await fetcher.fetch(payload.url)
    raw = await save_raw_post(session, raw)
    extractor = HeuristicExtractor()
    job = extractor.extract(raw)
    job = await save_job_post(session, job, raw_post_id=raw.id, extractor="heuristic")

    if job.application_url:
        application_page = await fetch_application_page(job.application_url, job_post_id=job.id)
        application_page = await save_raw_application_page(session, application_page)

        company = extractor.extract_company(application_page.html, source_url=application_page.final_url)
        if company:
            await set_job_post_company(session, job.id, company)
            job = job.model_copy(update={"company": company})

    return job
