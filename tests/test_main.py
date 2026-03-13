"""
Tests for cli.main — focusing on the check command's result display logic.
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.main import app, RESULT_THRESHOLD_FEW, _display_results


runner = CliRunner()

BOOK = {"hardcover_id": 1, "title": "The Bat", "author": "Jo Nesbø"}

# Build a list of fake results, more than the threshold
def _make_results(n: int) -> list[dict]:
    return [
        {"title": f"Book {i}", "author": f"Nesbø, Jo", "year": 2000 + i}
        for i in range(n)
    ]


class TestResultThreshold:
    def test_threshold_constant_is_10(self):
        """Sanity-check: threshold is still 10 so tests below are meaningful."""
        assert RESULT_THRESHOLD_FEW == 10

    def test_display_results_shows_all_when_no_limit(self):
        """_display_results with no limit renders every result."""
        results = _make_results(13)
        output = []
        with patch("cli.main.typer.echo", side_effect=lambda msg: output.append(msg)):
            _display_results(results, BOOK)
        # Each result produces one line
        assert len(output) == 13

    def test_display_results_respects_limit(self):
        """_display_results with limit=5 renders only 5 results (backwards compat)."""
        results = _make_results(13)
        output = []
        with patch("cli.main.typer.echo", side_effect=lambda msg: output.append(msg)):
            _display_results(results, BOOK, limit=5)
        assert len(output) == 5


class TestCheckCommand:
    def _run_check_patched(self, results1, results2, user_input="s"):
        """Run the `check` command with mocked DB, search, and user prompt."""
        with (
            patch("cli.main.get_connection"),
            patch("cli.main.init_db"),
            patch("cli.main.get_all_books", return_value=[BOOK]),
            patch("cli.main.record_decision"),
            patch("cli.main.search", side_effect=[results1, results2]),
            patch("cli.main.typer.prompt", return_value=user_input),
            patch("cli.main.random.choice", return_value=BOOK),
        ):
            return runner.invoke(app, ["check"])

    def test_phase2_many_results_shows_all(self):
        """When phase 2 still has too many results, all are shown (not just top 5)."""
        results1 = _make_results(13)  # triggers phase 2
        results2 = _make_results(13)  # still too many

        result = self._run_check_patched(results1, results2)

        # Output should mention all 13 results, not "top 5"
        assert "top 5" not in result.output
        assert "13" in result.output
        # All 13 items should be displayed (numbered [1] through [13])
        assert "[13]" in result.output

    def test_phase2_many_results_allows_picking_any(self):
        """User can pick result #13 (which would be index 12, beyond old top-5 limit)."""
        results1 = _make_results(13)
        results2 = _make_results(13)

        # Pick item 13 — previously impossible with [:5]
        result = self._run_check_patched(results1, results2, user_input="13")

        assert result.exit_code == 0
        # Should not show an "invalid choice" error
        assert "Invalid choice" not in result.output

    def test_phase2_few_results_unchanged(self):
        """When phase 2 returns ≤10 results, behavior is unchanged."""
        results1 = _make_results(13)  # triggers phase 2
        results2 = _make_results(5)   # phase 2 has few results → show all

        result = self._run_check_patched(results1, results2)

        assert result.exit_code == 0
        # Shows all 5
        assert "[5]" in result.output
        assert "[6]" not in result.output
