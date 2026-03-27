// ==UserScript==
// @name         Hardcover → Dover Library Linker
// @namespace    https://github.com/tclancy/hardcover-library-linker
// @version      2.0.0
// @description  Adds Dover Public Library search links next to book titles and authors on Hardcover bookshelf, list, and book detail pages
// @author       Tom Clancy
// @match        https://hardcover.app/@*/books/*
// @match        https://hardcover.app/@*/lists/*
// @match        https://hardcover.app/books/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // ── Library search URL builder ──────────────────────────────────────────────
  const LIBRARY_BASE = 'https://librarycatalog.dover.nh.gov/cgi-bin/koha/opac-search.pl';

  function libraryTitleUrl(title) {
    return LIBRARY_BASE + '?q=' + encodeURIComponent(title) + '&limit=itype:BK&limit=branch%3ADOVER';
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

  // ── Page type detection ───────────────────────────────────────────────────────
  //
  // Hardcover is a React SPA — the URL changes on navigation without a full page
  // reload. We re-detect page type on every inject call so the MutationObserver
  // works correctly across SPA navigations.
  //
  //   user-page    /@user/books/* or /@user/lists/*  — bookshelf / reading lists
  //   book-detail  /books/slug (no sub-path)          — individual book page
  //   other                                            — skip injection

  function getPageType() {
    const path = window.location.pathname;
    if (/^\/@[^/]+\//.test(path)) return 'user-page';       // /@user/books/*, /@user/lists/*
    if (/^\/books\/[^/]+$/.test(path)) return 'book-detail'; // /books/slug only, not /books/slug/editions
    return 'other';
  }

  // ── Bookshelf / list page injection ─────────────────────────────────────────
  //
  // Strategy: find book title anchors by their /books/ href, find author bylines
  // by the leaf <span> with text "By" followed by a sibling author container.
  //
  // Why href-based (not class-based): Tailwind class names are stable-ish, but
  // href patterns (/books/slug) are tied to routes which are much more stable.

  function injectBookshelfLinks() {
    // Book title links: <a href="/books/slug"> with meaningful text content
    const bookAnchors = document.querySelectorAll(
      'a[href^="/books/"]:not([' + INJECTED_ATTR + '])'
    );
    bookAnchors.forEach((anchor) => {
      const title = anchor.textContent.trim();
      if (!title || title.length < 2) return;
      anchor.setAttribute(INJECTED_ATTR, '1');
      injectAfter(anchor, makeLibLink(libraryTitleUrl(title), '📚 lib'));
    });

    // Author bylines: leaf <span> with text "By", next sibling is the author container
    //
    // Example DOM (as of 2026-03-27):
    //   <span class="flex-inline flex-row flex-wrap leading-5">
    //     <span class="text-md mr-1">By</span>      ← find this
    //     <span class="flex-inline flex-row mr-1">   ← take .innerText of this
    //       <span class="flex-inline flex-row items-center">
    //         <span>Lucy Ellmann</span>
    //       </span>
    //     </span>
    //   </span>
    const allSpans = document.querySelectorAll('span:not([' + INJECTED_ATTR + '])');
    allSpans.forEach((span) => {
      if (span.children.length > 0) return; // must be a leaf span
      const text = span.textContent.trim();
      if (text !== 'By' && !text.startsWith('By ')) return;

      const authorContainer = span.nextElementSibling;
      if (!authorContainer) return;

      const author = authorContainer.innerText.trim();
      if (!author || author.length < 2) return;

      span.setAttribute(INJECTED_ATTR, '1');
      authorContainer.parentNode.insertBefore(
        makeLibLink(libraryAuthorUrl(author), '📚 lib'),
        authorContainer.nextSibling
      );
    });
  }

  // ── Book detail page injection ────────────────────────────────────────────────
  //
  // On detail pages (/books/slug), the tab navigation also uses a[href^="/books/"]
  // anchors ("Book Info", "Editions", "Lists") — we must NOT use that selector here
  // or we inject library links into the nav tabs.
  //
  // Instead:
  //   - Title: use <h1> — semantic, route-independent, unlikely to change
  //   - Authors: use a[href^="/authors/"] — URL-based, stable as long as routes hold

  function injectDetailLinks() {
    // Title: inject after the h1
    const h1 = document.querySelector('h1:not([' + INJECTED_ATTR + '])');
    if (h1) {
      const title = h1.textContent.trim();
      if (title && title.length >= 2) {
        h1.setAttribute(INJECTED_ATTR, '1');
        injectAfter(h1, makeLibLink(libraryTitleUrl(title), '📚 lib'));
      }
    }

    // Authors: <a href="/authors/..."> or <a href="/contributors/...">
    // These may appear more than once on the page; INJECTED_ATTR prevents duplicates.
    const authorAnchors = document.querySelectorAll(
      'a[href^="/authors/"]:not([' + INJECTED_ATTR + ']), ' +
      'a[href^="/contributors/"]:not([' + INJECTED_ATTR + '])'
    );
    authorAnchors.forEach((anchor) => {
      const author = anchor.textContent.trim();
      if (!author || author.length < 2) return;
      anchor.setAttribute(INJECTED_ATTR, '1');
      injectAfter(anchor, makeLibLink(libraryAuthorUrl(author), '📚 lib'));
    });
  }

  // ── Entry point: dispatch based on current page type ─────────────────────────
  function injectAll() {
    const type = getPageType();
    if (type === 'user-page') injectBookshelfLinks();
    else if (type === 'book-detail') injectDetailLinks();
    // 'other': no-op — sub-pages like /books/slug/editions, /books/slug/lists, etc.
  }

  // ── MutationObserver: handles SPA navigation and lazy-loaded content ─────────
  let debounceTimer = null;

  function scheduleInject() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(injectAll, 300);
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
  injectAll();
})();
