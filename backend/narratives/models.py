from pydantic import BaseModel

from backend.trends.models import TrendResult


class NarrativeRequest(BaseModel):
    trend: TrendResult


class NarrativeCard(BaseModel):
    title: str
    text: str
