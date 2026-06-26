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
from tests.helpers.payloads import roster_coach_payload, roster_player_payload, team_payload

_BASE = "https://test.example"
_SEASON_ID = "15020"
_TEAM_ID = "12345"
_PLAYERS_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/players"
_COACHES_ENDPOINT = f"{_BASE}/api/seasons/{_SEASON_ID}/coaches"


@responses.activate
def test_create_player_minimal_fields(config: Config) -> None:
    """Test creating a player with only required fields."""
    player_response = roster_player_payload(season_id=_SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")
    assert result.id == "8043169"
    assert result.first_name == "AUSTIN"
    assert result.last_name == "ADAMSKY"
    assert result.season_id == _SEASON_ID


@responses.activate
def test_create_player_with_external_id(config: Config) -> None:
    """Test creating a player with external_id."""
    player_response = roster_player_payload(season_id=_SEASON_ID)
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
            _SEASON_ID,
            "AUSTIN",
            "ADAMSKY",
            external_id="BC7732F4-4993-492E-8CCB-4C2CA9C1912E",
        )
    assert result.external_id == "BC7732F4-4993-492E-8CCB-4C2CA9C1912E"


@responses.activate
def test_create_player_with_all_profile_fields(config: Config) -> None:
    """Test creating a player with all profile fields (biography, height, etc.)."""
    player_response = roster_player_payload(season_id=_SEASON_ID)
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
            _SEASON_ID,
            "AUSTIN",
            "ADAMSKY",
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
    assert result.id == "8043169"


@responses.activate
def test_create_player_with_optional_fields(config: Config) -> None:
    """Test creating a player with all optional fields."""
    player_response = roster_player_payload(season_id=_SEASON_ID)
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
            _SEASON_ID,
            "AUSTIN",
            "ADAMSKY",
            external_id="BC7732F4-4993-492E-8CCB-4C2CA9C1912E",
            jersey="98",
            position="Forward",
            status="Regular",
            designation="Captain",
        )
    assert result.id == "8043169"


@responses.activate
def test_create_player_with_team_id(config: Config) -> None:
    """Test creating a player with team_id."""
    player_response = roster_player_payload(season_id=_SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY", team_id=_TEAM_ID)
    assert result.id == "8043169"


@responses.activate
def test_create_player_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")


@responses.activate
def test_create_player_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")


@responses.activate
def test_create_player_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            create_player(session, _SEASON_ID, "AUSTIN", "ADAMSKY")


@responses.activate
def test_create_coach_minimal_fields(config: Config) -> None:
    """Test creating a coach with only required fields."""
    coach_response = roster_coach_payload(season_id=_SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")
    assert result.id == "1868550"
    assert result.first_name == "SHAWN"
    assert result.last_name == "ALLIE"
    assert result.season_id == _SEASON_ID


@responses.activate
def test_create_coach_with_external_id(config: Config) -> None:
    """Test creating a coach with external_id."""
    coach_response = roster_coach_payload(season_id=_SEASON_ID)
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
            _SEASON_ID,
            "SHAWN",
            "ALLIE",
            external_id="530b7441-1db6-437e-8e5f-777ab3f6cd6c",
        )
    assert result.external_id == "530b7441-1db6-437e-8e5f-777ab3f6cd6c"


@responses.activate
def test_create_coach_with_position(config: Config) -> None:
    """Test creating a coach with position."""
    coach_response = roster_coach_payload(season_id=_SEASON_ID, external_id=None)
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
            _SEASON_ID,
            "SHAWN",
            "ALLIE",
            position="Head Coach",
        )
    assert result.id == "1868550"


@responses.activate
def test_create_coach_with_team_id(config: Config) -> None:
    """Test creating a coach with team_id."""
    coach_response = roster_coach_payload(season_id=_SEASON_ID, external_id=None)
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_coach(session, _SEASON_ID, "SHAWN", "ALLIE", team_id=_TEAM_ID)
    assert result.id == "1868550"


@responses.activate
def test_create_coach_401_raises_authentication_error(config: Config) -> None:
    """Test that 401 response raises AuthenticationError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=401)
    with Session(config) as session:
        session.set_bearer_token("expired")
        with pytest.raises(AuthenticationError, match=r"401"):
            create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")


@responses.activate
def test_create_coach_404_raises_gamesheet_error(config: Config) -> None:
    """Test that 404 response raises GameSheetError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=404)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"404"):
            create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")


@responses.activate
def test_create_coach_500_raises_gamesheet_error(config: Config) -> None:
    """Test that 500 response raises GameSheetError."""
    responses.add(responses.POST, _COACHES_ENDPOINT, json={}, status=500)
    with Session(config) as session:
        session.set_bearer_token("valid")
        with pytest.raises(GameSheetError, match=r"500"):
            create_coach(session, _SEASON_ID, "SHAWN", "ALLIE")


@responses.activate
def test_create_team_player_calls_create_player_with_team_id(config: Config) -> None:
    """Test that create_team_player creates player and adds to team roster."""
    player_response = roster_player_payload(season_id=_SEASON_ID)
    # Mock POST to create player
    responses.add(
        responses.POST,
        _PLAYERS_ENDPOINT,
        json={"data": player_response},
        status=201,
    )
    # Mock GET team to fetch current roster
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    # Mock PATCH to update team roster
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(session, _SEASON_ID, _TEAM_ID, "AUSTIN", "ADAMSKY")
    assert result.id == "8043169"


