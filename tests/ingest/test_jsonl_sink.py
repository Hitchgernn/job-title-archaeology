import json
from datetime import UTC, datetime

from backend.ingest.models import map_raw_posting
from backend.ingest.sinks.jsonl import write_jsonl_archive


def test_write_jsonl_archive_writes_one_record_per_line(tmp_path):
    records = [
        map_raw_posting(
            "run-123",
            {"job_title": "AI Lead"},
            datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        ),
        map_raw_posting(
            "run-123",
            {"job_title": "Data Lead"},
            datetime(2026, 5, 23, 12, 1, tzinfo=UTC),
        ),
    ]

    output_path = write_jsonl_archive(tmp_path, "run-123", records)

    assert output_path.name == "brightdata_run-123.jsonl"
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["normalized_preview"]["title"] == "AI Lead"
    assert json.loads(lines[1])["normalized_preview"]["title"] == "Data Lead"
