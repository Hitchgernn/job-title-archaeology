import time
from pathlib import Path

import typer

from backend.archive.images import (
    GeminiImageProvider,
    build_archive_image_prompt,
    image_filename,
    save_image_bytes,
)
from backend.archive.llm import generate_archive_metadata
from backend.archive.prompts import PROMPT_VERSION
from backend.archive.repository import (
    fetch_cached_metadata,
    metadata_input_hash,
    update_cached_image,
    upsert_cached_metadata,
)
from backend.archive.router import ARCHIVE_SOURCE
from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.narratives.providers import GeminiNarrativeProvider, OpenRouterNarrativeProvider
from backend.trends.pipeline import run_trend_scoring

app = typer.Typer(help="Job Title Archaeology archive commands")


@app.callback()
def main() -> None:
    pass


@app.command()
def generate(
    limit: int = typer.Option(10, "--limit", min=1, max=200),
    force: bool = typer.Option(False, "--force"),
    provider_name: str = typer.Option("gemini", "--provider", help="gemini | openrouter"),
    request_delay: float = typer.Option(3.0, "--request-delay", help="seconds between requests"),
) -> None:
    connection = open_connection()
    generated = 0
    skipped = 0
    try:
        run_migrations(connection)
        if provider_name == "gemini":
            provider = GeminiNarrativeProvider()
        elif provider_name == "openrouter":
            provider = OpenRouterNarrativeProvider()
        else:
            raise typer.BadParameter(f"unsupported provider '{provider_name}'")
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
            connection.commit()
            generated += 1
            typer.echo(f"  [{generated}] {trend.display_title}")
            if request_delay > 0:
                time.sleep(request_delay)
    finally:
        connection.close()

    typer.echo(f"cached archive metadata for {generated} titles; skipped {skipped}")


@app.command("generate-images")
def generate_images(
    limit: int = typer.Option(10, "--limit", min=1, max=50),
    output_dir: Path = typer.Option(Path("frontend/public/archive-generated"), "--output-dir"),
    public_prefix: str = typer.Option("/archive-generated", "--public-prefix"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    connection = open_connection()
    generated = 0
    skipped = 0
    try:
        run_migrations(connection)
        provider = None
        trends = run_trend_scoring(connection, limit=limit, source=ARCHIVE_SOURCE)
        cached = fetch_cached_metadata(
            connection,
            [trend.normalized_title_id for trend in trends],
            PROMPT_VERSION,
        )
        for trend in trends:
            metadata = cached.get(trend.normalized_title_id)
            if metadata is None:
                skipped += 1
                continue
            if metadata.image_path and not force:
                skipped += 1
                continue
            if provider is None:
                provider = GeminiImageProvider()
            prompt = build_archive_image_prompt(trend, metadata)
            image_path = save_image_bytes(
                output_dir,
                image_filename(trend),
                provider.generate(prompt),
                public_prefix,
            )
            update_cached_image(
                connection,
                trend.normalized_title_id,
                PROMPT_VERSION,
                image_path,
                prompt,
                provider.__class__.__name__,
                provider.model,
            )
            generated += 1
        connection.commit()
    finally:
        connection.close()

    typer.echo(f"generated {generated} images; skipped {skipped}")


if __name__ == "__main__":
    app()
