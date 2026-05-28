from collections import Counter

from backend.archive.enrichment import build_dossier_metadata, build_record_metadata
from backend.archive.models import ArchiveEditorialMetadata, ArchiveResponse, ArchiveSummary, DossierResponse, EraDensity
from backend.trends.models import TrendResult, WeeklyCount


def build_archive_response(trends: list[TrendResult], metadata_by_title_id: dict[int, ArchiveEditorialMetadata] | None = None) -> ArchiveResponse:
    metadata_by_title_id = metadata_by_title_id or {}
    records = [
        build_record_metadata(trend, rank=index, metadata=metadata_by_title_id.get(trend.normalized_title_id))
        for index, trend in enumerate(trends, start=1)
    ]
    category_counts = dict(Counter(record.category for record in records))
    return ArchiveResponse(
        records=records,
        summary=ArchiveSummary(
            total_records=len(records),
            category_counts=category_counts,
            era_density=[
                EraDensity(label="Era 2020-26", percentage=82),
                EraDensity(label="Era 2010-19", percentage=14),
                EraDensity(label="Pre-2010", percentage=4),
            ],
        ),
    )


def build_dossier_response(
    trends: list[TrendResult],
    record_id: str,
    metadata_by_title_id: dict[int, ArchiveEditorialMetadata] | None = None,
    weekly_counts_by_title_id: dict[int, list[WeeklyCount]] | None = None,
) -> DossierResponse | None:
    metadata_by_title_id = metadata_by_title_id or {}
    weekly_counts_by_title_id = weekly_counts_by_title_id or {}
    for index, trend in enumerate(trends, start=1):
        dossier = build_dossier_metadata(
            trend,
            rank=index,
            metadata=metadata_by_title_id.get(trend.normalized_title_id),
            weekly_counts=weekly_counts_by_title_id.get(trend.normalized_title_id),
        )
        if dossier.record_id == record_id:
            return dossier
    return None
