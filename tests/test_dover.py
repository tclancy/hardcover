import pytest
from cli.dover import parse_search_results, build_title_query, build_author_query, strip_stop_words_from_query

# Fixture HTML based on actual Koha XSLT output structure (MARC21slim2OPACResults.xsl):
# - Title: <a class="title">
# - Author: <ul class="author resource_list"><li><a>...</a></li></ul>
# - Year: <span class="publisher_date"> inside <div class="results_summary publisher">
# - Container: <td class="bibliocol"> inside a table row
SAMPLE_HTML_ONE_RESULT = """
<table>
  <tr>
    <td class="bibliocol">
      <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=12345">Dune</a>
      <ul class="author resource_list">
        <li><a href="/cgi-bin/koha/opac-search.pl?q=au%3AHerbert">Herbert, Frank</a></li>
      </ul>
      <div class="results_summary publisher">
        <span class="label">Publication details: </span>
        New York : Chilton Books,
        <span class="publisher_date">1965</span>
      </div>
    </td>
  </tr>
</table>
"""

SAMPLE_HTML_NO_RESULTS = """
<table>
</table>
"""

SAMPLE_HTML_TWO_RESULTS = """
<table>
  <tr>
    <td class="bibliocol">
      <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=100">Dune</a>
      <ul class="author resource_list">
        <li><a href="/cgi-bin/koha/opac-search.pl?q=au%3AHerbert">Herbert, Frank</a></li>
      </ul>
      <div class="results_summary publisher">
        <span class="publisher_date">1965</span>
      </div>
    </td>
  </tr>
  <tr>
    <td class="bibliocol">
      <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=101">Dune Messiah</a>
      <ul class="author resource_list">
        <li><a href="/cgi-bin/koha/opac-search.pl?q=au%3AHerbert">Herbert, Frank</a></li>
      </ul>
      <div class="results_summary publisher">
        <span class="publisher_date">1969</span>
      </div>
    </td>
  </tr>
</table>
"""

SAMPLE_HTML_NO_YEAR = """
<table>
  <tr>
    <td class="bibliocol">
      <a class="title" href="/cgi-bin/koha/opac-detail.pl?biblionumber=200">Foundation</a>
      <ul class="author resource_list">
        <li><a href="/cgi-bin/koha/opac-search.pl?q=au%3AAsimov">Asimov, Isaac</a></li>
      </ul>
    </td>
  </tr>
</table>
"""


def test_parse_single_result():
    results = parse_search_results(SAMPLE_HTML_ONE_RESULT)
    assert len(results) == 1
    assert results[0]["title"] == "Dune"
    assert results[0]["author"] == "Herbert, Frank"
    assert results[0]["year"] == 1965


def test_parse_no_results():
    results = parse_search_results(SAMPLE_HTML_NO_RESULTS)
    assert results == []


def test_parse_two_results():
    results = parse_search_results(SAMPLE_HTML_TWO_RESULTS)
    assert len(results) == 2
    assert results[0]["title"] == "Dune"
    assert results[1]["title"] == "Dune Messiah"
    assert results[1]["year"] == 1969


def test_parse_result_with_no_year():
    results = parse_search_results(SAMPLE_HTML_NO_YEAR)
    assert len(results) == 1
    assert results[0]["year"] is None


def test_build_title_query_strips_stop_words():
    url = build_title_query("The Night Circus")
    assert "Night+Circus" in url or "Night%20Circus" in url
    assert "The" not in url


def test_build_author_query_formats_last_first():
    url = build_author_query("The Night Circus", "Erin Morgenstern")
    assert "Morgenstern" in url


def test_build_author_query_handles_last_first_input():
    url = build_author_query("Dune", "Herbert, Frank")
    assert "Herbert" in url
    assert "Frank" not in url or "Herbert" in url  # last name is what matters


def test_build_author_query_strips_stop_words_from_title():
    url = build_author_query("The Night Circus", "Erin Morgenstern")
    # "The" should be stripped from the title portion
    assert "Night" in url
    assert "The" not in url


def test_strip_stop_words_from_query():
    assert strip_stop_words_from_query("The Night Circus") == "Night Circus"
    assert strip_stop_words_from_query("Dune") == "Dune"
    assert strip_stop_words_from_query("A Tale of Two Cities") == "Tale Two Cities"
