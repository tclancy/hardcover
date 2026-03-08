import pytest
from unittest.mock import patch
from cli.hardcover import fetch_want_to_read, fetch_in_dover_list, extract_author_name


def test_extract_author_name_from_contributions():
    contributions = [{"author": {"name": "Frank Herbert"}}]
    assert extract_author_name(contributions) == "Frank Herbert"


def test_extract_author_name_empty():
    assert extract_author_name([]) == "Unknown"


def test_extract_author_name_none_author():
    # Guard against a contribution entry with a null author field
    contributions = [{"author": None}]
    assert extract_author_name(contributions) == "Unknown"


def test_fetch_want_to_read_parses_response():
    fake_response = {
        "data": {
            "me": [
                {
                    "user_books": [
                        {
                            "book": {
                                "id": 1,
                                "title": "Dune",
                                "slug": "dune",
                                "contributions": [{"author": {"name": "Frank Herbert"}}],
                            }
                        }
                    ]
                }
            ]
        }
    }
    with patch("cli.hardcover._graphql_post", return_value=fake_response):
        books = fetch_want_to_read(token="fake")
    assert len(books) == 1
    assert books[0]["title"] == "Dune"
    assert books[0]["author"] == "Frank Herbert"
    assert books[0]["hardcover_id"] == 1
    assert books[0]["slug"] == "dune"


def test_fetch_want_to_read_missing_slug():
    """Books without a slug field should default to empty string."""
    fake_response = {
        "data": {
            "me": [
                {
                    "user_books": [
                        {
                            "book": {
                                "id": 2,
                                "title": "Foundation",
                                "contributions": [{"author": {"name": "Isaac Asimov"}}],
                            }
                        }
                    ]
                }
            ]
        }
    }
    with patch("cli.hardcover._graphql_post", return_value=fake_response):
        books = fetch_want_to_read(token="fake")
    assert books[0]["slug"] == ""


def test_fetch_want_to_read_empty_list():
    fake_response = {"data": {"me": [{"user_books": []}]}}
    with patch("cli.hardcover._graphql_post", return_value=fake_response):
        books = fetch_want_to_read(token="fake")
    assert books == []


def test_fetch_in_dover_list_parses_response():
    fake_response = {
        "data": {
            "me": [
                {
                    "lists": [
                        {
                            "list_books": [
                                {
                                    "book": {
                                        "id": 10,
                                        "title": "Brave New World",
                                        "slug": "brave-new-world",
                                        "contributions": [
                                            {"author": {"name": "Aldous Huxley"}}
                                        ],
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    with patch("cli.hardcover._graphql_post", return_value=fake_response):
        books = fetch_in_dover_list(token="fake", slug="in-dover")
    assert len(books) == 1
    assert books[0]["title"] == "Brave New World"
    assert books[0]["author"] == "Aldous Huxley"
    assert books[0]["hardcover_id"] == 10


def test_fetch_in_dover_list_no_matching_list():
    fake_response = {"data": {"me": [{"lists": []}]}}
    with patch("cli.hardcover._graphql_post", return_value=fake_response):
        books = fetch_in_dover_list(token="fake", slug="in-dover")
    assert books == []
