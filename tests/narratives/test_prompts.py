from backend.narratives.models import NarrativeRequest
from backend.narratives.prompts import build_trend_prompt
from backend.trends.models import TrendResult, TrendScores


def make_trend() -> TrendResult:
    return TrendResult(
        normalized_title_id=10,
        display_title="AI Workflow Architect",
        token_key="ai|architect|workflow",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.86, concentration=0.6),
        trend_score=0.92,
        early_mover_companies=["Acme", "Globex"],
    )


def test_build_trend_prompt_includes_structured_trend_evidence() -> None:
    prompt = build_trend_prompt(NarrativeRequest(trend=make_trend()))

    assert "AI Workflow Architect" in prompt
    assert "trend_score: 0.92" in prompt
    assert "recent_count: 12" in prompt
    assert "prior_count: 1" in prompt
    assert "newness: 1.00" in prompt
    assert "velocity: 0.86" in prompt
    assert "concentration: 0.60" in prompt
    assert "early_movers: Acme, Globex" in prompt


def test_build_trend_prompt_requests_analyst_card_sections() -> None:
    prompt = build_trend_prompt(NarrativeRequest(trend=make_trend()))

    assert "summary" in prompt
    assert "evidence" in prompt
    assert "why_now" in prompt
    assert "watch_next" in prompt


def test_build_trend_prompt_uses_only_trend_result_fields() -> None:
    prompt = build_trend_prompt(NarrativeRequest(trend=make_trend()))

    assert "raw" not in prompt.lower()
    assert "api_key" not in prompt.lower()
    assert "database_url" not in prompt.lower()
