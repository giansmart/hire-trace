from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Domain(BaseModel):
    hostname: str
    registered_at: datetime | None = None
    age_days: int | None = None


class Company(BaseModel):
    name: str
    legal_name: str | None = None
    domain: Domain | None = None
    careers_url: str | None = None
    description: str | None = None
    founded_year: int | None = None
    logo_url: str | None = None
    social_profiles: list[str] = []
    source_urls: list[str] = []


class PublisherType(str, Enum):
    person = "person"
    company_account = "company_account"
    unknown = "unknown"


class Publisher(BaseModel):
    name: str
    type: PublisherType = PublisherType.unknown
    profile_url: str | None = None
    corporate_email: bool | None = None
    company: Company | None = None


class SalaryPeriod(str, Enum):
    hourly = "hourly"
    monthly = "monthly"
    yearly = "yearly"


class Salary(BaseModel):
    min: float | None = None
    max: float | None = None
    currency: str | None = None  # ISO 4217, e.g. "USD"
    period: SalaryPeriod | None = None


class RequestedData(str, Enum):
    cv = "cv"
    linkedin_profile = "linkedin_profile"
    phone = "phone"
    address = "address"
    voice_recording = "voice_recording"
    video_recording = "video_recording"
    passport = "passport"
    national_id = "national_id"
    bank_account = "bank_account"
    payment = "payment"
    crypto = "crypto"


class JobPost(BaseModel):
    id: UUID | None = None
    title: str
    description: str
    url: str
    source: str
    company: Company | None = None
    publisher: Publisher | None = None
    salary: Salary | None = None
    application_url: str | None = None
    requested_data: list[RequestedData] = []
    posted_at: datetime | None = None
