from collections import Counter

from backend.archive.enrichment import build_dossier_metadata, build_record_metadata
from backend.archive.models import ArchiveEditorialMetadata, ArchiveResponse, ArchiveSummary, DossierResponse, EraDensity, SerpSignal
from backend.trends.models import TrendResult, WeeklyCount


NAMED_ARCHIVE_IMAGE_RECORD_IDS = {
    "JTA-0045-AI-ARCHITECT",
    "JTA-0035-AI-SOLUTIONS-ARCHITECT",
    "JTA-1245-RELIABILITY-ENGINEER",
    "JTA-0785-ELECTRICAL-ENGINEER",
    "JTA-1425-LOGISTICS-COORDINATOR",
    "JTA-0047-AI-ENGINEER",
    "JTA-0672-PROPERTY-MANAGER",
    "JTA-0029-CONSULTANT-PRODUCT-QUALITY-SAFETY-LIFE-SCIENCES-HEALTHCARE",
    "JTA-2105-ENVIRONMENTAL-HEALTH-AND-SAFETY-SPECIALIST",
    "JTA-0001-AI-WORKFLOW-ARCHITECT",
    "JTA-0666-CONTROLS-AND-AUTOMATION-ENGINEER",
    "JTA-1680-DATA-SCIENTIST",
    "JTA-1352-DIRECTOR-OPERATIONS",
    "JTA-0248-AUTOMATION-TECHNICIAN",
    "JTA-2078-CONTROLS-ENGINEER",
    "JTA-0099-DIRECTOR-RESPONSIBLE-AI-GOVERNANCE-COMPLIANCE",
    "JTA-0051-SENIOR-DIRECTOR-HEAD-OF-CLINICAL-STATISTICAL-PROGRAMMING",
    "JTA-1576-SOFTWARE-ENGINEER",
    "JTA-0026-ASSOCIATE-DIRECTOR-MEDICAL-SAFETY",
    "JTA-0653-AUTOMATION-ENGINEER-CONTRACT",
    "JTA-0038-AI-AND-AUTOMATION-ENGINEER",
    "JTA-0092-ATMOSPHERIC-SCIENTIST-AI-TRAINER",
    "JTA-0044-CLIMATE-SCIENTIST-AI-TRAINER",
    "JTA-0043-CLINICAL-DATA-SCIENTIST-AI-TRAINER",
    "JTA-2106-ENVIRONMENTAL-SCIENTIST",
}

GENERIC_ARCHIVE_IMAGE = "/archive-generated/JTA-GENERIC-ARCHIVE.svg"


def image_for_record_id(record_id: str) -> str:
    if record_id in NAMED_ARCHIVE_IMAGE_RECORD_IDS:
        return f"/archive-generated/{record_id}.svg"
    return GENERIC_ARCHIVE_IMAGE


def build_archive_response(trends: list[TrendResult], metadata_by_title_id: dict[int, ArchiveEditorialMetadata] | None = None) -> ArchiveResponse:
    metadata_by_title_id = metadata_by_title_id or {}
    records = []
    for index, trend in enumerate(trends, start=1):
        record = build_record_metadata(trend, rank=index, metadata=metadata_by_title_id.get(trend.normalized_title_id))
        if record.image_path is None:
            record = record.model_copy(update={"image_path": image_for_record_id(record.record_id)})
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
            dossier = dossier.model_copy(update={"image_path": image_for_record_id(dossier.record_id)})
        if dossier.record_id == record_id:
            return dossier
    return None
