from pydantic import BaseModel, Field


class ArchiveRecord(BaseModel):
    record_id: str
    title: str
    category: str
    first_seen_label: str
    velocity_label: str
    score: float
    recent_count: int
    prior_count: int
    early_mover_companies: list[str] = Field(default_factory=list)
    excerpt: str


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
