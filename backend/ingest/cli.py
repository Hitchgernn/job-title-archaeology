from pathlib import Path

import typer

from backend.ingest.config import EnvSettings, load_collection_config
from backend.ingest.pipeline import run_collection
from backend.ingest.sources.brightdata import BrightDataClient

app = typer.Typer(help="Job Title Archaeology ingestion commands")


@app.callback()
def main() -> None:
    pass


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


if __name__ == "__main__":
    app()
