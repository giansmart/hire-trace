from abc import ABC, abstractmethod

from hire_trace.schemas import JobPost, RawPost


class JobExtractor(ABC):
    """Turns a captured RawPost into a structured JobPost.

    Swappable on purpose: different implementations (heuristic, LLM-based, ...)
    can run against the same stored RawPost to compare results, without the
    rest of the pipeline (enrichment, resolution, graph) knowing which one was used.
    """

    @abstractmethod
    def extract(self, raw: RawPost) -> JobPost: ...
