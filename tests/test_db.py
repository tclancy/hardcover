import pytest
from cli.db import (
    get_connection,
    init_db,
    upsert_book,
    upsert_in_dover,
    get_all_books,
    get_in_dover_books,
    record_decision,
    get_decisions_for_book,
)


@pytest.fixture
def db():
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


def test_init_creates_tables(db):
    tables = {
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"books", "in_dover", "searches", "decisions"}.issubset(tables)


def test_upsert_book_inserts(db):
    upsert_book(db, hardcover_id=1, title="Dune", author="Frank Herbert", slug="dune")
    books = get_all_books(db)
    assert len(books) == 1
    assert books[0]["title"] == "Dune"


def test_upsert_book_updates_existing(db):
    upsert_book(db, hardcover_id=1, title="Dune", author="Frank Herbert", slug="dune")
    upsert_book(
        db, hardcover_id=1, title="Dune: Updated", author="Frank Herbert", slug="dune"
    )
    books = get_all_books(db)
    assert len(books) == 1
    assert books[0]["title"] == "Dune: Updated"


def test_upsert_in_dover(db):
    upsert_in_dover(
        db, hardcover_id=2, title="Foundation", author="Isaac Asimov", slug="foundation"
    )
    rows = get_in_dover_books(db)
    assert len(rows) == 1


def test_record_and_fetch_decision(db):
    upsert_book(db, hardcover_id=1, title="Dune", author="Frank Herbert", slug="dune")
    record_decision(
        db,
        hardcover_id=1,
        koha_title="Dune",
        koha_author="Herbert, Frank",
        confirmed=True,
        confidence=0.95,
        search_query="Dune",
    )
    decisions = get_decisions_for_book(db, hardcover_id=1)
    assert len(decisions) == 1
    assert decisions[0]["confirmed"] is True
