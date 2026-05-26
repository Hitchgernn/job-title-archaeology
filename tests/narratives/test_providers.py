from unittest.mock import MagicMock, patch

import pytest

from backend.narratives.providers import GeminiNarrativeProvider, NarrativeConfigError, NarrativeProviderError


def test_gemini_provider_requires_api_key() -> None:
    with pytest.raises(NarrativeConfigError, match="GEMINI_API_KEY is required"):
        GeminiNarrativeProvider(api_key="")


def test_gemini_provider_generates_text_with_configured_model() -> None:
    response = MagicMock()
    response.text = "summary:\nAI workflow roles are emerging."
    client = MagicMock()
    client.models.generate_content.return_value = response

    with patch("backend.narratives.providers.genai.Client", return_value=client) as client_class:
        provider = GeminiNarrativeProvider(api_key="test-key", model="gemini-test")
        text = provider.generate("prompt text")

    client_class.assert_called_once_with(api_key="test-key")
    client.models.generate_content.assert_called_once_with(model="gemini-test", contents="prompt text")
    assert text == "summary:\nAI workflow roles are emerging."


def test_gemini_provider_raises_provider_error_for_api_failure() -> None:
    client = MagicMock()
    client.models.generate_content.side_effect = RuntimeError("boom")

    with patch("backend.narratives.providers.genai.Client", return_value=client):
        provider = GeminiNarrativeProvider(api_key="test-key", model="gemini-test")
        with pytest.raises(NarrativeProviderError, match="Gemini request failed"):
            provider.generate("prompt text")
