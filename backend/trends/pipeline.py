from collections import defaultdict
from datetime import datetime, timezone

from backend.trends.models import TrendPostingRow, TrendResult, WeeklyCount
from backend.trends.repository import fetch_trend_posting_rows, weekly_counts_from_postings
from backend.trends.scoring import score_title_group


def run_trend_scoring(connection, limit: int, now: datetime | None = None, source: str | None = None) -> list[TrendResult]:
    rows = fetch_trend_posting_rows(connection, source=source)
    if not rows:
        return []

    scoring_time = now or datetime.now(timezone.utc)
    groups: dict[int, list[TrendPostingRow]] = defaultdict(list)
    for row in rows:
        groups[row.normalized_title_id].append(row)

    results = [score_title_group(group_rows, now=scoring_time) for group_rows in groups.values()]
    results.sort(key=lambda result: (-result.trend_score, -result.recent_count, result.display_title))
    return results[:limit]


def fetch_weekly_counts_map(connection, normalized_title_ids: list[int], source: str | None = None, weeks: int = 12) -> dict[int, list[WeeklyCount]]:
    if not normalized_title_ids:
        return {}
    rows = fetch_trend_posting_rows(connection, source=source)
    return {
        title_id: weekly_counts_from_postings(rows, title_id, weeks=weeks)
        for title_id in normalized_title_ids
    }
