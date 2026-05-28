from unittest.mock import Mock, patch

import pytest

from backend.archive.images import (
    GeminiImageProvider,
    ImageProviderError,
    build_archive_image_prompt,
    image_filename,
    save_image_bytes,
)
from backend.archive.models import ArchiveEditorialMetadata
from backend.trends.models import TrendResult, TrendScores


def make_trend() -> TrendResult:
    return TrendResult(
        normalized_title_id=10,
        display_title="AI Workflow Architect",
        token_key="ai workflow architect",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.8, concentration=0.5),
        trend_score=0.91,
        early_mover_companies=["Acme"],
    )


def make_metadata() -> ArchiveEditorialMetadata:
    return ArchiveEditorialMetadata(
        category="Tech / Automation",
        sector="Software",
        lead_paragraph="Automation work is formalizing into a new role.",
        pull_quote="The work moved from scripts to systems.",
        preceding_titles=["Automation Engineer", "Workflow Analyst", "AI Specialist"],
        competencies=["Process mapping", "LLM orchestration", "Risk review", "Change management"],
        outlook="Teams will hire for judgment around automated work.",
    )


def test_build_archive_image_prompt_is_monochrome_and_textless():
    prompt = build_archive_image_prompt(make_trend(), make_metadata())

    assert "AI Workflow Architect" in prompt
    assert "monochrome" in prompt
    assert "black-and-white" in prompt
    assert "Do not include readable text" in prompt
    assert "Tech / Automation" in prompt


def test_image_filename_is_stable_slug():
    assert image_filename(make_trend()) == "10-ai-workflow-architect.png"


def test_save_image_bytes_writes_public_path(tmp_path):
    public_path = save_image_bytes(tmp_path, "10-ai-workflow-architect.png", b"png-bytes")

    assert public_path == "/archive-generated/10-ai-workflow-architect.png"
    assert (tmp_path / "10-ai-workflow-architect.png").read_bytes() == b"png-bytes"


def test_save_image_bytes_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError):
        save_image_bytes(tmp_path, "../bad.png", b"png-bytes")


def test_gemini_image_provider_returns_first_inline_image(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client = Mock()
    mock_response = Mock()
    mock_response.candidates = [Mock()]
    mock_response.candidates[0].content.parts = [Mock()]
    mock_response.candidates[0].content.parts[0].inline_data.data = b"image-bytes"
    mock_client.models.generate_content.return_value = mock_response

    with patch("backend.archive.images.genai.Client", return_value=mock_client):
        provider = GeminiImageProvider(model="gemini-2.5-flash-image-preview")
        result = provider.generate("prompt")

    assert result == b"image-bytes"
    mock_client.models.generate_content.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-2.5-flash-image-preview"
    assert call_kwargs["contents"] == "prompt"
    assert call_kwargs["config"].response_modalities == ["TEXT", "IMAGE"]


@pytest.mark.parametrize("candidates", [None, []])
def test_gemini_image_provider_rejects_empty_response(monkeypatch, candidates):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client = Mock()
    mock_response = Mock()
    mock_response.candidates = candidates
    mock_client.models.generate_content.return_value = mock_response

    with patch("backend.archive.images.genai.Client", return_value=mock_client):
        provider = GeminiImageProvider(model="gemini-2.5-flash-image-preview")
        with pytest.raises(ImageProviderError, match="Gemini response did not include image bytes"):
            provider.generate("prompt")


def test_gemini_image_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ImageProviderError, match="GEMINI_API_KEY is required"):
        GeminiImageProvider()
