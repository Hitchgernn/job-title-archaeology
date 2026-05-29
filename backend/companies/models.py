from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CompanyPostingRow(BaseModel):
    posting_id: int
    company: str | None = None
    normalized_title_id: int
    display_title: str
    posted_at: str | None = None
    scraped_at: datetime
    raw: dict[str, Any] = Field(default_factory=dict)


class CompanyTitleVelocity(BaseModel):
    normalized_title_id: int
    display_title: str
    count: int
    weekly_buckets: list[dict[str, Any]] = Field(default_factory=list)


class WeeklyHire(BaseModel):
    week_start: str
    count: int


class CompanySignal(BaseModel):
    company_key: str
    ticker: str | None = None
    display_name: str
    recent_hires_30d: int
    prior_hires_30d: int
    velocity_score: float
    top_titles: list[CompanyTitleVelocity] = Field(default_factory=list)
    computed_at: datetime


class CompanyDossier(BaseModel):
    company: CompanySignal
    weekly: list[WeeklyHire] = Field(default_factory=list)
    titles: list[CompanyTitleVelocity] = Field(default_factory=list)


class CompanyListSummary(BaseModel):
    tracked_count: int
    total_recent_hires: int
    last_computed_at: datetime | None = None


class CompanyListResponse(BaseModel):
    companies: list[CompanySignal]
    summary: CompanyListSummary
