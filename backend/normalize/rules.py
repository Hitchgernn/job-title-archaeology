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

US_STATE_CODES = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy", "dc",
}

LOCATION_HINTS = {"office", "headquarters", "hq", "remote", "hybrid", "onsite", "based"}

_PARENS_RE = re.compile(r"\s*\([^)]*\)")
_TRAILING_ID_RE = re.compile(r"\s+(?:id\s*)?[A-Z][A-Z0-9-]{4,}\s*$")
_SHIFT_RE = re.compile(r"\b(\d+(?:st|nd|rd|th)\s+shift(?:\s+position)?)\b", re.IGNORECASE)
_DEPT_PREFIX_RE = re.compile(r"^([A-Z]{2,}[A-Z0-9]*\s*[:\-]\s+)")
_TICKET_TRAILING_RE = re.compile(r"\s+ID\d{3,}\b", re.IGNORECASE)


def _looks_like_location(segment: str) -> bool:
    text = segment.strip().strip(",.- ")
    if not text:
        return False
    lowered = text.lower()
    if any(hint in lowered for hint in LOCATION_HINTS):
        return True
    parts = [part.strip() for part in re.split(r",|/", text) if part.strip()]
    if len(parts) >= 2 and parts[-1].lower().replace(".", "") in US_STATE_CODES:
        return True
    if len(parts) == 1 and parts[0].lower().replace(".", "") in US_STATE_CODES:
        return True
    if re.fullmatch(r"[A-Z][a-zA-Z .]+,\s*[A-Z]{2}", text):
        return True
    return False


def _strip_trailing_segments(text: str) -> str:
    cleaned = text
    while True:
        match = re.search(r"\s+[-–—|]\s+([^-–—|]+)$", cleaned)
        if not match:
            break
        tail = match.group(1)
        if _looks_like_location(tail) or re.fullmatch(r"[A-Z]{3,}[A-Z0-9-]*", tail.strip()):
            cleaned = cleaned[: match.start()].rstrip()
            continue
        break
    return cleaned


def clean_display_title(raw_title: str) -> str:
    text = unicodedata.normalize("NFKC", raw_title).strip()
    text = _PARENS_RE.sub("", text)
    text = _DEPT_PREFIX_RE.sub("", text)
    text = _TICKET_TRAILING_RE.sub("", text)
    text = _SHIFT_RE.sub("", text)
    text = _TRAILING_ID_RE.sub("", text)
    text = _strip_trailing_segments(text)
    text = re.sub(r"\s+", " ", text).strip(" -–—|,")
    return text or raw_title.strip()


def normalize_title(raw_title: str) -> NormalizedTitleResult:
    display_title = clean_display_title(raw_title)
    raw_lower = unicodedata.normalize("NFKC", raw_title).lower()
    work_mode = next((term for term in WORK_MODES if re.search(rf"\b{term}\b", raw_lower)), None)

    normalized = unicodedata.normalize("NFKC", display_title).strip().lower()
    normalized = normalized.replace("–", "-").replace("—", "-")
    normalized = re.sub(r"[()!,:]+", " ", normalized)
    normalized = normalized.replace("/", " ")
    normalized = normalized.replace("&", " ")
    normalized = normalized.replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()

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
