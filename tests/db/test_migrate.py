from unittest.mock import MagicMock

from backend.db.connection import open_connection
from backend.db.migrate import run_migrations


def test_run_migrations_creates_tables_and_indexes() -> None:
    connection = MagicMock()
    cursor = connection.cursor.return_value

    run_migrations(connection)

    sql_calls = [call.args[0] for call in cursor.execute.call_args_list]
    assert any("CREATE TABLE IF NOT EXISTS raw_job_postings" in sql for sql in sql_calls)
    assert any("CREATE TABLE IF NOT EXISTS normalized_titles" in sql for sql in sql_calls)
    assert any("CREATE TABLE IF NOT EXISTS job_posting_titles" in sql for sql in sql_calls)
    assert any("CREATE TABLE IF NOT EXISTS archive_metadata_cache" in sql for sql in sql_calls)
    assert any("CREATE INDEX IF NOT EXISTS idx_raw_job_postings_source_run_id" in sql for sql in sql_calls)
    assert any("CREATE INDEX IF NOT EXISTS idx_raw_job_postings_scraped_at" in sql for sql in sql_calls)
    assert any("CREATE INDEX IF NOT EXISTS idx_raw_job_postings_title" in sql for sql in sql_calls)
    connection.commit.assert_called_once()


def test_run_migrations_creates_sqlite_tables(tmp_path) -> None:
    connection = open_connection(f"sqlite:///{tmp_path / 'job_title_archaeology.db'}")
    try:
        run_migrations(connection)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        connection.close()

    assert "raw_job_postings" in tables
    assert "normalized_titles" in tables
    assert "job_posting_titles" in tables
    assert "archive_metadata_cache" in tables
