# Changelog

## 2026-03-03
- Initial userscript: `hardcover-library-linker.user.js`
- Injects `📚 lib` badge after each book title and author link on Hardcover shelf pages
- Title links search Dover Public Library by title; author links search by "Last, First"
- Uses href-pattern detection (`/books/`, `/authors/`) instead of fragile class selectors
- MutationObserver handles SPA navigation and lazy-loaded content
- README with installation instructions and library URL patterns
