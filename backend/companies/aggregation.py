from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Iterable

from backend.companies.models import CompanyPostingRow, CompanySignal, CompanyTitleVelocity, WeeklyHire
from backend.companies.tickers import display_for_ticker, normalize_company, resolve_ticker


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


def _iso_week(value: datetime) -> str:
    iso_year, iso_week, _ = value.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def aggregate_from_postings(rows: Iterable[CompanyPostingRow], now: datetime | None = None) -> list[CompanySignal]:
    scoring_time = now or datetime.now(timezone.utc)
    recent_start = scoring_time - timedelta(days=30)
    prior_start = recent_start - timedelta(days=30)

    grouped: dict[str, list[CompanyPostingRow]] = defaultdict(list)
    display_for_key: dict[str, str] = {}
    for row in rows:
        canonical = normalize_company(row.company)
        if not canonical:
            continue
        ticker = resolve_ticker(row.company)
        key = ticker or canonical
        grouped[key].append(row)
        if ticker:
            display_for_key[key] = display_for_ticker(ticker)
        else:
            display_for_key.setdefault(key, (row.company or canonical).strip())

    signals: list[CompanySignal] = []
    for key, group_rows in grouped.items():
        ticker = key if key in {"NVDA", "AMD", "PLTR", "MSFT"} else None
        recent = 0
        prior = 0
        title_counts: dict[int, dict[str, object]] = {}

        for row in group_rows:
            parsed = _parse_posted_at(row.posted_at)
            if parsed is None:
                continue
            if parsed >= recent_start:
                recent += 1
            elif parsed >= prior_start:
                prior += 1

            bucket = title_counts.setdefault(
                row.normalized_title_id,
                {"display_title": row.display_title, "count": 0, "weeks": defaultdict(int)},
            )
            bucket["count"] = int(bucket["count"]) + 1
            if parsed >= recent_start:
                bucket["weeks"][_iso_week(parsed)] += 1

        velocity = recent / max(prior, 1)

        top_titles = sorted(title_counts.items(), key=lambda item: -int(item[1]["count"]))[:5]
        title_velocities = [
            CompanyTitleVelocity(
                normalized_title_id=title_id,
                display_title=str(detail["display_title"]),
                count=int(detail["count"]),
                weekly_buckets=[
                    {"week_start": week, "count": count}
                    for week, count in sorted(detail["weeks"].items())
                ],
            )
            for title_id, detail in top_titles
        ]

        signals.append(
            CompanySignal(
                company_key=key.lower(),
                ticker=ticker,
                display_name=display_for_key[key],
                recent_hires_30d=recent,
                prior_hires_30d=prior,
                velocity_score=round(velocity, 4),
                top_titles=title_velocities,
                computed_at=scoring_time,
            )
        )

    signals.sort(key=lambda signal: (-signal.recent_hires_30d, -signal.velocity_score, signal.display_name))
    return signals


def weekly_hires_for_company(rows: Iterable[CompanyPostingRow], company_key: str, weeks: int = 12) -> list[WeeklyHire]:
    target = company_key.lower()
    bucket_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        canonical = normalize_company(row.company)
        if not canonical:
            continue
        ticker = resolve_ticker(row.company)
        key = (ticker or canonical).lower()
        if key != target:
            continue
        parsed = _parse_posted_at(row.posted_at)
        if parsed is None:
            continue
        bucket_counts[_iso_week(parsed)] += 1
    sorted_buckets = sorted(bucket_counts.items())
    if weeks > 0:
        sorted_buckets = sorted_buckets[-weeks:]
    return [WeeklyHire(week_start=week, count=count) for week, count in sorted_buckets]
