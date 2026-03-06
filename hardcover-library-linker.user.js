// ==UserScript==
// @name         Hardcover → Dover Library Linker
// @namespace    https://github.com/tclancy/hardcover-library-linker
// @version      1.1.0
// @description  Adds Dover Public Library search links next to book titles and authors on Hardcover bookshelf pages
// @author       Tom Clancy
// @match        https://hardcover.app/@*/books/*
// @match        https://hardcover.app/books/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // ── Library search URL builder ──────────────────────────────────────────────
  const LIBRARY_BASE = 'https://librarycatalog.dover.nh.gov/cgi-bin/koha/opac-search.pl';

  function libraryTitleUrl(title) {
    return LIBRARY_BASE + '?q=' + encodeURIComponent(title) + '&limit=itype:BK';
  }

  function libraryAuthorUrl(author) {
    // Koha prefers "Last, First" for author searches
    const formatted = formatAuthorForSearch(author);
    return LIBRARY_BASE + '?q=au%3A%22' + encodeURIComponent(formatted) + '%22';
  }

  function formatAuthorForSearch(name) {
    // If already "Last, First" leave it alone
    if (name.includes(',')) return name.trim();
    // Convert "First Last" → "Last, First"
    const parts = name.trim().split(/\s+/);
    if (parts.length < 2) return name.trim();
    const last = parts[parts.length - 1];
    const first = parts.slice(0, -1).join(' ');
    return last + ', ' + first;
  }

  // ── Link injection ───────────────────────────────────────────────────────────
  const INJECTED_ATTR = 'data-dover-injected';
  const LINK_STYLE = [
    'display:inline-block',
    'margin-left:5px',
    'padding:1px 5px',
    'font-size:0.7em',
    'line-height:1.4',
    'background:#e8f4ec',
    'color:#2a6049',
    'border:1px solid #9dc8b0',
    'border-radius:3px',
    'text-decoration:none',
    'vertical-align:middle',
    'white-space:nowrap',
    'font-weight:normal',
  ].join(';');

  function makeLibLink(href, label) {
    const a = document.createElement('a');
    a.href = href;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.textContent = label;
    a.setAttribute('style', LINK_STYLE);
    a.setAttribute('title', 'Search Dover Public Library');
    return a;
  }

  function injectAfter(el, link) {
    el.parentNode.insertBefore(link, el.nextSibling);
  }

  // ── Selector strategies ──────────────────────────────────────────────────────
  //
  // Hardcover is a React + Inertia.js SPA with Tailwind CSS.
  // Class names may be hashed/purged so we find elements by their href patterns:
  //   - Book links:   href="/books/<slug>"
  //   - Author links (detail pages): href="/authors/<slug>" or "/contributors/<slug>"
  //   - Author bylines (bookshelf pages): no anchor — a span.flex-inline containing
  //     a child span with "By" text, followed by a sibling span with the author name.
  //
  //     Example DOM structure:
  //       <span class="flex-inline flex-row flex-wrap leading-5">
  //         <span class="text-md mr-1">By</span>
  //         <span class="flex-inline flex-row mr-1">   ← author name container
  //           <span class="flex-inline flex-row items-center">
  //             <span>Lucy Ellmann</span>
  //           </span>
  //         </span>
  //       </span>
  //
  // Strategy: find the "By" span, take its nextElementSibling, grab .innerText.

  function injectBookLinks() {
    // Book title links
    const bookAnchors = document.querySelectorAll(
      'a[href^="/books/"]:not([' + INJECTED_ATTR + '])'
    );
    bookAnchors.forEach((anchor) => {
      const title = anchor.textContent.trim();
      if (!title || title.length < 2) return;
      anchor.setAttribute(INJECTED_ATTR, '1');
      const link = makeLibLink(libraryTitleUrl(title), '📚 lib');
      injectAfter(anchor, link);
    });

    // Author links (detail/author pages — anchor-based)
    const authorAnchors = document.querySelectorAll(
      'a[href^="/authors/"]:not([' + INJECTED_ATTR + ']), a[href^="/contributors/"]:not([' + INJECTED_ATTR + '])'
    );
    authorAnchors.forEach((anchor) => {
      const author = anchor.textContent.trim();
      if (!author || author.length < 2) return;
      anchor.setAttribute(INJECTED_ATTR, '1');
      const link = makeLibLink(libraryAuthorUrl(author), '📚 lib');
      injectAfter(anchor, link);
    });

    // Author bylines (bookshelf pages — span-based, no anchor)
    // Find every span whose direct text content is "By" or starts with "By"
    // then take the next sibling span as the author name container.
    const allSpans = document.querySelectorAll('span:not([' + INJECTED_ATTR + '])');
    allSpans.forEach((span) => {
      if (span.children.length > 0) return;
      const text = span.textContent.trim();
      if (text !== 'By' && !text.startsWith('By ')) return;

      const authorContainer = span.nextElementSibling;
      if (!authorContainer) return;

      const author = authorContainer.innerText.trim();
      if (!author || author.length < 2) return;

      span.setAttribute(INJECTED_ATTR, '1');
      const link = makeLibLink(libraryAuthorUrl(author), '📚 lib');
      authorContainer.parentNode.insertBefore(link, authorContainer.nextSibling);
    });
  }

  // ── MutationObserver: handles SPA navigation and lazy-loaded content ─────────
  let debounceTimer = null;

  function scheduleInject() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(injectBookLinks, 300);
  }

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.addedNodes.length > 0) {
        scheduleInject();
        break;
      }
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // ── Initial run ──────────────────────────────────────────────────────────────
  // Run once after DOM is ready; MutationObserver handles everything after that.
  injectBookLinks();
})();
