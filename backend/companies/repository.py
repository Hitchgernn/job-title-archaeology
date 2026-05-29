import json

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from backend.companies.models import CompanyPostingRow, CompanySignal, CompanyTitleVelocity


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


_FETCH_POSTING_ROWS_SQL = """
SELECT
    raw_job_postings.id AS posting_id,
    raw_job_postings.company AS company,
    normalized_titles.id AS normalized_title_id,
    normalized_titles.display_title AS display_title,
    raw_job_postings.posted_at AS posted_at,
    raw_job_postings.scraped_at AS scraped_at,
    raw_job_postings.raw AS raw
FROM raw_job_postings
JOIN job_posting_titles
  ON job_posting_titles.raw_job_posting_id = raw_job_postings.id
JOIN normalized_titles
  ON normalized_titles.id = job_posting_titles.normalized_title_id
"""


def fetch_company_posting_rows(connection) -> list[CompanyPostingRow]:
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(_FETCH_POSTING_ROWS_SQL)
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
        for row in rows:
            row["raw"] = json.loads(row["raw"]) if row["raw"] else {}
        return [CompanyPostingRow(**row) for row in rows]

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(_FETCH_POSTING_ROWS_SQL)
        return [CompanyPostingRow(**row) for row in cursor.fetchall()]


def _serialize_top_titles(top_titles: list[CompanyTitleVelocity]) -> str:
    return json.dumps([title.model_dump() for title in top_titles])


def upsert_company_signal(connection, signal: CompanySignal) -> None:
    if is_sqlite_connection(connection):
        sql = """
        INSERT INTO company_signals (
            company_key, ticker, display_name, recent_hires_30d, prior_hires_30d, velocity_score, top_titles, computed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (company_key) DO UPDATE SET
            ticker = EXCLUDED.ticker,
            display_name = EXCLUDED.display_name,
            recent_hires_30d = EXCLUDED.recent_hires_30d,
            prior_hires_30d = EXCLUDED.prior_hires_30d,
            velocity_score = EXCLUDED.velocity_score,
            top_titles = EXCLUDED.top_titles,
            computed_at = EXCLUDED.computed_at
        """
        cursor = connection.cursor()
        try:
            cursor.execute(
                sql,
                (
                    signal.company_key,
                    signal.ticker,
                    signal.display_name,
                    signal.recent_hires_30d,
                    signal.prior_hires_30d,
                    signal.velocity_score,
                    _serialize_top_titles(signal.top_titles),
                    signal.computed_at.isoformat(),
                ),
            )
        finally:
            cursor.close()
        return

    sql = """
    INSERT INTO company_signals (
        company_key, ticker, display_name, recent_hires_30d, prior_hires_30d, velocity_score, top_titles, computed_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (company_key) DO UPDATE SET
        ticker = EXCLUDED.ticker,
        display_name = EXCLUDED.display_name,
        recent_hires_30d = EXCLUDED.recent_hires_30d,
        prior_hires_30d = EXCLUDED.prior_hires_30d,
        velocity_score = EXCLUDED.velocity_score,
        top_titles = EXCLUDED.top_titles,
        computed_at = EXCLUDED.computed_at
    """
    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            (
                signal.company_key,
                signal.ticker,
                signal.display_name,
                signal.recent_hires_30d,
                signal.prior_hires_30d,
                signal.velocity_score,
                Jsonb([title.model_dump() for title in signal.top_titles]),
                signal.computed_at,
            ),
        )


def fetch_company_signals(connection, limit: int = 50) -> list[CompanySignal]:
    sql = """
    SELECT company_key, ticker, display_name, recent_hires_30d, prior_hires_30d, velocity_score, top_titles, computed_at
    FROM company_signals
    ORDER BY recent_hires_30d DESC, velocity_score DESC, display_name ASC
    LIMIT ?
    """
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, (limit,))
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
        result: list[CompanySignal] = []
        for row in rows:
            row["top_titles"] = [
                CompanyTitleVelocity.model_validate(item)
                for item in json.loads(row["top_titles"])
            ]
            result.append(CompanySignal(**row))
        return result

    pg_sql = sql.replace("?", "%s")
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(pg_sql, (limit,))
        rows = list(cursor.fetchall())
    result = []
    for row in rows:
        row["top_titles"] = [CompanyTitleVelocity.model_validate(item) for item in row["top_titles"]]
        result.append(CompanySignal(**row))
    return result


def fetch_company_signal_by_key(connection, key: str) -> CompanySignal | None:
    canonical = key.lower()
    sql = """
    SELECT company_key, ticker, display_name, recent_hires_30d, prior_hires_30d, velocity_score, top_titles, computed_at
    FROM company_signals
    WHERE company_key = ? OR LOWER(ticker) = ?
    LIMIT 1
    """
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, (canonical, canonical))
            row = cursor.fetchone()
        finally:
            cursor.close()
        if row is None:
            return None
        data = dict(row)
        data["top_titles"] = [CompanyTitleVelocity.model_validate(item) for item in json.loads(data["top_titles"])]
        return CompanySignal(**data)

    pg_sql = sql.replace("?", "%s")
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(pg_sql, (canonical, canonical))
        row = cursor.fetchone()
    if row is None:
        return None
    row["top_titles"] = [CompanyTitleVelocity.model_validate(item) for item in row["top_titles"]]
    return CompanySignal(**row)
