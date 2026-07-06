# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for completed games download CLI command."""

from __future__ import annotations

import tempfile
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli
from gamesheet_sdk.games import Game, TeamInfo
from tests.fixtures.constants import TEST_ACCESS_TOKEN, TEST_REFRESH_TOKEN


def test_build_scoresheet_filename_sanitize() -> None:
    """Test _build_scoresheet_filename sanitizes team names and divisions properly."""
    from gamesheet_sdk.cli.commands.games_completed import _build_scoresheet_filename

    # Create a Game with special characters in names
    game = Game(
        id=123,
        status="completed",
        date="2026-07-15",
        visitor=TeamInfo(
            id=1,
            title="Team A / B",
            divisionId=10,
            divisionTitle="U15 AA",
        ),
        home=TeamInfo(id=2, title="Team C & D", divisionId=11, divisionTitle="U16 AAA"),
        game_number="G-101",
    )

    filename = _build_scoresheet_filename(game)

    # Verify special characters are replaced with underscores (hyphens preserved)
    assert filename == "2026-07-15-scoresheet-123-team_a_b-u15_aa-vs-team_c_d-u16_aaa-g-101.pdf"


def test_build_scoresheet_filename_none_values() -> None:
    """Test _build_scoresheet_filename handles None values."""
    from gamesheet_sdk.cli.commands.games_completed import _build_scoresheet_filename

    # Create a Game with None/empty values
    game = Game(
        id=456,
        status="completed",
        date="2026-07-20",
        visitor=TeamInfo(id=3, title="", division_title=None),
        home=TeamInfo(id=4, title="", division_title=""),
        game_number=None,
    )

    filename = _build_scoresheet_filename(game)

    # Verify None/empty values become "unknown"
    assert filename == "2026-07-20-scoresheet-456-unknown-unknown-vs-unknown-unknown-unknown.pdf"


def test_build_scoresheet_filename_collapse_underscores() -> None:
    """Test _build_scoresheet_filename collapses multiple underscores."""
    from gamesheet_sdk.cli.commands.games_completed import _build_scoresheet_filename

    # Create game with names that will create multiple consecutive underscores
    game = Game(
        id=789,
        status="completed",
        date="2026-07-25",
        visitor=TeamInfo(id=5, title="Team   A", divisionId=20, divisionTitle="U15"),
        home=TeamInfo(id=6, title="Team---B", divisionId=21, divisionTitle="U16"),
        game_number="101",
    )

    filename = _build_scoresheet_filename(game)

    # Verify multiple underscores are collapsed to single underscore
    assert "_" in filename
    assert "__" not in filename


def test_completed_download_with_auto_filename(runner: CliRunner) -> None:
    """Test completed game download with auto-generated filename."""
    with (
        patch("gamesheet_sdk.cli.commands.games_completed.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games_completed.run_action_or_exit",
        ) as mock_run,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value=TEST_REFRESH_TOKEN,
        ),
        patch(
            "gamesheet_sdk.cli.helpers.load_access_token",
            return_value=TEST_ACCESS_TOKEN,
        ),
    ):
        # First call: _get_game_action (for filename generation)
        # Second call: _download_completed_game_pdf_action
        mock_run.side_effect = [
            Game(
                id=999,
                status="completed",
                date="2026-07-30",
                visitor=TeamInfo(
                    id=7,
                    title="Eagles",
                    divisionId=30,
                    divisionTitle="U18 AA",
                ),
                home=TeamInfo(
                    id=8,
                    title="Hawks",
                    divisionId=31,
                    divisionTitle="U18 AAA",
                ),
                game_number="201",
            ),
            None,  # download returns None
        ]

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-dl",
                "completed",
                "download",
                "--game-id",
                "999",
            ],
        )

        assert not result.exit_code
        assert mock_run.call_count == 2  # get + download
        # Verify auto-generated filename was used in download call
        download_args = mock_run.call_args_list[1][0]
        assert download_args[2] == "999"  # game_id
        assert download_args[3] == "2026-07-30-scoresheet-999-eagles-u18_aa-vs-hawks-u18_aaa-201.pdf"
        assert "Successfully downloaded scoresheet" in result.output


def test_completed_download_with_explicit_filename(runner: CliRunner) -> None:
    """Test completed game download with explicit output path."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        output_path = f.name

    with (
        patch("gamesheet_sdk.cli.commands.games_completed.build_authenticated_session"),
        patch(
            "gamesheet_sdk.cli.commands.games_completed.run_action_or_exit",
        ) as mock_run,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value=TEST_REFRESH_TOKEN,
        ),
        patch(
            "gamesheet_sdk.cli.helpers.load_access_token",
            return_value=TEST_ACCESS_TOKEN,
        ),
    ):
        mock_run.return_value = None  # download returns None

        result = runner.invoke(
            cli,
            [
                "games",
                "--season-id",
                "season-dl2",
                "completed",
                "download",
                "--game-id",
                "888",
                "--output-path",
                output_path,
            ],
        )

        assert not result.exit_code
        assert mock_run.call_count == 1  # only download (no get_game call)
        # Verify explicit filename was used
        args = mock_run.call_args[0]
        assert args[2] == "888"  # game_id
        assert args[3] == output_path
        assert f"Successfully downloaded scoresheet to {output_path}" in result.output
