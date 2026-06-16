"""Integration tests for games CLI commands."""

from __future__ import annotations

import tempfile
from pathlib import Path

import responses

# Explicit import for coverage tracking of dynamically-loaded Click commands
# pylint: disable-next=unused-import
import gamesheet_sdk.cli.commands.games  # noqa: F401
from gamesheet_sdk.cli import main

_BFF_BASE = "https://bff-dashboard-api-awy26srzoa-nn.a.run.app"
_SEASON_ID = "15020"
_ENDPOINT = f"{_BFF_BASE}/games-list/v1"
_TOKEN_PATH = Path(tempfile.gettempdir()) / ".gamesheet" / "access_token"


def _bff_response(games: list[dict[str, object]]) -> dict[str, object]:
    """Build a BFF API response."""
    return {"status": "success", "data": games}


def _mock_token() -> None:
    """Create a mock access token file."""
    _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_PATH.write_text("mock-token")


def _cleanup_token() -> None:
    """Remove mock token file."""
    if _TOKEN_PATH.exists():

        _TOKEN_PATH.unlink()


@responses.activate
def test_games_completed_list_json_format() -> None:
    """Test games completed list with JSON output."""
    _mock_token()
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_bff_response([]),
        status=200,
    )
    result = main(["games", "--season-id", _SEASON_ID, "completed", "list", "-F", "json"])
    assert result == 0
    _cleanup_token()


@responses.activate
def test_games_scheduled_list_json_format() -> None:
    """Test games scheduled list with JSON output."""
    _mock_token()
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_bff_response([]),
        status=200,
    )
    result = main(["games", "--season-id", _SEASON_ID, "scheduled", "list", "-F", "json"])
    assert result == 0
    _cleanup_token()


@responses.activate
def test_games_brackets_list_json_format() -> None:
    """Test games brackets list with JSON output."""
    _mock_token()
    responses.add(
        responses.GET,
        _ENDPOINT,
        json=_bff_response([]),
        status=200,
    )
    result = main(["games", "--season-id", _SEASON_ID, "brackets", "list", "-F", "json"])
    assert result == 0
    _cleanup_token()
