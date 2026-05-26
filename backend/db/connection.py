import os
import sqlite3
from pathlib import Path

import psycopg


class DatabaseConfigError(RuntimeError):
    pass


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise DatabaseConfigError("DATABASE_URL is required")
    return database_url


def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite:///")


def sqlite_path_from_url(database_url: str) -> str:
    return database_url.removeprefix("sqlite:///")


def open_connection(database_url: str | None = None):
    resolved_url = database_url or get_database_url()
    if is_sqlite_url(resolved_url):
        path = Path(sqlite_path_from_url(resolved_url))
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        return connection
    return psycopg.connect(resolved_url)
