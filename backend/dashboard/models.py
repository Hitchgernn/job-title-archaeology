from pydantic import BaseModel, Field


class DashboardTrendCard(BaseModel):
    rank: int
    title: str
    score: float
    recent_count: int
    prior_count: int
    newness: float
    velocity: float
    concentration: float
    early_mover_companies: list[str] = Field(default_factory=list)
    narrative: str


class DashboardSummary(BaseModel):
    trend_count: int
    average_score: float
    early_mover_count: int


class DashboardResponse(BaseModel):
    trends: list[DashboardTrendCard]
    summary: DashboardSummary
