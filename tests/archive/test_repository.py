from backend.archive.models import ArchiveEditorialMetadata
from backend.archive.repository import fetch_cached_metadata, metadata_input_hash, upsert_cached_metadata
from backend.archive.prompts import PROMPT_VERSION
from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.trends.models import TrendResult, TrendScores


def make_metadata() -> ArchiveEditorialMetadata:
    return ArchiveEditorialMetadata(
        category="Tech / Architecture",
        sector="Technology",
        lead_paragraph="AI solutions architecture is becoming a named role for teams that need durable ownership of model-enabled products, integration decisions, governance checkpoints, and delivery standards across business functions.",
        pull_quote="AI architecture becomes visible when integration pressure turns into operating structure.",
        preceding_titles=["Solutions Architect", "Cloud Architect", "AI Engineer"],
        competencies=["System design", "AI integration", "Governance review", "Stakeholder translation"],
        outlook="Expect the title to spread where companies need durable ownership of AI implementation decisions across product, platform, and operating teams.",
    )


def make_trend() -> TrendResult:
    return TrendResult(
        normalized_title_id=1,
        display_title="AI Solutions Architect",
        token_key="ai|architect|solutions",
        recent_count=18,
        prior_count=0,
        scores=TrendScores(newness=1.0, velocity=0.9, concentration=0.7),
        trend_score=0.95,
        early_mover_companies=["Acme", "Northstar"],
    )


def test_archive_metadata_cache_roundtrips_sqlite(tmp_path) -> None:
    connection = open_connection(f"sqlite:///{tmp_path / 'job_title_archaeology.db'}")
    try:
        run_migrations(connection)
        connection.execute(
            """
            INSERT INTO normalized_titles (
                canonical_title, display_title, token_key, level_terms, first_seen_at, last_seen_at, occurrence_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("ai solutions architect", "AI Solutions Architect", "ai|architect|solutions", "[]", "2026-05-27", "2026-05-27", 1),
        )
        metadata = make_metadata()
        upsert_cached_metadata(connection, 1, PROMPT_VERSION, "Provider", "model", metadata_input_hash(make_trend()), metadata)
        connection.commit()

        fetched = fetch_cached_metadata(connection, [1], PROMPT_VERSION)
    finally:
        connection.close()

    assert fetched[1].category == "Tech / Architecture"
    assert fetched[1].competencies == metadata.competencies
