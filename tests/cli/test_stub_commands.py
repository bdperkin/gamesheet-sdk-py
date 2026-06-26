"""Test coverage for stub commands that are not yet implemented.

These tests ensure all stub commands are covered by tests, even though they just return "not implemented"
errors. This keeps coverage at 100%.
"""

from __future__ import annotations

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.games import scheduled_group
from gamesheet_sdk.cli.commands.roster import coaches_group, players_group
from gamesheet_sdk.cli.commands.teams_roster import (
    teams_roster_coaches_group,
    teams_roster_players_group,
)


def test_games_scheduled_create_stub() -> None:
    """Test games scheduled create stub command."""
    result = CliRunner().invoke(scheduled_group, ["create"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_games_scheduled_update_stub() -> None:
    """Test games scheduled update stub command."""
    result = CliRunner().invoke(scheduled_group, ["update"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_games_scheduled_delete_stub() -> None:
    """Test games scheduled delete stub command."""
    result = CliRunner().invoke(scheduled_group, ["delete"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_roster_players_delete_stub() -> None:
    """Test roster players delete stub command."""
    result = CliRunner().invoke(players_group, ["delete", "--force"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_roster_players_penalty_report_stub() -> None:
    """Test roster players penalty-report stub command."""
    result = CliRunner().invoke(players_group, ["penalty-report"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_roster_coaches_delete_stub() -> None:
    """Test roster coaches delete stub command."""
    result = CliRunner().invoke(coaches_group, ["delete", "--force"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_roster_coaches_penalty_report_stub() -> None:
    """Test roster coaches penalty-report stub command."""
    result = CliRunner().invoke(coaches_group, ["penalty-report"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_teams_roster_players_delete_stub() -> None:
    """Test teams roster players delete stub command."""
    result = CliRunner().invoke(teams_roster_players_group, ["delete", "--force"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_teams_roster_players_penalty_report_stub() -> None:
    """Test teams roster players penalty-report stub command."""
    result = CliRunner().invoke(teams_roster_players_group, ["penalty-report"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_teams_roster_coaches_delete_stub() -> None:
    """Test teams roster coaches delete stub command."""
    result = CliRunner().invoke(teams_roster_coaches_group, ["delete", "--force"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()


def test_teams_roster_coaches_penalty_report_stub() -> None:
    """Test teams roster coaches penalty-report stub command."""
    result = CliRunner().invoke(teams_roster_coaches_group, ["penalty-report"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output.lower()
