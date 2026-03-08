import difflib
import re

STOP_WORDS = {"the", "a", "an", "of", "in", "and", "or", "to", "for", "with", "at", "by", "from", "on", "as"}

WEIGHTS = {
    "title_exact": 1.0,
    "title_fuzzy": 0.8,
    "author_last": 0.6,
    "year": 0.2,
}
TOTAL_WEIGHT = sum(WEIGHTS.values())


def strip_stop_words(title: str) -> str:
    words = title.split()
    filtered = [w for w in words if w.lower() not in STOP_WORDS]
    return " ".join(filtered) if filtered else title


def normalize_title(title: str) -> str:
    title = title.strip().lower()
    title = strip_stop_words(title)
    title = re.sub(r"[^\w\s]", "", title)
    return title


def _extract_last_name(author: str) -> str:
    """Handle both 'First Last' and 'Last, First' formats."""
    author = author.strip()
    if "," in author:
        return author.split(",")[0].strip().lower()
    parts = author.split()
    return parts[-1].lower() if parts else author.lower()


def score_match(*, hc_title: str, hc_author: str,
                koha_title: str, koha_author: str,
                koha_year: int | None, hc_year: int | None = None) -> float:
    norm_hc = normalize_title(hc_title)
    norm_koha = normalize_title(koha_title)

    title_exact = 1.0 if norm_hc == norm_koha else 0.0
    title_fuzzy = difflib.SequenceMatcher(None, norm_hc, norm_koha).ratio()

    hc_last = _extract_last_name(hc_author)
    koha_last = _extract_last_name(koha_author)
    author_last = 1.0 if hc_last == koha_last else 0.0

    year_score = 0.0
    if hc_year is not None and koha_year is not None:
        year_score = 1.0 if hc_year == koha_year else 0.0

    weighted = (
        WEIGHTS["title_exact"] * title_exact
        + WEIGHTS["title_fuzzy"] * title_fuzzy
        + WEIGHTS["author_last"] * author_last
        + WEIGHTS["year"] * year_score
    )
    return weighted / TOTAL_WEIGHT
