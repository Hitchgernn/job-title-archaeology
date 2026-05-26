from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.narratives.models import NarrativeCard
from backend.trends.models import TrendResult, TrendScores


def make_trend() -> TrendResult:
    return TrendResult(
        normalized_title_id=10,
        display_title="AI Workflow Architect",
        token_key="ai|architect|workflow",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.86, concentration=0.6),
        trend_score=0.92,
        early_mover_companies=["Acme", "Globex"],
    )


def test_dashboard_trends_route_returns_response() -> None:
    client = TestClient(app)
    connection = MagicMock()

    with patch("backend.dashboard.router.open_connection", return_value=connection), patch("backend.dashboard.router.GeminiNarrativeProvider") as provider_class, patch("backend.dashboard.router.run_trend_scoring", return_value=[make_trend()]), patch("backend.dashboard.router.generate_narrative_cards_for_trends", return_value=[NarrativeCard(title="AI Workflow Architect", text="summary:\nAI workflow roles are emerging.")]):
        response = client.get("/dashboard/trends?limit=5")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["trend_count"] == 1
    assert body["trends"][0]["title"] == "AI Workflow Architect"
    assert body["trends"][0]["score"] == 0.92
    assert "AI workflow roles" in body["trends"][0]["narrative"]
    provider_class.assert_called_once()
    connection.close.assert_called_once()


def test_dashboard_trends_route_returns_empty_response() -> None:
    client = TestClient(app)
    connection = MagicMock()

    with patch("backend.dashboard.router.open_connection", return_value=connection), patch("backend.dashboard.router.GeminiNarrativeProvider"), patch("backend.dashboard.router.run_trend_scoring", return_value=[]), patch("backend.dashboard.router.generate_narrative_cards_for_trends", return_value=[]) as narrative_cards:
        response = client.get("/dashboard/trends")

    assert response.status_code == 200
    body = response.json()
    assert body["trends"] == []
    assert body["summary"]["trend_count"] == 0
    narrative_cards.assert_not_called()
    connection.close.assert_called_once()


def test_dashboard_trends_route_reuses_scored_trends_for_narratives() -> None:
    client = TestClient(app)
    connection = MagicMock()
    trend = make_trend()
    card = NarrativeCard(title="AI Workflow Architect", text="summary:\nAI workflow roles are emerging.")

    with patch("backend.dashboard.router.open_connection", return_value=connection), patch("backend.dashboard.router.GeminiNarrativeProvider"), patch("backend.dashboard.router.run_trend_scoring", return_value=[trend]) as scoring, patch("backend.dashboard.router.generate_narrative_cards_for_trends", return_value=[card]) as narrative_cards:
        response = client.get("/dashboard/trends?limit=5")

    assert response.status_code == 200
    scoring.assert_called_once_with(connection, limit=5)
    narrative_cards.assert_called_once()
    assert narrative_cards.call_args.args[0] == [trend]
    connection.close.assert_called_once()


def test_dashboard_trends_route_hides_internal_errors() -> None:
    client = TestClient(app)
    connection = MagicMock()

    with patch("backend.dashboard.router.open_connection", return_value=connection), patch("backend.dashboard.router.run_trend_scoring", side_effect=RuntimeError("secret database DSN")):
        response = client.get("/dashboard/trends")

    assert response.status_code == 500
    assert response.json()["detail"] == "failed to build dashboard response"
    assert "secret" not in response.text
    connection.close.assert_called_once()
