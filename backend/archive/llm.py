import json
import re

from pydantic import ValidationError

from backend.archive.enrichment import _metadata_for
from backend.archive.models import ArchiveEditorialMetadata
from backend.archive.prompts import build_archive_metadata_prompt
from backend.narratives.providers import NarrativeProvider
from backend.trends.models import TrendResult


_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_json(text: str) -> str:
    stripped = text.strip()
    fence_match = _FENCED_JSON_RE.search(stripped)
    if fence_match:
        stripped = fence_match.group(1).strip()
    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return stripped[first_brace : last_brace + 1]
    return stripped


def parse_archive_metadata(text: str) -> ArchiveEditorialMetadata:
    return ArchiveEditorialMetadata.model_validate(json.loads(_extract_json(text)))


def generate_archive_metadata(trend: TrendResult, provider: NarrativeProvider) -> ArchiveEditorialMetadata:
    try:
        return parse_archive_metadata(provider.generate(build_archive_metadata_prompt(trend)))
    except (json.JSONDecodeError, ValidationError):
        return _metadata_for(trend.display_title)
