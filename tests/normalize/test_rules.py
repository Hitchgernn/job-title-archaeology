from backend.normalize.models import NormalizedTitleResult
from backend.normalize.rules import normalize_title


def test_normalize_title_extracts_level_and_work_mode() -> None:
    result = normalize_title("Senior GenAI Product Ops Lead (Remote)")

    assert isinstance(result, NormalizedTitleResult)
    assert result.display_title == "Senior GenAI Product Ops Lead"
    assert result.canonical_title == "generative ai product operations"
    assert result.level_terms == ["senior", "lead"]
    assert result.work_mode == "remote"
    assert result.token_key == "ai|generative|operations|product"
    assert result.confidence == 1.0
    assert result.method == "rules_v1"
    assert result.usable is True


def test_normalize_title_handles_punctuation_and_case() -> None:
    result = normalize_title("AI / ML Engineer!!!")

    assert result.canonical_title == "artificial intelligence machine learning engineer"
    assert result.token_key == "artificial|engineer|intelligence|learning|machine"


def test_normalize_title_marks_empty_output_unusable() -> None:
    result = normalize_title("Remote!!!")

    assert result.canonical_title == ""
    assert result.token_key == ""
    assert result.usable is False
    assert result.confidence == 0.0
