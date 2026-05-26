from unittest.mock import Mock, patch

import pytest

from backend.ingest.config import CollectionConfig
from backend.ingest.pipeline import CollectionResult, run_collection


def _config(tmp_path):
    return CollectionConfig.model_validate(
        {
            "brightdata": {
                "base_url": "https://api.brightdata.com",
                "dataset_id": "gd_job_postings",
            },
            "collection": {
                "output_dir": tmp_path,
                "target_records": 500,
                "poll_delay_seconds": 1,
                "max_poll_attempts": 2,
                "keywords": ["AI"],
                "locations": ["United States"],
                "industries": ["Technology"],
            },
        }
    )


def test_run_collection_writes_jsonl_without_database(tmp_path):
    client = Mock()
    client.start_collection.return_value = "run-123"
    client.fetch_results.return_value = [
        {"job_title": "AI Lead"},
        {"job_title": "Data Lead"},
    ]

    result = run_collection(client, _config(tmp_path), database_url=None)

    assert isinstance(result, CollectionResult)
    assert result.run_id == "run-123"
    assert result.record_count == 2
    assert result.postgres_inserted is None
    assert result.archive_path.exists()
    client.poll_collection.assert_called_once_with("run-123", 1, 2)


def test_run_collection_rejects_empty_results(tmp_path):
    client = Mock()
    client.start_collection.return_value = "run-empty"
    client.fetch_results.return_value = []

    with pytest.raises(RuntimeError, match="0 records"):
        run_collection(client, _config(tmp_path), database_url=None)


@patch("backend.ingest.pipeline.load_raw_postings", return_value=2)
def test_run_collection_with_database_url_loads_postgres(load_raw_postings, tmp_path):
    client = Mock()
    client.start_collection.return_value = "run-123"
    client.fetch_results.return_value = [
        {"job_title": "AI Lead"},
        {"job_title": "Data Lead"},
    ]

    result = run_collection(client, _config(tmp_path), database_url="postgresql://example")

    assert result.postgres_inserted == 2
    load_raw_postings.assert_called_once()
