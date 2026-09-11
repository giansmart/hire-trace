import json
import re
from datetime import datetime
from urllib.parse import urlparse

from hire_trace.extraction.base import JobExtractor
from hire_trace.schemas import (
    Company,
    Domain,
    JobPost,
    Publisher,
    PublisherType,
    RawPost,
    Salary,
    SalaryPeriod,
)

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

_URL_RE = re.compile(r"https?://\S+")
_TRAILING_PUNCTUATION_RE = re.compile(r"[)\].,;:!?]+$")
_YEAR_RE = re.compile(r"\d{4}")


class HeuristicExtractor(JobExtractor):
    """Best-effort, no-ML extractor.

    Tries structured data first (schema.org JSON-LD — e.g. LinkedIn embeds a
    SocialMediaPosting block with the real post text even without JS rendering),
    since it's far more reliable than parsing rendered HTML. Falls back to blind
    tag-stripping when no structured data is found.

    Company is intentionally left unset for now: telling "the company hiring"
    apart from "the person who posted" needs more than this heuristic.

    application_url is the last link found in the post text (both legit and
    fake postings redirect to an external link, usually a shortened one like
    lnkd.in — resolving where it actually goes is enrichment's job, not this
    extractor's).
    """

    def extract(self, raw: RawPost) -> JobPost:
        posting = self._find_structured_posting(raw.html)
        if posting is not None:
            return self._from_structured(raw, posting)
        return self._from_plain_html(raw)

    def extract_company(self, html: str, source_url: str | None = None) -> Company | None:
        """Looks for a schema.org Organization block — e.g. the hiring company's
        own careers page usually has one, richer than a JobPosting's bare
        hiringOrganization stub (founding date, description, social profiles)."""
        for candidate in self._iter_ldjson(html):
            if isinstance(candidate, dict) and candidate.get("@type") == "Organization":
                return self._company_from_organization(candidate, source_url)
        return None

    @staticmethod
    def _iter_ldjson(html: str):
        for match in _LDJSON_RE.finditer(html):
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            yield from (data if isinstance(data, list) else [data])

    def _find_structured_posting(self, html: str) -> dict | None:
        for candidate in self._iter_ldjson(html):
            if isinstance(candidate, dict) and candidate.get("@type") in _STRUCTURED_TYPES:
                return candidate
        return None

    def _from_structured(self, raw: RawPost, posting: dict) -> JobPost:
        body = _TAG_RE.sub(" ", posting.get("articleBody") or posting.get("description") or "")
        description = self._clean_multiline(body)
        title = self._guess_title(body) or posting.get("headline") or "Untitled"

        author = posting.get("author") or {}
        publisher = (
            Publisher(name=author["name"], type=PublisherType.person, profile_url=author.get("url"))
            if author.get("name")
            else None
        )

        return JobPost(
            title=title,
            description=description,
            url=raw.url or "",
            source=raw.source,
            publisher=publisher,
            salary=self._guess_salary(description),
            application_url=self._guess_application_url(description),
            posted_at=self._parse_date(posting.get("datePublished")),
        )

    def _from_plain_html(self, raw: RawPost) -> JobPost:
        title_match = _TITLE_TAG_RE.search(raw.html)
        title = self._collapse_all(title_match.group(1)) if title_match else "Untitled"
        description = self._collapse_all(_TAG_RE.sub(" ", raw.html))

        return JobPost(
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
    def _company_from_organization(org: dict, source_url: str | None) -> Company:
        url = org.get("url")
        hostname = urlparse(url).hostname if url else None

        logo = org.get("logo")
        logo_url = logo.get("url") if isinstance(logo, dict) else logo

        same_as = org.get("sameAs") or []
        social_profiles = same_as if isinstance(same_as, list) else [same_as]

        year_match = _YEAR_RE.search(org.get("foundingDate") or "")

        return Company(
            name=org["name"],
            legal_name=org.get("legalName"),
            domain=Domain(hostname=hostname) if hostname else None,
            description=org.get("description"),
            founded_year=int(year_match.group()) if year_match else None,
            logo_url=logo_url,
            social_profiles=social_profiles,
            source_urls=[source_url] if source_url else [],
        )

    @staticmethod
    def _guess_application_url(text: str) -> str | None:
        urls = _URL_RE.findall(text)
        if not urls:
            return None
        return _TRAILING_PUNCTUATION_RE.sub("", urls[-1])

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
