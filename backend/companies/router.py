from fastapi import APIRouter, HTTPException, Query

from backend.companies.aggregation import weekly_hires_for_company
from backend.companies.models import CompanyDossier, CompanyListResponse, CompanyListSummary
from backend.companies.repository import (
    fetch_company_posting_rows,
    fetch_company_signal_by_key,
    fetch_company_signals,
)
from backend.db.connection import open_connection
from backend.db.migrate import run_migrations

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
def list_companies(limit: int = Query(20, ge=1, le=200)) -> CompanyListResponse:
    connection = open_connection()
    try:
        run_migrations(connection)
        signals = fetch_company_signals(connection, limit=limit)
    finally:
        connection.close()

    return CompanyListResponse(
        companies=signals,
        summary=CompanyListSummary(
            tracked_count=len(signals),
            total_recent_hires=sum(signal.recent_hires_30d for signal in signals),
            last_computed_at=max((signal.computed_at for signal in signals), default=None),
        ),
    )


@router.get("/{key}", response_model=CompanyDossier)
def company_dossier(key: str) -> CompanyDossier:
    connection = open_connection()
    try:
        run_migrations(connection)
        signal = fetch_company_signal_by_key(connection, key)
        if signal is None:
            raise HTTPException(status_code=404, detail="company not found")
        rows = fetch_company_posting_rows(connection)
        weekly = weekly_hires_for_company(rows, signal.company_key, weeks=12)
    finally:
        connection.close()

    return CompanyDossier(
        company=signal,
        weekly=weekly,
        titles=signal.top_titles,
    )
