from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from backend.db.connection import open_connection
from backend.ingest.config import CollectionConfig
from backend.ingest.models import map_raw_posting
from backend.ingest.sinks.jsonl import write_jsonl_archive
from backend.ingest.sinks.postgres import load_raw_postings
from backend.normalize.pipeline import run_normalization


class CollectionClient(Protocol):
    def start_collection(self, dataset_id: str, payload: dict[str, object]) -> str:
        ...

    def poll_collection(
        self,
        run_id: str,
        poll_delay_seconds: int,
        max_attempts: int,
    ) -> None:
        ...

    def fetch_results(self, run_id: str) -> list[dict[str, object]]:
        ...


@dataclass(frozen=True)
class CollectionResult:
    run_id: str
    archive_path: Path
    record_count: int
    postgres_inserted: int | None


def build_collection_payload(config: CollectionConfig) -> dict[str, object]:
    collection = config.collection
    return {
        "limit": collection.target_records,
        "keywords": collection.keywords,
        "locations": collection.locations,
        "industries": collection.industries,
    }


def normalize_database(database_url: str, limit: int = 1000) -> None:
    connection = open_connection(database_url)
    try:
        run_normalization(connection, limit=limit)
        connection.commit()
    finally:
        connection.close()


def run_collection(
    client: CollectionClient,
    config: CollectionConfig,
    database_url: str | None,
) -> CollectionResult:
    payload = build_collection_payload(config)
    run_id = client.start_collection(config.brightdata.dataset_id, payload)
    client.poll_collection(
        run_id,
        config.collection.poll_delay_seconds,
        config.collection.max_poll_attempts,
    )

    raw_records = client.fetch_results(run_id)
    if not raw_records:
        raise RuntimeError(f"Bright Data run {run_id} returned 0 records")

    scraped_at = datetime.now(UTC)
    envelopes = [map_raw_posting(run_id, raw_record, scraped_at) for raw_record in raw_records]
    archive_path = write_jsonl_archive(config.collection.output_dir, run_id, envelopes)
    postgres_inserted = load_raw_postings(database_url, envelopes) if database_url else None
    if database_url:
        normalize_database(database_url, limit=1000)

    return CollectionResult(
        run_id=run_id,
        archive_path=archive_path,
        record_count=len(envelopes),
        postgres_inserted=postgres_inserted,
    )
