from fastapi import APIRouter, HTTPException, Query

from backend.archive.models import ArchiveResponse, DossierResponse, SerpSignal
from backend.archive.prompts import PROMPT_VERSION
from backend.archive.repository import fetch_cached_metadata
from backend.archive.service import build_archive_response, build_dossier_response
from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.serp.repository import fetch_serp_signals_for_titles
from backend.trends.pipeline import fetch_weekly_counts_map, run_trend_scoring

router = APIRouter(prefix="/archive", tags=["archive"])
ARCHIVE_SOURCE = "brightdata_web_scraper"


@router.get("/titles", response_model=ArchiveResponse)
def archive_titles(limit: int = Query(50, ge=1, le=200)) -> ArchiveResponse:
    connection = open_connection()
    try:
        run_migrations(connection)
        trends = run_trend_scoring(connection, limit=limit, source=ARCHIVE_SOURCE)
        metadata = fetch_cached_metadata(connection, [trend.normalized_title_id for trend in trends], PROMPT_VERSION)
        return build_archive_response(trends, metadata)
    finally:
        connection.close()


@router.get("/titles/{record_id}", response_model=DossierResponse)
def archive_dossier(record_id: str, limit: int = Query(50, ge=1, le=200)) -> DossierResponse:
    connection = open_connection()
    try:
        run_migrations(connection)
        trends = run_trend_scoring(connection, limit=limit, source=ARCHIVE_SOURCE)
        title_ids = [trend.normalized_title_id for trend in trends]
        metadata = fetch_cached_metadata(connection, title_ids, PROMPT_VERSION)
        weekly_counts = fetch_weekly_counts_map(connection, title_ids, source=ARCHIVE_SOURCE)
        raw_serp = fetch_serp_signals_for_titles(connection, title_ids)
        serp_signals = {
            title_id: [SerpSignal(title=hit.title, url=hit.url, snippet=hit.snippet, source=hit.source) for hit in hits]
            for title_id, hits in raw_serp.items()
        }
        dossier = build_dossier_response(trends, record_id, metadata, weekly_counts, serp_signals)
    finally:
        connection.close()

    if dossier is None:
        raise HTTPException(status_code=404, detail="archive record not found")
    return dossier
