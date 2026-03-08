# Hardcover → Dover Library Linker

A Tampermonkey userscript that adds Dover Public Library search links next to book titles and author names on your Hardcover Want to Read page.

## What It Does

On `https://hardcover.app/@tclancy/books/want-to-read` (and any other Hardcover shelf page), the script injects a small `📚 lib` badge after each book title and author name. Clicking a badge opens a library catalog search in a new tab.

- **Title link** → searches by book title
- **Author link** → searches by author name (formatted as "Last, First" for Koha)

## Installation

1. Install [Tampermonkey](https://www.tampermonkey.net/) in Chrome/Firefox/Edge if you haven't already.
2. Click the Tampermonkey icon → **Create a new script**.
3. Delete the default content and paste the contents of `hardcover-library-linker.user.js`.
4. Save (Cmd+S or Ctrl+S).
5. Navigate to your Hardcover Want to Read page — links should appear automatically.

## How It Works

Hardcover is a React + Inertia.js SPA with Tailwind CSS. Rather than relying on fragile class names, the script finds:
- `<a href="/books/...">` elements → book title links
- `<a href="/authors/...">` or `<a href="/contributors/...">` elements → author links

This is robust against Tailwind class purging/hashing and works after SPA navigation via a `MutationObserver`.

## Library URL Patterns

The script uses Dover Public Library's Koha catalog:

| Search type | URL pattern |
|---|---|
| By title | `https://librarycatalog.dover.nh.gov/cgi-bin/koha/opac-search.pl?q=TITLE+ENCODED` |
| By author | `https://librarycatalog.dover.nh.gov/cgi-bin/koha/opac-search.pl?q=au%3A%22Last%2C+First%22` |

To change the library, update `LIBRARY_BASE` in the script.

## Known Limitations

- Links appear wherever Hardcover renders `<a href="/books/...">` — this includes book detail pages, not just the shelf list. This is intentional; searching for any book from any page is useful.
- Real-time availability is not checked — the link opens the search results page where availability is shown.
- Hardcover is actively migrating from Next.js to Rails + Inertia.js (as of early 2026). If the script stops working, check whether book/author links still use `/books/` and `/authors/` href patterns.

## Updating

Edit the installed script via the Tampermonkey dashboard. Changes take effect on next page load.

## Notes

- Multiple authors
- skip emojis, etc. Ignore commas
- Drop articles from search text
