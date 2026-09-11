from abc import ABC, abstractmethod

from hire_trace.schemas import Job, RawDocument


class JobExtractor(ABC):
    """Turns a captured RawDocument into structured Job entities.

    Swappable on purpose: different implementations (heuristic, LLM-based, ...)
    can run against the same stored RawDocument to compare results, without the
    rest of the pipeline (enrichment, resolution, graph) knowing which one was used.
    """

    @abstractmethod
    def extract(self, raw: RawDocument) -> Job: ...
