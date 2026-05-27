from datetime import UTC, datetime
from unittest.mock import Mock, patch

from backend.db.connection import open_connection
from backend.ingest.models import map_raw_posting
from backend.ingest.sinks.postgres import load_raw_postings


def test_load_raw_postings_creates_table_and_inserts_records() -> None:
    connection = Mock()
    cursor = Mock()
    cursor.rowcount = 1
    cursor.fetchone.return_value = None
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
    assert cursor.execute.call_count == 1
    assert "INSERT INTO raw_job_postings" in cursor.execute.call_args_list[0].args[0]
    assert connection.commit.call_count >= 1


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
        row = connection.execute("SELECT title, title_key, company, company_key, raw FROM raw_job_postings").fetchone()
    finally:
        connection.close()

    assert inserted == 1
    assert row["title"] == "AI Workflow Architect"
    assert row["title_key"] == "ai workflow architect"
    assert row["company"] == "Acme"
    assert row["company_key"] == "acme"
    assert "AI Workflow Architect" in row["raw"]


def test_load_raw_postings_dedupes_same_title_and_company(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'job_title_archaeology.db'}"
    records = [
        map_raw_posting(
            "run-123",
            {"job_title": "AI Workflow Architect", "company_name": "Acme"},
            datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        ),
        map_raw_posting(
            "run-456",
            {"job_title": " ai   workflow architect ", "company_name": "ACME"},
            datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
        ),
    ]

    first_inserted = load_raw_postings(database_url, records[:1])
    second_inserted = load_raw_postings(database_url, records[1:])

    connection = open_connection(database_url)
    try:
        count = connection.execute("SELECT COUNT(*) FROM raw_job_postings").fetchone()[0]
    finally:
        connection.close()

    assert first_inserted == 1
    assert second_inserted == 0
    assert count == 1


def test_load_raw_postings_dedupes_existing_rows_without_keys(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'job_title_archaeology.db'}"
    connection = open_connection(database_url)
    try:
        connection.execute(
            """
            CREATE TABLE raw_job_postings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_run_id TEXT NOT NULL,
                scraped_at TEXT NOT NULL,
                title TEXT,
                company TEXT,
                location TEXT,
                url TEXT,
                posted_at TEXT,
                raw TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            INSERT INTO raw_job_postings (source, source_run_id, scraped_at, title, company, raw)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("brightdata_web_scraper", "old", "2026-05-23T12:00:00Z", "AI Workflow Architect", "Acme", "{}"),
        )
        connection.commit()
    finally:
        connection.close()

    inserted = load_raw_postings(
        database_url,
        [
            map_raw_posting(
                "new",
                {"job_title": "AI Workflow Architect", "company_name": "Acme"},
                datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
            )
        ],
    )

    connection = open_connection(database_url)
    try:
        count = connection.execute("SELECT COUNT(*) FROM raw_job_postings").fetchone()[0]
    finally:
        connection.close()

    assert inserted == 0
    assert count == 1


def test_load_raw_postings_allows_same_title_for_new_company(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'job_title_archaeology.db'}"
    records = [
        map_raw_posting(
            "run-123",
            {"job_title": "AI Workflow Architect", "company_name": "Acme"},
            datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        ),
        map_raw_posting(
            "run-456",
            {"job_title": "AI Workflow Architect", "company_name": "Northstar"},
            datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
        ),
    ]

    inserted = load_raw_postings(database_url, records)

    connection = open_connection(database_url)
    try:
        count = connection.execute("SELECT COUNT(*) FROM raw_job_postings").fetchone()[0]
    finally:
        connection.close()

    assert inserted == 2
    assert count == 2
