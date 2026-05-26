from datetime import datetime, timezone
from unittest.mock import MagicMock

from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.trends.repository import fetch_trend_posting_rows


def test_fetch_trend_posting_rows_maps_joined_rows() -> None:
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    scraped_at = datetime(2026, 5, 22, tzinfo=timezone.utc)
    cursor.fetchall.return_value = [
        {
            "posting_id": 1,
            "normalized_title_id": 10,
            "display_title": "AI Workflow Architect",
            "token_key": "ai|architect|workflow",
            "company": "Acme",
            "scraped_at": scraped_at,
            "raw": {"industry": "Technology"},
        }
    ]

    rows = fetch_trend_posting_rows(connection)

    assert len(rows) == 1
    assert rows[0].posting_id == 1
    assert rows[0].normalized_title_id == 10
    assert rows[0].company == "Acme"
    assert rows[0].raw == {"industry": "Technology"}
    executed_sql = cursor.execute.call_args.args[0]
    assert "JOIN job_posting_titles" in executed_sql
    assert "JOIN normalized_titles" in executed_sql
    assert "raw_job_postings.scraped_at <= NOW()" in executed_sql


def test_fetch_trend_posting_rows_supports_sqlite(tmp_path) -> None:
    connection = open_connection(f"sqlite:///{tmp_path / 'job_title_archaeology.db'}")
    try:
        run_migrations(connection)
        connection.execute(
            """
            INSERT INTO raw_job_postings (source, source_run_id, scraped_at, title, company, raw)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "test",
                "run-123",
                "2026-05-23T12:00:00Z",
                "AI Workflow Architect",
                "Acme",
                '{"industry": "Technology"}',
            ),
        )
        connection.execute(
            """
            INSERT INTO normalized_titles (
                canonical_title, display_title, token_key, level_terms, first_seen_at, last_seen_at, occurrence_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ai workflow architect",
                "AI Workflow Architect",
                "ai|architect|workflow",
                "[]",
                "2026-05-23T12:00:00Z",
                "2026-05-23T12:00:00Z",
                1,
            ),
        )
        connection.execute(
            """
            INSERT INTO job_posting_titles (raw_job_posting_id, normalized_title_id, raw_title, confidence, method)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, 1, "AI Workflow Architect", 1.0, "rules"),
        )
        connection.commit()

        rows = fetch_trend_posting_rows(connection)
    finally:
        connection.close()

    assert len(rows) == 1
    assert rows[0].display_title == "AI Workflow Architect"
    assert rows[0].company == "Acme"
    assert rows[0].raw == {"industry": "Technology"}
