from unittest.mock import Mock, patch

import pytest

from backend.db.connection import DEFAULT_SQLITE_URL, get_database_url, open_connection


def test_get_database_url_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")

    assert get_database_url() == "postgresql://example"


def test_get_database_url_defaults_to_local_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert get_database_url() == DEFAULT_SQLITE_URL


def test_open_connection_uses_psycopg_connect() -> None:
    connection = Mock()
    with patch("backend.db.connection.psycopg.connect", return_value=connection) as connect:
        result = open_connection("postgresql://example")

    connect.assert_called_once_with("postgresql://example")
    assert result is connection


def test_open_connection_uses_sqlite_for_sqlite_url(tmp_path) -> None:
    database_path = tmp_path / "job_title_archaeology.db"
    connection = open_connection(f"sqlite:///{database_path}")
    try:
        assert connection.execute("SELECT 1").fetchone()[0] == 1
    finally:
        connection.close()
