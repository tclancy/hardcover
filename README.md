# Hardcover → Dover Library Tools

Tools for checking whether books on your Hardcover "Want to Read" list are available at the Dover Public Library.

## v2: Dover CLI (`dover`)

An interactive Python CLI that picks a random book from your Hardcover list, searches the Dover Library catalog, and records match decisions with confidence scoring.

### Setup

```bash
cd ~/Documents/work/hardcover
uv sync
uv run playwright install chromium
cp .env.example .env  # add your Hardcover API token
```

### Usage

```bash
# Fetch your Hardcover book lists and cache locally
uv run dover sync

# Pick a random book and search Dover Library
uv run dover check
```

`check` runs a two-phase search:
1. **Phase 1**: Title-only search (stop words stripped)
2. **Phase 2**: Title + author last name (if Phase 1 returns too many results)

Results are shown with a confidence score (0.0-1.0) based on title similarity, author match, and publication year. You pick the correct match or skip.

All decisions are stored in a local SQLite database (`data/hardcover.db`) for future analysis and weight calibration.

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Hardcover API token (get yours at https://hardcover.app/account/api)
- Chromium (installed via Playwright for Cloudflare bypass)

---

## v1: Browser Userscript

A Tampermonkey userscript that adds Dover Public Library search links next to book titles and author names on Hardcover shelf pages.

### What It Does

On `https://hardcover.app/@tclancy/books/want-to-read` (and any other Hardcover shelf page), the script injects a small `📚 lib` badge after each book title and author name. Clicking a badge opens a library catalog search in a new tab.

### Installation

1. Install [Tampermonkey](https://www.tampermonkey.net/) in Chrome/Firefox/Edge.
2. Click the Tampermonkey icon → **Create a new script**.
3. Delete the default content and paste the contents of `hardcover-library-linker.user.js`.
4. Save (Cmd+S or Ctrl+S).
5. Navigate to your Hardcover Want to Read page — links should appear automatically.

---

## Library URL Patterns

Both tools use Dover Public Library's Koha catalog:

| Search type | URL pattern |
|---|---|
| By title | `https://librarycatalog.dover.nh.gov/cgi-bin/koha/opac-search.pl?q=TITLE+ENCODED` |
| By author | `https://librarycatalog.dover.nh.gov/cgi-bin/koha/opac-search.pl?q=au%3A%22Last%2C+First%22` |

## Known Limitations

- The Dover catalog is behind Cloudflare WAF — the CLI uses a headed (non-headless) Chromium browser to bypass this, which briefly flashes a window offscreen during each search
- Koha's search engine has no concept of stop words, so common words like "The" or "A" produce noisy results — the CLI strips these before searching
- Real-time availability is not checked — results show catalog entries, not current checkout status
