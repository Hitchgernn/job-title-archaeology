from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.companies.models import CompanySignal, CompanyTitleVelocity


client = TestClient(app)


def make_signal(ticker: str = "NVDA", display: str = "NVIDIA", recent: int = 12) -> CompanySignal:
    return CompanySignal(
        company_key=ticker.lower(),
        ticker=ticker,
        display_name=display,
        recent_hires_30d=recent,
        prior_hires_30d=4,
        velocity_score=3.0,
        top_titles=[
            CompanyTitleVelocity(
                normalized_title_id=1,
                display_title="AI Architect",
                count=8,
                weekly_buckets=[{"week_start": "2026-W21", "count": 4}],
            )
        ],
        computed_at=datetime(2026, 5, 28, tzinfo=UTC),
    )


def test_companies_endpoint_returns_signals_list() -> None:
    connection = MagicMock()
    with patch("backend.companies.router.open_connection", return_value=connection), patch(
        "backend.companies.router.fetch_company_signals", return_value=[make_signal()]
    ):
        response = client.get("/companies?limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["tracked_count"] == 1
    assert payload["companies"][0]["ticker"] == "NVDA"
    assert payload["companies"][0]["recent_hires_30d"] == 12


def test_companies_endpoint_summary_counts_total_recent_hires() -> None:
    connection = MagicMock()
    with patch("backend.companies.router.open_connection", return_value=connection), patch(
        "backend.companies.router.fetch_company_signals",
        return_value=[make_signal(recent=10), make_signal(ticker="AMD", display="AMD", recent=6)],
    ):
        response = client.get("/companies?limit=10")

    payload = response.json()
    assert payload["summary"]["total_recent_hires"] == 16
    assert payload["summary"]["tracked_count"] == 2


def test_companies_dossier_returns_company_with_weekly_history() -> None:
    connection = MagicMock()
    with patch("backend.companies.router.open_connection", return_value=connection), patch(
        "backend.companies.router.fetch_company_signal_by_key", return_value=make_signal()
    ), patch(
        "backend.companies.router.fetch_company_posting_rows", return_value=[]
    ):
        response = client.get("/companies/NVDA")

    assert response.status_code == 200
    payload = response.json()
    assert payload["company"]["ticker"] == "NVDA"
    assert "weekly" in payload
    assert "titles" in payload


def test_companies_dossier_returns_404_for_unknown_company() -> None:
    connection = MagicMock()
    with patch("backend.companies.router.open_connection", return_value=connection), patch(
        "backend.companies.router.fetch_company_signal_by_key", return_value=None
    ):
        response = client.get("/companies/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "company not found"
