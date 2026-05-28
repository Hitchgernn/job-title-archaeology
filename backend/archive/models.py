from pydantic import BaseModel, Field, field_validator


class ArchiveSectorBreakdown(BaseModel):
    sector: str
    percentage: int

    @field_validator("sector")
    @classmethod
    def require_sector(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("sector must not be empty")
        return stripped

    @field_validator("percentage")
    @classmethod
    def require_percentage(cls, value: int) -> int:
        if value < 0 or value > 100:
            raise ValueError("percentage must be between 0 and 100")
        return value


class ArchiveEditorialMetadata(BaseModel):
    category: str
    sector: str
    lead_paragraph: str
    pull_quote: str
    preceding_titles: list[str] = Field(min_length=3, max_length=3)
    competencies: list[str] = Field(min_length=4, max_length=4)
    outlook: str
    sector_breakdown: list[ArchiveSectorBreakdown] = Field(default_factory=list)
    image_prompt: str | None = None
    image_path: str | None = None
    image_provider: str | None = None
    image_model: str | None = None

    @field_validator("category", "sector", "lead_paragraph", "pull_quote", "outlook")
    @classmethod
    def require_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped

    @field_validator("preceding_titles", "competencies")
    @classmethod
    def require_items(cls, values: list[str]) -> list[str]:
        stripped = [value.strip() for value in values]
        if any(not value for value in stripped):
            raise ValueError("items must not be empty")
        return stripped


class ArchiveRecord(BaseModel):
    record_id: str
    title: str
    category: str
    category_detail: str
    categories: list[str]
    first_seen_label: str
    velocity_label: str
    score: float
    recent_count: int
    prior_count: int
    early_mover_companies: list[str] = Field(default_factory=list)
    excerpt: str
    image_path: str | None = None


class EraDensity(BaseModel):
    label: str
    percentage: int


class ArchiveSummary(BaseModel):
    total_records: int
    category_counts: dict[str, int]
    era_density: list[EraDensity]


class ArchiveResponse(BaseModel):
    records: list[ArchiveRecord]
    summary: ArchiveSummary


class AdoptionPoint(BaseModel):
    label: str
    value: int
    annotation: str | None = None


class SectorDensity(BaseModel):
    sector: str
    percentage: int


class EarlyAdopter(BaseModel):
    company: str
    date_label: str
    location_label: str


class DossierResponse(ArchiveRecord):
    subheadline: str
    lead_paragraph: str
    pull_quote: str
    adoption_points: list[AdoptionPoint]
    sector_density: list[SectorDensity]
    early_adopters: list[EarlyAdopter]
    preceding_titles: list[str]
    competencies: list[str]
    outlook: str
