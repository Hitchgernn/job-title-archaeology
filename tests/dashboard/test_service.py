from backend.dashboard.service import build_dashboard_response
from backend.narratives.models import NarrativeCard
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
        early_mover_companies=["Acme", "Globex"],
    )


def test_build_dashboard_response_maps_trends_and_cards() -> None:
    response = build_dashboard_response(
        trends=[make_trend()],
        narratives=[NarrativeCard(title="AI Workflow Architect", text="summary:\nAI workflow roles are emerging.")],
    )

    assert response.summary.trend_count == 1
    assert response.summary.average_score == 0.92
    assert response.summary.early_mover_count == 2
    assert response.trends[0].rank == 1
    assert response.trends[0].title == "AI Workflow Architect"
    assert response.trends[0].score == 0.92
    assert response.trends[0].recent_count == 12
    assert response.trends[0].early_mover_companies == ["Acme", "Globex"]
    assert "AI workflow roles" in response.trends[0].narrative


def test_build_dashboard_response_handles_empty_input() -> None:
    response = build_dashboard_response(trends=[], narratives=[])

    assert response.trends == []
    assert response.summary.trend_count == 0
    assert response.summary.average_score == 0.0
    assert response.summary.early_mover_count == 0
