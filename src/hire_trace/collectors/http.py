from datetime import UTC, datetime

import httpx

from hire_trace.collectors.base import Fetcher
from hire_trace.schemas import RawPost


class HttpFetcher(Fetcher):
    """Plain HTTP GET. No JS rendering — fine for static pages, will miss content
    that's only injected client-side (e.g. some LinkedIn job pages)."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(follow_redirects=True, timeout=10.0)

    async def fetch(self, url: str) -> RawPost:
        response = await self._client.get(url)
        return RawPost(
            url=url,
            html=response.text,
            source="http",
            status_code=response.status_code,
            fetched_at=datetime.now(UTC),
        )
