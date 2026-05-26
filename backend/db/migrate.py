POSTGRES_RAW_JOB_POSTINGS_SQL = """
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

POSTGRES_NORMALIZED_TITLES_SQL = """
CREATE TABLE IF NOT EXISTS normalized_titles (
    id BIGSERIAL PRIMARY KEY,
    canonical_title TEXT NOT NULL,
    display_title TEXT NOT NULL,
    token_key TEXT NOT NULL UNIQUE,
    level_terms TEXT[] NOT NULL DEFAULT '{}',
    work_mode TEXT,
    first_seen_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ,
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

POSTGRES_JOB_POSTING_TITLES_SQL = """
CREATE TABLE IF NOT EXISTS job_posting_titles (
    id BIGSERIAL PRIMARY KEY,
    raw_job_posting_id BIGINT NOT NULL REFERENCES raw_job_postings(id) ON DELETE CASCADE,
    normalized_title_id BIGINT NOT NULL REFERENCES normalized_titles(id) ON DELETE CASCADE,
    raw_title TEXT NOT NULL,
    confidence NUMERIC NOT NULL,
    method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(raw_job_posting_id)
)
"""

SQLITE_RAW_JOB_POSTINGS_SQL = """
CREATE TABLE IF NOT EXISTS raw_job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_run_id TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    title TEXT,
    company TEXT,
    location TEXT,
    url TEXT,
    posted_at TEXT,
    raw TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

SQLITE_NORMALIZED_TITLES_SQL = """
CREATE TABLE IF NOT EXISTS normalized_titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_title TEXT NOT NULL,
    display_title TEXT NOT NULL,
    token_key TEXT NOT NULL UNIQUE,
    level_terms TEXT NOT NULL DEFAULT '[]',
    work_mode TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

SQLITE_JOB_POSTING_TITLES_SQL = """
CREATE TABLE IF NOT EXISTS job_posting_titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_job_posting_id INTEGER NOT NULL REFERENCES raw_job_postings(id) ON DELETE CASCADE,
    normalized_title_id INTEGER NOT NULL REFERENCES normalized_titles(id) ON DELETE CASCADE,
    raw_title TEXT NOT NULL,
    confidence REAL NOT NULL,
    method TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(raw_job_posting_id)
)
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_raw_job_postings_source_run_id ON raw_job_postings(source_run_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_job_postings_scraped_at ON raw_job_postings(scraped_at)",
    "CREATE INDEX IF NOT EXISTS idx_raw_job_postings_title ON raw_job_postings(title)",
]


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


def run_migrations(connection) -> None:
    statements = (
        [SQLITE_RAW_JOB_POSTINGS_SQL, SQLITE_NORMALIZED_TITLES_SQL, SQLITE_JOB_POSTING_TITLES_SQL]
        if is_sqlite_connection(connection)
        else [POSTGRES_RAW_JOB_POSTINGS_SQL, POSTGRES_NORMALIZED_TITLES_SQL, POSTGRES_JOB_POSTING_TITLES_SQL]
    )
    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
        for statement in INDEX_SQL:
            cursor.execute(statement)
    finally:
        cursor.close()
    connection.commit()
