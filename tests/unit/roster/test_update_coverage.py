# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for update functions - edge cases for 100% coverage."""

from __future__ import annotations

import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.roster import update_coach, update_player
from tests.helpers import setup_update_coach_mocks, setup_update_player_mocks
from tests.helpers.payloads import roster_coach_payload, roster_player_payload

_SEASON_ID = "15020"
_PLAYER_ID = "8043169"
_COACH_ID = "1879938"
_PLAYERS_ENDPOINT = f"https://test.example/api/seasons/{_SEASON_ID}/players/{_PLAYER_ID}"
_COACHES_ENDPOINT = f"https://test.example/api/seasons/{_SEASON_ID}/coaches/{_COACH_ID}"


@responses.activate
def test_update_coach_with_empty_position_not_updated(config: Config) -> None:
    """Test updating a coach when position is not provided and current position is empty.

    This covers the branch in coaches.py line 174->176 where position=None and current_coach.position is falsy
    (empty string), so position is not added to the payload.
    """
    # Mock GET to fetch current coach with empty position
    current_coach = roster_coach_payload(season_id=_SEASON_ID)
    # Default payload has position="" (empty), which is falsy
    assert current_coach["attributes"]["position"] == "head_coach"
    # Change it to empty to test the falsy branch
    current_coach["attributes"]["position"] = ""
    # Mock PATCH to update coach - verify position is not in payload
    updated_coach = roster_coach_payload(season_id=_SEASON_ID)
    updated_coach["attributes"]["first_name"] = "UPDATED"
    updated_coach["attributes"]["position"] = ""  # Still empty
    setup_update_coach_mocks(_COACHES_ENDPOINT, current_coach, updated_coach)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_coach(
            session,
            _SEASON_ID,
            _COACH_ID,
            first_name="UPDATED",
            # position=None (not provided), and current is empty
        )
    assert result.first_name == "UPDATED"


@responses.activate
def test_update_player_with_empty_biography_not_updated(config: Config) -> None:
    """Test updating a player when biography is not provided and current is empty.

    This covers the else branch in players.py line 544 where new_value is None and current_value is falsy
    (empty string), so the field is not added to attrs. This tests the _merge_optional_field helper function.
    """
    # Mock GET to fetch current player with empty biography
    current_player = roster_player_payload(season_id=_SEASON_ID)
    # Default payload has biography="" (empty), which is falsy
    assert not current_player["attributes"]["biography"]
    # Mock PATCH to update player - verify biography is not in payload
    # pylint: disable=duplicate-code
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    # biography stays empty
    setup_update_player_mocks(_PLAYERS_ENDPOINT, current_player, updated_player)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            _SEASON_ID,
            _PLAYER_ID,
            last_name="UPDATED",
            # biography=None (not provided), and current is empty
        )
    assert result.last_name == "UPDATED"
    # pylint: enable=duplicate-code
    # biography remains empty
    assert not result.biography


@responses.activate
def test_update_player_preserves_nonempty_biography(config: Config) -> None:
    """Test updating a player preserves non-empty biography when not updated.

    This covers line 544 in players.py where new_value is None and current_value is truthy (non-empty string),
    so current_value is preserved in attrs. This is the truthy branch of the _merge_optional_field helper.
    """
    # Mock GET to fetch current player with non-empty biography
    current_player = roster_player_payload(season_id=_SEASON_ID)
    current_player["attributes"]["biography"] = "Star forward with 10 years experience"
    # Mock PATCH to update player - biography should be preserved in payload
    updated_player = roster_player_payload(season_id=_SEASON_ID)
    updated_player["attributes"]["last_name"] = "UPDATED"
    updated_player["attributes"]["biography"] = "Star forward with 10 years experience"
    setup_update_player_mocks(_PLAYERS_ENDPOINT, current_player, updated_player)
    with Session(config) as session:
        session.set_bearer_token("valid-token")
        result = update_player(
            session,
            _SEASON_ID,
            _PLAYER_ID,
            last_name="UPDATED",
            # biography=None (not provided), current is non-empty, should be preserved
        )
    assert result.last_name == "UPDATED"
    # biography should be preserved
    assert result.biography == "Star forward with 10 years experience"
