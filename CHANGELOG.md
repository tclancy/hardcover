# Changelog

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
