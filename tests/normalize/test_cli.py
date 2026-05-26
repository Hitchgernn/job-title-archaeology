from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from backend.normalize.cli import app
from backend.normalize.pipeline import NormalizeSummary


def test_migrate_command_runs_migrations() -> None:
    runner = CliRunner()
    with patch("backend.normalize.cli.open_connection") as open_connection, patch("backend.normalize.cli.run_migrations") as run_migrations:
        connection = MagicMock()
        open_connection.return_value = connection

        result = runner.invoke(app, ["migrate"])

    assert result.exit_code == 0
    run_migrations.assert_called_once_with(connection)
    connection.close.assert_called_once()


def test_normalize_command_runs_pipeline() -> None:
    runner = CliRunner()
    with patch("backend.normalize.cli.open_connection") as open_connection, patch("backend.normalize.cli.run_normalization") as run_normalization:
        connection = MagicMock()
        open_connection.return_value = connection
        run_normalization.return_value = NormalizeSummary(processed=2, linked=2, skipped=0, unique_titles=1)

        result = runner.invoke(app, ["normalize", "--limit", "1000"])

    assert result.exit_code == 0
    assert "processed=2" in result.stdout
    assert "linked=2" in result.stdout
    run_normalization.assert_called_once_with(connection, limit=1000)
    connection.close.assert_called_once()
