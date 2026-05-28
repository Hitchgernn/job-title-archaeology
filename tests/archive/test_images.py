from backend.archive.images import build_archive_image_prompt, image_filename, save_image_bytes
from backend.archive.models import ArchiveEditorialMetadata
from backend.trends.models import TrendResult, TrendScores


def make_trend() -> TrendResult:
    return TrendResult(
        normalized_title_id=42,
        display_title="AI Workflow Architect",
        token_key="ai workflow architect",
        recent_count=12,
        prior_count=1,
        scores=TrendScores(newness=1.0, velocity=0.8, concentration=0.5),
        trend_score=0.91,
        early_mover_companies=["Acme"],
    )


def make_metadata() -> ArchiveEditorialMetadata:
    return ArchiveEditorialMetadata(
        category="Tech / Automation",
        sector="Software",
        lead_paragraph="Automation work is formalizing into a new role.",
        pull_quote="The work moved from scripts to systems.",
        preceding_titles=["Automation Engineer", "Workflow Analyst", "AI Specialist"],
        competencies=["Process mapping", "LLM orchestration", "Risk review", "Change management"],
        outlook="Teams will hire for judgment around automated work.",
    )


def test_build_archive_image_prompt_is_monochrome_and_textless():
    prompt = build_archive_image_prompt(make_trend(), make_metadata())

    assert "AI Workflow Architect" in prompt
    assert "monochrome" in prompt
    assert "black-and-white" in prompt
    assert "Do not include readable text" in prompt
    assert "Tech / Automation" in prompt


def test_image_filename_is_stable_slug():
    assert image_filename(make_trend()) == "ai-workflow-architect.png"


def test_save_image_bytes_writes_public_path(tmp_path):
    public_path = save_image_bytes(tmp_path, "ai-workflow-architect.png", b"png-bytes")

    assert public_path == "/archive-generated/ai-workflow-architect.png"
    assert (tmp_path / "ai-workflow-architect.png").read_bytes() == b"png-bytes"
