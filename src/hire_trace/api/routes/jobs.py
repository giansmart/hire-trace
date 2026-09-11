from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from hire_trace.collectors import HttpFetcher, save_raw_post
from hire_trace.core.db import get_session
from hire_trace.extraction import HeuristicExtractor, save_job_post
from hire_trace.schemas import JobPost

router = APIRouter(prefix="/jobs", tags=["jobs"])


class AnalyzeJobRequest(BaseModel):
    url: str


@router.post("/analyze", response_model=JobPost)
async def analyze_job(
    payload: AnalyzeJobRequest,
    session: AsyncSession = Depends(get_session),
) -> JobPost:
    """Fetches the URL, persists the raw HTML, and runs the heuristic extractor.

    Placeholder wiring to prove the pipeline end to end — no enrichment,
    resolution, or trust scoring yet.
    """
    fetcher = HttpFetcher()
    raw = await fetcher.fetch(payload.url)
    raw = await save_raw_post(session, raw)
    extractor = HeuristicExtractor()
    job = extractor.extract(raw)
    return await save_job_post(session, job, raw_post_id=raw.id, extractor="heuristic")
