import json
import re
from typing import Sequence

import psycopg
from psycopg.types.json import Jsonb

from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.ingest.models import RawJobPostingEnvelope

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_job_postings (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    source_run_id TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,
    title TEXT,
    title_key TEXT,
    company TEXT,
    company_key TEXT,
    location TEXT,
    url TEXT,
    posted_at TEXT,
    posting_id TEXT,
    raw JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

_INSERT_SQL = """
INSERT INTO raw_job_postings (
    source,
    source_run_id,
    scraped_at,
    title,
    title_key,
    company,
    company_key,
    location,
    url,
    posted_at,
    posting_id,
    raw
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING
"""

_SQLITE_INSERT_SQL = """
INSERT INTO raw_job_postings (
    source,
    source_run_id,
    scraped_at,
    title,
    title_key,
    company,
    company_key,
    location,
    url,
    posted_at,
    posting_id,
    raw
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT DO NOTHING
"""

_EXISTS_SQL = """
SELECT 1
FROM raw_job_postings
WHERE source = %s
  AND (title_key = %s OR lower(btrim(title)) = %s)
  AND (company_key = %s OR lower(btrim(company)) = %s)
LIMIT 1
"""

_SQLITE_EXISTS_SQL = """
SELECT 1
FROM raw_job_postings
WHERE source = ?
  AND (title_key = ? OR lower(trim(title)) = ?)
  AND (company_key = ? OR lower(trim(company)) = ?)
LIMIT 1
"""

_POSTING_ID_EXISTS_SQL = """
SELECT 1
FROM raw_job_postings
WHERE source = %s AND posting_id = %s
LIMIT 1
"""

_SQLITE_POSTING_ID_EXISTS_SQL = """
SELECT 1
FROM raw_job_postings
WHERE source = ? AND posting_id = ?
LIMIT 1
"""


def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite:///")


def dedupe_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", value.strip().casefold())
    return normalized or None


def row_exists(cursor, sql: str, source: str, title_key: str | None, company_key: str | None) -> bool:
    if not title_key or not company_key:
        return False
    cursor.execute(sql, (source, title_key, title_key, company_key, company_key))
    return cursor.fetchone() is not None


def posting_id_exists(cursor, sql: str, source: str, posting_id: str | None) -> bool:
    if not posting_id:
        return False
    cursor.execute(sql, (source, posting_id))
    return cursor.fetchone() is not None


def load_raw_postings(database_url: str, records: Sequence[RawJobPostingEnvelope]) -> int:
    if is_sqlite_url(database_url):
        connection = open_connection(database_url)
        try:
            run_migrations(connection)
            inserted = 0
            cursor = connection.cursor()
            try:
                for record in records:
                    preview = record.normalized_preview
                    title_key = dedupe_key(preview.title)
                    company_key = dedupe_key(preview.company)
                    posting_id = preview.posting_id
                    if posting_id and posting_id_exists(cursor, _SQLITE_POSTING_ID_EXISTS_SQL, record.source, posting_id):
                        continue
                    if not posting_id and row_exists(cursor, _SQLITE_EXISTS_SQL, record.source, title_key, company_key):
                        continue
                    cursor.execute(
                        _SQLITE_INSERT_SQL,
                        (
                            record.source,
                            record.source_run_id,
                            record.scraped_at.isoformat(),
                            preview.title,
                            title_key,
                            preview.company,
                            company_key,
                            preview.location,
                            preview.url,
                            preview.posted_at,
                            posting_id,
                            json.dumps(record.raw),
                        ),
                    )
                    inserted += cursor.rowcount
            finally:
                cursor.close()
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return inserted

    connection = psycopg.connect(database_url)
    try:
        run_migrations(connection)
        with connection.cursor() as cursor:
            inserted = 0
            for record in records:
                preview = record.normalized_preview
                title_key = dedupe_key(preview.title)
                company_key = dedupe_key(preview.company)
                posting_id = preview.posting_id
                if posting_id and posting_id_exists(cursor, _POSTING_ID_EXISTS_SQL, record.source, posting_id):
                    continue
                if not posting_id and row_exists(cursor, _EXISTS_SQL, record.source, title_key, company_key):
                    continue
                cursor.execute(
                    _INSERT_SQL,
                    (
                        record.source,
                        record.source_run_id,
                        record.scraped_at,
                        preview.title,
                        title_key,
                        preview.company,
                        company_key,
                        preview.location,
                        preview.url,
                        preview.posted_at,
                        posting_id,
                        Jsonb(record.raw),
                    ),
                )
                inserted += cursor.rowcount
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return inserted
