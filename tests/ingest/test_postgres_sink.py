from datetime import UTC, datetime
from unittest.mock import Mock, patch

from backend.db.connection import open_connection
from backend.ingest.models import map_raw_posting
from backend.ingest.sinks.postgres import load_raw_postings


def test_load_raw_postings_creates_table_and_inserts_records() -> None:
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=None)
    records = [
        map_raw_posting(
            "run-123",
            {"job_title": "AI Lead"},
            datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        )
    ]

    with patch("backend.ingest.sinks.postgres.psycopg.connect", return_value=connection) as connect:
        inserted = load_raw_postings("postgresql://example", records)

    connect.assert_called_once_with("postgresql://example")
    assert inserted == 1
    assert cursor.execute.call_count == 2
    assert "CREATE TABLE IF NOT EXISTS raw_job_postings" in cursor.execute.call_args_list[0].args[0]
    assert "INSERT INTO raw_job_postings" in cursor.execute.call_args_list[1].args[0]
    connection.commit.assert_called_once()


def test_load_raw_postings_supports_sqlite_url(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'job_title_archaeology.db'}"
    records = [
        map_raw_posting(
            "run-123",
            {"job_title": "AI Workflow Architect", "company_name": "Acme"},
            datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        )
    ]

    inserted = load_raw_postings(database_url, records)

    connection = open_connection(database_url)
    try:
        row = connection.execute("SELECT title, company, raw FROM raw_job_postings").fetchone()
    finally:
        connection.close()

    assert inserted == 1
    assert row["title"] == "AI Workflow Architect"
    assert row["company"] == "Acme"
    assert "AI Workflow Architect" in row["raw"]
