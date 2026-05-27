import json

from pydantic import ValidationError

from backend.archive.enrichment import _metadata_for
from backend.archive.models import ArchiveEditorialMetadata
from backend.archive.prompts import build_archive_metadata_prompt
from backend.narratives.providers import NarrativeProvider
from backend.trends.models import TrendResult


def parse_archive_metadata(text: str) -> ArchiveEditorialMetadata:
    return ArchiveEditorialMetadata.model_validate(json.loads(text))


def generate_archive_metadata(trend: TrendResult, provider: NarrativeProvider) -> ArchiveEditorialMetadata:
    try:
        return parse_archive_metadata(provider.generate(build_archive_metadata_prompt(trend)))
    except (json.JSONDecodeError, ValidationError, RuntimeError):
        return _metadata_for(trend.display_title)
