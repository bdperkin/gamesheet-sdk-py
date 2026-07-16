# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for assign/unassign player and coach functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import AuthenticationError, Config, GameSheetError, Session
from gamesheet_sdk.admin.roster import (
    assign_coach,
    assign_player,
    assign_team_coach,
    assign_team_player,
    unassign_coach,
    unassign_player,
    unassign_team_coach,
    unassign_team_player,
)
from tests.helpers import (
    COACH_ID_PRIMARY,
    PLAYER_ID,
    SEASON_ID,
    TEAM_ID,
    TEST_BASE_URL,
    roster_coach_payload,
    roster_player_payload,
    team_payload,
)

_TEAM_ID = TEAM_ID
_PLAYER_ID = PLAYER_ID
_COACH_ID = COACH_ID_PRIMARY
_PLAYERS_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/players/{_PLAYER_ID}"
_COACHES_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/coaches/{_COACH_ID}"


@responses.activate
def test_assign_player_minimal_fields(config: Config) -> None:
    """Test assigning a player with no optional fields."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(season_id=SEASON_ID)
    # Mock GET player to ensure it exists
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=200,
    )
    team_data = team_payload(_TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_player(session, SEASON_ID, _PLAYER_ID, _TEAM_ID)
    assert result.id == _PLAYER_ID


@responses.activate
def test_assign_player_with_optional_fields(config: Config) -> None:
    """Test assigning a player with all optional fields."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=200,
    )
    team_data = team_payload(_TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_player(
            session,
            SEASON_ID,
            _PLAYER_ID,
            _TEAM_ID,
            jersey="99",
            position="Forward",
            status="Regular",
            designation="Captain",
        )
    assert result.id == _PLAYER_ID
    assert result.number == "99"
    assert result.position == "Forward"
    assert result.status == "Regular"
    assert result.designation == "Captain"


@responses.activate
def test_assign_player_already_assigned_raises_error(config: Config) -> None:
    """Test that assigning an already-assigned player raises GameSheetError."""
    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=200,
    )
    team_data = team_payload(
        _TEAM_ID,
        players=[{"id": _PLAYER_ID, "status": "playing"}],
    )
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match=r"already assigned"):
            assign_player(session, SEASON_ID, _PLAYER_ID, _TEAM_ID)


@responses.activate
def test_assign_coach_minimal_fields(config: Config) -> None:
    """Test assigning a coach with no optional fields."""
    from tests.helpers import setup_team_roster_update_mocks

    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    # Mock GET coach to ensure it exists
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=200,
    )
    team_data = team_payload(_TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_coach(session, SEASON_ID, _COACH_ID, _TEAM_ID)
    assert result.id == _COACH_ID
    assert result.status == "coaching"


@responses.activate
def test_assign_coach_with_position(config: Config) -> None:
    """Test assigning a coach with position."""
    from tests.helpers import setup_team_roster_update_mocks

    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=200,
    )
    team_data = team_payload(_TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_coach(
            session,
            SEASON_ID,
            _COACH_ID,
            _TEAM_ID,
            position="Head Coach",
        )
    assert result.id == _COACH_ID
    assert result.position == "Head Coach"
    assert result.status == "coaching"


@responses.activate
def test_assign_coach_already_assigned_raises_error(config: Config) -> None:
    """Test that assigning an already-assigned coach raises GameSheetError."""
    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=200,
    )
    team_data = team_payload(
        _TEAM_ID,
        coaches=[{"id": _COACH_ID, "status": "coaching"}],
    )
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match=r"already assigned"):
            assign_coach(session, SEASON_ID, _COACH_ID, _TEAM_ID)


@responses.activate
def test_unassign_player_success(config: Config) -> None:
    """Test unassigning a player from a team."""
    team_data = team_payload(
        _TEAM_ID,
        players=[{"id": _PLAYER_ID, "status": "playing"}],
    )
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        unassign_player(session, SEASON_ID, _PLAYER_ID, _TEAM_ID)


