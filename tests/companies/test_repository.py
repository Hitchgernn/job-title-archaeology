from datetime import UTC, datetime

from backend.companies.models import CompanyPostingRow, CompanySignal, CompanyTitleVelocity
from backend.companies.repository import (
    fetch_company_posting_rows,
    fetch_company_signals,
    upsert_company_signal,
)
from backend.db.connection import open_connection
from backend.db.migrate import run_migrations


def _seed(connection) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO raw_job_postings (source, source_run_id, scraped_at, title, title_key, company, company_key, location, url, posted_at, posting_id, raw)
            VALUES ('brightdata_web_scraper', 'r1', '2026-05-28T00:00:00Z', 'AI Architect', 'ai architect', 'NVIDIA', 'nvidia', 'CA', NULL, '2026-05-22T00:00:00Z', 'p1', '{}')
            """
        )
        raw_posting_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO normalized_titles (canonical_title, display_title, token_key, occurrence_count)
            VALUES ('ai architect', 'AI Architect', 'ai|architect', 1)
            """
        )
        title_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO job_posting_titles (raw_job_posting_id, normalized_title_id, raw_title, confidence, method)
            VALUES (?, ?, 'AI Architect', 1.0, 'rules_v1')
            """,
            (raw_posting_id, title_id),
        )
    finally:
        cursor.close()
    connection.commit()


def test_fetch_company_posting_rows_returns_joined_data(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    connection = open_connection(database_url)
    try:
        run_migrations(connection)
        _seed(connection)
        rows = fetch_company_posting_rows(connection)
    finally:
        connection.close()

    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row, CompanyPostingRow)
    assert row.company == "NVIDIA"
    assert row.display_title == "AI Architect"
    assert row.posted_at == "2026-05-22T00:00:00Z"


def test_upsert_and_fetch_company_signals_round_trips(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    connection = open_connection(database_url)
    try:
        run_migrations(connection)
        signal = CompanySignal(
            company_key="nvda",
            ticker="NVDA",
            display_name="NVIDIA",
            recent_hires_30d=12,
            prior_hires_30d=4,
            velocity_score=3.0,
            top_titles=[
                CompanyTitleVelocity(
                    normalized_title_id=1,
                    display_title="AI Architect",
                    count=8,
                )
            ],
            computed_at=datetime(2026, 5, 28, tzinfo=UTC),
        )
        upsert_company_signal(connection, signal)
        connection.commit()
        signals = fetch_company_signals(connection)
    finally:
        connection.close()

    assert len(signals) == 1
    fetched = signals[0]
    assert fetched.ticker == "NVDA"
    assert fetched.recent_hires_30d == 12
    assert fetched.top_titles[0].display_title == "AI Architect"


def test_upsert_replaces_existing_company_signal(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    connection = open_connection(database_url)
    try:
        run_migrations(connection)
        first = CompanySignal(
            company_key="nvda",
            ticker="NVDA",
            display_name="NVIDIA",
            recent_hires_30d=5,
            prior_hires_30d=1,
            velocity_score=5.0,
            top_titles=[],
            computed_at=datetime(2026, 5, 27, tzinfo=UTC),
        )
        upsert_company_signal(connection, first)
        second = first.model_copy(update={"recent_hires_30d": 11, "computed_at": datetime(2026, 5, 28, tzinfo=UTC)})
        upsert_company_signal(connection, second)
        connection.commit()
        signals = fetch_company_signals(connection)
    finally:
        connection.close()

    assert len(signals) == 1
    assert signals[0].recent_hires_30d == 11
