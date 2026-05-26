from unittest.mock import MagicMock, patch

from backend.narratives.pipeline import generate_narrative_cards
from backend.trends.models import TrendResult, TrendScores


def make_trend(title: str = "AI Workflow Architect") -> TrendResult:
    return TrendResult(
        normalized_title_id=10,
        display_title=title,
        token_key="ai|architect|workflow",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.86, concentration=0.6),
        trend_score=0.92,
        early_mover_companies=["Acme"],
    )


def test_generate_narrative_cards_calls_trends_and_provider() -> None:
    connection = MagicMock()
    provider = MagicMock()
    provider.generate.return_value = "summary:\nAI workflow roles are emerging."

    with patch("backend.narratives.pipeline.run_trend_scoring", return_value=[make_trend()]):
        cards = generate_narrative_cards(connection, provider=provider, limit=5)

    assert len(cards) == 1
    assert cards[0].title == "AI Workflow Architect"
    assert "AI workflow roles" in cards[0].text
    provider.generate.assert_called_once()
    prompt = provider.generate.call_args.args[0]
    assert "AI Workflow Architect" in prompt


def test_generate_narrative_cards_returns_empty_list_for_no_trends() -> None:
    connection = MagicMock()
    provider = MagicMock()

    with patch("backend.narratives.pipeline.run_trend_scoring", return_value=[]):
        cards = generate_narrative_cards(connection, provider=provider, limit=5)

    assert cards == []
    provider.generate.assert_not_called()


def test_generate_narrative_cards_falls_back_for_empty_provider_text() -> None:
    connection = MagicMock()
    provider = MagicMock()
    provider.generate.return_value = ""

    with patch("backend.narratives.pipeline.run_trend_scoring", return_value=[make_trend()]):
        cards = generate_narrative_cards(connection, provider=provider, limit=5)

    assert cards[0].title == "AI Workflow Architect"
    assert "trend score 0.92" in cards[0].text


def test_generate_narrative_cards_falls_back_for_provider_error() -> None:
    connection = MagicMock()
    provider = MagicMock()
    provider.generate.side_effect = RuntimeError("quota exhausted")

    with patch("backend.narratives.pipeline.run_trend_scoring", return_value=[make_trend()]):
        cards = generate_narrative_cards(connection, provider=provider, limit=5)

    assert cards[0].title == "AI Workflow Architect"
    assert "trend score 0.92" in cards[0].text
