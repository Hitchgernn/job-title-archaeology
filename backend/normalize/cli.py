import typer

from backend.db.connection import open_connection
from backend.db.migrate import run_migrations
from backend.normalize.pipeline import run_normalization

app = typer.Typer(help="Job Title Archaeology normalization commands")


@app.callback()
def main() -> None:
    pass


@app.command()
def migrate() -> None:
    connection = open_connection()
    try:
        run_migrations(connection)
    finally:
        connection.close()
    typer.echo("migrations complete")


@app.command()
def normalize(limit: int = typer.Option(1000, "--limit", min=1)) -> None:
    connection = open_connection()
    try:
        summary = run_normalization(connection, limit=limit)
    finally:
        connection.close()
    typer.echo(
        f"processed={summary.processed} linked={summary.linked} skipped={summary.skipped} unique_titles={summary.unique_titles}"
    )


if __name__ == "__main__":
    app()
