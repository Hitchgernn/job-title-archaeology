import os
from pathlib import Path

import typer

from backend.ingest.config import EnvSettings, load_collection_config
from backend.ingest.pipeline import (
    build_indeed_inputs,
    build_linkedin_inputs,
    import_json_file,
    run_collection,
    run_keyword_collection,
)
from backend.ingest.sources.brightdata import BrightDataClient

app = typer.Typer(help="Job Title Archaeology ingestion commands")


@app.callback()
def main() -> None:
    pass


@app.command("import-json")
def import_json(
    source: Path = typer.Argument(..., exists=True, readable=True),
    run_id: str = typer.Option("brightdata-json-import", "--run-id"),
    output_dir: Path = typer.Option(Path("data/raw"), "--output-dir"),
) -> None:
    result = import_json_file(source, run_id, output_dir, os.getenv("DATABASE_URL"))

    typer.echo(f"Imported {result.record_count} records from {source}")
    typer.echo(f"Archive: {result.archive_path}")
    if result.postgres_inserted is not None:
        typer.echo(f"Database inserted: {result.postgres_inserted}")


@app.command()
def collect(config: Path = typer.Option(..., "--config", exists=True, readable=True)) -> None:
    collection_config = load_collection_config(config)
    env = EnvSettings()
    scraper_id = env.brightdata_web_scraper_id or collection_config.brightdata.dataset_id
    collection_config.brightdata.dataset_id = scraper_id
    client = BrightDataClient(env.brightdata_api_token, collection_config.brightdata.base_url)
    result = run_collection(client, collection_config, env.database_url)

    typer.echo(f"Collected {result.record_count} records from run {result.run_id}")
    typer.echo(f"Archive: {result.archive_path}")
    if result.postgres_inserted is not None:
        typer.echo(f"PostgreSQL inserted: {result.postgres_inserted}")


@app.command()
def discover(
    source: str = typer.Option(..., "--source", help="indeed | linkedin"),
    keywords: str = typer.Option(..., "--keywords", help="comma-separated keywords"),
    locations: str = typer.Option("United States", "--locations", help="comma-separated locations"),
    country: str = typer.Option("US", "--country"),
    output_dir: Path = typer.Option(Path("data/raw"), "--output-dir"),
    poll_delay_seconds: int = typer.Option(15, "--poll-delay-seconds"),
    max_poll_attempts: int = typer.Option(120, "--max-poll-attempts"),
    limit_per_input: int = typer.Option(None, "--limit-per-input", help="cap records per keyword/location pair"),
) -> None:
    env = EnvSettings()
    dataset_id = env.dataset_id_for(source)
    if not dataset_id:
        raise typer.BadParameter(f"missing dataset id for source '{source}' in env")

    keyword_list = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]
    location_list = [location.strip() for location in locations.split(",") if location.strip()]
    if not keyword_list:
        raise typer.BadParameter("keywords list is empty")
    if not location_list:
        raise typer.BadParameter("locations list is empty")

    if source == "indeed":
        inputs = build_indeed_inputs(keyword_list, location_list, country)
    elif source == "linkedin":
        inputs = build_linkedin_inputs(keyword_list, location_list, country)
    else:
        raise typer.BadParameter(f"unsupported source '{source}'")

    client = BrightDataClient(env.brightdata_api_token, "https://api.brightdata.com")
    result = run_keyword_collection(
        client,
        dataset_id=dataset_id,
        inputs=inputs,
        output_dir=output_dir,
        poll_delay_seconds=poll_delay_seconds,
        max_poll_attempts=max_poll_attempts,
        database_url=env.database_url,
        limit_per_input=limit_per_input,
    )

    typer.echo(f"Collected {result.record_count} records from run {result.run_id}")
    typer.echo(f"Archive: {result.archive_path}")
    if result.postgres_inserted is not None:
        typer.echo(f"Database inserted: {result.postgres_inserted}")


if __name__ == "__main__":
    app()
