import json
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
    company TEXT,
    location TEXT,
    url TEXT,
    posted_at TEXT,
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
    company,
    location,
    url,
    posted_at,
    raw
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_SQLITE_INSERT_SQL = """
INSERT INTO raw_job_postings (
    source,
    source_run_id,
    scraped_at,
    title,
    company,
    location,
    url,
    posted_at,
    raw
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite:///")


def load_raw_postings(database_url: str, records: Sequence[RawJobPostingEnvelope]) -> int:
    if is_sqlite_url(database_url):
        connection = open_connection(database_url)
        try:
            run_migrations(connection)
            cursor = connection.cursor()
            try:
                for record in records:
                    preview = record.normalized_preview
                    cursor.execute(
                        _SQLITE_INSERT_SQL,
                        (
                            record.source,
                            record.source_run_id,
                            record.scraped_at.isoformat(),
                            preview.title,
                            preview.company,
                            preview.location,
                            preview.url,
                            preview.posted_at,
                            json.dumps(record.raw),
                        ),
                    )
            finally:
                cursor.close()
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return len(records)

    connection = psycopg.connect(database_url)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_CREATE_TABLE_SQL)
            for record in records:
                preview = record.normalized_preview
                cursor.execute(
                    _INSERT_SQL,
                    (
                        record.source,
                        record.source_run_id,
                        record.scraped_at,
                        preview.title,
                        preview.company,
                        preview.location,
                        preview.url,
                        preview.posted_at,
                        Jsonb(record.raw),
                    ),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return len(records)
