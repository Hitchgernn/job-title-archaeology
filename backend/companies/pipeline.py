from datetime import datetime, timezone

from backend.companies.aggregation import aggregate_from_postings
from backend.companies.models import CompanySignal
from backend.companies.repository import fetch_company_posting_rows, upsert_company_signal


def recompute_company_signals(connection, now: datetime | None = None) -> list[CompanySignal]:
    rows = fetch_company_posting_rows(connection)
    signals = aggregate_from_postings(rows, now=now or datetime.now(timezone.utc))
    for signal in signals:
        upsert_company_signal(connection, signal)
    connection.commit()
    return signals
