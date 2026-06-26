"""Tests for update_player and update_coach functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.roster import (
    update_coach,
    update_player,
    update_team_coach,
    update_team_player,
)
from tests.helpers.payloads import roster_coach_payload, roster_player_payload, team_payload

_SEASON_ID = "15020"
_TEAM_ID = "523675"
_PLAYER_ID = "8043169"
_COACH_ID = "1879938"
_PLAYERS_ENDPOINT = f"https://test.example/api/seasons/{_SEASON_ID}/players/{_PLAYER_ID}"
_COACHES_ENDPOINT = f"https://test.example/api/seasons/{_SEASON_ID}/coaches/{_COACH_ID}"


@responses.activate
def test_update_player_updates_fields(config: Config) -> None:
    """Test updating a player updates the specified fields."""
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=_SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            _SEASON_ID,
            _PLAYER_ID,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_player_with_photo_upload(config: Config) -> None:
    """Test updating a player with photo upload."""
    import tempfile

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jpg", delete=False) as temp_file:
        temp_file.write("fake image content")
        temp_path = temp_file.name

    # Mock upload URL request
    responses.add(
        responses.POST,
        "https://bff-dashboard-api-awy26srzoa-nn.a.run.app/dwg/assets/upload-url",
        json={
            "status": "success",
            "data": {"uploadURL": "https://upload.example.com/test", "id": "test-image-id"},
        },
        status=200,
    )
    # Mock upload request
    responses.add(
        responses.POST,
        "https://upload.example.com/test",
        json={"success": True},
        status=200,
    )
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=_SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"][
        "photo_url"
    ] = "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA/test-image-id"
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            _SEASON_ID,
            _PLAYER_ID,
            photo_path=temp_path,
        )
    assert result.photo_url
    assert "test-image-id" in result.photo_url


@responses.activate
def test_update_player_remove_photo(config: Config) -> None:
    """Test updating a player to remove photo."""
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=_SEASON_ID)
    current_player["attributes"]["photo_url"] = "https://example.com/old-photo.jpg"
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"]["photo_url"] = ""
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            _SEASON_ID,
            _PLAYER_ID,
            remove_photo=True,
        )
    assert not result.photo_url


@responses.activate
def test_update_player_no_fields_raises_error(config: Config) -> None:
    """Test updating a player with no fields raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match="At least one field must be provided"):
            update_player(session, _SEASON_ID, _PLAYER_ID)


@responses.activate
def test_update_player_photo_and_remove_photo_raises_error(config: Config) -> None:
    """Test updating a player with both photo and remove_photo raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match="Cannot both upload a photo and remove it"):
            update_player(
                session,
                _SEASON_ID,
                _PLAYER_ID,
                photo_path="/tmp/test.jpg",  # noqa: S108
                remove_photo=True,
            )


@responses.activate
def test_update_coach_updates_fields(config: Config) -> None:
    """Test updating a coach updates the specified fields."""
    # Mock GET to fetch current coach
    current_coach = roster_coach_payload(season_id=_SEASON_ID)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": current_coach},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=_SEASON_ID)
    updated_coach["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        _COACHES_ENDPOINT,
        json={"data": updated_coach},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_coach(
            session,
            _SEASON_ID,
            _COACH_ID,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_coach_no_fields_raises_error(config: Config) -> None:
    """Test updating a coach with no fields raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match="At least one field must be provided"):
            update_coach(session, _SEASON_ID, _COACH_ID)


@responses.activate
def test_update_team_player_updates_fields(config: Config) -> None:
    """Test updating a team player updates the specified fields."""
    # Mock GET team to fetch current team player (via list_team_players)
    team_data = team_payload()
    current_player_payload = roster_player_payload(season_id=_SEASON_ID)
    team_data["attributes"]["roster"] = {
        "players": [
            {"id": _PLAYER_ID, "number": "99", "position": "centre", "status": "playing", "duty": ""},
        ],
        "coaches": [],
    }
    team_data["relationships"]["players"] = {"data": [{"type": "players", "id": _PLAYER_ID}]}
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_player_payload]},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{_SEASON_ID}/players/{_PLAYER_ID}",
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_player(
            session,
            _SEASON_ID,
            _TEAM_ID,
            _PLAYER_ID,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_team_coach_updates_fields(config: Config) -> None:
    """Test updating a team coach updates the specified fields."""
    # Mock GET team to fetch current team coach (via list_team_coaches)
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(coach_id=_COACH_ID, season_id=_SEASON_ID)
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [{"id": _COACH_ID, "position": "Head Coach", "status": "coaching", "signature": ""}],
    }
    team_data["relationships"]["coaches"] = {"data": [{"type": "coaches", "id": _COACH_ID}]}
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=_SEASON_ID)
    updated_coach["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{_SEASON_ID}/coaches/{_COACH_ID}",
        json={"data": updated_coach},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            _SEASON_ID,
            _TEAM_ID,
            _COACH_ID,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_team_coach_with_position_updates_roster(config: Config) -> None:
    """Test updating a team coach with position updates the team roster."""
    # Mock GET team to fetch current team coach (via list_team_coaches)
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(coach_id=_COACH_ID, season_id=_SEASON_ID)
    current_coach_payload["attributes"]["position"] = "Assistant Coach"
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [{"id": _COACH_ID, "position": "Assistant Coach", "status": "coaching", "signature": ""}],
    }
    team_data["relationships"]["coaches"] = {"data": [{"type": "coaches", "id": _COACH_ID}]}
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=_SEASON_ID)
    updated_coach["attributes"]["position"] = "Head Coach"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{_SEASON_ID}/coaches/{_COACH_ID}",
        json={"data": updated_coach},
        status=200,
    )
    # Mock team GET for roster update (second call for position change)
    team_data2 = team_payload()
    team_data2["attributes"]["roster"] = {
        "players": [],
        "coaches": [{"id": _COACH_ID, "position": "Assistant Coach", "status": "coaching", "signature": ""}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data2},
        status=200,
    )
    # Mock team PATCH for roster update
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data2},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            _SEASON_ID,
            _TEAM_ID,
            _COACH_ID,
            position="Head Coach",
        )
    assert result.position == "Head Coach"


