from datetime import datetime, timezone

from backend.trends.models import TrendPostingRow, TrendScores, TrendResult


def test_trend_models_store_score_inputs() -> None:
    scraped_at = datetime(2026, 5, 20, tzinfo=timezone.utc)
    row = TrendPostingRow(
        posting_id=1,
        normalized_title_id=10,
        display_title="Generative AI Product Operations",
        token_key="ai|generative|operations|product",
        company="Acme",
        scraped_at=scraped_at,
        raw={"industry": "Technology"},
    )
    scores = TrendScores(newness=1.0, velocity=0.5, concentration=0.25)
    result = TrendResult(
        normalized_title_id=10,
        display_title="Generative AI Product Operations",
        token_key="ai|generative|operations|product",
        recent_count=3,
        prior_count=1,
        scores=scores,
        trend_score=0.6375,
        early_mover_companies=["Acme"],
    )

    assert row.company == "Acme"
    assert row.raw["industry"] == "Technology"
    assert result.scores.velocity == 0.5
    assert result.early_mover_companies == ["Acme"]


from backend.trends.scoring import extract_industries, score_title_group


def test_extract_industries_reads_common_raw_fields() -> None:
    assert extract_industries({"industry": "Technology"}) == {"Technology"}
    assert extract_industries({"industries": ["Healthcare", "AI"]}) == {"Healthcare", "AI"}
    assert extract_industries({"companyIndustry": "Financial Services"}) == {"Financial Services"}
    assert extract_industries({"sector": "Manufacturing"}) == {"Manufacturing"}
    assert extract_industries({"category": "Operations"}) == {"Operations"}
    assert extract_industries({"other": "missing"}) == set()


def test_score_title_group_scores_recent_only_title_high() -> None:
    now = datetime(2026, 5, 23, tzinfo=timezone.utc)
    rows = [
        TrendPostingRow(
            posting_id=1,
            normalized_title_id=10,
            display_title="AI Workflow Architect",
            token_key="ai|architect|workflow",
            company="Acme",
            scraped_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
            raw={"industry": "Technology"},
        ),
        TrendPostingRow(
            posting_id=2,
            normalized_title_id=10,
            display_title="AI Workflow Architect",
            token_key="ai|architect|workflow",
            company="Globex",
            location="Remote",
            posted_at="2026-05-20T12:00:00+00:00",
            scraped_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
            raw={"industry": "Healthcare"},
        ),
    ]

    result = score_title_group(rows, now=now)

    assert result.recent_count == 2
    assert result.prior_count == 0
    assert result.scores.newness == 1.0
    assert result.scores.velocity == 1.0
    assert result.scores.concentration == 0.4
    assert result.trend_score == 0.85
    assert result.early_mover_companies == ["Globex", "Acme"]
    assert result.early_movers[0].company == "Globex"
    assert result.early_movers[0].date_label == "May 2026"
    assert result.early_movers[0].location_label == "Remote"


def test_score_title_group_uses_prior_baseline() -> None:
    now = datetime(2026, 5, 23, tzinfo=timezone.utc)
    rows = [
        TrendPostingRow(
            posting_id=1,
            normalized_title_id=11,
            display_title="Prompt Engineer",
            token_key="engineer|prompt",
            company="Acme",
            scraped_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
            raw={"industry": "Technology"},
        ),
        TrendPostingRow(
            posting_id=2,
            normalized_title_id=11,
            display_title="Prompt Engineer",
            token_key="engineer|prompt",
            company="Globex",
            scraped_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
            raw={"industry": "Technology"},
        ),
        TrendPostingRow(
            posting_id=3,
            normalized_title_id=11,
            display_title="Prompt Engineer",
            token_key="engineer|prompt",
            company="Initech",
            scraped_at=datetime(2026, 5, 5, tzinfo=timezone.utc),
            raw={"industry": "Technology"},
        ),
    ]

    result = score_title_group(rows, now=now)

    assert result.recent_count == 1
    assert result.prior_count == 2
    assert result.scores.newness == 0.0
    assert result.scores.velocity == 1.0
    assert result.scores.concentration == 0.2
    assert result.trend_score == 0.4


def test_score_title_group_ignores_future_rows_and_missing_company() -> None:
    now = datetime(2026, 5, 23, tzinfo=timezone.utc)
    rows = [
        TrendPostingRow(
            posting_id=1,
            normalized_title_id=12,
            display_title="Synthetic Data Engineer",
            token_key="data|engineer|synthetic",
            company=None,
            scraped_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
            raw={},
        ),
        TrendPostingRow(
            posting_id=2,
            normalized_title_id=12,
            display_title="Synthetic Data Engineer",
            token_key="data|engineer|synthetic",
            company="Future Corp",
            scraped_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
            raw={"industry": "Technology"},
        ),
    ]

    result = score_title_group(rows, now=now)

    assert result.recent_count == 1
    assert result.prior_count == 0
    assert result.scores.concentration == 0.0
    assert result.early_mover_companies == []
