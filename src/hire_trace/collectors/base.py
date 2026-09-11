import re
from abc import ABC, abstractmethod

from hire_trace.schemas import RawPost

_SCRIPT_OR_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_MIN_MEANINGFUL_TEXT_LENGTH = 200


class Fetcher(ABC):
    """Fetches a single URL and captures it as a RawPost.

    Deliberately dumb: no entity extraction here, just getting the raw HTML down
    and tagged with where it came from. Swappable so a JS-rendering fetcher
    (Playwright) can replace this later without touching anything downstream.
    """

    @abstractmethod
    async def fetch(self, url: str) -> RawPost: ...


def looks_like_empty_shell(html: str) -> bool:
    """True when there's too little visible text to be real content — the
    signature of a JS-only SPA that ships an empty shell over plain HTTP,
    with everything injected client-side after the bundle runs."""
    without_script_or_style = _SCRIPT_OR_STYLE_RE.sub(" ", html)
    text = _WHITESPACE_RE.sub(" ", _TAG_RE.sub(" ", without_script_or_style)).strip()
    return len(text) < _MIN_MEANINGFUL_TEXT_LENGTH
