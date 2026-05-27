import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from backend.ingest.cli import app
from backend.ingest.pipeline import CollectionResult


def test_import_json_command_loads_downloaded_brightdata_file(tmp_path: Path) -> None:
    source_path = tmp_path / "brightdata_jobs_sample.json"
    source_path.write_text(
        json.dumps([
            {
                "job_title": "Clinical AI Safety Officer",
                "company_name": "Northstar Health",
                "job_location": "Boston, MA",
                "date_posted_parsed": "2026-05-20",
                "apply_link": "https://example.com/apply",
            }
        ]),
        encoding="utf-8",
    )
    runner = CliRunner()

    with patch("backend.ingest.cli.import_json_file") as import_json_file:
        import_json_file.return_value = CollectionResult(
            run_id="brightdata-sample",
            archive_path=tmp_path / "brightdata_brightdata-sample.jsonl",
            record_count=1,
            postgres_inserted=1,
        )
        result = runner.invoke(app, ["import-json", str(source_path), "--run-id", "brightdata-sample"])

    assert result.exit_code == 0
    assert "Imported 1 records" in result.stdout
    import_json_file.assert_called_once()


def test_collect_command_runs_pipeline(tmp_path: Path) -> None:
    config_path = tmp_path / "day1.yaml"
    config_path.write_text(
        """
brightdata:
  base_url: https://api.brightdata.com
  dataset_id: gd_test
collection:
  output_dir: data/raw
  target_records: 500
  poll_delay_seconds: 1
  max_poll_attempts: 2
  keywords:
    - AI
  locations:
    - United States
  industries:
    - Technology
""".strip(),
        encoding="utf-8",
    )
    runner = CliRunner()

    with patch("backend.ingest.cli.run_collection") as run_collection:
        run_collection.return_value = CollectionResult(
            run_id="run-123",
            archive_path=tmp_path / "brightdata_run-123.jsonl",
            record_count=2,
            postgres_inserted=None,
        )
        result = runner.invoke(app, ["collect", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "run-123" in result.stdout
    assert "2 records" in result.stdout
    run_collection.assert_called_once()
