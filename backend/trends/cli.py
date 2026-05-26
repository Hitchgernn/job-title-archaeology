import typer

from backend.db.connection import open_connection
from backend.trends.pipeline import run_trend_scoring

app = typer.Typer(help="Job Title Archaeology trend commands")


@app.callback()
def main() -> None:
    pass


@app.command()
def score(limit: int = typer.Option(20, "--limit", min=1)) -> None:
    connection = open_connection()
    try:
        trends = run_trend_scoring(connection, limit=limit)
    finally:
        connection.close()

    if not trends:
        typer.echo("no trends found")
        return

    for index, trend in enumerate(trends, start=1):
        early_movers = ", ".join(trend.early_mover_companies)
        suffix = f" early_movers={early_movers}" if early_movers else ""
        typer.echo(
            f"{index}. {trend.display_title} — "
            f"score={trend.trend_score:.2f} "
            f"recent={trend.recent_count} "
            f"prior={trend.prior_count} "
            f"newness={trend.scores.newness:.2f} "
            f"velocity={trend.scores.velocity:.2f} "
            f"concentration={trend.scores.concentration:.2f}"
            f"{suffix}"
        )


if __name__ == "__main__":
    app()
