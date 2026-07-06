# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for create_player and create_coach functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import (
    AuthenticationError,
    Config,
    GameSheetError,
    Session,
)
from gamesheet_sdk.roster import (
    create_coach,
    create_player,
    create_team_coach,
    create_team_player,
)
from tests.helpers import (
    COACH_EXTERNAL_ID,
    COACH_FIRST_NAME,
    COACH_ID_PRIMARY,
    COACH_LAST_NAME,
    PLAYER_EXTERNAL_ID,
    PLAYER_FIRST_NAME,
    PLAYER_ID,
    PLAYER_LAST_NAME,
    SEASON_ID,
    TEAM_ID,
    TEST_BASE_URL,
    coaches_endpoint,
    players_endpoint,
    roster_coach_payload,
    roster_player_payload,
    team_payload,
)

_PLAYERS_ENDPOINT = players_endpoint(SEASON_ID)
_COACHES_ENDPOINT = coaches_endpoint(SEASON_ID)


@responses.activate
def test_create_player_minimal_fields(config: Config) -> None:
    """Test creating a player with only required fields."""
    player_response = roster_player_payload(
        season_id=SEASON_ID,
        first_name=PLAYER_FIRST_NAME,
        last_name=PLAYER_LAST_NAME,
        external_id=None,
    )
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(session, SEASON_ID, PLAYER_FIRST_NAME, PLAYER_LAST_NAME)
    assert result.id == PLAYER_ID
    assert result.first_name == PLAYER_FIRST_NAME
    assert result.last_name == PLAYER_LAST_NAME
    assert result.season_id == SEASON_ID


@responses.activate
def test_create_player_with_external_id(config: Config) -> None:
    """Test creating a player with external_id."""
    player_response = roster_player_payload(
        season_id=SEASON_ID,
        external_id=PLAYER_EXTERNAL_ID,
    )
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(
            session,
            SEASON_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            external_id=PLAYER_EXTERNAL_ID,
        )
    assert result.external_id == PLAYER_EXTERNAL_ID


@responses.activate
def test_create_player_with_all_profile_fields(config: Config) -> None:
    """Test creating a player with all profile fields (biography, height, etc.)."""
    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(
            session,
            SEASON_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            biography="Player biography",
            height="6'2\"",
            weight="185",
            shot_hand="right",
            birthdate="1990-01-15",
            hometown="Toronto",
            country="CA",
            province="Ontario",
            drafted_by="Toronto Maple Leafs",
            committed_to="University of Toronto",
        )
    assert result.id == PLAYER_ID


@responses.activate
def test_create_player_with_optional_fields(config: Config) -> None:
    """Test creating a player with all optional fields."""
    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(
            session,
            SEASON_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            external_id=PLAYER_EXTERNAL_ID,
            jersey="98",
            position="Forward",
            status="Regular",
            designation="Captain",
        )
    assert result.id == PLAYER_ID


@responses.activate
def test_create_player_with_team_id(config: Config) -> None:
    """Test creating a player with team_id."""
    player_response = roster_player_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(
            session,
            SEASON_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            team_id=TEAM_ID,
        )
    assert result.id == PLAYER_ID


@responses.activate
def test_create_player_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            create_player(session, SEASON_ID, PLAYER_FIRST_NAME, PLAYER_LAST_NAME)


@responses.activate
def test_create_player_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            create_player(session, SEASON_ID, PLAYER_FIRST_NAME, PLAYER_LAST_NAME)


@responses.activate
def test_create_player_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            create_player(session, SEASON_ID, PLAYER_FIRST_NAME, PLAYER_LAST_NAME)


@responses.activate
def test_create_coach_minimal_fields(config: Config) -> None:
    """Test creating a coach with only required fields."""
    coach_response = roster_coach_payload(
        season_id=SEASON_ID,
        first_name=COACH_FIRST_NAME,
        last_name=COACH_LAST_NAME,
        external_id=None,
    )
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(session, SEASON_ID, COACH_FIRST_NAME, COACH_LAST_NAME)
    assert result.id == COACH_ID_PRIMARY
    assert result.first_name == COACH_FIRST_NAME
    assert result.last_name == COACH_LAST_NAME
    assert result.season_id == SEASON_ID


@responses.activate
def test_create_coach_with_external_id(config: Config) -> None:
    """Test creating a coach with external_id."""
    coach_response = roster_coach_payload(
        season_id=SEASON_ID,
        external_id=COACH_EXTERNAL_ID,
    )
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(
            session,
            SEASON_ID,
            COACH_FIRST_NAME,
            COACH_LAST_NAME,
            external_id=COACH_EXTERNAL_ID,
        )
    assert result.external_id == COACH_EXTERNAL_ID


@responses.activate
def test_create_coach_with_position(config: Config) -> None:
    """Test creating a coach with position."""
    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(
            session,
            SEASON_ID,
            COACH_FIRST_NAME,
            COACH_LAST_NAME,
            position="Head Coach",
        )
    assert result.id == COACH_ID_PRIMARY


@responses.activate
def test_create_coach_with_team_id(config: Config) -> None:
    """Test creating a coach with team_id."""
    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(
            session,
            SEASON_ID,
            COACH_FIRST_NAME,
            COACH_LAST_NAME,
            team_id=TEAM_ID,
        )
    assert result.id == COACH_ID_PRIMARY


@responses.activate
def test_create_coach_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            create_coach(session, SEASON_ID, COACH_FIRST_NAME, COACH_LAST_NAME)


