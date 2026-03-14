import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent / "data" / "hardcover.db"


def get_connection(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            hardcover_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            slug TEXT,
            synced_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS in_dover (
            hardcover_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            slug TEXT,
            synced_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardcover_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            phase INTEGER NOT NULL,
            result_count INTEGER NOT NULL,
            searched_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (hardcover_id) REFERENCES books(hardcover_id)
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardcover_id INTEGER NOT NULL,
            koha_title TEXT,
            koha_author TEXT,
            confirmed INTEGER NOT NULL,
            confidence REAL,
            search_query TEXT,
            decided_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (hardcover_id) REFERENCES books(hardcover_id)
        );
    """)
    conn.commit()


def upsert_book(
    conn: sqlite3.Connection, *, hardcover_id: int, title: str, author: str, slug: str
) -> None:
    conn.execute(
        """
        INSERT INTO books (hardcover_id, title, author, slug, synced_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(hardcover_id) DO UPDATE SET
            title=excluded.title,
            author=excluded.author,
            slug=excluded.slug,
            synced_at=excluded.synced_at
    """,
        (hardcover_id, title, author, slug),
    )
    conn.commit()


def upsert_in_dover(
    conn: sqlite3.Connection, *, hardcover_id: int, title: str, author: str, slug: str
) -> None:
    conn.execute(
        """
        INSERT INTO in_dover (hardcover_id, title, author, slug, synced_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(hardcover_id) DO UPDATE SET
            title=excluded.title,
            author=excluded.author,
            slug=excluded.slug,
            synced_at=excluded.synced_at
    """,
        (hardcover_id, title, author, slug),
    )
    conn.commit()


def get_all_books(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM books").fetchall()]


def get_in_dover_books(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM in_dover").fetchall()]


def record_decision(
    conn: sqlite3.Connection,
    *,
    hardcover_id: int,
    koha_title: str | None,
    koha_author: str | None,
    confirmed: bool,
    confidence: float | None,
    search_query: str,
) -> None:
    conn.execute(
        """
        INSERT INTO decisions (hardcover_id, koha_title, koha_author, confirmed, confidence, search_query)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            hardcover_id,
            koha_title,
            koha_author,
            int(confirmed),
            confidence,
            search_query,
        ),
    )
    conn.commit()


def get_decisions_for_book(
    conn: sqlite3.Connection, *, hardcover_id: int
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM decisions WHERE hardcover_id = ? ORDER BY decided_at DESC",
        (hardcover_id,),
    ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["confirmed"] = bool(d["confirmed"])
        result.append(d)
    return result
