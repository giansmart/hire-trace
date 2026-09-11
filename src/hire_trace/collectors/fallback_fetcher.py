from hire_trace.collectors.base import Fetcher, looks_like_empty_shell
from hire_trace.collectors.http import HttpFetcher
from hire_trace.collectors.playwright_fetcher import PlaywrightFetcher
from hire_trace.schemas import RawPost


class FallbackFetcher(Fetcher):
    """Tries a plain HTTP GET first (fast, cheap); only pays for a real
    browser render when that result looks like an empty SPA shell."""

    def __init__(self, http: Fetcher | None = None, playwright: Fetcher | None = None) -> None:
        self._http = http or HttpFetcher()
        self._playwright = playwright or PlaywrightFetcher()

    async def fetch(self, url: str) -> RawPost:
        raw = await self._http.fetch(url)
        if looks_like_empty_shell(raw.html):
            return await self._playwright.fetch(url)
        return raw
