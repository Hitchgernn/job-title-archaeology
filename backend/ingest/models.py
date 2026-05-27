from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_serializer


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


class NormalizedPreview(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    url: str | None = None
    posted_at: str | None = None


class RawJobPostingEnvelope(BaseModel):
    source: str = "brightdata_web_scraper"
    source_run_id: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw: dict[str, Any]
    normalized_preview: NormalizedPreview

    @field_serializer("scraped_at")
    def serialize_scraped_at(self, value: datetime) -> str:
        return _serialize_datetime(value)


def _first_present(raw: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def map_raw_posting(
    source_run_id: str,
    raw: dict[str, Any],
    scraped_at: datetime | None = None,
) -> RawJobPostingEnvelope:
    return RawJobPostingEnvelope(
        source_run_id=source_run_id,
        scraped_at=scraped_at or datetime.now(UTC),
        raw=raw,
        normalized_preview=NormalizedPreview(
            title=_first_present(raw, ("job_title", "title", "position", "name", "job_name")),
            company=_first_present(raw, ("company_name", "company", "employer", "company_url_text")),
            location=_first_present(raw, ("location", "job_location", "city", "country", "formatted_location")),
            url=_first_present(raw, ("url", "job_url", "apply_url", "apply_link", "job_posting_url", "link")),
            posted_at=_first_present(raw, ("date_posted", "date_posted_parsed", "posted_at", "posted_date", "job_posted_date", "published_at", "created_at")),
        ),
    )
