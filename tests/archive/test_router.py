from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from backend.app.main import app
from backend.trends.models import TrendResult, TrendScores


client = TestClient(app)


def make_trend(title: str = "AI Workflow Architect") -> TrendResult:
    return TrendResult(
        normalized_title_id=10,
        display_title=title,
        token_key="ai|architect|workflow",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.86, concentration=0.6),
        trend_score=0.92,
        early_mover_companies=["Acme AI Lab", "Northstar Systems"],
    )


def test_archive_titles_returns_records() -> None:
    connection = MagicMock()
    with patch("backend.archive.router.open_connection", return_value=connection), patch(
        "backend.archive.router.run_trend_scoring", return_value=[make_trend()]
    ), patch("backend.archive.router.fetch_cached_metadata", return_value={}):
        response = client.get("/archive/titles?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_records"] == 1
    assert payload["records"][0]["record_id"] == "JTA-0001-AI-WORKFLOW-ARCHITECT"
    connection.close.assert_called_once()


def test_archive_titles_does_not_instantiate_gemini_provider() -> None:
    connection = MagicMock()
    with patch("backend.archive.router.open_connection", return_value=connection), patch(
        "backend.archive.router.run_trend_scoring", return_value=[make_trend()]
    ), patch("backend.narratives.providers.GeminiNarrativeProvider") as provider:
        response = client.get("/archive/titles?limit=5")

    assert response.status_code == 200
    provider.assert_not_called()


def test_archive_dossier_returns_selected_record() -> None:
    connection = MagicMock()
    with patch("backend.archive.router.open_connection", return_value=connection), patch(
        "backend.archive.router.run_trend_scoring", return_value=[make_trend(), make_trend("Agent Operations Lead")]
    ), patch("backend.archive.router.fetch_cached_metadata", return_value={}):
        response = client.get("/archive/titles/JTA-0002-AGENT-OPERATIONS-LEAD?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Agent Operations Lead"
    assert payload["record_id"] == "JTA-0002-AGENT-OPERATIONS-LEAD"
    assert payload["pull_quote"]


def test_archive_dossier_returns_404_for_unknown_record() -> None:
    connection = MagicMock()
    with patch("backend.archive.router.open_connection", return_value=connection), patch(
        "backend.archive.router.run_trend_scoring", return_value=[make_trend()]
    ), patch("backend.archive.router.fetch_cached_metadata", return_value={}):
        response = client.get("/archive/titles/JTA-9999-NOPE?limit=5")

    assert response.status_code == 404
    assert response.json()["detail"] == "archive record not found"
