"""Tests for get_team_coach function."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, GameSheetError, Session
from gamesheet_sdk.roster import get_team_coach

_BASE = "https://test.example"
_SEASON_ID = "15020"
_TEAM_ID = "12345"


@responses.activate
def test_get_team_coach_returns_coach_with_roster_metadata(config: Config) -> None:
    """Test that get_team_coach returns a coach with team roster metadata."""
    _coach_id = "1879740"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _TEAM_ID,
                "attributes": {
                    "roster": {
                        "coaches": [
                            {
                                "id": _coach_id,
                                "position": "Manager",
                                "status": "coaching",
                                "signature": "LOU_SIGNATURE",
                            },
                        ],
                    },
                },
            },
            "included": [
                {
                    "type": "coaches",
                    "id": _coach_id,
                    "attributes": {
                        "external_id": "FB031B8B-2AB4-4682-817F-6E6076315241",
                        "first_name": "LOU",
                        "last_name": "LAMORIELLO",
                        "created_at": "2026-06-25T02:48:40.059871Z",
                        "updated_at": "2026-06-25T03:40:20.968536Z",
                    },
                    "relationships": {
                        "season": {"data": {"type": "seasons", "id": _SEASON_ID}},
                    },
                },
            ],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        result = get_team_coach(session, _SEASON_ID, _TEAM_ID, _coach_id)
    assert result.id == _coach_id
    assert result.season_id == _SEASON_ID
    assert result.first_name == "LOU"
    assert result.last_name == "LAMORIELLO"
    assert result.position == "Manager"
    assert result.status == "coaching"
    assert result.signature == "LOU_SIGNATURE"


@responses.activate
def test_get_team_coach_raises_error_when_coach_not_on_team(config: Config) -> None:
    """Test that get_team_coach raises GameSheetError when coach is not on the team."""
    _coach_id = "nonexistent"
    _get_endpoint = f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}"
    responses.add(
        responses.GET,
        _get_endpoint,
        json={
            "data": {
                "type": "teams",
                "id": _TEAM_ID,
                "attributes": {
                    "roster": {
                        "coaches": [],
                    },
                },
            },
            "included": [],
        },
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("abc")
        with pytest.raises(
            GameSheetError,
            match=f"Coach {_coach_id} not found on team {_TEAM_ID}",
        ):
            get_team_coach(session, _SEASON_ID, _TEAM_ID, _coach_id)