@responses.activate
def test_create_coach_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            create_coach(session, SEASON_ID, COACH_FIRST_NAME, COACH_LAST_NAME)


@responses.activate
def test_create_coach_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            create_coach(session, SEASON_ID, COACH_FIRST_NAME, COACH_LAST_NAME)


@responses.activate
def test_create_team_player_calls_create_player_with_team_id(config: Config) -> None:
    """Test that create_team_player creates player and adds to team roster."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(season_id=SEASON_ID)
    # Mock POST to create player
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            SEASON_ID,
            TEAM_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
        )
    assert result.id == PLAYER_ID


@responses.activate
def test_create_team_coach_calls_create_coach_with_team_id(config: Config) -> None:
    """Test that create_team_coach creates coach and adds to team roster."""
    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    from tests.helpers import setup_team_roster_update_mocks

    # Mock POST to create coach
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_coach(
            session,
            SEASON_ID,
            TEAM_ID,
            COACH_FIRST_NAME,
            COACH_LAST_NAME,
        )
    assert result.id == COACH_ID_PRIMARY
    assert result.status == "coaching"


@responses.activate
def test_create_team_player_with_optional_fields(config: Config) -> None:
    """Test that create_team_player handles optional fields."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            SEASON_ID,
            TEAM_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            jersey="99",
            position="Forward",
            status="Regular",
            designation="Captain",
        )
    assert result.id == PLAYER_ID
    assert result.number == "99"
    assert result.position == "Forward"
    assert result.status == "Regular"
    assert result.designation == "Captain"


@responses.activate
def test_create_team_player_with_affiliated_status(config: Config) -> None:
    """Test that create_team_player handles Affiliated status."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            SEASON_ID,
            TEAM_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            status="Affiliated",
        )
    assert result.id == PLAYER_ID


@responses.activate
def test_create_team_coach_with_position(config: Config) -> None:
    """Test that create_team_coach handles position parameter."""
    from tests.helpers import setup_team_roster_update_mocks

    coach_response = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_coach(
            session,
            SEASON_ID,
            TEAM_ID,
            COACH_FIRST_NAME,
            COACH_LAST_NAME,
            position="Head Coach",
        )
    assert result.id == COACH_ID_PRIMARY
    assert result.position == "Head Coach"
    assert result.status == "coaching"


@responses.activate
def test_create_team_player_with_external_id(config: Config) -> None:
    """Test that create_team_player handles external_id parameter."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(
        season_id=SEASON_ID,
        external_id="TEST-EXT-123",
    )
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            SEASON_ID,
            TEAM_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            external_id="TEST-EXT-123",
        )
    assert result.id == PLAYER_ID
    assert result.external_id == "TEST-EXT-123"


@responses.activate
def test_create_team_coach_with_external_id(config: Config) -> None:
    """Test that create_team_coach handles external_id parameter."""
    from tests.helpers import setup_team_roster_update_mocks

    coach_response = roster_coach_payload(
        season_id=SEASON_ID,
        external_id="TEST-EXT-456",
    )
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_coach(
            session,
            SEASON_ID,
            TEAM_ID,
            COACH_FIRST_NAME,
            COACH_LAST_NAME,
            external_id="TEST-EXT-456",
        )
    assert result.id == COACH_ID_PRIMARY
    assert result.external_id == "TEST-EXT-456"


@responses.activate
def test_create_team_player_with_all_profile_fields(config: Config) -> None:
    """Test that create_team_player handles all profile fields."""
    from tests.helpers import setup_team_roster_update_mocks

    player_response = roster_player_payload(
        season_id=SEASON_ID,
        external_id="TEST-PROFILE",
    )
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    team_data = team_payload(TEAM_ID)
    setup_team_roster_update_mocks(TEST_BASE_URL, SEASON_ID, TEAM_ID, team_data)
    responses.add(
        responses.PATCH,
        f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/teams-v2/{TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            SEASON_ID,
            TEAM_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            external_id="TEST-PROFILE",
            biography="Player biography",
            height="6'2\"",
            weight="185",
            shot_hand="right",
            birthdate="1990-01-15",
            hometown="Toronto",
            country="CA",
            province="Ontario",
            drafted_by="Toronto Maple Leafs",
            committed_to="University of Toronto",
        )
    assert result.id == PLAYER_ID
    assert result.external_id == "TEST-PROFILE"


@responses.activate
def test_create_player_with_photo(config: Config) -> None:
    """Test creating a player with photo upload."""
    from tests.helpers import setup_photo_upload_mocks

    temp_path = setup_photo_upload_mocks()
    # Mock player creation
    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(
            session,
            SEASON_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            photo_path=temp_path,
        )
    assert result.id == PLAYER_ID


@responses.activate
def test_create_team_player_with_photo(config: Config) -> None:
    """Test creating a team player with photo upload."""
    from tests.helpers import setup_photo_upload_mocks

    team_temp_path = setup_photo_upload_mocks()
    # Mock player creation
    player_response = roster_player_payload(season_id=SEASON_ID)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    # Mock team fetch
    team_response = team_payload()
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{TEAM_ID}",
        json={"data": team_response},
        status=200,
    )
    # Mock team update
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/teams-v2/{TEAM_ID}",
        json={"data": team_response},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            SEASON_ID,
            TEAM_ID,
            PLAYER_FIRST_NAME,
            PLAYER_LAST_NAME,
            photo_path=team_temp_path,
        )
    assert result.id == PLAYER_ID
