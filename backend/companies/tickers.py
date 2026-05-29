TICKER_ALIASES: dict[str, tuple[str, ...]] = {
    "NVDA": ("nvidia", "nvidia corporation", "nvidia corp", "nvidia inc"),
    "AMD": ("amd", "advanced micro devices", "advanced micro devices inc", "advanced micro devices, inc"),
    "PLTR": ("palantir", "palantir technologies", "palantir technologies inc"),
    "MSFT": ("microsoft", "microsoft corporation", "microsoft corp"),
}

TICKER_DISPLAY: dict[str, str] = {
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "PLTR": "Palantir",
    "MSFT": "Microsoft",
}


def normalize_company(name: str | None) -> str:
    if not name:
        return ""
    cleaned = " ".join(name.strip().lower().split())
    cleaned = cleaned.replace(", inc", " inc").replace(", llc", " llc").replace(", ltd", " ltd")
    cleaned = cleaned.replace(",", " ").replace(".", " ")
    return " ".join(cleaned.split())


def resolve_ticker(name: str | None) -> str | None:
    canonical = normalize_company(name)
    if not canonical:
        return None
    for ticker, aliases in TICKER_ALIASES.items():
        if canonical in aliases:
            return ticker
        for alias in aliases:
            if canonical.startswith(alias + " ") or canonical.endswith(" " + alias):
                return ticker
    return None


def display_for_ticker(ticker: str) -> str:
    return TICKER_DISPLAY.get(ticker, ticker)
