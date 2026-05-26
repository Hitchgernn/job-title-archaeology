from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from backend.normalize.pipeline import NormalizeSummary, run_normalization


@patch("backend.normalize.pipeline.link_posting_to_title")
@patch("backend.normalize.pipeline.upsert_normalized_title", side_effect=[7, 7])
@patch("backend.normalize.pipeline.fetch_unlinked_raw_postings")
def test_run_normalization_groups_variants(fetch_unlinked_raw_postings, upsert_normalized_title, link_posting_to_title) -> None:
    connection = MagicMock()
    fetch_unlinked_raw_postings.return_value = [
        {
            "id": 1,
            "title": "Senior GenAI Product Ops Lead (Remote)",
            "scraped_at": datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        },
        {
            "id": 2,
            "title": "Gen AI Product Operations Lead",
            "scraped_at": datetime(2026, 5, 23, 12, 5, tzinfo=UTC),
        },
    ]

    summary = run_normalization(connection, limit=1000)

    assert isinstance(summary, NormalizeSummary)
    assert summary.processed == 2
    assert summary.linked == 2
    assert summary.skipped == 0
    assert summary.unique_titles == 1
    assert upsert_normalized_title.call_count == 2
    assert link_posting_to_title.call_count == 2
    connection.commit.assert_called_once()


@patch("backend.normalize.pipeline.fetch_unlinked_raw_postings")
def test_run_normalization_skips_unusable_titles(fetch_unlinked_raw_postings) -> None:
    connection = MagicMock()
    fetch_unlinked_raw_postings.return_value = [
        {
            "id": 1,
            "title": "Remote!!!",
            "scraped_at": datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
        }
    ]

    summary = run_normalization(connection, limit=1000)

    assert summary.processed == 1
    assert summary.linked == 0
    assert summary.skipped == 1
    assert summary.unique_titles == 0
