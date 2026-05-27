from collections import defaultdict
from datetime import datetime, timezone

from backend.trends.models import TrendPostingRow, TrendResult
from backend.trends.repository import fetch_trend_posting_rows
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
