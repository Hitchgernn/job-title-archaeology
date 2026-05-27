from datetime import UTC, datetime

from backend.ingest.models import RawJobPostingEnvelope, map_raw_posting


def test_map_raw_posting_extracts_preview_fields():
    raw = {
        "job_title": "Prompt Engineer",
        "company_name": "Anthropic",
        "location": "San Francisco, CA",
        "url": "https://example.com/jobs/prompt-engineer",
        "date_posted": "2026-05-22",
        "extra": "preserved",
    }
    scraped_at = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)

    envelope = map_raw_posting("run-123", raw, scraped_at)

    assert envelope.source == "brightdata_web_scraper"
    assert envelope.source_run_id == "run-123"
    assert envelope.raw == raw
    assert envelope.normalized_preview.title == "Prompt Engineer"
    assert envelope.normalized_preview.company == "Anthropic"
    assert envelope.normalized_preview.location == "San Francisco, CA"
    assert envelope.normalized_preview.url == "https://example.com/jobs/prompt-engineer"
    assert envelope.normalized_preview.posted_at == "2026-05-22"


def test_map_raw_posting_accepts_bright_data_dataset_fields():
    raw = {
        "title": "Clinical AI Safety Officer",
        "company": "Northstar Health",
        "job_location": "Boston, MA",
        "job_url": "https://example.com/jobs/clinical-ai-safety-officer",
        "posted_date": "2026-05-20",
        "description": "Own AI safety review for clinical workflows.",
    }

    envelope = map_raw_posting("brightdata-demo-run", raw)

    assert envelope.source == "brightdata_web_scraper"
    assert envelope.source_run_id == "brightdata-demo-run"
    assert envelope.normalized_preview.title == "Clinical AI Safety Officer"
    assert envelope.normalized_preview.company == "Northstar Health"
    assert envelope.normalized_preview.location == "Boston, MA"
    assert envelope.normalized_preview.url == "https://example.com/jobs/clinical-ai-safety-officer"
    assert envelope.normalized_preview.posted_at == "2026-05-20"


def test_envelope_serializes_iso_timestamp():
    envelope = RawJobPostingEnvelope.model_validate(
        {
            "source_run_id": "run-123",
            "scraped_at": "2026-05-23T12:00:00Z",
            "raw": {"title": "Prompt Engineer"},
            "normalized_preview": {"title": "Prompt Engineer"},
        }
    )

    payload = envelope.model_dump(mode="json")

    assert payload["scraped_at"] == "2026-05-23T12:00:00Z"
