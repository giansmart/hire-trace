import re
from datetime import UTC, datetime
from uuid import UUID

import httpx

from hire_trace.collectors.base import Fetcher, looks_like_empty_shell
from hire_trace.collectors.playwright_fetcher import PlaywrightFetcher
from hire_trace.schemas import RawApplicationPage, RawPost

_LINKEDIN_EXTERNAL_LINK_RE = re.compile(
    r'data-tracking-control-name="external_url_click"[^>]*href="([^"]+)"'
)


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


async def fetch_application_page(
    url: str, job_post_id: UUID, client: httpx.AsyncClient | None = None
) -> RawApplicationPage:
    """Follows application_url (redirects included, e.g. lnkd.in) and captures
    whatever page it lands on.

    LinkedIn's own redirect target is often an interstitial ("This link will
    take you to a page that's not on LinkedIn") rather than the real
    destination — that's a real page LinkedIn serves over HTTP, not a
    client-side prompt, so a plain GET lands on it just the same. We detect it
    by its "external_url_click" link and follow that one extra hop.
    """
    client = client or httpx.AsyncClient(follow_redirects=True, timeout=10.0)
    response = await client.get(url)

    match = _LINKEDIN_EXTERNAL_LINK_RE.search(response.text)
    if match:
        response = await client.get(match.group(1))

    html = response.text
    final_url = str(response.url)
    status_code = response.status_code

    if looks_like_empty_shell(html):
        rendered = await PlaywrightFetcher().fetch(final_url)
        html = rendered.html
        status_code = rendered.status_code

    return RawApplicationPage(
        job_post_id=job_post_id,
        url=url,
        final_url=final_url,
        html=html,
        status_code=status_code,
        fetched_at=datetime.now(UTC),
    )
