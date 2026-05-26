import json
from datetime import UTC, datetime, timedelta

from backend.db.migrate import run_migrations
from backend.normalize.pipeline import run_normalization

DEMO_RUN_ID = "demo-seed-2026-05-24"

DEMO_TITLES = [
    ("AI Workflow Architect", "Acme", "Technology", 1),
    ("AI Workflow Architect", "Globex", "Finance", 2),
    ("AI Workflow Architect", "Northstar", "Healthcare", 3),
    ("AI Workflow Architect", "Atlas", "Retail", 4),
    ("Agent Operations Lead", "Acme", "Technology", 1),
    ("Agent Operations Lead", "Beacon", "Logistics", 2),
    ("Agent Operations Lead", "Helio", "Energy", 3),
    ("LLM Reliability Engineer", "Northstar", "Healthcare", 1),
    ("LLM Reliability Engineer", "Atlas", "Retail", 2),
    ("LLM Reliability Engineer", "Cobalt", "Manufacturing", 3),
    ("Prompt Systems Analyst", "DeltaWorks", "Consulting", 4),
    ("Automation Governance Manager", "Evergreen", "Insurance", 5),
]

PRIOR_TITLES = [
    ("Data Analyst", "LegacyCo", "Technology", 15),
    ("Product Manager", "LegacyCo", "Technology", 18),
]


def is_sqlite_connection(connection) -> bool:
    return connection.__class__.__module__.startswith("sqlite3")


def placeholder(connection) -> str:
    return "?" if is_sqlite_connection(connection) else "%s"


def raw_payload(title: str, company: str, industry: str) -> dict[str, str]:
    return {
        "job_title": title,
        "company_name": company,
        "industry": industry,
        "source": "synthetic_demo_seed",
    }


def insert_postings(connection, postings: list[tuple[str, str, str, int]]) -> None:
    value_placeholder = placeholder(connection)
    sql = f"""
    INSERT INTO raw_job_postings (source, source_run_id, scraped_at, title, company, raw)
    VALUES ({value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder}, {value_placeholder})
    """
    now = datetime.now(UTC)
    cursor = connection.cursor()
    try:
        for title, company, industry, days_ago in postings:
            payload = raw_payload(title, company, industry)
            raw = json.dumps(payload) if is_sqlite_connection(connection) else payload
            cursor.execute(
                sql,
                (
                    "synthetic_demo_seed",
                    DEMO_RUN_ID,
                    (now - timedelta(days=days_ago)).isoformat(),
                    title,
                    company,
                    raw,
                ),
            )
    finally:
        cursor.close()


def delete_existing_seed(connection) -> None:
    value_placeholder = placeholder(connection)
    cursor = connection.cursor()
    try:
        cursor.execute(f"DELETE FROM raw_job_postings WHERE source_run_id = {value_placeholder}", (DEMO_RUN_ID,))
    finally:
        cursor.close()


def seed_demo_data(connection) -> dict[str, int]:
    run_migrations(connection)
    delete_existing_seed(connection)
    insert_postings(connection, DEMO_TITLES + PRIOR_TITLES)
    connection.commit()
    summary = run_normalization(connection, limit=1000)
    connection.commit()
    return {
        "raw_postings": len(DEMO_TITLES) + len(PRIOR_TITLES),
        "linked_titles": summary.linked,
        "unique_titles": summary.unique_titles,
    }


def main() -> None:
    from backend.db.connection import open_connection

    connection = open_connection()
    try:
        summary = seed_demo_data(connection)
    finally:
        connection.close()
    print(f"seeded raw_postings={summary['raw_postings']} linked_titles={summary['linked_titles']} unique_titles={summary['unique_titles']}")


if __name__ == "__main__":
    main()
