from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx


@dataclass(frozen=True)
class SerpHit:
    title: str
    url: str
    snippet: str
    source: str


class BrightDataSerpClient:
    BASE_URL = "https://api.brightdata.com"

    def __init__(self, api_token: str, zone: str = "serp_api1", base_url: str | None = None) -> None:
        self.api_token = api_token
        self.zone = zone
        self.base_url = (base_url or self.BASE_URL).rstrip("/")

    def _domain(self, url: str) -> str:
        try:
            host = urlparse(url).netloc
        except Exception:
            return ""
        return host.removeprefix("www.")

    def search(self, query: str, limit: int = 5) -> list[SerpHit]:
        google_query = urlencode({"q": query, "brd_json": "1"})
        payload: dict[str, Any] = {
            "zone": self.zone,
            "url": f"https://www.google.com/search?{google_query}",
            "format": "json",
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        response = httpx.post(f"{self.base_url}/request", headers=headers, json=payload, timeout=60)
        if not response.is_success:
            raise RuntimeError(
                f"Bright Data SERP request failed with status {response.status_code}: {response.text[:300]}"
            )
        data = response.json()
        if isinstance(data, dict) and "body" in data:
            body = data.get("body")
            if isinstance(body, str):
                body = json.loads(body)
            if isinstance(body, dict):
                data = body
        organic = []
        if isinstance(data, dict):
            organic = data.get("organic") or data.get("results") or []
        hits: list[SerpHit] = []
        for item in organic[:limit]:
            url = str(item.get("link") or item.get("url") or "").strip()
            if not url:
                continue
            hits.append(
                SerpHit(
                    title=str(item.get("title") or "").strip(),
                    url=url,
                    snippet=str(item.get("description") or item.get("snippet") or "").strip(),
                    source=self._domain(url),
                )
            )
        return hits