@responses.activate
def test_update_player_with_all_profile_fields(config: Config) -> None:
    """Test updating a player with all profile fields."""
    # Mock GET to fetch current player
    current_player = roster_player_payload(season_id=_SEASON_ID)
    responses.add(
        responses.GET,
        _PLAYERS_ENDPOINT,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"]["biography"] = "Test bio"
    updated_player["attributes"]["height"] = "6'2\""
    updated_player["attributes"]["weight"] = "200"
    updated_player["attributes"]["shot_hand"] = "R"
    updated_player["attributes"]["birthdate"] = "2000-01-01"
    updated_player["attributes"]["hometown"] = "Toronto"
    updated_player["attributes"]["country"] = "Canada"
    updated_player["attributes"]["province"] = "Ontario"
    updated_player["attributes"]["drafted_by"] = "Team A"
    updated_player["attributes"]["committed_to"] = "Team B"
    responses.add(
        responses.PATCH,
        _PLAYERS_ENDPOINT,
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            _SEASON_ID,
            _PLAYER_ID,
            biography="Test bio",
            height="6'2\"",
            weight="200",
            shot_hand="R",
            birthdate="2000-01-01",
            hometown="Toronto",
            country="Canada",
            province="Ontario",
            drafted_by="Team A",
            committed_to="Team B",
        )
    assert result.biography == "Test bio"
    assert result.height == "6'2\""


@responses.activate
def test_update_coach_with_all_fields(config: Config) -> None:
    """Test updating a coach with all fields."""
    # Mock GET to fetch current coach
    current_coach = roster_coach_payload(season_id=_SEASON_ID)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": current_coach},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=_SEASON_ID)
    updated_coach["attributes"]["first_name"] = "NEW"
    updated_coach["attributes"]["last_name"] = "COACH"
    updated_coach["attributes"]["position"] = "Head Coach"
    updated_coach["attributes"]["external_id"] = "ext-123"
    responses.add(
        responses.PATCH,
        _COACHES_ENDPOINT,
        json={"data": updated_coach},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_coach(
            session,
            _SEASON_ID,
            _COACH_ID,
            first_name="NEW",
            last_name="COACH",
            position="Head Coach",
            external_id="ext-123",
        )
    assert result.first_name == "NEW"
    assert result.last_name == "COACH"


@responses.activate
def test_update_team_player_with_all_profile_fields(config: Config) -> None:
    """Test updating a team player with all profile fields."""
    # Mock GET team to fetch current team player (via list_team_players)
    team_data = team_payload()
    current_player_payload = roster_player_payload(season_id=_SEASON_ID)
    team_data["attributes"]["roster"] = {
        "players": [
            {"id": _PLAYER_ID, "number": "99", "position": "centre", "status": "playing", "duty": ""},
        ],
        "coaches": [],
    }
    team_data["relationships"]["players"] = {"data": [{"type": "players", "id": _PLAYER_ID}]}
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_player_payload]},
        status=200,
    )
    # Mock PATCH to update player
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"]["biography"] = "Test bio"
    updated_player["attributes"]["height"] = "6'0\""
    updated_player["attributes"]["weight"] = "180"
    updated_player["attributes"]["shot_hand"] = "L"
    updated_player["attributes"]["birthdate"] = "1999-12-31"
    updated_player["attributes"]["hometown"] = "Montreal"
    updated_player["attributes"]["country"] = "Canada"
    updated_player["attributes"]["province"] = "Quebec"
    updated_player["attributes"]["drafted_by"] = "Team C"
    updated_player["attributes"]["committed_to"] = "Team D"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{_SEASON_ID}/players/{_PLAYER_ID}",
        json={"data": updated_player},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_player(
            session,
            _SEASON_ID,
            _TEAM_ID,
            _PLAYER_ID,
            biography="Test bio",
            height="6'0\"",
            weight="180",
            shot_hand="L",
            birthdate="1999-12-31",
            hometown="Montreal",
            country="Canada",
            province="Quebec",
            drafted_by="Team C",
            committed_to="Team D",
        )
    assert result.biography == "Test bio"


@responses.activate
def test_update_team_coach_no_fields_raises_error(config: Config) -> None:
    """Test updating a team coach with no fields raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match="At least one field must be provided"):
            update_team_coach(session, _SEASON_ID, _TEAM_ID, _COACH_ID)
