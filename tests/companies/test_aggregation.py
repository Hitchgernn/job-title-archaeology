from datetime import datetime, timezone

from backend.companies.aggregation import aggregate_from_postings
from backend.companies.models import CompanyPostingRow


def make_row(
    company: str,
    title: str,
    title_id: int,
    posted_at: str,
    posting_id: int = 1,
) -> CompanyPostingRow:
    return CompanyPostingRow(
        posting_id=posting_id,
        company=company,
        normalized_title_id=title_id,
        display_title=title,
        posted_at=posted_at,
        scraped_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
    )


def test_aggregate_groups_by_company_and_resolves_ticker() -> None:
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    rows = [
        make_row("NVIDIA", "AI Architect", 1, "2026-05-20T00:00:00Z", posting_id=1),
        make_row("NVIDIA Corporation", "AI Architect", 1, "2026-05-22T00:00:00Z", posting_id=2),
        make_row("Palantir Technologies", "ML Engineer", 2, "2026-05-25T00:00:00Z", posting_id=3),
    ]

    signals = aggregate_from_postings(rows, now=now)
    by_ticker = {signal.ticker: signal for signal in signals if signal.ticker}

    assert "NVDA" in by_ticker
    assert by_ticker["NVDA"].display_name == "NVIDIA"
    assert by_ticker["NVDA"].recent_hires_30d == 2
    assert "PLTR" in by_ticker


def test_aggregate_computes_velocity_score_relative_to_prior_window() -> None:
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    rows = [
        make_row("NVIDIA", "AI Architect", 1, "2026-05-20T00:00:00Z", posting_id=1),
        make_row("NVIDIA", "AI Architect", 1, "2026-05-22T00:00:00Z", posting_id=2),
        make_row("NVIDIA", "AI Architect", 1, "2026-05-26T00:00:00Z", posting_id=3),
        make_row("NVIDIA", "AI Architect", 1, "2026-04-01T00:00:00Z", posting_id=4),
    ]

    signals = aggregate_from_postings(rows, now=now)
    nvda = next(signal for signal in signals if signal.ticker == "NVDA")

    assert nvda.recent_hires_30d == 3
    assert nvda.prior_hires_30d == 1
    assert nvda.velocity_score == 3.0


def test_aggregate_top_titles_breakdown_per_company() -> None:
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    rows = [
        make_row("NVIDIA", "AI Architect", 1, "2026-05-20T00:00:00Z", posting_id=1),
        make_row("NVIDIA", "AI Architect", 1, "2026-05-22T00:00:00Z", posting_id=2),
        make_row("NVIDIA", "ML Engineer", 2, "2026-05-25T00:00:00Z", posting_id=3),
    ]

    signals = aggregate_from_postings(rows, now=now)
    nvda = next(signal for signal in signals if signal.ticker == "NVDA")

    titles_by_id = {item.normalized_title_id: item for item in nvda.top_titles}
    assert titles_by_id[1].count == 2
    assert titles_by_id[1].display_title == "AI Architect"
    assert titles_by_id[2].count == 1


def test_aggregate_skips_rows_without_company() -> None:
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    rows = [
        make_row("", "AI Architect", 1, "2026-05-20T00:00:00Z", posting_id=1),
        make_row(None, "AI Architect", 1, "2026-05-21T00:00:00Z", posting_id=2),
        make_row("NVIDIA", "AI Architect", 1, "2026-05-22T00:00:00Z", posting_id=3),
    ]

    signals = aggregate_from_postings(rows, now=now)

    assert len(signals) == 1
    assert signals[0].ticker == "NVDA"


def test_aggregate_includes_unmapped_companies_without_ticker() -> None:
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    rows = [
        make_row("Acme Robotics", "Field Engineer", 9, "2026-05-25T00:00:00Z", posting_id=1),
    ]

    signals = aggregate_from_postings(rows, now=now)

    assert len(signals) == 1
    assert signals[0].ticker is None
    assert signals[0].company_key == "acme robotics"
    assert signals[0].display_name == "Acme Robotics"
