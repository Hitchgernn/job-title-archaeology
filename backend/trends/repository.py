import json
from datetime import datetime, timezone

from psycopg.rows import dict_row

from backend.trends.models import TrendPostingRow, WeeklyCount


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


def fetch_trend_posting_rows(connection, source: str | None = None) -> list[TrendPostingRow]:
    current_timestamp = "CURRENT_TIMESTAMP" if is_sqlite_connection(connection) else "NOW()"
    scraped_at_expression = "datetime(raw_job_postings.scraped_at)" if is_sqlite_connection(connection) else "raw_job_postings.scraped_at"
    value_placeholder = "?" if is_sqlite_connection(connection) else "%s"
    source_filter = f"AND raw_job_postings.source = {value_placeholder}" if source else ""
    sql = f"""
    SELECT
        raw_job_postings.id AS posting_id,
        normalized_titles.id AS normalized_title_id,
        normalized_titles.display_title,
        normalized_titles.token_key,
        raw_job_postings.company,
        raw_job_postings.scraped_at,
        raw_job_postings.posted_at,
        raw_job_postings.raw
    FROM raw_job_postings
    JOIN job_posting_titles
      ON job_posting_titles.raw_job_posting_id = raw_job_postings.id
    JOIN normalized_titles
      ON normalized_titles.id = job_posting_titles.normalized_title_id
    WHERE {scraped_at_expression} <= {current_timestamp}
      {source_filter}
    ORDER BY normalized_titles.id, raw_job_postings.scraped_at, raw_job_postings.id
    """
    params = (source,) if source else ()
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
        for row in rows:
            row["raw"] = json.loads(row["raw"])
        return [TrendPostingRow(**row) for row in rows]

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(sql, params)
        return [TrendPostingRow(**row) for row in cursor.fetchall()]


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


def _iso_week_start(value: datetime) -> str:
    iso_year, iso_week, _ = value.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def weekly_counts_from_postings(rows: list[TrendPostingRow], normalized_title_id: int, weeks: int = 12) -> list[WeeklyCount]:
    title_rows = [row for row in rows if row.normalized_title_id == normalized_title_id]
    parsed_dates = [d for d in (_parse_posted_at(row.posted_at) for row in title_rows) if d is not None]
    if not parsed_dates:
        return []
    bucket_counts: dict[str, int] = {}
    for date_value in parsed_dates:
        bucket_counts[_iso_week_start(date_value)] = bucket_counts.get(_iso_week_start(date_value), 0) + 1
    sorted_buckets = sorted(bucket_counts.items(), key=lambda item: item[0])
    if weeks > 0:
        sorted_buckets = sorted_buckets[-weeks:]
    return [WeeklyCount(week_start=label, count=count) for label, count in sorted_buckets]
