from backend.archive.prompts import build_archive_metadata_prompt
from backend.trends.models import TrendResult, TrendScores


def make_trend() -> TrendResult:
    return TrendResult(
        normalized_title_id=1,
        display_title="AI Solutions Architect",
        token_key="ai|architect|solutions",
        recent_count=18,
        prior_count=0,
        scores=TrendScores(newness=1.0, velocity=0.9, concentration=0.7),
        trend_score=0.95,
        early_mover_companies=["Acme", "Northstar"],
    )


def test_archive_metadata_prompt_sets_json_shape_and_style_constraints() -> None:
    prompt = build_archive_metadata_prompt(make_trend())

    assert "Return only valid JSON" in prompt
    assert "35-45 words" in prompt
    assert "12-18 words" in prompt
    assert "exactly 3" in prompt
    assert "exactly 4" in prompt
    assert "25-35 words" in prompt
    assert "AI Solutions Architect" in prompt
    assert "GEMINI_API_KEY" not in prompt
    assert "DATABASE_URL" not in prompt
