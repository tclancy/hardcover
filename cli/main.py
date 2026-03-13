import os
import random
import typer
from dotenv import load_dotenv
from cli.db import (
    get_connection,
    init_db,
    upsert_book,
    upsert_in_dover,
    get_all_books,
    record_decision,
)
from cli.dover import build_title_query, build_author_query, search
from cli.hardcover import fetch_want_to_read, fetch_in_dover_list
from cli.scorer import score_match

load_dotenv()
app = typer.Typer(
    help="Dover Library CLI — check your Hardcover Want to Read list against Dover Public Library"
)

RESULT_THRESHOLD_FEW = 10  # ≤10 results: show them all
RESULT_THRESHOLD_MANY = 10  # >10: trigger phase 2


@app.callback()
def main():
    """Dover Library CLI — check your Hardcover Want to Read list against Dover Public Library."""


def _get_token() -> str:
    token = os.environ.get("HARDCOVER_TOKEN", "")
    if not token:
        typer.echo(
            "Error: HARDCOVER_TOKEN not set. Add it to .env or export it.", err=True
        )
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


def _display_results(results: list[dict], book: dict, limit: int | None = None) -> None:
    display = results[:limit] if limit else results
    for i, r in enumerate(display, 1):
        score = score_match(
            hc_title=book["title"],
            hc_author=book["author"],
            koha_title=r["title"],
            koha_author=r.get("author", ""),
            koha_year=r.get("year"),
        )
        typer.echo(
            f"  [{i}] {r['title']} — {r.get('author', 'Unknown')} ({r.get('year', '?')})  score={score:.2f}"
        )


def _ask_user(results: list[dict], book: dict, query: str, conn) -> None:
    if not results:
        typer.echo("  No results found.")
        record_decision(
            conn,
            hardcover_id=book["hardcover_id"],
            koha_title=None,
            koha_author=None,
            confirmed=False,
            confidence=None,
            search_query=query,
        )
        return

    _display_results(results, book)
    choice = (
        typer.prompt("Enter result number to confirm match, or 's' to skip")
        .strip()
        .lower()
    )

    if choice == "s" or choice == "":
        record_decision(
            conn,
            hardcover_id=book["hardcover_id"],
            koha_title=None,
            koha_author=None,
            confirmed=False,
            confidence=None,
            search_query=query,
        )
        typer.echo("  Skipped.")
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                picked = results[idx]
                score = score_match(
                    hc_title=book["title"],
                    hc_author=book["author"],
                    koha_title=picked["title"],
                    koha_author=picked.get("author", ""),
                    koha_year=picked.get("year"),
                )
                record_decision(
                    conn,
                    hardcover_id=book["hardcover_id"],
                    koha_title=picked["title"],
                    koha_author=picked.get("author"),
                    confirmed=True,
                    confidence=score,
                    search_query=query,
                )
                typer.echo(f"  Confirmed: {picked['title']} (score={score:.2f})")
            else:
                typer.echo("  Invalid choice, skipping.")
        except ValueError:
            typer.echo("  Invalid choice, skipping.")


@app.command()
def check():
    """Pick a random book from Want to Read and search Dover Library."""
    conn = get_connection()
    init_db(conn)
    books = get_all_books(conn)

    if not books:
        typer.echo("No books cached. Run `dover sync` first.")
        raise typer.Exit(1)

    book = random.choice(books)
    typer.echo(f'\nChecking: "{book["title"]}" by {book["author"]}')
    typer.echo("─" * 50)

    # Phase 1: title only
    q1 = build_title_query(book["title"])
    typer.echo("Phase 1 search (title only)...")
    results1 = search(q1)
    typer.echo(f"  {len(results1)} result(s)")

    if len(results1) == 0:
        typer.echo("  No results found — recording as not found.")
        record_decision(
            conn,
            hardcover_id=book["hardcover_id"],
            koha_title=None,
            koha_author=None,
            confirmed=False,
            confidence=None,
            search_query=q1,
        )
        return

    if len(results1) <= RESULT_THRESHOLD_FEW:
        _ask_user(results1, book, q1, conn)
        return

    # Phase 2: title + author last name
    typer.echo(f"  Too many results ({len(results1)}), trying phase 2...")
    q2 = build_author_query(book["title"], book["author"])
    typer.echo("Phase 2 search (title + author)...")
    results2 = search(q2)
    typer.echo(f"  {len(results2)} result(s)")

    if len(results2) <= RESULT_THRESHOLD_FEW:
        _ask_user(results2, book, q2, conn)
    else:
        # Still too many — show all results sorted by confidence score
        typer.echo(
            f"  Still many results — showing all {len(results2)} sorted by confidence:"
        )
        scored = sorted(
            results2,
            key=lambda r: score_match(
                hc_title=book["title"],
                hc_author=book["author"],
                koha_title=r["title"],
                koha_author=r.get("author", ""),
                koha_year=r.get("year"),
            ),
            reverse=True,
        )
        _ask_user(scored, book, q2, conn)
