from __future__ import annotations

import time
from typing import Any

import httpx
from pydantic import HttpUrl


class BrightDataError(RuntimeError):
    """Base error for Bright Data collection failures."""


class BrightDataRunFailed(BrightDataError):
    """Raised when a Bright Data collection run reaches a failed state."""


class BrightDataTimeout(BrightDataError):
    """Raised when a Bright Data collection run does not complete in time."""


class BrightDataClient:
    def __init__(self, api_token: str, base_url: str | HttpUrl) -> None:
        self.api_token = api_token
        self.base_url = str(base_url).rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def start_collection(self, dataset_id: str, payload: dict[str, Any], query: dict[str, Any] | None = None) -> str:
        action = "start collection"
        params: dict[str, Any] = {"dataset_id": dataset_id}
        if query:
            params.update(query)
        response = self._request(
            action,
            "post",
            f"{self.base_url}/datasets/v3/trigger",
            params=params,
            headers=self._headers,
            json=payload,
            timeout=60,
        )
        self._raise_for_status(response, action)
        data = self._json(response, action)
        snapshot_id = data.get("snapshot_id") or data.get("id")
        if not snapshot_id:
            raise BrightDataError("start collection response missing snapshot_id or id")
        return str(snapshot_id)

    def poll_collection(
        self,
        run_id: str,
        poll_delay_seconds: float,
        max_attempts: int,
    ) -> dict[str, Any]:
        ready_statuses = {"ready", "done", "completed", "success"}
        failed_statuses = {"failed", "error", "canceled", "cancelled"}

        for attempt in range(max_attempts):
            action = "poll collection"
            response = self._request(
                action,
                "get",
                f"{self.base_url}/datasets/v3/progress/{run_id}",
                headers=self._headers,
                timeout=60,
            )
            self._raise_for_status(response, action)
            data = self._json(response, action)
            status = str(data.get("status", "")).lower()
            if status in ready_statuses:
                return data
            if status in failed_statuses:
                raise BrightDataRunFailed(f"Bright Data run {run_id} failed with status {status}")
            if attempt < max_attempts - 1:
                time.sleep(poll_delay_seconds)

        raise BrightDataTimeout(
            f"Bright Data run {run_id} did not complete after {max_attempts} attempts"
        )

    def fetch_results(self, run_id: str) -> list[dict[str, Any]]:
        action = "fetch results"
        response = self._request(
            action,
            "get",
            f"{self.base_url}/datasets/v3/snapshot/{run_id}",
            params={"format": "json"},
            headers=self._headers,
            timeout=60,
        )
        self._raise_for_status(response, action)
        data = self._json(response, action)
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            if not data:
                raise BrightDataError(f"Bright Data {action} returned 0 records from {response.url}")
            return data
        if isinstance(data, dict):
            items = data.get("data")
            if isinstance(items, list) and all(isinstance(item, dict) for item in items):
                if not items:
                    raise BrightDataError(f"Bright Data {action} returned 0 records from {response.url}")
                return items
        raise BrightDataError("fetch results response must be a list of objects or contain data list")

    def _request(self, action: str, method: str, url: str, **kwargs: Any) -> httpx.Response:
        try:
            return httpx.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise BrightDataError(f"Bright Data {action} request failed for {url}: {exc}") from exc

    def _json(self, response: httpx.Response, action: str) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise BrightDataError(
                f"Bright Data {action} response from {response.url} was not valid JSON: {exc}"
            ) from exc

    def _raise_for_status(self, response: httpx.Response, action: str) -> None:
        if response.is_success:
            return
        response_text = response.text[:500]
        raise BrightDataError(
            f"Bright Data {action} failed for {response.url} with status {response.status_code}: {response_text}"
        )
