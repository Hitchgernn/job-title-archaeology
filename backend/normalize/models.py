from pydantic import BaseModel, Field


class NormalizedTitleResult(BaseModel):
    display_title: str
    canonical_title: str
    token_key: str
    level_terms: list[str] = Field(default_factory=list)
    work_mode: str | None = None
    confidence: float
    method: str = "rules_v1"
    usable: bool
