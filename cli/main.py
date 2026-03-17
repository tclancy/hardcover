import os
import random
import statistics
import typer
from dotenv import load_dotenv
from cli.db import (
    get_connection,
    init_db,
    upsert_book,
    upsert_in_dover,
    get_all_books,
    get_in_dover_books,
    record_decision,
)
from cli.dover import build_title_query, build_author_query, search
from cli.hardcover import (
    fetch_want_to_read,
    fetch_in_dover_list,
    fetch_in_dover_list_id,
    add_book_to_list,
)
from cli.scorer import score_match

load_dotenv()
app = typer.Typer(
    help="Dover Library CLI — check your Hardcover Want to Read list against Dover Public Library"
)

RESULT_THRESHOLD_FEW = 10  # ≤10 results: show them all
RESULT_THRESHOLD_MANY = 10  # >10: trigger phase 2
AUTO_CONFIRM_THRESHOLD = 0.82  # confidence >= this → auto-add without asking


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


def _best_score(results: list[dict], book: dict) -> tuple[float, dict | None]:
    """Return (best_score, best_result) for a list of Koha results against a book."""
    if not results:
        return 0.0, None
    scored = [
        (
            score_match(
                hc_title=book["title"],
                hc_author=book["author"],
                koha_title=r["title"],
                koha_author=r.get("author", ""),
                koha_year=r.get("year"),
            ),
            r,
        )
        for r in results
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0]


def _try_auto_add(
    book: dict,
    results: list[dict],
    query: str,
    conn,
    token: str,
    list_id: int,
) -> bool:
    """Auto-add if best match meets threshold. Returns True if auto-added."""
    best_score, best_result = _best_score(results, book)
    if best_score < AUTO_CONFIRM_THRESHOLD or best_result is None:
        return False
    ok = add_book_to_list(token, list_id, book["hardcover_id"])
    if ok:
        record_decision(
            conn,
            hardcover_id=book["hardcover_id"],
            koha_title=best_result["title"],
            koha_author=best_result.get("author"),
            confirmed=True,
            confidence=best_score,
            search_query=query,
        )
        typer.echo(
            f"  Auto-added: {best_result['title']} "
            f"(score={best_score:.2f} ≥ {AUTO_CONFIRM_THRESHOLD})"
        )
    else:
        typer.echo(
            f"  High-confidence match found (score={best_score:.2f}) "
            "but Hardcover API call failed — skipping auto-add."
        )
    return True


def _setup_auto_add(auto_add: bool, token: str) -> tuple[bool, int | None]:
    """Resolve list_id for auto-add; returns (enabled, list_id)."""
    if not auto_add:
        return False, None
    list_id = fetch_in_dover_list_id(token)
    if list_id is None:
        typer.echo("Warning: Could not fetch In Dover list ID — auto-add disabled.")
        return False, None
    return True, list_id


def _present_results(
    results: list[dict], book: dict, query: str, conn, token: str, list_id: int | None
) -> None:
    """Auto-add if threshold met; otherwise prompt the user."""
    if list_id and _try_auto_add(book, results, query, conn, token, list_id):
        return
    _ask_user(results, book, query, conn)


@app.command()
def check(
    auto_add: bool = typer.Option(
        True, "--auto-add/--no-auto-add", help="Auto-add high-confidence matches to In Dover list"
    ),
):
    """Pick a random book from Want to Read and search Dover Library."""
    token = _get_token() if auto_add else ""
    conn = get_connection()
    init_db(conn)
    books = get_all_books(conn)

    if not books:
        typer.echo("No books cached. Run `dover sync` first.")
        raise typer.Exit(1)

    auto_add, list_id = _setup_auto_add(auto_add, token)

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
        _present_results(results1, book, q1, conn, token, list_id)
        return

    # Phase 2: title + author last name
    typer.echo(f"  Too many results ({len(results1)}), trying phase 2...")
    q2 = build_author_query(book["title"], book["author"])
    typer.echo("Phase 2 search (title + author)...")
    results2 = search(q2)
    typer.echo(f"  {len(results2)} result(s)")

    if len(results2) <= RESULT_THRESHOLD_FEW:
        _present_results(results2, book, q2, conn, token, list_id)
        return

    # Still too many — sort by score and present
    typer.echo(f"  Still many results — showing all {len(results2)} sorted by confidence:")
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
    _present_results(scored, book, q2, conn, token, list_id)


def _print_calibration_report(scores: list[float], failed: list[str]) -> None:
    """Print score distribution and threshold coverage table."""
    typer.echo("\n" + "═" * 50)
    typer.echo("CALIBRATION RESULTS")
    typer.echo("═" * 50)
    if not scores:
        typer.echo("No results found for any book. Cloudflare may be blocking headless mode.")
        typer.echo("Try running: dover calibrate --no-headless")
        return
    typer.echo(f"Books with results:  {len(scores)}")
    typer.echo(f"Books with no hits:  {len(failed)}")
    typer.echo(f"Min score:  {min(scores):.2f}")
    typer.echo(f"Max score:  {max(scores):.2f}")
    typer.echo(f"Mean score: {statistics.mean(scores):.2f}")
    typer.echo(f"Median:     {statistics.median(scores):.2f}")
    if len(scores) >= 2:
        typer.echo(f"Stdev:      {statistics.stdev(scores):.2f}")
    typer.echo("\nCoverage at various thresholds:")
    for threshold in (0.90, 0.85, 0.82, 0.80, 0.75, 0.70):
        captured = sum(1 for s in scores if s >= threshold)
        pct = 100 * captured / len(scores)
        marker = " ← current" if threshold == AUTO_CONFIRM_THRESHOLD else ""
        typer.echo(f"  ≥{threshold:.2f}: {captured}/{len(scores)} ({pct:.0f}%){marker}")


def _search_with_fallback(book: dict, headless: bool) -> list[dict]:
    """Search by title; fall back to title+author if no results."""
    results = search(build_title_query(book["title"]), headless=headless)
    if not results:
        results = search(build_author_query(book["title"], book["author"]), headless=headless)
    return results


@app.command()
def calibrate(
    headless: bool = typer.Option(
        True,
        "--headless/--no-headless",
        help="Use headless browser (faster; may be blocked by Cloudflare WAF)",
    ),
):
    """Run all In Dover books through library search and report confidence score distribution.

    Uses the 67-book In Dover list as verified positives to find a reliable
    auto-confirm threshold. Run this after fixing the title parser to see real scores.
    """
    conn = get_connection()
    init_db(conn)
    books = get_in_dover_books(conn)

    if not books:
        typer.echo("No In Dover books cached. Run `dover sync` first.")
        raise typer.Exit(1)

    typer.echo(f"Calibrating against {len(books)} In Dover books...")
    if headless:
        typer.echo("  (headless mode — if scores are all 0, try --no-headless)")
    typer.echo("─" * 50)

    scores: list[float] = []
    failed: list[str] = []

    for i, book in enumerate(books, 1):
        typer.echo(f"[{i}/{len(books)}] {book['title']}")
        results = _search_with_fallback(book, headless)
        if not results:
            typer.echo("    no results")
            failed.append(book["title"])
            continue
        best, _ = _best_score(results, book)
        scores.append(best)
        typer.echo(f"    best score: {best:.2f}")

    _print_calibration_report(scores, failed)
