from backend.archive.enrichment import build_dossier_metadata, build_record_metadata, stable_record_id
from backend.archive.models import ArchiveEditorialMetadata
from backend.trends.models import TrendResult, TrendScores


def make_metadata() -> ArchiveEditorialMetadata:
    return ArchiveEditorialMetadata(
        category="Tech / LLM",
        sector="Technology",
        lead_paragraph="Generated metadata reframes this role around live hiring evidence, operating pressure, and visible adoption patterns from the Bright Data corpus instead of relying on a curated fallback paragraph.",
        pull_quote="Generated archive language follows the evidence instead of fixed copy.",
        preceding_titles=["Solutions Architect", "AI Engineer", "Platform Lead"],
        competencies=["System design", "AI integration", "Governance review", "Stakeholder translation"],
        outlook="Expect adoption to widen where teams need clear ownership of AI implementation, evaluation, and cross-functional delivery standards.",
    )


def make_trend(title: str = "AI Workflow Architect", normalized_title_id: int = 10) -> TrendResult:
    return TrendResult(
        normalized_title_id=normalized_title_id,
        display_title=title,
        token_key="ai|architect|workflow",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.86, concentration=0.6),
        trend_score=0.92,
        early_mover_companies=["Acme AI Lab", "Northstar Systems"],
    )


def test_stable_record_id_uses_normalized_title_id_and_title() -> None:
    assert stable_record_id(10, "AI Workflow Architect") == "JTA-0010-AI-WORKFLOW-ARCHITECT"


def test_build_record_metadata_uses_curated_title_data() -> None:
    metadata = build_record_metadata(make_trend(), rank=1)

    assert metadata.record_id == "JTA-0010-AI-WORKFLOW-ARCHITECT"
    assert metadata.category == "TECH"
    assert metadata.category_detail == "Tech / Automation"
    assert metadata.categories == ["TECH"]
    assert metadata.first_seen_label == "May 2026 · Bright Data Corpus"
    assert metadata.velocity_label == "High · 86% growth index"
    assert "workflow" in metadata.excerpt.lower()


def test_build_dossier_metadata_uses_curated_title_data() -> None:
    dossier = build_dossier_metadata(make_trend(), rank=1)

    assert dossier.subheadline == "First detected in Technology · 2 companies found in the Bright Data corpus"
    assert "operating layer" in dossier.pull_quote
    assert dossier.adoption_points[-1].annotation == "Bright Data peak"
    assert dossier.sector_density[0].sector == "Technology"
    assert dossier.early_adopters[0].company == "Acme AI Lab"
    assert "AI Program Manager" in dossier.preceding_titles
    assert "Workflow design" in dossier.competencies


def test_cross_sector_archive_metadata() -> None:
    record = build_record_metadata(make_trend("Clinical AI Safety Officer"), rank=1)

    assert record.category == "HEALTHCARE"
    assert record.category_detail == "HEALTHCARE"
    assert record.categories == ["HEALTHCARE"]
    assert "clinical" in record.excerpt.lower()


def test_unknown_title_gets_deterministic_fallback_metadata() -> None:
    dossier = build_dossier_metadata(make_trend("Quantum Payroll Cartographer", normalized_title_id=20), rank=2)

    assert dossier.record_id == "JTA-0020-QUANTUM-PAYROLL-CARTOGRAPHER"
    assert dossier.category == "TECH"
    assert dossier.category_detail == "Tech / Operations"
    assert dossier.categories == ["TECH"]
    assert dossier.first_seen_label == "May 2026 · Bright Data Corpus"
    assert dossier.early_adopters[0].company == "Acme AI Lab"
    assert dossier.sector_density[0].percentage == 45


from backend.archive.service import build_archive_response, build_dossier_response


def test_build_archive_response_summarizes_records() -> None:
    response = build_archive_response([make_trend(), make_trend("Agent Operations Lead", normalized_title_id=20)])

    assert len(response.records) == 2
    assert response.summary.total_records == 2
    assert response.summary.category_counts == {"TECH": 2}
    assert response.summary.era_density[0].label == "Era 2020-26"
    assert response.records[0].record_id == "JTA-0010-AI-WORKFLOW-ARCHITECT"


def test_build_dossier_response_finds_record_by_id() -> None:
    dossier = build_dossier_response([make_trend(), make_trend("Agent Operations Lead", normalized_title_id=20)], "JTA-0020-AGENT-OPERATIONS-LEAD")

    assert dossier is not None
    assert dossier.title == "Agent Operations Lead"
    assert dossier.record_id == "JTA-0020-AGENT-OPERATIONS-LEAD"


def test_build_dossier_response_returns_none_for_unknown_id() -> None:
    assert build_dossier_response([make_trend()], "JTA-9999-NOPE") is None


def test_build_archive_response_uses_cached_metadata() -> None:
    response = build_archive_response([make_trend()], {10: make_metadata()})

    assert response.records[0].category == "TECH"
    assert response.records[0].category_detail == "Tech / LLM"
    assert "Generated metadata" in response.records[0].excerpt


def test_build_archive_response_uses_cached_image_path() -> None:
    path = "/archive-generated/ai-workflow-architect.png"
    metadata = make_metadata().model_copy(update={"image_path": path})

    response = build_archive_response([make_trend()], {10: metadata})

    assert response.records[0].image_path == path


def test_build_archive_response_assigns_generated_images_by_rank() -> None:
    trends = [make_trend(f"Role {index}", normalized_title_id=index) for index in range(1, 22)]

    response = build_archive_response(trends)

    assert response.records[0].image_path == "/archive-generated/JTA-0001-AI-SOLUTIONS-ARCHITECT.png"
    assert response.records[9].image_path == "/archive-generated/JTA-0010-CLINICAL-DATA-SCIENTIST-AI-TRAINER.png"
    assert response.records[10].image_path == "/archive-generated/JTA-0001-AI-SOLUTIONS-ARCHITECT.png"
    assert response.records[20].image_path == "/archive-generated/JTA-0001-AI-SOLUTIONS-ARCHITECT.png"


def test_build_dossier_response_uses_cached_metadata() -> None:
    dossier = build_dossier_response([make_trend()], "JTA-0010-AI-WORKFLOW-ARCHITECT", {10: make_metadata()})

    assert dossier is not None
    assert dossier.category == "TECH"
    assert dossier.category_detail == "Tech / LLM"
    assert dossier.categories == ["TECH"]
    assert dossier.preceding_titles == ["Solutions Architect", "AI Engineer", "Platform Lead"]


def test_build_dossier_response_uses_cached_image_path() -> None:
    path = "/archive-generated/ai-workflow-architect.png"
    metadata = make_metadata().model_copy(update={"image_path": path})

    dossier = build_dossier_response([make_trend()], "JTA-0010-AI-WORKFLOW-ARCHITECT", {10: metadata})

    assert dossier is not None
    assert dossier.image_path == path
