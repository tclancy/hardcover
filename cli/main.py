import os
import random
import typer
from dotenv import load_dotenv
from pathlib import Path
from cli.db import get_connection, init_db, upsert_book, upsert_in_dover, get_all_books
from cli.hardcover import fetch_want_to_read, fetch_in_dover_list

load_dotenv()
app = typer.Typer(help="Dover Library CLI — check your Hardcover Want to Read list against Dover Public Library")


@app.callback()
def main():
    """Dover Library CLI — check your Hardcover Want to Read list against Dover Public Library."""


def _get_token() -> str:
    token = os.environ.get("HARDCOVER_TOKEN", "")
    if not token:
        typer.echo("Error: HARDCOVER_TOKEN not set. Add it to .env or export it.", err=True)
        raise typer.Exit(1)
    return token


@app.command()
def sync():
    """Fetch Want to Read and In Dover lists from Hardcover and cache locally."""
    token = _get_token()
    conn = get_connection()
    init_db(conn)

    typer.echo("Fetching Want to Read list...")
    want_to_read = fetch_want_to_read(token)
    for book in want_to_read:
        upsert_book(conn, **book)
    typer.echo(f"  Synced {len(want_to_read)} books.")

    typer.echo("Fetching In Dover list...")
    in_dover = fetch_in_dover_list(token)
    for book in in_dover:
        upsert_in_dover(conn, **book)
    typer.echo(f"  Synced {len(in_dover)} books in Dover list.")

    typer.echo("Done. Run `dover check` to start matching.")
