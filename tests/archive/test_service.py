from backend.archive.enrichment import build_dossier_metadata, build_record_metadata, stable_record_id
from backend.trends.models import TrendResult, TrendScores


def make_trend(title: str = "AI Workflow Architect") -> TrendResult:
    return TrendResult(
        normalized_title_id=10,
        display_title=title,
        token_key="ai|architect|workflow",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.86, concentration=0.6),
        trend_score=0.92,
        early_mover_companies=["Acme AI Lab", "Northstar Systems"],
    )


def test_stable_record_id_uses_rank_and_title() -> None:
    assert stable_record_id(1, "AI Workflow Architect") == "JTA-0001-AI-WORKFLOW-ARCHITECT"


def test_build_record_metadata_uses_curated_title_data() -> None:
    metadata = build_record_metadata(make_trend(), rank=1)

    assert metadata.record_id == "JTA-0001-AI-WORKFLOW-ARCHITECT"
    assert metadata.category == "Tech / Automation"
    assert metadata.first_seen_label == "May 2026 · Demo Corpus"
    assert metadata.velocity_label == "High · 86% growth index"
    assert "workflow" in metadata.excerpt.lower()


def test_build_dossier_metadata_uses_curated_title_data() -> None:
    dossier = build_dossier_metadata(make_trend(), rank=1)

    assert dossier.subheadline == "First detected in Technology · 2 companies adopted in the current demo window"
    assert "operating layer" in dossier.pull_quote
    assert dossier.adoption_points[-1].annotation == "Current demo peak"
    assert dossier.sector_density[0].sector == "Technology"
    assert dossier.early_adopters[0].company == "Acme AI Lab"
    assert "AI Program Manager" in dossier.preceding_titles
    assert "Workflow design" in dossier.competencies


def test_unknown_title_gets_deterministic_fallback_metadata() -> None:
    dossier = build_dossier_metadata(make_trend("Quantum Payroll Cartographer"), rank=2)

    assert dossier.record_id == "JTA-0002-QUANTUM-PAYROLL-CARTOGRAPHER"
    assert dossier.category == "Tech / Operations"
    assert dossier.first_seen_label == "May 2026 · Demo Corpus"
    assert dossier.early_adopters[0].company == "Acme AI Lab"
    assert dossier.sector_density[0].percentage == 45


from backend.archive.service import build_archive_response, build_dossier_response


def test_build_archive_response_summarizes_records() -> None:
    response = build_archive_response([make_trend(), make_trend("Agent Operations Lead")])

    assert len(response.records) == 2
    assert response.summary.total_records == 2
    assert response.summary.category_counts == {"Tech / Automation": 1, "Tech / Operations": 1}
    assert response.summary.era_density[0].label == "Era 2020-26"
    assert response.records[0].record_id == "JTA-0001-AI-WORKFLOW-ARCHITECT"


def test_build_dossier_response_finds_record_by_id() -> None:
    dossier = build_dossier_response([make_trend(), make_trend("Agent Operations Lead")], "JTA-0002-AGENT-OPERATIONS-LEAD")

    assert dossier is not None
    assert dossier.title == "Agent Operations Lead"
    assert dossier.record_id == "JTA-0002-AGENT-OPERATIONS-LEAD"


def test_build_dossier_response_returns_none_for_unknown_id() -> None:
    assert build_dossier_response([make_trend()], "JTA-9999-NOPE") is None
