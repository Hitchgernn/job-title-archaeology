import json
from datetime import datetime
from typing import Iterable

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from backend.serp.client import SerpHit


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


def _serialize_hits(hits: Iterable[SerpHit]) -> str:
    return json.dumps([{"title": h.title, "url": h.url, "snippet": h.snippet, "source": h.source} for h in hits])


def _deserialize_hits(payload: object) -> list[SerpHit]:
    if isinstance(payload, str):
        items = json.loads(payload)
    elif isinstance(payload, list):
        items = payload
    else:
        return []
    return [
        SerpHit(
            title=str(item.get("title", "")),
            url=str(item.get("url", "")),
            snippet=str(item.get("snippet", "")),
            source=str(item.get("source", "")),
        )
        for item in items
    ]


def upsert_serp_signal(
    connection,
    *,
    normalized_title_id: int,
    query_kind: str,
    query: str,
    hits: Iterable[SerpHit],
    fetched_at: datetime,
) -> None:
    serialized = _serialize_hits(hits)
    if is_sqlite_connection(connection):
        sql = """
        INSERT INTO serp_signals (normalized_title_id, query_kind, query, results, fetched_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (normalized_title_id, query_kind) DO UPDATE SET
            query = EXCLUDED.query,
            results = EXCLUDED.results,
            fetched_at = EXCLUDED.fetched_at
        """
        cursor = connection.cursor()
        try:
            cursor.execute(sql, (normalized_title_id, query_kind, query, serialized, fetched_at.isoformat()))
        finally:
            cursor.close()
        return

    pg_sql = """
    INSERT INTO serp_signals (normalized_title_id, query_kind, query, results, fetched_at)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (normalized_title_id, query_kind) DO UPDATE SET
        query = EXCLUDED.query,
        results = EXCLUDED.results,
        fetched_at = EXCLUDED.fetched_at
    """
    with connection.cursor() as cursor:
        cursor.execute(
            pg_sql,
            (normalized_title_id, query_kind, query, Jsonb(json.loads(serialized)), fetched_at),
        )


def fetch_serp_signals_for_titles(connection, normalized_title_ids: list[int]) -> dict[int, list[SerpHit]]:
    if not normalized_title_ids:
        return {}
    placeholder = "?" if is_sqlite_connection(connection) else "%s"
    placeholders = ", ".join([placeholder] * len(normalized_title_ids))
    sql = f"""
    SELECT normalized_title_id, results
    FROM serp_signals
    WHERE normalized_title_id IN ({placeholders})
    ORDER BY normalized_title_id, query_kind
    """
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, tuple(normalized_title_ids))
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
    else:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(sql, tuple(normalized_title_ids))
            rows = list(cursor.fetchall())

    grouped: dict[int, list[SerpHit]] = {}
    for row in rows:
        title_id = int(row["normalized_title_id"])
        grouped.setdefault(title_id, []).extend(_deserialize_hits(row["results"]))
    return grouped
