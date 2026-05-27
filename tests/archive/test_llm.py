from backend.archive.llm import generate_archive_metadata, parse_archive_metadata
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


class Provider:
    def __init__(self, text: str) -> None:
        self.text = text

    def generate(self, prompt: str) -> str:
        return self.text


def valid_json() -> str:
    return """{
        "category": "Tech / Architecture",
        "sector": "Technology",
        "lead_paragraph": "AI solutions architecture is moving from broad cloud design into a focused role for shaping model-enabled products, integration paths, governance checkpoints, and delivery standards across teams that now depend on applied artificial intelligence.",
        "pull_quote": "AI architecture becomes visible when integration pressure turns into operating structure.",
        "preceding_titles": ["Solutions Architect", "Cloud Architect", "AI Engineer"],
        "competencies": ["System design", "AI integration", "Governance review", "Stakeholder translation"],
        "outlook": "Expect the title to spread where companies need durable ownership of AI implementation decisions across product, platform, and operating teams."
    }"""


def test_parse_archive_metadata_accepts_valid_json() -> None:
    metadata = parse_archive_metadata(valid_json())

    assert metadata.category == "Tech / Architecture"
    assert len(metadata.preceding_titles) == 3
    assert len(metadata.competencies) == 4


def test_generate_archive_metadata_falls_back_on_invalid_json() -> None:
    metadata = generate_archive_metadata(make_trend(), Provider("not json"))

    assert metadata.category == "Tech / Operations"
    assert "AI Solutions Architect" in metadata.lead_paragraph
