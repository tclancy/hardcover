# Changelog

## 2026-03-18

- fix: Handle Koha exact-match redirect to `opac-detail.pl` — `search()` was returning 0 results when Koha redirected to the detail page instead of a search results page
- feat: Add `parse_detail_page()` using Koha Bootstrap OPAC detail selectors; results carry `exact_match: True` for traceability
- 46 tests passing; branch: `claude/exact-match-search-5`; PR #6

## 2026-03-17

- fix: Title parsing bug — `get_text(separator=" ")` prevents MARC subfield spans running together; strip trailing `/ Author Name.` responsibility statement. Confidence scores for known positives should jump from ~0.42 to ~0.85–0.95.
- feat: Add `idx=ti` parameter to title queries to target Koha title index, reducing stop-word noise
- feat: Add `dover calibrate` command — searches all 67 In Dover books, reports score distribution and threshold coverage table; supports `--headless/--no-headless`
- feat: Auto-add high-confidence matches (≥0.82) to Hardcover In Dover list during `dover check`; add `--no-auto-add` flag to disable
- feat: Add `fetch_in_dover_list_id()` and `add_book_to_list()` to `cli/hardcover.py`
- 42 tests passing; branch: `claude/calibrate-and-auto-add-issue-3`; PR #4

## 2026-03-16

- research: Issue #3 — investigated confidence scoring and training set for Dover library matching
  - Found title parsing bug in `dover.py:68`: `get_text(strip=True)` merges MARC subfield spans without spaces; explains 0.40–0.44 scores on confirmed correct matches
  - Identified 67-book In Dover list as ready-made training set (no additional data collection needed)
  - Researched Koha/Zebra CCL syntax: `idx=ti` and `ti,phr:` phrase search improvements
  - Findings posted to issue #3; status → needs-response pending Tom's 3 answers

## 2026-03-13

- fix: Show all phase-2 results sorted by confidence when result count exceeds threshold — removes silent top-5 truncation that hid the correct match (issue #1: The Bat by Jo Nesbø)
- feat: Add tests/test_main.py with 6 tests covering check command result display logic
- 35 tests passing; branch: `claude/fix-all-results-issue-1`

## 2026-03-08

- v2: Dover CLI (`dover`) — interactive Python CLI for checking Want to Read books against Dover Library
- `dover sync` fetches Hardcover Want to Read and In Dover lists via GraphQL API, caches in SQLite
- `dover check` picks a random book, runs two-phase Koha search (title, then title+author), prompts for confirmation
- Weighted confidence scorer (title exact/fuzzy match, author last name, publication year)
- Playwright-based search to bypass Cloudflare WAF on the library catalog
- Local SQLite database tracks books, search results, and user match decisions

## 2026-03-06
- Fix author detection on bookshelf pages: Hardcover's bookshelf has no `<a>` tag for authors, only nested spans
- New strategy: find leaf `<span>` with "By" text, grab `nextElementSibling.innerText` for author name
- Both anchor-based (detail pages) and span-based (bookshelf) author detection now work
- Version bumped to 1.1.0

## 2026-03-03
- Initial userscript: `hardcover-library-linker.user.js`
- Injects `📚 lib` badge after each book title and author link on Hardcover shelf pages
- Title links search Dover Public Library by title; author links search by "Last, First"
- Uses href-pattern detection (`/books/`, `/authors/`) instead of fragile class selectors
- MutationObserver handles SPA navigation and lazy-loaded content
- README with installation instructions and library URL patterns
