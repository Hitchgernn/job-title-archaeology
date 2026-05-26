import json
from datetime import datetime
from typing import Any

from backend.normalize.models import NormalizedTitleResult


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


def placeholder(connection) -> str:
    return "?" if is_sqlite_connection(connection) else "%s"


def now_sql(connection) -> str:
    return "CURRENT_TIMESTAMP" if is_sqlite_connection(connection) else "NOW()"


def fetch_unlinked_raw_postings(connection, limit: int) -> list[dict[str, Any]]:
    limit_placeholder = placeholder(connection)
    sql = f"""
    SELECT raw_job_postings.id, raw_job_postings.title, raw_job_postings.scraped_at
    FROM raw_job_postings
    LEFT JOIN job_posting_titles ON job_posting_titles.raw_job_posting_id = raw_job_postings.id
    WHERE job_posting_titles.id IS NULL
      AND raw_job_postings.title IS NOT NULL
      AND raw_job_postings.title <> ''
    ORDER BY raw_job_postings.id
    LIMIT {limit_placeholder}
    """
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    with connection.cursor(row_factory=dict) as cursor:
        cursor.execute(sql, (limit,))
        return cursor.fetchall()


def upsert_normalized_title(
    connection,
    normalized: NormalizedTitleResult,
    first_seen_at: datetime,
    last_seen_at: datetime,
) -> int:
    value_placeholder = placeholder(connection)
    current_timestamp = now_sql(connection)
    sql = f"""
    INSERT INTO normalized_titles (
        canonical_title,
        display_title,
        token_key,
        level_terms,
        work_mode,
        first_seen_at,
        last_seen_at,
        occurrence_count,
        updated_at
    ) VALUES ({value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, 1, {current_timestamp})
    ON CONFLICT (token_key) DO UPDATE SET
        display_title = EXCLUDED.display_title,
        level_terms = EXCLUDED.level_terms,
        work_mode = EXCLUDED.work_mode,
        first_seen_at = MIN(normalized_titles.first_seen_at, EXCLUDED.first_seen_at),
        last_seen_at = MAX(normalized_titles.last_seen_at, EXCLUDED.last_seen_at),
        occurrence_count = normalized_titles.occurrence_count + 1,
        updated_at = {current_timestamp}
    RETURNING id
    """
    level_terms = json.dumps(normalized.level_terms) if is_sqlite_connection(connection) else normalized.level_terms
    first_seen_value = first_seen_at.isoformat() if is_sqlite_connection(connection) and isinstance(first_seen_at, datetime) else first_seen_at
    last_seen_value = last_seen_at.isoformat() if is_sqlite_connection(connection) and isinstance(last_seen_at, datetime) else last_seen_at
    params = (
        normalized.canonical_title,
        normalized.display_title,
        normalized.token_key,
        level_terms,
        normalized.work_mode,
        first_seen_value,
        last_seen_value,
    )
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            return int(cursor.fetchone()[0])
        finally:
            cursor.close()

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return int(cursor.fetchone()[0])


def link_posting_to_title(
    connection,
    raw_job_posting_id: int,
    normalized_title_id: int,
    raw_title: str,
    normalized: NormalizedTitleResult,
) -> None:
    value_placeholder = placeholder(connection)
    sql = f"""
    INSERT INTO job_posting_titles (
        raw_job_posting_id,
        normalized_title_id,
        raw_title,
        confidence,
        method
    ) VALUES ({value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder})
    ON CONFLICT (raw_job_posting_id) DO UPDATE SET
        normalized_title_id = EXCLUDED.normalized_title_id,
        raw_title = EXCLUDED.raw_title,
        confidence = EXCLUDED.confidence,
        method = EXCLUDED.method
    """
    params = (
        raw_job_posting_id,
        normalized_title_id,
        raw_title,
        normalized.confidence,
        normalized.method,
    )
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()
        return

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
