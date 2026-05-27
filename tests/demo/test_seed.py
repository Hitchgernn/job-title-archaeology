from backend.db.connection import open_connection
from backend.demo.seed import DEMO_TITLES, seed_demo_data
from backend.trends.pipeline import run_trend_scoring


def test_demo_seed_includes_cross_sector_titles() -> None:
    titles = {title for title, _company, _industry, _days_ago in DEMO_TITLES}

    assert "Clinical AI Safety Officer" in titles
    assert "Robotics Fleet Coordinator" in titles
    assert "Algorithmic Accountability Officer" in titles


def test_seed_demo_data_creates_dashboard_trends(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'job_title_archaeology.db'}"
    connection = open_connection(database_url)
    try:
        summary = seed_demo_data(connection)
        trends = run_trend_scoring(connection, limit=5)
    finally:
        connection.close()

    assert summary["raw_postings"] >= 12
    assert summary["linked_titles"] >= 12
    assert len(trends) >= 3
    assert trends[0].recent_count > 0
    assert trends[0].trend_score > 0
    assert trends[0].early_mover_companies


def test_seed_demo_data_is_idempotent(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'job_title_archaeology.db'}"
    connection = open_connection(database_url)
    try:
        first = seed_demo_data(connection)
        second = seed_demo_data(connection)
        raw_count = connection.execute("SELECT COUNT(*) FROM raw_job_postings").fetchone()[0]
    finally:
        connection.close()

    assert first["raw_postings"] == second["raw_postings"]
    assert raw_count == first["raw_postings"]