@responses.activate
def test_unassign_player_not_assigned_raises_error(config: Config) -> None:
    """Test that unassigning a player not on the roster raises GameSheetError."""
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match=r"not assigned"):
            unassign_player(session, SEASON_ID, _PLAYER_ID, _TEAM_ID)


@responses.activate
def test_unassign_coach_success(config: Config) -> None:
    """Test unassigning a coach from a team."""
    team_data = team_payload(
        _TEAM_ID,
        coaches=[{"id": _COACH_ID, "status": "coaching"}],
    )
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        unassign_coach(session, SEASON_ID, _COACH_ID, _TEAM_ID)


@responses.activate
def test_unassign_coach_not_assigned_raises_error(config: Config) -> None:
    """Test that unassigning a coach not on the roster raises GameSheetError."""
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(GameSheetError, match=r"not assigned"):
            unassign_coach(session, SEASON_ID, _COACH_ID, _TEAM_ID)


@responses.activate
def test_assign_team_player_calls_assign_player(config: Config) -> None:
    """Test that assign_team_player is an alias for assign_player."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=200,
    )
    team_data = team_payload(_TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_team_player(session, SEASON_ID, _TEAM_ID, _PLAYER_ID)
    assert result.id == _PLAYER_ID


@responses.activate
def test_unassign_team_player_calls_unassign_player(config: Config) -> None:
    """Test that unassign_team_player is an alias for unassign_player."""
    from tests.helpers import setup_team_roster_update_mocks

    team_data = team_payload(
        _TEAM_ID,
        players=[{"id": _PLAYER_ID, "status": "playing"}],
    )
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        unassign_team_player(session, SEASON_ID, _TEAM_ID, _PLAYER_ID)


@responses.activate
def test_assign_team_coach_calls_assign_coach(config: Config) -> None:
    """Test that assign_team_coach is an alias for assign_coach."""
    from tests.helpers import setup_team_roster_update_mocks

    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=200,
    )
    team_data = team_payload(_TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_team_coach(session, SEASON_ID, _TEAM_ID, _COACH_ID)
    assert result.id == _COACH_ID
    assert result.status == "coaching"


@responses.activate
def test_unassign_team_coach_calls_unassign_coach(config: Config) -> None:
    """Test that unassign_team_coach is an alias for unassign_coach."""
    from tests.helpers import setup_team_roster_update_mocks

    team_data = team_payload(
        _TEAM_ID,
        coaches=[{"id": _COACH_ID, "status": "coaching"}],
    )
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, _TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        unassign_team_coach(session, SEASON_ID, _TEAM_ID, _COACH_ID)


@responses.activate
def test_assign_player_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _PLAYERS_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            assign_player(session, SEASON_ID, _PLAYER_ID, _TEAM_ID)


@responses.activate
def test_assign_player_with_existing_other_players_on_roster(config: Config) -> None:
    """Test assigning a player when roster has other players (not the one being assigned)."""
    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=200,
    )
    # Team has other players but not the one being assigned
    team_data = team_payload(
        _TEAM_ID,
        players=[
            {"id": "other-player-1", "status": "playing"},
            {"id": "other-player-2", "status": "playing"},
        ],
    )
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_player(session, SEASON_ID, _PLAYER_ID, _TEAM_ID)
    assert result.id == _PLAYER_ID


@responses.activate
def test_assign_coach_with_existing_other_coaches_on_roster(config: Config) -> None:
    """Test assigning a coach when roster has other coaches (not the one being assigned)."""
    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=200,
    )
    # Team has other coaches but not the one being assigned
    team_data = team_payload(
        _TEAM_ID,
        coaches=[
            {"id": "other-coach-1", "status": "coaching"},
            {"id": "other-coach-2", "status": "coaching"},
        ],
    )
    responses.add(
        responses.GET,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = assign_coach(session, SEASON_ID, _COACH_ID, _TEAM_ID)
    assert result.id == _COACH_ID
    assert result.status == "coaching"


@responses.activate
def test_assign_coach_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.GET, _COACHES_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            assign_coach(session, SEASON_ID, _COACH_ID, _TEAM_ID)
