from fastapi import APIRouter, HTTPException, Query

from backend.archive.models import ArchiveResponse, DossierResponse
from backend.archive.service import build_archive_response, build_dossier_response
from backend.db.connection import open_connection
from backend.trends.pipeline import run_trend_scoring

router = APIRouter(prefix="/archive", tags=["archive"])
ARCHIVE_SOURCE = "brightdata_web_scraper"


@router.get("/titles", response_model=ArchiveResponse)
def archive_titles(limit: int = Query(10, ge=1, le=50)) -> ArchiveResponse:
    connection = open_connection()
    try:
        trends = run_trend_scoring(connection, limit=limit, source=ARCHIVE_SOURCE)
        return build_archive_response(trends)
    finally:
        connection.close()


@router.get("/titles/{record_id}", response_model=DossierResponse)
def archive_dossier(record_id: str, limit: int = Query(10, ge=1, le=50)) -> DossierResponse:
    connection = open_connection()
    try:
        trends = run_trend_scoring(connection, limit=limit, source=ARCHIVE_SOURCE)
        dossier = build_dossier_response(trends, record_id)
    finally:
        connection.close()

    if dossier is None:
        raise HTTPException(status_code=404, detail="archive record not found")
    return dossier
