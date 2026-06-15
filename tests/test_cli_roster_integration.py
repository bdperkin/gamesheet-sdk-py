"""Integration tests for roster CLI commands."""

from __future__ import annotations

import tempfile
from pathlib import Path

import responses

# Explicit import for coverage tracking of dynamically-loaded Click commands
# pylint: disable-next=unused-import
import gamesheet_sdk.cli.commands.roster  # noqa: F401,E401
from gamesheet_sdk.cli import main

_BASE = "https://gamesheet.app"
_SEASON_ID = "15020"
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches"
_TOKEN_PATH = Path(tempfile.gettempdir()) / ".gamesheet" / "access_token"


def _payload(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a JSON:API ``{"data": [...]}`` body."""
    return {"data": rows}


def _mock_token() -> None:
    """Create a mock access token file."""
    _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_PATH.write_text("mock-token")


def _cleanup_token() -> None:
    """Remove mock token file."""
    if _TOKEN_PATH.exists():

        _TOKEN_PATH.unlink()


@responses.activate
def test_roster_players_list_json_format() -> None:
    """Test roster players list with JSON output."""
    _mock_token()
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json=_payload([]),
        status=200,
    )
    result = main(["roster", "--season-id", _SEASON_ID, "players", "list", "-F", "json"])
    assert result == 0
    _cleanup_token()


@responses.activate
def test_roster_coaches_list_json_format() -> None:
    """Test roster coaches list with JSON output."""
    _mock_token()
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json=_payload([]),
        status=200,
    )
    result = main(["roster", "--season-id", _SEASON_ID, "coaches", "list", "-F", "json"])
    assert result == 0
    _cleanup_token()
