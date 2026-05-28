import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

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


def build_indeed_inputs(keywords: list[str], locations: list[str], country: str = "US") -> list[dict[str, str]]:
    return [
        {
            "country": country,
            "domain": "indeed.com",
            "keyword_search": keyword,
            "location": location,
            "date_posted": "",
            "posted_by": "",
            "location_radius": "",
        }
        for keyword in keywords
        for location in locations
    ]


def build_linkedin_inputs(keywords: list[str], locations: list[str], country: str = "US") -> list[dict[str, str]]:
    return [
        {
            "location": location,
            "keyword": keyword,
            "country": country,
            "time_range": "Past month",
            "job_type": "",
            "experience_level": "",
            "remote": "",
            "company": "",
            "location_radius": "",
        }
        for keyword in keywords
        for location in locations
    ]


def run_keyword_collection(
    client: CollectionClient,
    *,
    dataset_id: str,
    inputs: list[dict[str, Any]],
    output_dir: Path,
    poll_delay_seconds: int,
    max_poll_attempts: int,
    database_url: str | None,
    limit_per_input: int | None = None,
) -> CollectionResult:
    payload: dict[str, Any] = {"input": inputs}
    query = {
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword",
    }
    if limit_per_input is not None:
        query["limit_per_input"] = str(limit_per_input)
    run_id = client.start_collection(dataset_id, payload, query)
    client.poll_collection(run_id, poll_delay_seconds, max_poll_attempts)

    raw_records = client.fetch_results(run_id)
    if not raw_records:
        raise RuntimeError(f"Bright Data run {run_id} returned 0 records")

    scraped_at = datetime.now(UTC)
    envelopes = [map_raw_posting(run_id, raw_record, scraped_at) for raw_record in raw_records]
    archive_path = write_jsonl_archive(output_dir, run_id, envelopes)
    postgres_inserted = load_raw_postings(database_url, envelopes) if database_url else None
    if database_url:
        normalize_database(database_url, limit=1000)

    return CollectionResult(
        run_id=run_id,
        archive_path=archive_path,
        record_count=len(envelopes),
        postgres_inserted=postgres_inserted,
    )


def normalize_database(database_url: str, limit: int = 1000) -> None:
    connection = open_connection(database_url)
    try:
        run_normalization(connection, limit=limit)
        connection.commit()
    finally:
        connection.close()


def _records_from_json_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "results", "items"):
            items = payload.get(key)
            if isinstance(items, list) and all(isinstance(item, dict) for item in items):
                return items
    raise ValueError("Bright Data JSON must be a list of objects or contain data/results/items list")


def import_json_file(
    source_path: Path,
    run_id: str,
    output_dir: Path,
    database_url: str | None,
) -> CollectionResult:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    raw_records = _records_from_json_payload(payload)
    if not raw_records:
        raise RuntimeError(f"Bright Data file {source_path} contained 0 records")

    scraped_at = datetime.now(UTC)
    envelopes = [map_raw_posting(run_id, raw_record, scraped_at) for raw_record in raw_records]
    archive_path = write_jsonl_archive(output_dir, run_id, envelopes)
    postgres_inserted = load_raw_postings(database_url, envelopes) if database_url else None
    if database_url:
        normalize_database(database_url, limit=1000)

    return CollectionResult(
        run_id=run_id,
        archive_path=archive_path,
        record_count=len(envelopes),
        postgres_inserted=postgres_inserted,
    )


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
