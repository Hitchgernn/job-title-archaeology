from dataclasses import dataclass

from backend.normalize.repository import (
    fetch_unlinked_raw_postings,
    link_posting_to_title,
    upsert_normalized_title,
)
from backend.normalize.rules import normalize_title


@dataclass(frozen=True)
class NormalizeSummary:
    processed: int
    linked: int
    skipped: int
    unique_titles: int


def run_normalization(connection, limit: int) -> NormalizeSummary:
    rows = fetch_unlinked_raw_postings(connection, limit)
    processed = len(rows)
    linked = 0
    skipped = 0
    unique_token_keys: set[str] = set()

    for row in rows:
        normalized = normalize_title(row["title"])
        if not normalized.usable:
            skipped += 1
            continue
        normalized_title_id = upsert_normalized_title(
            connection,
            normalized,
            first_seen_at=row["scraped_at"],
            last_seen_at=row["scraped_at"],
        )
        link_posting_to_title(
            connection,
            raw_job_posting_id=row["id"],
            normalized_title_id=normalized_title_id,
            raw_title=row["title"],
            normalized=normalized,
        )
        linked += 1
        unique_token_keys.add(normalized.token_key)

    connection.commit()
    return NormalizeSummary(
        processed=processed,
        linked=linked,
        skipped=skipped,
        unique_titles=len(unique_token_keys),
    )
