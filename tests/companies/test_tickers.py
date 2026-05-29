from backend.companies.tickers import resolve_ticker


def test_resolve_ticker_matches_known_company_alias() -> None:
    assert resolve_ticker("nvidia") == "NVDA"
    assert resolve_ticker("NVIDIA Corporation") == "NVDA"
    assert resolve_ticker("nvidia corp") == "NVDA"


def test_resolve_ticker_returns_none_for_unknown_company() -> None:
    assert resolve_ticker("Random Mom & Pop Co") is None


def test_resolve_ticker_handles_palantir_amd_microsoft() -> None:
    assert resolve_ticker("Palantir Technologies") == "PLTR"
    assert resolve_ticker("Advanced Micro Devices") == "AMD"
    assert resolve_ticker("Microsoft") == "MSFT"
