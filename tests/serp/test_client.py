import json
from datetime import datetime, timezone
from unittest.mock import patch

from backend.serp.client import BrightDataSerpClient, SerpHit


def make_mock_response(items: list[dict]) -> dict:
    return {"organic": items}


def test_search_returns_top_hits_with_normalized_fields() -> None:
    payload = {
        "organic": [
            {"title": "NVIDIA hires AI chief", "link": "https://example.com/news", "description": "Major AI hire."},
            {"title": "AI Architect role rising", "link": "https://news.example.com/ai", "description": "Trend report."},
        ]
    }

    with patch("backend.serp.client.httpx.post") as mock_post:
        mock_post.return_value.is_success = True
        mock_post.return_value.json.return_value = payload
        client = BrightDataSerpClient(api_token="test-token", zone="serp_api1")
        hits = client.search("AI Architect press release")

    assert len(hits) == 2
    assert isinstance(hits[0], SerpHit)
    assert hits[0].title == "NVIDIA hires AI chief"
    assert hits[0].url == "https://example.com/news"
    assert hits[0].snippet == "Major AI hire."
    assert hits[0].source == "example.com"


def test_search_caps_results_to_requested_limit() -> None:
    payload = {
        "organic": [
            {"title": f"Result {i}", "link": f"https://example{i}.com", "description": "snippet"}
            for i in range(10)
        ]
    }
    with patch("backend.serp.client.httpx.post") as mock_post:
        mock_post.return_value.is_success = True
        mock_post.return_value.json.return_value = payload
        client = BrightDataSerpClient(api_token="test-token", zone="serp_api1")
        hits = client.search("query", limit=3)

    assert len(hits) == 3


def test_search_returns_empty_list_when_no_organic_results() -> None:
    with patch("backend.serp.client.httpx.post") as mock_post:
        mock_post.return_value.is_success = True
        mock_post.return_value.json.return_value = {}
        client = BrightDataSerpClient(api_token="test-token", zone="serp_api1")
        hits = client.search("query")

    assert hits == []


def test_search_url_encodes_complex_query_for_bright_data() -> None:
    query = '"AI Architect" hiring announcement OR press release -site:indeed.com -site:linkedin.com'

    with patch("backend.serp.client.httpx.post") as mock_post:
        mock_post.return_value.is_success = True
        mock_post.return_value.json.return_value = {"organic": []}
        client = BrightDataSerpClient(api_token="test-token", zone="serp_api1")
        client.search(query)

    payload = mock_post.call_args.kwargs["json"]
    assert payload["url"] == (
        "https://www.google.com/search?"
        "q=%22AI+Architect%22+hiring+announcement+OR+press+release+"
        "-site%3Aindeed.com+-site%3Alinkedin.com&brd_json=1"
    )


def test_search_decodes_bright_data_body_json_string() -> None:
    payload = {
        "body": json.dumps(
            {
                "organic": [
                    {"title": "AI Architect hiring", "link": "https://example.com/ai", "description": "Hiring news."}
                ]
            }
        ),
        "status_code": 200,
    }

    with patch("backend.serp.client.httpx.post") as mock_post:
        mock_post.return_value.is_success = True
        mock_post.return_value.json.return_value = payload
        client = BrightDataSerpClient(api_token="test-token", zone="serp_api1")
        hits = client.search("AI Architect")

    assert len(hits) == 1
    assert hits[0].title == "AI Architect hiring"
    assert hits[0].url == "https://example.com/ai"
    assert hits[0].snippet == "Hiring news."


def test_search_raises_on_http_error() -> None:
    with patch("backend.serp.client.httpx.post") as mock_post:
        mock_post.return_value.is_success = False
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "boom"
        client = BrightDataSerpClient(api_token="test-token", zone="serp_api1")

        try:
            client.search("query")
            assert False, "expected error"
        except RuntimeError as exc:
            assert "500" in str(exc)
