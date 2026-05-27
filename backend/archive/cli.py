import typer

from backend.archive.llm import generate_archive_metadata
from backend.archive.prompts import PROMPT_VERSION
from backend.archive.repository import fetch_cached_metadata, metadata_input_hash, upsert_cached_metadata
from backend.archive.router import ARCHIVE_SOURCE
from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.narratives.providers import GeminiNarrativeProvider
from backend.trends.pipeline import run_trend_scoring

app = typer.Typer(help="Job Title Archaeology archive commands")


@app.callback()
def main() -> None:
    pass


@app.command()
def generate(
    limit: int = typer.Option(10, "--limit", min=1, max=50),
    force: bool = typer.Option(False, "--force"),
) -> None:
    connection = open_connection()
    generated = 0
    skipped = 0
    try:
        run_migrations(connection)
        provider = GeminiNarrativeProvider()
        trends = run_trend_scoring(connection, limit=limit, source=ARCHIVE_SOURCE)
        cached = {} if force else fetch_cached_metadata(connection, [trend.normalized_title_id for trend in trends], PROMPT_VERSION)
        for trend in trends:
            if trend.normalized_title_id in cached:
                skipped += 1
                continue
            metadata = generate_archive_metadata(trend, provider)
            upsert_cached_metadata(
                connection,
                trend.normalized_title_id,
                PROMPT_VERSION,
                provider.__class__.__name__,
                provider.model,
                metadata_input_hash(trend),
                metadata,
            )
            generated += 1
        connection.commit()
    finally:
        connection.close()

    typer.echo(f"cached archive metadata for {generated} titles; skipped {skipped}")


if __name__ == "__main__":
    app()
