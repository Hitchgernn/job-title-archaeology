from datetime import UTC, datetime

from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.serp.client import SerpHit
from backend.serp.repository import fetch_serp_signals_for_titles, upsert_serp_signal


def test_upsert_and_fetch_serp_signals_round_trips(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    connection = open_connection(database_url)
    try:
        run_migrations(connection)
        connection.execute(
            "INSERT INTO normalized_titles (canonical_title, display_title, token_key, occurrence_count) "
            "VALUES ('ai architect', 'AI Architect', 'ai|architect', 1)"
        )
        title_id = connection.execute("SELECT id FROM normalized_titles").fetchone()[0]
        upsert_serp_signal(
            connection,
            normalized_title_id=title_id,
            query_kind="press",
            query="AI Architect press release",
            hits=[
                SerpHit(title="hit one", url="https://example.com/a", snippet="snippet a", source="example.com"),
                SerpHit(title="hit two", url="https://news.example.com/b", snippet="snippet b", source="news.example.com"),
            ],
            fetched_at=datetime(2026, 5, 28, tzinfo=UTC),
        )
        connection.commit()
        signals = fetch_serp_signals_for_titles(connection, [title_id])
    finally:
        connection.close()

    assert title_id in signals
    rows = signals[title_id]
    assert len(rows) == 2
    assert rows[0].title == "hit one"
    assert rows[1].source == "news.example.com"


def test_upsert_replaces_existing_query_kind(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    connection = open_connection(database_url)
    try:
        run_migrations(connection)
        connection.execute(
            "INSERT INTO normalized_titles (canonical_title, display_title, token_key, occurrence_count) "
            "VALUES ('ai architect', 'AI Architect', 'ai|architect', 1)"
        )
        title_id = connection.execute("SELECT id FROM normalized_titles").fetchone()[0]
        upsert_serp_signal(
            connection,
            normalized_title_id=title_id,
            query_kind="press",
            query="q1",
            hits=[SerpHit(title="old", url="https://example.com/old", snippet="s", source="example.com")],
            fetched_at=datetime(2026, 5, 27, tzinfo=UTC),
        )
        upsert_serp_signal(
            connection,
            normalized_title_id=title_id,
            query_kind="press",
            query="q1",
            hits=[SerpHit(title="new", url="https://example.com/new", snippet="s", source="example.com")],
            fetched_at=datetime(2026, 5, 28, tzinfo=UTC),
        )
        connection.commit()
        signals = fetch_serp_signals_for_titles(connection, [title_id])
    finally:
        connection.close()

    rows = signals[title_id]
    assert len(rows) == 1
    assert rows[0].title == "new"
