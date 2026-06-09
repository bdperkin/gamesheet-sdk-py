"""Tests for games and roster CLI commands."""

from __future__ import annotations

import pytest

from gamesheet_sdk.cli import main

_DUMMY_SEASON = "12345"


@pytest.mark.parametrize(
    "subcommand",
    [
        "scheduled",
        "completed",
        "brackets",
    ],
)
def test_games_subcommand_help(subcommand: str) -> None:
    """Test that games sub-commands help pages render."""
    result = main(["games", "--season-id", _DUMMY_SEASON, subcommand, "--help"])
    assert result == 0


@pytest.mark.parametrize(
    "subcommand",
    [
        "players",
        "coaches",
    ],
)
def test_roster_subcommand_help(subcommand: str) -> None:
    """Test that roster sub-commands help pages render."""
    result = main(["roster", "--season-id", _DUMMY_SEASON, subcommand, "--help"])
    assert result == 0


def test_games_help() -> None:
    """Test that games command help renders."""
    result = main(["games", "--help"])
    assert result == 0


def test_roster_help() -> None:
    """Test that roster command help renders."""
    result = main(["roster", "--help"])
    assert result == 0


def test_games_scheduled_list_help() -> None:
    """Test that games scheduled list help renders."""
    result = main(["games", "--season-id", _DUMMY_SEASON, "scheduled", "list", "--help"])
    assert result == 0


def test_games_completed_list_help() -> None:
    """Test that games completed list help renders."""
    result = main(["games", "--season-id", _DUMMY_SEASON, "completed", "list", "--help"])
    assert result == 0


def test_games_brackets_list_help() -> None:
    """Test that games brackets list help renders."""
    result = main(["games", "--season-id", _DUMMY_SEASON, "brackets", "list", "--help"])
    assert result == 0


def test_roster_players_list_help() -> None:
    """Test that roster players list help renders."""
    result = main(["roster", "--season-id", _DUMMY_SEASON, "players", "list", "--help"])
    assert result == 0


def test_roster_coaches_list_help() -> None:
    """Test that roster coaches list help renders."""
    result = main(["roster", "--season-id", _DUMMY_SEASON, "coaches", "list", "--help"])
    assert result == 0


def test_games_scheduled_ls_alias_help() -> None:
    """Test that games scheduled ls alias works."""
    result = main(["games", "--season-id", _DUMMY_SEASON, "scheduled", "ls", "--help"])
    assert result == 0


def test_games_completed_ls_alias_help() -> None:
    """Test that games completed ls alias works."""
    result = main(["games", "--season-id", _DUMMY_SEASON, "completed", "ls", "--help"])
    assert result == 0


def test_roster_players_ls_alias_help() -> None:
    """Test that roster players ls alias works."""
    result = main(["roster", "--season-id", _DUMMY_SEASON, "players", "ls", "--help"])
    assert result == 0


def test_roster_coaches_ls_alias_help() -> None:
    """Test that roster coaches ls alias works."""
    result = main(["roster", "--season-id", _DUMMY_SEASON, "coaches", "ls", "--help"])
    assert result == 0


def test_games_missing_season_id_error() -> None:
    """Test that games requires --season-id."""
    result = main(["games", "scheduled", "list"])
    # Should fail with non-zero exit code due to missing required option
    assert result != 0


def test_roster_missing_season_id_error() -> None:
    """Test that roster requires --season-id."""
    result = main(["roster", "players", "list"])
    # Should fail with non-zero exit code due to missing required option
    assert result != 0
