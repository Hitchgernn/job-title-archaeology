POSTGRES_RAW_JOB_POSTINGS_SQL = """
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

POSTGRES_ARCHIVE_METADATA_CACHE_SQL = """
CREATE TABLE IF NOT EXISTS archive_metadata_cache (
    id BIGSERIAL PRIMARY KEY,
    normalized_title_id BIGINT NOT NULL REFERENCES normalized_titles(id) ON DELETE CASCADE,
    prompt_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(normalized_title_id, prompt_version)
)
"""

SQLITE_RAW_JOB_POSTINGS_SQL = """
CREATE TABLE IF NOT EXISTS raw_job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_run_id TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    title TEXT,
    title_key TEXT,
    company TEXT,
    company_key TEXT,
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

SQLITE_ARCHIVE_METADATA_CACHE_SQL = """
CREATE TABLE IF NOT EXISTS archive_metadata_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_title_id INTEGER NOT NULL REFERENCES normalized_titles(id) ON DELETE CASCADE,
    prompt_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(normalized_title_id, prompt_version)
)
"""

POSTGRES_ALTER_SQL = [
    "ALTER TABLE raw_job_postings ADD COLUMN IF NOT EXISTS title_key TEXT",
    "ALTER TABLE raw_job_postings ADD COLUMN IF NOT EXISTS company_key TEXT",
    "ALTER TABLE raw_job_postings ADD COLUMN IF NOT EXISTS posting_id TEXT",
]

SQLITE_ALTER_SQL = [
    "ALTER TABLE raw_job_postings ADD COLUMN title_key TEXT",
    "ALTER TABLE raw_job_postings ADD COLUMN company_key TEXT",
    "ALTER TABLE raw_job_postings ADD COLUMN posting_id TEXT",
]

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_raw_job_postings_source_run_id ON raw_job_postings(source_run_id)",
    "CREATE INDEX IF NOT EXISTS idx_raw_job_postings_scraped_at ON raw_job_postings(scraped_at)",
    "CREATE INDEX IF NOT EXISTS idx_raw_job_postings_title ON raw_job_postings(title)",
    "CREATE INDEX IF NOT EXISTS idx_raw_job_postings_posted_at ON raw_job_postings(posted_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_job_postings_source_posting_id ON raw_job_postings(source, posting_id) WHERE posting_id IS NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_job_postings_source_title_company_key ON raw_job_postings(source, title_key, company_key) WHERE title_key IS NOT NULL AND company_key IS NOT NULL AND posting_id IS NULL",
]


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


def run_migrations(connection) -> None:
    statements = (
        [SQLITE_RAW_JOB_POSTINGS_SQL, SQLITE_NORMALIZED_TITLES_SQL, SQLITE_JOB_POSTING_TITLES_SQL, SQLITE_ARCHIVE_METADATA_CACHE_SQL]
        if is_sqlite_connection(connection)
        else [POSTGRES_RAW_JOB_POSTINGS_SQL, POSTGRES_NORMALIZED_TITLES_SQL, POSTGRES_JOB_POSTING_TITLES_SQL, POSTGRES_ARCHIVE_METADATA_CACHE_SQL]
    )
    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
        alter_statements = SQLITE_ALTER_SQL if is_sqlite_connection(connection) else POSTGRES_ALTER_SQL
        for statement in alter_statements:
            try:
                cursor.execute(statement)
            except Exception as exc:
                if "duplicate column" not in str(exc).lower():
                    raise
        for statement in INDEX_SQL:
            cursor.execute(statement)
    finally:
        cursor.close()
    connection.commit()
