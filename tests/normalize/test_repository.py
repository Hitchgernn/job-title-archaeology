from datetime import UTC, datetime
from unittest.mock import MagicMock

from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.normalize.models import NormalizedTitleResult
from backend.normalize.repository import fetch_unlinked_raw_postings, link_posting_to_title, upsert_normalized_title


def test_fetch_unlinked_raw_postings_returns_rows() -> None:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        {
            "id": 1,
            "title": "Senior GenAI Product Ops Lead (Remote)",
            "scraped_at": datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        }
    ]

    rows = fetch_unlinked_raw_postings(connection, limit=100)

    assert rows[0]["id"] == 1
    assert "LEFT JOIN job_posting_titles" in cursor.execute.call_args.args[0]


def test_upsert_normalized_title_returns_id() -> None:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = [7]
    result = NormalizedTitleResult(
        display_title="Senior GenAI Product Ops Lead",
        canonical_title="generative ai product operations",
        token_key="ai|generative|operations|product",
        level_terms=["senior", "lead"],
        work_mode="remote",
        confidence=1.0,
        usable=True,
    )

    normalized_title_id = upsert_normalized_title(
        connection,
        result,
        first_seen_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        last_seen_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
    )

    assert normalized_title_id == 7
    assert "INSERT INTO normalized_titles" in cursor.execute.call_args.args[0]


def test_link_posting_to_title_inserts_link() -> None:
    connection = MagicMock()
    result = NormalizedTitleResult(
        display_title="Senior GenAI Product Ops Lead",
        canonical_title="generative ai product operations",
        token_key="ai|generative|operations|product",
        level_terms=["senior", "lead"],
        work_mode="remote",
        confidence=1.0,
        usable=True,
    )

    link_posting_to_title(connection, raw_job_posting_id=3, normalized_title_id=7, raw_title="Senior GenAI Product Ops Lead (Remote)", normalized=result)

    cursor = connection.cursor.return_value.__enter__.return_value
    assert "INSERT INTO job_posting_titles" in cursor.execute.call_args.args[0]


def test_sqlite_repository_flow_links_raw_posting_to_normalized_title(tmp_path) -> None:
    connection = open_connection(f"sqlite:///{tmp_path / 'job_title_archaeology.db'}")
    try:
        run_migrations(connection)
        connection.execute(
            """
            INSERT INTO raw_job_postings (source, source_run_id, scraped_at, title, raw)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "test",
                "run-123",
                "2026-05-23T12:00:00Z",
                "Senior AI Workflow Architect",
                '{"title": "Senior AI Workflow Architect"}',
            ),
        )
        connection.commit()

        rows = fetch_unlinked_raw_postings(connection, limit=10)
        normalized = NormalizedTitleResult(
            display_title="Senior AI Workflow Architect",
            canonical_title="ai workflow architect",
            token_key="ai|architect|workflow",
            level_terms=["senior"],
            work_mode=None,
            confidence=1.0,
            usable=True,
        )
        normalized_title_id = upsert_normalized_title(
            connection,
            normalized,
            first_seen_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
            last_seen_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        )
        link_posting_to_title(connection, rows[0]["id"], normalized_title_id, rows[0]["title"], normalized)
        connection.commit()
        linked = connection.execute("SELECT raw_title FROM job_posting_titles").fetchone()
    finally:
        connection.close()

    assert rows[0]["title"] == "Senior AI Workflow Architect"
    assert normalized_title_id == 1
    assert linked["raw_title"] == "Senior AI Workflow Architect"
