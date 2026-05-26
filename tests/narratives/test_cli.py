from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from backend.narratives.cli import app
from backend.narratives.models import NarrativeCard


def test_generate_command_prints_cards() -> None:
    runner = CliRunner()
    card = NarrativeCard(title="AI Workflow Architect", text="summary:\nAI workflows are emerging.")

    with patch("backend.narratives.cli.open_connection") as open_connection, patch("backend.narratives.cli.GeminiNarrativeProvider") as provider_class, patch("backend.narratives.cli.generate_narrative_cards") as generate_narrative_cards:
        connection = MagicMock()
        provider = MagicMock()
        open_connection.return_value = connection
        provider_class.return_value = provider
        generate_narrative_cards.return_value = [card]

        result = runner.invoke(app, ["generate", "--limit", "5"])

    assert result.exit_code == 0
    assert "1. AI Workflow Architect" in result.stdout
    assert "summary:" in result.stdout
    assert "AI workflows are emerging." in result.stdout
    generate_narrative_cards.assert_called_once_with(connection, provider=provider, limit=5)
    connection.close.assert_called_once()


def test_generate_command_prints_empty_message() -> None:
    runner = CliRunner()

    with patch("backend.narratives.cli.open_connection") as open_connection, patch("backend.narratives.cli.GeminiNarrativeProvider") as provider_class, patch("backend.narratives.cli.generate_narrative_cards") as generate_narrative_cards:
        connection = MagicMock()
        provider = MagicMock()
        open_connection.return_value = connection
        provider_class.return_value = provider
        generate_narrative_cards.return_value = []

        result = runner.invoke(app, ["generate"])

    assert result.exit_code == 0
    assert "no trends found" in result.stdout
    generate_narrative_cards.assert_called_once_with(connection, provider=provider, limit=5)
    connection.close.assert_called_once()
