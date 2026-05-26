from pathlib import Path
from typing import Sequence

from backend.ingest.models import RawJobPostingEnvelope


def _safe_run_id(run_id: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in run_id)


def write_jsonl_archive(
    output_dir: Path,
    run_id: str,
    records: Sequence[RawJobPostingEnvelope],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"brightdata_{_safe_run_id(run_id)}.jsonl"

    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json())
            file.write("\n")

    return output_path
