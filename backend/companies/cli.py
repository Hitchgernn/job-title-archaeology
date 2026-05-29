import typer

from backend.companies.pipeline import recompute_company_signals
from backend.db.connection import open_connection
from backend.db.migrate import run_migrations

app = typer.Typer(help="Job Title Archaeology company commands")


@app.callback()
def main() -> None:
    pass


@app.command()
def recompute() -> None:
    connection = open_connection()
    try:
        run_migrations(connection)
        signals = recompute_company_signals(connection)
    finally:
        connection.close()

    typer.echo(f"recomputed {len(signals)} company signals")
    for signal in signals[:10]:
        ticker = signal.ticker or "—"
        typer.echo(f"  {ticker:5s} {signal.display_name[:40]:40s} {signal.recent_hires_30d:4d} recent · {signal.velocity_score:.2f}x")


if __name__ == "__main__":
    app()
