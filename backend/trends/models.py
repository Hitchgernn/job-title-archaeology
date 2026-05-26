from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TrendPostingRow(BaseModel):
    posting_id: int
    normalized_title_id: int
    display_title: str
    token_key: str
    company: str | None = None
    scraped_at: datetime
    raw: dict[str, Any] = Field(default_factory=dict)


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
    scores: TrendScores
    trend_score: float
    early_mover_companies: list[str] = Field(default_factory=list)
