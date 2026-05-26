from backend.narratives.models import NarrativeRequest


def build_trend_prompt(request: NarrativeRequest) -> str:
    trend = request.trend
    early_movers = ", ".join(trend.early_mover_companies) if trend.early_mover_companies else "none"
    return "\n".join(
        [
            "You are an analyst explaining emerging job title signals.",
            "Write a concise analyst card with these exact sections:",
            "summary:",
            "evidence:",
            "why_now:",
            "watch_next:",
            "Use only the structured signal data below.",
            f"title: {trend.display_title}",
            f"trend_score: {trend.trend_score:.2f}",
            f"recent_count: {trend.recent_count}",
            f"prior_count: {trend.prior_count}",
            f"newness: {trend.scores.newness:.2f}",
            f"velocity: {trend.scores.velocity:.2f}",
            f"concentration: {trend.scores.concentration:.2f}",
            f"early_movers: {early_movers}",
        ]
    )
