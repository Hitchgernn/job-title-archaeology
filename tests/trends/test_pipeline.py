from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from backend.trends.models import TrendPostingRow
from backend.trends.pipeline import run_trend_scoring


def test_run_trend_scoring_groups_and_ranks_titles() -> None:
    now = datetime(2026, 5, 23, tzinfo=timezone.utc)
    connection = MagicMock()
    rows = [
        TrendPostingRow(
            posting_id=1,
            normalized_title_id=10,
            display_title="AI Workflow Architect",
            token_key="ai|architect|workflow",
            company="Acme",
            scraped_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
            raw={"industry": "Technology"},
        ),
        TrendPostingRow(
            posting_id=2,
            normalized_title_id=10,
            display_title="AI Workflow Architect",
            token_key="ai|architect|workflow",
            company="Globex",
            scraped_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
            raw={"industry": "Healthcare"},
        ),
        TrendPostingRow(
            posting_id=3,
            normalized_title_id=11,
            display_title="Prompt Engineer",
            token_key="engineer|prompt",
            company="Initech",
            scraped_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
            raw={},
        ),
    ]

    with patch("backend.trends.pipeline.fetch_trend_posting_rows", return_value=rows):
        results = run_trend_scoring(connection, limit=1, now=now)

    assert len(results) == 1
    assert results[0].display_title == "AI Workflow Architect"
    assert results[0].recent_count == 2


def test_run_trend_scoring_returns_empty_list_for_no_rows() -> None:
    connection = MagicMock()
    now = datetime(2026, 5, 23, tzinfo=timezone.utc)

    with patch("backend.trends.pipeline.fetch_trend_posting_rows", return_value=[]):
        results = run_trend_scoring(connection, limit=20, now=now)

    assert results == []
