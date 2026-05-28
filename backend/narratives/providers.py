import os
from typing import Protocol

import httpx
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


class OpenRouterNarrativeProvider:
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None) -> None:
        resolved_api_key = api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY")
        if not resolved_api_key:
            raise NarrativeConfigError("OPENROUTER_API_KEY is required")
        self.api_key = resolved_api_key
        self.model = model or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
        self.base_url = (base_url or os.getenv("OPENROUTER_BASE_URL") or self.BASE_URL).rstrip("/")

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        try:
            response = httpx.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise NarrativeProviderError(f"OpenRouter request failed: {exc}") from exc
        except ValueError as exc:
            raise NarrativeProviderError(f"OpenRouter response was not valid JSON: {exc}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise NarrativeProviderError(f"OpenRouter response missing choices: {data}")
        message = choices[0].get("message") or {}
        text = message.get("content")
        if not isinstance(text, str):
            raise NarrativeProviderError(f"OpenRouter response missing content: {data}")
        return text.strip()
