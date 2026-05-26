import os
from typing import Protocol

from google import genai


class NarrativeConfigError(RuntimeError):
    pass


class NarrativeProviderError(RuntimeError):
    pass


class NarrativeProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...


class GeminiNarrativeProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        resolved_api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        if not resolved_api_key:
            raise NarrativeConfigError("GEMINI_API_KEY is required")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = genai.Client(api_key=resolved_api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(model=self.model, contents=prompt)
        except Exception as exc:
            raise NarrativeProviderError(f"Gemini request failed: {exc}") from exc
        return (response.text or "").strip()
