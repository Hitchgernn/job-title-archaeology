from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from backend.archive.cli import app
from backend.archive.models import ArchiveEditorialMetadata
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
        early_mover_companies=["Acme AI Lab", "Northstar Systems"],
    )


def make_metadata() -> ArchiveEditorialMetadata:
    return ArchiveEditorialMetadata(
        category="Tech / Automation",
        sector="Technology",
        lead_paragraph="Generated metadata reframes this role around live hiring evidence, operating pressure, and visible adoption patterns from the Bright Data corpus instead of relying on a curated fallback paragraph.",
        pull_quote="Generated archive language follows the evidence instead of fixed copy.",
        preceding_titles=["Program Manager", "Automation Lead", "AI Engineer"],
        competencies=["Workflow design", "AI integration", "Governance review", "Stakeholder translation"],
        outlook="Expect adoption to widen where teams need clear ownership of AI implementation, evaluation, and cross-functional delivery standards.",
    )


def test_generate_skips_cached_metadata() -> None:
    connection = MagicMock()
    provider = MagicMock()
    runner = CliRunner()

    with patch("backend.archive.cli.open_connection", return_value=connection), patch(
        "backend.archive.cli.GeminiNarrativeProvider", return_value=provider
    ), patch("backend.archive.cli.run_trend_scoring", return_value=[make_trend()]), patch(
        "backend.archive.cli.fetch_cached_metadata", return_value={10: make_metadata()}
    ), patch("backend.archive.cli.upsert_cached_metadata") as upsert:
        result = runner.invoke(app, ["generate", "--limit", "10"])

    assert result.exit_code == 0
    assert "cached archive metadata for 0 titles; skipped 1" in result.stdout
    provider.generate.assert_not_called()
    upsert.assert_not_called()


def test_generate_force_regenerates_cached_metadata() -> None:
    connection = MagicMock()
    provider = MagicMock()
    provider.model = "gemini-test"
    runner = CliRunner()

    with patch("backend.archive.cli.open_connection", return_value=connection), patch(
        "backend.archive.cli.GeminiNarrativeProvider", return_value=provider
    ), patch("backend.archive.cli.run_trend_scoring", return_value=[make_trend()]), patch(
        "backend.archive.cli.generate_archive_metadata", return_value=make_metadata()
    ), patch("backend.archive.cli.fetch_cached_metadata") as fetch_cached, patch(
        "backend.archive.cli.upsert_cached_metadata"
    ) as upsert:
        result = runner.invoke(app, ["generate", "--limit", "10", "--force"])

    assert result.exit_code == 0
    assert "cached archive metadata for 1 titles; skipped 0" in result.stdout
    fetch_cached.assert_not_called()
    upsert.assert_called_once()


def test_generate_images_skips_cached_image_without_provider(tmp_path) -> None:
    connection = MagicMock()
    runner = CliRunner()
    metadata = make_metadata().model_copy(
        update={"image_path": "/archive-generated/10-ai-workflow-architect.png"}
    )

    with patch("backend.archive.cli.open_connection", return_value=connection), patch(
        "backend.archive.cli.GeminiImageProvider"
    ) as provider_class, patch(
        "backend.archive.cli.run_trend_scoring", return_value=[make_trend()]
    ), patch(
        "backend.archive.cli.fetch_cached_metadata", return_value={10: metadata}
    ), patch("backend.archive.cli.update_cached_image") as update_cached:
        result = runner.invoke(
            app, ["generate-images", "--limit", "10", "--output-dir", str(tmp_path)]
        )

    assert result.exit_code == 0
    assert "generated 0 images; skipped 1" in result.stdout
    provider_class.assert_not_called()
    update_cached.assert_not_called()


def test_generate_images_skips_missing_metadata_without_provider(tmp_path) -> None:
    connection = MagicMock()
    runner = CliRunner()

    with patch("backend.archive.cli.open_connection", return_value=connection), patch(
        "backend.archive.cli.GeminiImageProvider"
    ) as provider_class, patch(
        "backend.archive.cli.run_trend_scoring", return_value=[make_trend()]
    ), patch(
        "backend.archive.cli.fetch_cached_metadata", return_value={}
    ), patch("backend.archive.cli.update_cached_image") as update_cached:
        result = runner.invoke(
            app, ["generate-images", "--limit", "10", "--output-dir", str(tmp_path)]
        )

    assert result.exit_code == 0
    assert "generated 0 images; skipped 1" in result.stdout
    provider_class.assert_not_called()
    update_cached.assert_not_called()


def test_generate_images_force_writes_image_and_updates_cache(tmp_path) -> None:
    connection = MagicMock()
    provider = MagicMock()
    provider.model = "gemini-image"
    provider.generate.return_value = b"image-bytes"
    runner = CliRunner()
    metadata = make_metadata().model_copy(update={"image_path": "/archive-generated/old.png"})

    with patch("backend.archive.cli.open_connection", return_value=connection), patch(
        "backend.archive.cli.GeminiImageProvider", return_value=provider
    ), patch("backend.archive.cli.run_trend_scoring", return_value=[make_trend()]), patch(
        "backend.archive.cli.fetch_cached_metadata", return_value={10: metadata}
    ), patch("backend.archive.cli.update_cached_image") as update_cached:
        result = runner.invoke(
            app,
            [
                "generate-images",
                "--limit",
                "10",
                "--output-dir",
                str(tmp_path),
                "--force",
            ],
        )

    assert result.exit_code == 0
    assert "generated 1 images; skipped 0" in result.stdout
    assert (tmp_path / "10-ai-workflow-architect.png").read_bytes() == b"image-bytes"
    update_cached.assert_called_once()
