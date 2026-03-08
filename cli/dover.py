"""Dover Public Library (Koha OPAC) search client.

Selectors are based on the Koha MARC21slim2OPACResults.xsl XSLT output:
  - Title:   a.title
  - Author:  ul.author (class "author resource_list") → first li text
  - Year:    span.publisher_date
  - Container: td.bibliocol (wraps each result's XSLT output in the results table)
"""

import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from cli.scorer import strip_stop_words

KOHA_BASE = "https://librarycatalog.dover.nh.gov/cgi-bin/koha/opac-search.pl"
KOHA_LIMITS = "&limit=itype%3ABK&limit=branch%3ADOVER"

# CSS selectors verified against Koha XSLT output (MARC21slim2OPACResults.xsl)
RESULT_CONTAINER = "td.bibliocol"
TITLE_SELECTOR = "a.title"
AUTHOR_SELECTOR = "ul.author"
YEAR_SELECTOR = "span.publisher_date"


def strip_stop_words_from_query(title: str) -> str:
    """Strip common stop words from a title string."""
    return strip_stop_words(title)


def build_title_query(title: str) -> str:
    """Build a Koha search URL for a title-only search (stop words stripped)."""
    clean = strip_stop_words_from_query(title)
    return f"{KOHA_BASE}?q={quote_plus(clean)}{KOHA_LIMITS}"


def build_author_query(title: str, author: str) -> str:
    """Build a Koha search URL combining stop-word-stripped title and author last name."""
    clean_title = strip_stop_words_from_query(title)
    # Handle both "First Last" and "Last, First" formats
    author = author.strip()
    if "," in author:
        last = author.split(",")[0].strip()
    else:
        parts = author.split()
        last = parts[-1] if parts else author
    query = f"{clean_title} {last}"
    return f"{KOHA_BASE}?q={quote_plus(query)}{KOHA_LIMITS}"


def parse_search_results(html: str) -> list[dict]:
    """Parse Koha OPAC search results HTML into a list of result dicts.

    Each dict has keys:
      - title (str)
      - author (str)
      - year (int | None)
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for container in soup.select(RESULT_CONTAINER):
        title_el = container.select_one(TITLE_SELECTOR)
        author_el = container.select_one(AUTHOR_SELECTOR)
        year_el = container.select_one(YEAR_SELECTOR)

        title = title_el.get_text(strip=True) if title_el else ""
        author = author_el.get_text(separator=", ", strip=True) if author_el else ""

        year: int | None = None
        if year_el:
            text = year_el.get_text(strip=True)
            m = re.search(r"\b(19|20)\d{2}\b", text)
            if m:
                year = int(m.group())

        if title:
            results.append({"title": title, "author": author, "year": year})

    return results


def search(query_url: str) -> list[dict]:
    """Fetch a Koha search URL using a headless browser and return parsed results."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(query_url, wait_until="domcontentloaded", timeout=15000)
            # Wait for results container or no-results message
            try:
                page.wait_for_selector("td.bibliocol, #noresults, .alert-info", timeout=8000)
            except Exception:
                pass  # proceed and parse whatever we got
            html = page.content()
        finally:
            browser.close()
    return parse_search_results(html)
