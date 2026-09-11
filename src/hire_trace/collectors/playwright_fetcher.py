from datetime import UTC, datetime

from playwright.async_api import async_playwright

from hire_trace.collectors.base import Fetcher
from hire_trace.schemas import RawPost


class PlaywrightFetcher(Fetcher):
    """Renders the page in a real headless browser before capturing HTML.

    Slow and heavy compared to HttpFetcher (a browser process per fetch) —
    only worth paying for when a plain GET gets back an empty JS-only shell.
    """

    async def fetch(self, url: str) -> RawPost:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                # "networkidle" hangs on pages with persistent background
                # activity (analytics, polling, websockets) that never lets the
                # network go quiet. "load" + a short fixed wait for the SPA to
                # finish rendering is slower to trust but far more reliable.
                response = await page.goto(url, wait_until="load")
                await page.wait_for_timeout(1500)
                html = await page.content()
            finally:
                await browser.close()

        return RawPost(
            url=url,
            html=html,
            source="playwright",
            status_code=response.status if response else None,
            fetched_at=datetime.now(UTC),
        )
