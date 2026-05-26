from backend.narratives.models import NarrativeCard, NarrativeRequest
from backend.narratives.prompts import build_trend_prompt
from backend.narratives.providers import NarrativeProvider
from backend.trends.models import TrendResult
from backend.trends.pipeline import run_trend_scoring


def fallback_card_text(trend: TrendResult) -> str:
    movers = ", ".join(trend.early_mover_companies) if trend.early_mover_companies else "none"
    return (
        f"summary:\n{trend.display_title} is emerging with trend score {trend.trend_score:.2f}.\n"
        f"evidence:\nrecent={trend.recent_count}, prior={trend.prior_count}, early_movers={movers}\n"
        "why_now:\nThe role may reflect new operating needs around AI, automation, or data workflows.\n"
        "watch_next:\nMonitor whether postings spread to more companies and industries."
    )


def generate_narrative_cards_for_trends(trends: list[TrendResult], provider: NarrativeProvider) -> list[NarrativeCard]:
    cards: list[NarrativeCard] = []
    for trend in trends:
        prompt = build_trend_prompt(NarrativeRequest(trend=trend))
        try:
            generated_text = provider.generate(prompt)
        except Exception:
            generated_text = ""
        cards.append(NarrativeCard(title=trend.display_title, text=generated_text or fallback_card_text(trend)))
    return cards


def generate_narrative_cards(connection, provider: NarrativeProvider, limit: int) -> list[NarrativeCard]:
    trends = run_trend_scoring(connection, limit=limit)
    return generate_narrative_cards_for_trends(trends, provider)
