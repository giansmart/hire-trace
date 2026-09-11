from abc import ABC, abstractmethod

from hire_trace.schemas import RawDocument


class Fetcher(ABC):
    """Fetches a single URL and captures it as a RawDocument.

    Deliberately dumb: no entity extraction here, just getting the raw HTML down
    and tagged with where it came from. Swappable so a JS-rendering fetcher
    (Playwright) can replace this later without touching anything downstream.
    """

    @abstractmethod
    async def fetch(self, url: str) -> RawDocument: ...
