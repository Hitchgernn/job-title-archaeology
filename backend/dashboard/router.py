from fastapi import APIRouter, HTTPException, Query

from backend.dashboard.models import DashboardResponse
from backend.dashboard.service import build_dashboard_response
from backend.db.connection import open_connection
from backend.narratives.pipeline import generate_narrative_cards_for_trends
from backend.narratives.providers import GeminiNarrativeProvider
from backend.trends.pipeline import run_trend_scoring

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/trends", response_model=DashboardResponse)
def dashboard_trends(limit: int = Query(5, ge=1, le=20)) -> DashboardResponse:
    connection = open_connection()
    try:
        provider = GeminiNarrativeProvider()
        trends = run_trend_scoring(connection, limit=limit)
        narratives = generate_narrative_cards_for_trends(trends, provider) if trends else []
        return build_dashboard_response(trends=trends, narratives=narratives)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="failed to build dashboard response") from exc
    finally:
        connection.close()
