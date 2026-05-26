import httpx
import pytest
import respx
from httpx import Response

from backend.ingest.sources.brightdata import (
    BrightDataClient,
    BrightDataError,
    BrightDataRunFailed,
    BrightDataTimeout,
)


@respx.mock
def test_start_collection_posts_dataset_request() -> None:
    route = respx.post("https://api.brightdata.com/datasets/v3/trigger").mock(
        return_value=Response(200, json={"snapshot_id": "snap-123"})
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    snapshot_id = client.start_collection("gd_job_postings", {"keyword": "AI"})

    assert snapshot_id == "snap-123"
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer token"
    assert request.headers["Content-Type"] == "application/json"
    assert request.url.params["dataset_id"] == "gd_job_postings"


@respx.mock
def test_start_collection_bad_response_raises_status_context() -> None:
    respx.post("https://api.brightdata.com/datasets/v3/trigger").mock(
        return_value=Response(401, text="bad token")
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    with pytest.raises(BrightDataError, match="trigger.*401.*bad token"):
        client.start_collection("gd_job_postings", {"keyword": "AI"})


@respx.mock
def test_start_collection_wraps_http_error_with_action_context() -> None:
    respx.post("https://api.brightdata.com/datasets/v3/trigger").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    with pytest.raises(BrightDataError, match="start collection.*trigger.*connection refused"):
        client.start_collection("gd_job_postings", {"keyword": "AI"})


@respx.mock
def test_start_collection_wraps_invalid_json_with_action_context() -> None:
    respx.post("https://api.brightdata.com/datasets/v3/trigger").mock(
        return_value=Response(200, text="not json")
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    with pytest.raises(BrightDataError, match="start collection.*JSON"):
        client.start_collection("gd_job_postings", {"keyword": "AI"})


@respx.mock
def test_poll_collection_ready_returns_status_payload() -> None:
    respx.get("https://api.brightdata.com/datasets/v3/progress/snap-123").mock(
        return_value=Response(200, json={"status": "ready"})
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    result = client.poll_collection("snap-123", poll_delay_seconds=0, max_attempts=1)

    assert result == {"status": "ready"}


@respx.mock
def test_poll_collection_failed_status_raises_run_failed() -> None:
    respx.get("https://api.brightdata.com/datasets/v3/progress/snap-123").mock(
        return_value=Response(200, json={"status": "failed"})
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    with pytest.raises(BrightDataRunFailed):
        client.poll_collection("snap-123", poll_delay_seconds=0, max_attempts=1)


@respx.mock
def test_poll_collection_running_times_out_after_max_attempts() -> None:
    respx.get("https://api.brightdata.com/datasets/v3/progress/snap-123").mock(
        return_value=Response(200, json={"status": "running"})
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    with pytest.raises(BrightDataTimeout):
        client.poll_collection("snap-123", poll_delay_seconds=0, max_attempts=1)


@respx.mock
def test_fetch_results_returns_snapshot_list() -> None:
    payload = [{"job_title": "AI Lead"}]
    route = respx.get("https://api.brightdata.com/datasets/v3/snapshot/snap-123").mock(
        return_value=Response(200, json=payload)
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    results = client.fetch_results("snap-123")

    assert results == payload
    request = route.calls.last.request
    assert request.url.params["format"] == "json"


@respx.mock
def test_fetch_results_rejects_empty_snapshot_list() -> None:
    respx.get("https://api.brightdata.com/datasets/v3/snapshot/snap-123").mock(
        return_value=Response(200, json=[])
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    with pytest.raises(BrightDataError, match="0 records.*snapshot"):
        client.fetch_results("snap-123")


@respx.mock
def test_fetch_results_rejects_empty_data_list() -> None:
    respx.get("https://api.brightdata.com/datasets/v3/snapshot/snap-123").mock(
        return_value=Response(200, json={"data": []})
    )
    client = BrightDataClient("token", "https://api.brightdata.com")

    with pytest.raises(BrightDataError, match="0 records.*snapshot"):
        client.fetch_results("snap-123")
