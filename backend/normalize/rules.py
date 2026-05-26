import re
import unicodedata

from backend.normalize.models import NormalizedTitleResult

LEVEL_TERMS = ("senior", "sr", "junior", "jr", "lead", "principal", "staff", "head", "director")
WORK_MODES = ("remote", "hybrid", "onsite")
STOPWORDS = {"the", "and", "of"}
REPLACEMENTS = {
    "gen ai": "generative_ai_placeholder",
    "genai": "generative_ai_placeholder",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "ops": "operations",
}
NOISE_TERMS = {"hiring", "urgent", "contract", "full-time"}


def normalize_title(raw_title: str) -> NormalizedTitleResult:
    display_title = re.sub(r"\s*\([^)]*remote[^)]*\)", "", raw_title, flags=re.IGNORECASE).strip()
    normalized = unicodedata.normalize("NFKC", raw_title).strip().lower()
    normalized = re.sub(r"[()!,]+", " ", normalized)
    normalized = normalized.replace("/", " ")
    normalized = normalized.replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    work_mode = next((term for term in WORK_MODES if term in normalized.split()), None)

    for source, target in REPLACEMENTS.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)

    tokens = []
    level_terms = []
    for token in normalized.split():
        if token in LEVEL_TERMS:
            canonical_level = {"sr": "senior", "jr": "junior"}.get(token, token)
            if canonical_level not in level_terms:
                level_terms.append(canonical_level)
            continue
        if token in WORK_MODES or token in NOISE_TERMS or token in STOPWORDS:
            continue
        if token == "generative_ai_placeholder":
            tokens.extend(["generative", "ai"])
            continue
        tokens.append(token)

    canonical_title = " ".join(tokens)
    token_key = "|".join(sorted(dict.fromkeys(tokens))) if tokens else ""
    usable = bool(tokens)

    return NormalizedTitleResult(
        display_title=display_title,
        canonical_title=canonical_title,
        token_key=token_key,
        level_terms=level_terms,
        work_mode=work_mode,
        confidence=1.0 if usable else 0.0,
        usable=usable,
    )