@responses.activate
def test_create_team_coach_calls_create_coach_with_team_id(config: Config) -> None:
    """Test that create_team_coach creates coach and adds to team roster."""
    coach_response = roster_coach_payload(season_id=_SEASON_ID, external_id=None)
    # Mock POST to create coach
    responses.add(
        responses.POST,
        _COACHES_ENDPOINT,
        json={"data": coach_response},
        status=201,
    )
    # Mock GET team to fetch current roster
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    # Mock PATCH to update team roster
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_coach(session, _SEASON_ID, _TEAM_ID, "SHAWN", "ALLIE")
    assert result.id == "1868550"
    assert result.status == "coaching"


@responses.activate
def test_create_team_player_with_optional_fields(config: Config) -> None:
    """Test that create_team_player handles optional fields."""
    player_response = roster_player_payload(season_id=_SEASON_ID)
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={"data": player_response}, status=201)
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            _SEASON_ID,
            _TEAM_ID,
            "AUSTIN",
            "ADAMSKY",
            jersey="99",
            position="Forward",
            status="Regular",
            designation="Captain",
        )
    assert result.id == "8043169"
    assert result.number == "99"
    assert result.position == "Forward"
    assert result.status == "Regular"
    assert result.designation == "Captain"


@responses.activate
def test_create_team_player_with_affiliated_status(config: Config) -> None:
    """Test that create_team_player handles Affiliated status."""
    player_response = roster_player_payload(season_id=_SEASON_ID)
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={"data": player_response}, status=201)
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            _SEASON_ID,
            _TEAM_ID,
            "AUSTIN",
            "ADAMSKY",
            status="Affiliated",
        )
    assert result.id == "8043169"


@responses.activate
def test_create_team_coach_with_position(config: Config) -> None:
    """Test that create_team_coach handles position parameter."""
    coach_response = roster_coach_payload(season_id=_SEASON_ID, external_id=None)
    responses.add(responses.POST, _COACHES_ENDPOINT, json={"data": coach_response}, status=201)
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_coach(
            session,
            _SEASON_ID,
            _TEAM_ID,
            "SHAWN",
            "ALLIE",
            position="Head Coach",
        )
    assert result.id == "1868550"
    assert result.position == "Head Coach"
    assert result.status == "coaching"


@responses.activate
def test_create_team_player_with_external_id(config: Config) -> None:
    """Test that create_team_player handles external_id parameter."""
    player_response = roster_player_payload(season_id=_SEASON_ID, external_id="TEST-EXT-123")
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={"data": player_response}, status=201)
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            _SEASON_ID,
            _TEAM_ID,
            "AUSTIN",
            "ADAMSKY",
            external_id="TEST-EXT-123",
        )
    assert result.id == "8043169"
    assert result.external_id == "TEST-EXT-123"


@responses.activate
def test_create_team_coach_with_external_id(config: Config) -> None:
    """Test that create_team_coach handles external_id parameter."""
    coach_response = roster_coach_payload(season_id=_SEASON_ID, external_id="TEST-EXT-456")
    responses.add(responses.POST, _COACHES_ENDPOINT, json={"data": coach_response}, status=201)
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_coach(
            session,
            _SEASON_ID,
            _TEAM_ID,
            "SHAWN",
            "ALLIE",
            external_id="TEST-EXT-456",
        )
    assert result.id == "1868550"
    assert result.external_id == "TEST-EXT-456"


@responses.activate
def test_create_team_player_with_all_profile_fields(config: Config) -> None:
    """Test that create_team_player handles all profile fields."""
    player_response = roster_player_payload(season_id=_SEASON_ID, external_id="TEST-PROFILE")
    responses.add(responses.POST, _PLAYERS_ENDPOINT, json={"data": player_response}, status=201)
    team_data = team_payload(_TEAM_ID)
    responses.add(
        responses.GET,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{_BASE}/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            _SEASON_ID,
            _TEAM_ID,
            "AUSTIN",
            "ADAMSKY",
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
    assert result.id == "8043169"
    assert result.external_id == "TEST-PROFILE"


@responses.activate
def test_create_player_with_photo(config: Config) -> None:
    """Test creating a player with photo upload."""
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
    # Mock player creation
    player_response = roster_player_payload(season_id=_SEASON_ID)
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
            _SEASON_ID,
            "AUSTIN",
            "ADAMSKY",
            photo_path=temp_path,
        )
    assert result.id == "8043169"


@responses.activate
def test_create_team_player_with_photo(config: Config) -> None:
    """Test creating a team player with photo upload."""
    import tempfile

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jpg", delete=False) as temp_file:
        temp_file.write("fake image content")
        team_temp_path = temp_file.name

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
    # Mock player creation
    player_response = roster_player_payload(season_id=_SEASON_ID)
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
        f"https://test.example/api/seasons/{_SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_response},
        status=200,
    )
    # Mock team update
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{_SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_response},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = create_team_player(
            session,
            _SEASON_ID,
            _TEAM_ID,
            "AUSTIN",
            "ADAMSKY",
            photo_path=team_temp_path,
        )
    assert result.id == "8043169"
