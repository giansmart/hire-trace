import json
import re
from datetime import datetime

from hire_trace.extraction.base import JobExtractor
from hire_trace.schemas import Job, Publisher, PublisherType, RawDocument, Salary, SalaryPeriod

_LDJSON_RE = re.compile(
    r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL
)
_STRUCTURED_TYPES = {"SocialMediaPosting", "JobPosting"}

_TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_COLLAPSE_ALL_WHITESPACE_RE = re.compile(r"\s+")
_COLLAPSE_BLANK_LINES_RE = re.compile(r"\n{3,}")
_COLLAPSE_SPACES_RE = re.compile(r"[ \t]+")

_SALARY_RE = re.compile(
    r"(?P<currency>USD|EUR|GBP|MXN|COP|PEN)?\s*\$\s?(?P<min>[\d,]+(?:\.\d+)?)"
    r"(?:\s*(?:-|–|to)\s*\$?\s?(?P<max>[\d,]+(?:\.\d+)?))?"
    r"\s*(?:/|per\s+)?\s*(?P<period>month(?:ly)?|year(?:ly)?|annum|hour(?:ly)?)?",
    re.IGNORECASE,
)
_PERIOD_MAP = {
    "month": SalaryPeriod.monthly,
    "monthly": SalaryPeriod.monthly,
    "year": SalaryPeriod.yearly,
    "yearly": SalaryPeriod.yearly,
    "annum": SalaryPeriod.yearly,
    "hour": SalaryPeriod.hourly,
    "hourly": SalaryPeriod.hourly,
}


class HeuristicExtractor(JobExtractor):
    """Best-effort, no-ML extractor.

    Tries structured data first (schema.org JSON-LD — e.g. LinkedIn embeds a
    SocialMediaPosting block with the real post text even without JS rendering),
    since it's far more reliable than parsing rendered HTML. Falls back to blind
    tag-stripping when no structured data is found.

    Company is intentionally left unset for now: telling "the company hiring"
    apart from "the person who posted" needs more than this heuristic.
    """

    def extract(self, raw: RawDocument) -> Job:
        posting = self._find_structured_posting(raw.html)
        if posting is not None:
            return self._from_structured(raw, posting)
        return self._from_plain_html(raw)

    def _find_structured_posting(self, html: str) -> dict | None:
        for match in _LDJSON_RE.finditer(html):
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            for candidate in data if isinstance(data, list) else [data]:
                if isinstance(candidate, dict) and candidate.get("@type") in _STRUCTURED_TYPES:
                    return candidate
        return None

    def _from_structured(self, raw: RawDocument, posting: dict) -> Job:
        body = _TAG_RE.sub(" ", posting.get("articleBody") or posting.get("description") or "")
        description = self._clean_multiline(body)
        title = self._guess_title(body) or posting.get("headline") or "Untitled"

        author = posting.get("author") or {}
        publisher = (
            Publisher(name=author["name"], type=PublisherType.person, profile_url=author.get("url"))
            if author.get("name")
            else None
        )

        return Job(
            title=title,
            description=description,
            url=raw.url or "",
            source=raw.source,
            publisher=publisher,
            salary=self._guess_salary(description),
            posted_at=self._parse_date(posting.get("datePublished")),
        )

    def _from_plain_html(self, raw: RawDocument) -> Job:
        title_match = _TITLE_TAG_RE.search(raw.html)
        title = self._collapse_all(title_match.group(1)) if title_match else "Untitled"
        description = self._collapse_all(_TAG_RE.sub(" ", raw.html))

        return Job(
            title=title,
            description=description,
            url=raw.url or "",
            source=raw.source,
            salary=self._guess_salary(description),
        )

    @staticmethod
    def _guess_title(body: str) -> str | None:
        first_line = body.strip().split("\n", 1)[0].strip()
        return first_line[:200] or None

    @staticmethod
    def _guess_salary(text: str) -> Salary | None:
        match = _SALARY_RE.search(text)
        if not match:
            return None
        period = match.group("period")
        return Salary(
            min=float(match.group("min").replace(",", "")),
            max=float(match.group("max").replace(",", "")) if match.group("max") else None,
            currency=match.group("currency"),
            period=_PERIOD_MAP.get(period.lower()) if period else None,
        )

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _clean_multiline(text: str) -> str:
        text = text.replace("\xa0", " ")
        text = _COLLAPSE_SPACES_RE.sub(" ", text)
        text = _COLLAPSE_BLANK_LINES_RE.sub("\n\n", text)
        return text.strip()

    @staticmethod
    def _collapse_all(text: str) -> str:
        return _COLLAPSE_ALL_WHITESPACE_RE.sub(" ", text).strip()
