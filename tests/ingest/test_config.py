from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.ingest.config import CollectionConfig, load_collection_config


def test_load_collection_config(tmp_path: Path) -> None:
    config_path = tmp_path / "configs" / "collections" / "day1.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        """
brightdata:
  base_url: https://api.brightdata.com
  dataset_id: gd_test
collection:
  output_dir: data/raw
  target_records: 750
  poll_delay_seconds: 1
  max_poll_attempts: 3
  keywords:
    - AI
    - security
  locations:
    - United States
  industries:
    - Technology
""".lstrip(),
        encoding="utf-8",
    )

    config = load_collection_config(config_path)

    assert str(config.brightdata.base_url) == "https://api.brightdata.com/"
    assert config.brightdata.dataset_id == "gd_test"
    assert config.collection.output_dir == tmp_path / "data" / "raw"
    assert config.collection.target_records == 750
    assert config.collection.poll_delay_seconds == 1
    assert config.collection.max_poll_attempts == 3
    assert config.collection.keywords == ["AI", "security"]
    assert config.collection.locations == ["United States"]
    assert config.collection.industries == ["Technology"]


def test_load_brightdata_jobs_config() -> None:
    config = load_collection_config(Path("configs/brightdata_jobs.yaml"))

    assert config.collection.target_records == 50
    assert "AI Workflow Architect" in config.collection.keywords
    assert "Clinical AI Safety Officer" in config.collection.keywords
    assert "Robotics Fleet Coordinator" in config.collection.keywords


def test_collection_config_rejects_empty_keywords() -> None:
    with pytest.raises(ValidationError):
        CollectionConfig.model_validate(
            {
                "brightdata": {
                    "base_url": "https://api.brightdata.com",
                    "dataset_id": "gd_test",
                },
                "collection": {
                    "output_dir": "data/raw",
                    "target_records": 750,
                    "poll_delay_seconds": 1,
                    "max_poll_attempts": 3,
                    "keywords": [],
                    "locations": ["United States"],
                    "industries": ["Technology"],
                },
            }
        )
