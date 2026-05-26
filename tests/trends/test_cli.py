from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from backend.trends.cli import app
from backend.trends.models import TrendResult, TrendScores


def test_score_command_prints_ranked_trends() -> None:
    runner = CliRunner()
    trend = TrendResult(
        normalized_title_id=10,
        display_title="AI Workflow Architect",
        token_key="ai|architect|workflow",
        recent_count=2,
        prior_count=0,
        scores=TrendScores(newness=1.0, velocity=1.0, concentration=0.4),
        trend_score=0.85,
        early_mover_companies=["Acme", "Globex"],
    )

    with patch("backend.trends.cli.open_connection") as open_connection, patch("backend.trends.cli.run_trend_scoring") as run_trend_scoring:
        connection = MagicMock()
        open_connection.return_value = connection
        run_trend_scoring.return_value = [trend]

        result = runner.invoke(app, ["score", "--limit", "20"])

    assert result.exit_code == 0
    assert "1. AI Workflow Architect" in result.stdout
    assert "score=0.85" in result.stdout
    assert "recent=2" in result.stdout
    assert "prior=0" in result.stdout
    assert "early_movers=Acme, Globex" in result.stdout
    run_trend_scoring.assert_called_once_with(connection, limit=20)
    connection.close.assert_called_once()


def test_score_command_prints_empty_message() -> None:
    runner = CliRunner()

    with patch("backend.trends.cli.open_connection") as open_connection, patch("backend.trends.cli.run_trend_scoring") as run_trend_scoring:
        connection = MagicMock()
        open_connection.return_value = connection
        run_trend_scoring.return_value = []

        result = runner.invoke(app, ["score"])

    assert result.exit_code == 0
    assert "no trends found" in result.stdout
    run_trend_scoring.assert_called_once_with(connection, limit=20)
    connection.close.assert_called_once()
