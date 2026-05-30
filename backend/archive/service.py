from collections import Counter

from backend.archive.enrichment import build_dossier_metadata, build_record_metadata
from backend.archive.models import ArchiveEditorialMetadata, ArchiveResponse, ArchiveSummary, DossierResponse, EraDensity, SerpSignal
from backend.trends.models import TrendResult, WeeklyCount


GENERATED_ARCHIVE_IMAGES = (
    "/archive-generated/JTA-0001-AI-SOLUTIONS-ARCHITECT.png",
    "/archive-generated/JTA-0002-PRINCIPAL-AI-ARCHITECT.png",
    "/archive-generated/JTA-0003-CONSULTANT-PRODUCT-QUALITY-SAFETY-LIFE-SCIENCES-HEALTHCARE.png",
    "/archive-generated/JTA-0004-DIRECTOR-RESPONSIBLE-AI-GOVERNANCE-COMPLIANCE-AIRLHV.png",
    "/archive-generated/JTA-0005-SENIOR-DIRECTOR-HEAD-OF-CLINICAL-STATISTICAL-PROGRAMMING.png",
    "/archive-generated/JTA-0006-AI-WORKFLOW-ARCHITECT.png",
    "/archive-generated/JTA-0007-ASSOCIATE-DIRECTOR-MEDICAL-SAFETY-SCIENTIST.png",
    "/archive-generated/JTA-0008-ATMOSPHERIC-SCIENTIST-AI-TRAINER.png",
    "/archive-generated/JTA-0009-CLIMATE-SCIENTIST-AI-TRAINER.png",
    "/archive-generated/JTA-0010-CLINICAL-DATA-SCIENTIST-AI-TRAINER.png",
)


def image_for_rank(rank: int) -> str:
    return GENERATED_ARCHIVE_IMAGES[(rank - 1) % len(GENERATED_ARCHIVE_IMAGES)]


def build_archive_response(trends: list[TrendResult], metadata_by_title_id: dict[int, ArchiveEditorialMetadata] | None = None) -> ArchiveResponse:
    metadata_by_title_id = metadata_by_title_id or {}
    records = []
    for index, trend in enumerate(trends, start=1):
        record = build_record_metadata(trend, rank=index, metadata=metadata_by_title_id.get(trend.normalized_title_id))
        if record.image_path is None:
            record = record.model_copy(update={"image_path": image_for_rank(index)})
        records.append(record)
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
    serp_signals_by_title_id: dict[int, list[SerpSignal]] | None = None,
) -> DossierResponse | None:
    metadata_by_title_id = metadata_by_title_id or {}
    weekly_counts_by_title_id = weekly_counts_by_title_id or {}
    serp_signals_by_title_id = serp_signals_by_title_id or {}
    for index, trend in enumerate(trends, start=1):
        dossier = build_dossier_metadata(
            trend,
            rank=index,
            metadata=metadata_by_title_id.get(trend.normalized_title_id),
            weekly_counts=weekly_counts_by_title_id.get(trend.normalized_title_id),
            serp_signals=serp_signals_by_title_id.get(trend.normalized_title_id),
        )
        if dossier.image_path is None:
            dossier = dossier.model_copy(update={"image_path": image_for_rank(index)})
        if dossier.record_id == record_id:
            return dossier
    return None
