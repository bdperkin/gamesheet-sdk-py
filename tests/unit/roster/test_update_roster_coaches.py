# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for update_coach and update_team_coach functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.admin.roster import update_coach, update_team_coach
from tests.fixtures.constants import TEST_ERROR_PATTERN_AT_LEAST_ONE_FIELD
from tests.helpers import (
    COACH_ID_SECONDARY,
    SEASON_ID,
    TEAM_ID_SECONDARY,
    TEST_BASE_URL,
    setup_update_coach_mocks,
)
from tests.helpers.payloads import roster_coach_payload, team_payload

_TEAM_ID = TEAM_ID_SECONDARY
_COACHES_ENDPOINT = f"{TEST_BASE_URL}/api/seasons/{SEASON_ID}/coaches/{COACH_ID_SECONDARY}"


@responses.activate
def test_update_coach_updates_fields(config: Config) -> None:
    """Test updating a coach updates the specified fields."""
    # Mock GET to fetch current coach
    current_coach = roster_coach_payload(season_id=SEASON_ID)
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=SEASON_ID)
    updated_coach["attributes"]["last_name"] = "UPDATED"
    setup_update_coach_mocks(_COACHES_ENDPOINT, current_coach, updated_coach)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_coach(
            session,
            SEASON_ID,
            COACH_ID_SECONDARY,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_coach_no_fields_raises_error(config: Config) -> None:
    """Test updating a coach with no fields raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match=TEST_ERROR_PATTERN_AT_LEAST_ONE_FIELD):
            update_coach(session, SEASON_ID, COACH_ID_SECONDARY)


@responses.activate
def test_update_team_coach_updates_fields(config: Config) -> None:
    """Test updating a team coach updates the specified fields."""
    # Mock GET team to fetch current team coach (via list_team_coaches)
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
    )
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": COACH_ID_SECONDARY,
                "position": "Head Coach",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    team_data["relationships"]["coaches"] = {
        "data": [{"type": "coaches", "id": COACH_ID_SECONDARY}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=SEASON_ID)
    updated_coach["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/coaches/{COACH_ID_SECONDARY}",
        json={"data": updated_coach},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            SEASON_ID,
            _TEAM_ID,
            COACH_ID_SECONDARY,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_team_coach_with_position_updates_roster(config: Config) -> None:
    """Test updating a team coach with position updates the team roster."""
    # Mock GET team to fetch current team coach (via list_team_coaches)
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
    )
    current_coach_payload["attributes"]["position"] = "Assistant Coach"
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": COACH_ID_SECONDARY,
                "position": "Assistant Coach",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    team_data["relationships"]["coaches"] = {
        "data": [{"type": "coaches", "id": COACH_ID_SECONDARY}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=SEASON_ID)
    updated_coach["attributes"]["position"] = "Head Coach"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/coaches/{COACH_ID_SECONDARY}",
        json={"data": updated_coach},
        status=200,
    )
    # Mock team GET for roster update (second call for position change)
    team_data2 = team_payload()
    team_data2["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": COACH_ID_SECONDARY,
                "position": "Assistant Coach",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data2},
        status=200,
    )
    # Mock team PATCH for roster update
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data2},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            SEASON_ID,
            _TEAM_ID,
            COACH_ID_SECONDARY,
            position="Head Coach",
        )
    assert result.position == "Head Coach"


@responses.activate
def test_update_coach_with_all_fields(config: Config) -> None:
    """Test updating a coach with all fields."""
    # Mock GET to fetch current coach
    current_coach = roster_coach_payload(season_id=SEASON_ID)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": current_coach},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=SEASON_ID)
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
            SEASON_ID,
            COACH_ID_SECONDARY,
            first_name="NEW",
            last_name="COACH",
            position="Head Coach",
            external_id="ext-123",
        )
    assert result.first_name == "NEW"
    assert result.last_name == "COACH"


@responses.activate
def test_update_team_coach_no_fields_raises_error(config: Config) -> None:
    """Test updating a team coach with no fields raises ValueError."""
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        with pytest.raises(ValueError, match=TEST_ERROR_PATTERN_AT_LEAST_ONE_FIELD):
            update_team_coach(session, SEASON_ID, _TEAM_ID, COACH_ID_SECONDARY)


@responses.activate
def test_update_coach_preserves_existing_position(config: Config) -> None:
    """Test updating a coach preserves existing position when position=None."""
    # Mock GET to fetch current coach with position set
    current_coach = roster_coach_payload(season_id=SEASON_ID)
    current_coach["attributes"]["position"] = "Assistant Coach"
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": current_coach},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=SEASON_ID)
    updated_coach["attributes"]["last_name"] = "UPDATED"
    updated_coach["attributes"]["position"] = "Assistant Coach"
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
            SEASON_ID,
            COACH_ID_SECONDARY,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_coach_preserves_existing_external_id(config: Config) -> None:
    """Test updating a coach preserves existing external_id when external_id=None."""
    # Mock GET to fetch current coach with external_id set
    current_coach = roster_coach_payload(
        season_id=SEASON_ID,
        external_id="existing-ext-id",
    )
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": current_coach},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(
        season_id=SEASON_ID,
        external_id="existing-ext-id",
    )
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
            SEASON_ID,
            COACH_ID_SECONDARY,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"
    assert result.external_id == "existing-ext-id"


@responses.activate
def test_update_team_coach_with_external_id(config: Config) -> None:
    """Test updating a team coach with explicit external_id."""
    # Mock GET team to fetch current team coach
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
        external_id=None,
    )
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": COACH_ID_SECONDARY,
                "position": "Head Coach",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    team_data["relationships"]["coaches"] = {
        "data": [{"type": "coaches", "id": COACH_ID_SECONDARY}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
        external_id="new-ext-id",
    )
    updated_coach["attributes"]["external_id"] = "new-ext-id"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/coaches/{COACH_ID_SECONDARY}",
        json={"data": updated_coach},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            SEASON_ID,
            _TEAM_ID,
            COACH_ID_SECONDARY,
            external_id="new-ext-id",
        )
    assert result.external_id == "new-ext-id"


@responses.activate
def test_update_coach_with_no_external_id_preserved(config: Config) -> None:
    """Test updating a coach when neither new nor current external_id exists."""
    # Mock GET to fetch current coach without external_id
    current_coach = roster_coach_payload(season_id=SEASON_ID, external_id=None)
    responses.add(
        responses.GET,
        _COACHES_ENDPOINT,
        json={"data": current_coach},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=SEASON_ID, external_id=None)
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
            SEASON_ID,
            COACH_ID_SECONDARY,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_team_coach_preserves_existing_external_id(config: Config) -> None:
    """Test updating a team coach preserves existing external_id when external_id=None."""
    # Mock GET team to fetch current team coach with external_id
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
        external_id="existing-ext-id",
    )
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": COACH_ID_SECONDARY,
                "position": "Head Coach",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    team_data["relationships"]["coaches"] = {
        "data": [{"type": "coaches", "id": COACH_ID_SECONDARY}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
        external_id="existing-ext-id",
    )
    updated_coach["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/coaches/{COACH_ID_SECONDARY}",
        json={"data": updated_coach},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            SEASON_ID,
            _TEAM_ID,
            COACH_ID_SECONDARY,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"
    assert result.external_id == "existing-ext-id"


@responses.activate
def test_update_team_coach_with_no_external_id_preserved(config: Config) -> None:
    """Test updating a team coach when neither new nor current external_id exists."""
    # Mock GET team to fetch current team coach without external_id
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
        external_id=None,
    )
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": COACH_ID_SECONDARY,
                "position": "Head Coach",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    team_data["relationships"]["coaches"] = {
        "data": [{"type": "coaches", "id": COACH_ID_SECONDARY}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
        external_id=None,
    )
    updated_coach["attributes"]["last_name"] = "UPDATED"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/coaches/{COACH_ID_SECONDARY}",
        json={"data": updated_coach},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            SEASON_ID,
            _TEAM_ID,
            COACH_ID_SECONDARY,
            last_name="UPDATED",
        )
    assert result.last_name == "UPDATED"


@responses.activate
def test_update_team_coach_position_when_not_in_roster(config: Config) -> None:
    """Test updating position when coach not in roster (edge case for coverage)."""
    # Mock GET team to fetch current team coach
    team_data = team_payload()
    current_coach_payload = roster_coach_payload(
        coach_id=COACH_ID_SECONDARY,
        season_id=SEASON_ID,
    )
    current_coach_payload["attributes"]["position"] = "Assistant Coach"
    team_data["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": COACH_ID_SECONDARY,
                "position": "Assistant Coach",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    team_data["relationships"]["coaches"] = {
        "data": [{"type": "coaches", "id": COACH_ID_SECONDARY}],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}?include=players%2Ccoaches",
        json={"data": team_data, "included": [current_coach_payload]},
        status=200,
    )
    # Mock PATCH to update coach
    updated_coach = roster_coach_payload(season_id=SEASON_ID)
    updated_coach["attributes"]["position"] = "Head Coach"
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/coaches/{COACH_ID_SECONDARY}",
        json={"data": updated_coach},
        status=200,
    )
    # Mock team GET for roster update - roster has OTHER coaches but not this one
    team_data2 = team_payload()
    team_data2["attributes"]["roster"] = {
        "players": [],
        "coaches": [
            {
                "id": "other-coach-1",
                "position": "Head Coach",
                "status": "coaching",
                "signature": "",
            },
            {
                "id": "other-coach-2",
                "position": "Assistant",
                "status": "coaching",
                "signature": "",
            },
        ],
    }
    responses.add(
        responses.GET,
        f"https://test.example/api/seasons/{SEASON_ID}/teams/{_TEAM_ID}",
        json={"data": team_data2},
        status=200,
    )
    # Mock team PATCH for roster update
    responses.add(
        responses.PATCH,
        f"https://test.example/api/seasons/{SEASON_ID}/teams-v2/{_TEAM_ID}",
        json={"data": team_data2},
        status=200,
    )
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_team_coach(
            session,
            SEASON_ID,
            _TEAM_ID,
            COACH_ID_SECONDARY,
            position="Head Coach",
        )
    assert result.position == "Head Coach"
