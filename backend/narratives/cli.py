import typer

from backend.db.connection import open_connection
from backend.narratives.pipeline import generate_narrative_cards
from backend.narratives.providers import GeminiNarrativeProvider

app = typer.Typer(help="Job Title Archaeology narrative commands")


@app.callback()
def main() -> None:
    pass


@app.command()
def generate(limit: int = typer.Option(5, "--limit", min=1)) -> None:
    connection = open_connection()
    try:
        provider = GeminiNarrativeProvider()
        cards = generate_narrative_cards(connection, provider=provider, limit=limit)
    finally:
        connection.close()

    if not cards:
        typer.echo("no trends found")
        return

    for index, card in enumerate(cards, start=1):
        typer.echo(f"{index}. {card.title}")
        typer.echo(card.text)
        typer.echo("")


if __name__ == "__main__":
    app()
