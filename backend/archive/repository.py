import hashlib
import json

from psycopg.rows import dict_row

from backend.archive.models import ArchiveEditorialMetadata
from backend.trends.models import TrendResult


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


def placeholder(connection) -> str:
    return "?" if is_sqlite_connection(connection) else "%s"


def metadata_input_hash(trend: TrendResult) -> str:
    payload = trend.model_dump(mode="json")
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def fetch_cached_metadata(connection, normalized_title_ids: list[int], prompt_version: str) -> dict[int, ArchiveEditorialMetadata]:
    if not normalized_title_ids:
        return {}
    value_placeholder = placeholder(connection)
    placeholders = ", ".join([value_placeholder] * len(normalized_title_ids))
    sql = f"""
    SELECT normalized_title_id, metadata
    FROM archive_metadata_cache
    WHERE prompt_version = {value_placeholder}
      AND normalized_title_id IN ({placeholders})
    """
    params = (prompt_version, *normalized_title_ids)
    if is_sqlite_connection(connection):
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()
        return {int(row["normalized_title_id"]): ArchiveEditorialMetadata.model_validate(json.loads(row["metadata"])) for row in rows}

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(sql, params)
        return {int(row["normalized_title_id"]): ArchiveEditorialMetadata.model_validate(row["metadata"]) for row in cursor.fetchall()}


def upsert_cached_metadata(
    connection,
    normalized_title_id: int,
    prompt_version: str,
    provider: str,
    model: str,
    input_hash: str,
    metadata: ArchiveEditorialMetadata,
) -> None:
    value_placeholder = placeholder(connection)
    serialized_metadata = metadata.model_dump_json() if is_sqlite_connection(connection) else metadata.model_dump(mode="json")
    updated_at = "CURRENT_TIMESTAMP" if is_sqlite_connection(connection) else "NOW()"
    sql = f"""
    INSERT INTO archive_metadata_cache (normalized_title_id, prompt_version, provider, model, input_hash, metadata)
    VALUES ({value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder})
    ON CONFLICT (normalized_title_id, prompt_version) DO UPDATE SET
        provider = EXCLUDED.provider,
        model = EXCLUDED.model,
        input_hash = EXCLUDED.input_hash,
        metadata = EXCLUDED.metadata,
        updated_at = {updated_at}
    """
    cursor = connection.cursor()
    try:
        cursor.execute(sql, (normalized_title_id, prompt_version, provider, model, input_hash, serialized_metadata))
    finally:
        cursor.close()
