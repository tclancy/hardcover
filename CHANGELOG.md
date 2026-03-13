# Changelog

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
