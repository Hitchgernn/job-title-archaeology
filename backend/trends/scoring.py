from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.trends.models import EarlyMoverSignal, TrendPostingRow, TrendResult, TrendScores

INDUSTRY_KEYS = ("industry", "industries", "company_industry", "companyIndustry", "sector", "category")


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def extract_industries(raw: dict[str, Any]) -> set[str]:
    industries: set[str] = set()
    for key in INDUSTRY_KEYS:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            industries.add(value.strip())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    industries.add(item.strip())
    return industries


def _parse_posted_at(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _date_label(value: datetime) -> str:
    return value.strftime("%B %Y")


def score_title_group(rows: Iterable[TrendPostingRow], now: datetime) -> TrendResult:
    ordered_rows = sorted(rows, key=lambda row: (row.scraped_at, row.posting_id))
    if not ordered_rows:
        raise ValueError("score_title_group requires at least one row")

    recent_start = now - timedelta(days=7)
    prior_start = recent_start - timedelta(days=21)
    eligible_rows = [row for row in ordered_rows if row.scraped_at <= now]
    recent_rows = [row for row in eligible_rows if row.scraped_at >= recent_start]
    prior_rows = [row for row in eligible_rows if prior_start <= row.scraped_at < recent_start]

    recent_count = len(recent_rows)
    prior_count = len(prior_rows)
    newness = 1.0 if recent_count > 0 and prior_count == 0 else 0.0
    prior_weekly_rate = prior_count / 3
    velocity = clamp(recent_count / max(prior_weekly_rate, 1)) if recent_count else 0.0

    industries: set[str] = set()
    for row in recent_rows:
        industries.update(extract_industries(row.raw))
    concentration = clamp(len(industries) / 5)

    scores = TrendScores(newness=newness, velocity=velocity, concentration=concentration)
    trend_score = round((scores.newness * 0.40) + (scores.velocity * 0.35) + (scores.concentration * 0.25), 4)

    early_mover_companies: list[str] = []
    early_movers: list[EarlyMoverSignal] = []
    seen_companies: set[str] = set()
    for row in eligible_rows:
        if row.company and row.company not in seen_companies:
            seen_companies.add(row.company)
            early_mover_companies.append(row.company)
            posted_at = _parse_posted_at(row.posted_at)
            signal_date = posted_at or row.scraped_at
            early_movers.append(
                EarlyMoverSignal(
                    company=row.company,
                    date_label=_date_label(signal_date),
                    location_label=row.location or "Remote",
                    posted_at=posted_at,
                    scraped_at=row.scraped_at,
                )
            )
        if len(early_mover_companies) == 3:
            break

    first_row = ordered_rows[0]
    return TrendResult(
        normalized_title_id=first_row.normalized_title_id,
        display_title=first_row.display_title,
        token_key=first_row.token_key,
        recent_count=recent_count,
        prior_count=prior_count,
        total_count=len(ordered_rows),
        scores=scores,
        trend_score=trend_score,
        early_mover_companies=early_mover_companies,
        early_movers=early_movers,
    )
