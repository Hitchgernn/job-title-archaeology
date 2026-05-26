from backend.dashboard.models import DashboardResponse, DashboardSummary, DashboardTrendCard
from backend.narratives.models import NarrativeCard
from backend.trends.models import TrendResult


def build_dashboard_response(trends: list[TrendResult], narratives: list[NarrativeCard]) -> DashboardResponse:
    narrative_by_title = {card.title: card.text for card in narratives}
    cards: list[DashboardTrendCard] = []
    for index, trend in enumerate(trends, start=1):
        cards.append(
            DashboardTrendCard(
                rank=index,
                title=trend.display_title,
                score=trend.trend_score,
                recent_count=trend.recent_count,
                prior_count=trend.prior_count,
                newness=trend.scores.newness,
                velocity=trend.scores.velocity,
                concentration=trend.scores.concentration,
                early_mover_companies=trend.early_mover_companies,
                narrative=narrative_by_title.get(trend.display_title, ""),
            )
        )

    average_score = round(sum(card.score for card in cards) / len(cards), 2) if cards else 0.0
    early_mover_count = len({company for card in cards for company in card.early_mover_companies})
    return DashboardResponse(
        trends=cards,
        summary=DashboardSummary(
            trend_count=len(cards),
            average_score=average_score,
            early_mover_count=early_mover_count,
        ),
    )
