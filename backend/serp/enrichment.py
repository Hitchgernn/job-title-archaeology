from datetime import datetime, timezone

from backend.serp.client import BrightDataSerpClient
from backend.serp.repository import upsert_serp_signal


def build_press_query(title: str) -> str:
    quoted = title.replace('"', "")
    return f'"{quoted}" hiring announcement OR press release -site:indeed.com -site:linkedin.com'


def enrich_title_with_press(
    connection,
    *,
    client: BrightDataSerpClient,
    normalized_title_id: int,
    title: str,
    limit: int = 5,
    now: datetime | None = None,
) -> int:
    query = build_press_query(title)
    hits = client.search(query, limit=limit)
    upsert_serp_signal(
        connection,
        normalized_title_id=normalized_title_id,
        query_kind="press",
        query=query,
        hits=hits,
        fetched_at=now or datetime.now(timezone.utc),
    )
    return len(hits)
