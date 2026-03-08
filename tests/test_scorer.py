from cli.scorer import score_match, strip_stop_words, normalize_title

def test_strip_stop_words_removes_articles():
    assert strip_stop_words("The Night Circus") == "Night Circus"
    assert strip_stop_words("A Tale of Two Cities") == "Tale Two Cities"
    assert strip_stop_words("Of Mice and Men") == "Mice Men"

def test_strip_stop_words_preserves_non_stop_words():
    assert strip_stop_words("Dune") == "Dune"

def test_normalize_title_lowercases_and_strips():
    assert normalize_title("  The DUNE  ") == "dune"

def test_perfect_match_scores_high():
    result = score_match(
        hc_title="Dune", hc_author="Frank Herbert",
        koha_title="Dune", koha_author="Herbert, Frank", koha_year=None
    )
    assert result > 0.9

def test_no_match_scores_low():
    result = score_match(
        hc_title="Dune", hc_author="Frank Herbert",
        koha_title="Foundation", koha_author="Asimov, Isaac", koha_year=None
    )
    assert result < 0.3

def test_close_title_scores_medium():
    result = score_match(
        hc_title="The Night Circus",  hc_author="Erin Morgenstern",
        koha_title="Night Circus", koha_author="Morgenstern, Erin", koha_year=None
    )
    assert result > 0.7

def test_author_last_name_match_boosts_score():
    with_author = score_match(
        hc_title="Dune", hc_author="Frank Herbert",
        koha_title="Dune", koha_author="Herbert, Frank", koha_year=None
    )
    without_author = score_match(
        hc_title="Dune", hc_author="Frank Herbert",
        koha_title="Dune", koha_author="Smith, John", koha_year=None
    )
    assert with_author > without_author
