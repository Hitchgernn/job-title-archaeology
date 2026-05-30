from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TrendPostingRow(BaseModel):
    posting_id: int
    normalized_title_id: int
    display_title: str
    token_key: str
    company: str | None = None
    location: str | None = None
    scraped_at: datetime
    posted_at: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class EarlyMoverSignal(BaseModel):
    company: str
    date_label: str
    location_label: str
    posted_at: datetime | None = None
    scraped_at: datetime


class WeeklyCount(BaseModel):
    week_start: str
    count: int


class TrendScores(BaseModel):
    newness: float
    velocity: float
    concentration: float


class TrendResult(BaseModel):
    normalized_title_id: int
    display_title: str
    token_key: str
    recent_count: int
    prior_count: int
    total_count: int = 0
    scores: TrendScores
    trend_score: float
    early_mover_companies: list[str] = Field(default_factory=list)
    early_movers: list[EarlyMoverSignal] = Field(default_factory=list)
