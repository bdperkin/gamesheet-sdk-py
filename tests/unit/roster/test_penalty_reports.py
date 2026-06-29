# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for penalty report functions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gamesheet_sdk.roster import (
    get_coach_penalty_report,
    get_player_penalty_report,
)
from tests.helpers import (
    COACH_EXTERNAL_ID_TERTIARY,
    PLAYER_EXTERNAL_ID_SECONDARY,
)


def test_get_coach_penalty_report_success(mock_session: MagicMock) -> None:
    """Test successful coach penalty report retrieval."""
    mock_coach_response = MagicMock()
    mock_coach_response.status_code = 200
    mock_coach_response.json.return_value = {
        "data": {
            "id": "1879742",
            "type": "coaches",
            "attributes": {
                "external_id": PLAYER_EXTERNAL_ID_SECONDARY,
                "first_name": "SCOTTY",
                "last_name": "BOWMAN",
                "created_at": "2026-06-25T02:49:39.469641Z",
                "updated_at": "2026-06-29T04:18:09.831608Z",
                "vendor_data": {},
                "suspension": {"number": 0, "length": 0},
            },
        },
    }
    mock_penalty_response = MagicMock()
    mock_penalty_response.status_code = 200
    mock_penalty_response.json.return_value = {
        "status": "success",
        "data": {
            "coach_games": [],
            "coach_penalties": [],
            "rostered_coaches": [],
            "season_coaches": [],
        },
    }
    mock_session.get.side_effect = [mock_coach_response, mock_penalty_response]
    report = get_coach_penalty_report(mock_session, "15020", "1879742")
    assert "coach_games" in report
    assert "coach_penalties" in report
    assert mock_session.get.call_count == 2


def test_get_player_penalty_report_success(mock_session: MagicMock) -> None:
    """Test successful player penalty report retrieval."""
    mock_player_response = MagicMock()
    mock_player_response.status_code = 200
    mock_player_response.json.return_value = {
        "data": {
            "id": "8113805",
            "type": "players",
            "attributes": {
                "external_id": COACH_EXTERNAL_ID_TERTIARY,
                "first_name": "WAYNE",
                "last_name": "GRETZKY",
                "birthdate": None,
                "photo_url": "",
                "biography": "",
                "height": "",
                "weight": "",
                "shot_hand": "",
                "province": "",
                "hometown": "",
                "country": "",
                "drafted_by": "",
                "committed_to": "",
                "created_at": "2026-06-25T03:22:59.567319Z",
                "updated_at": "2026-06-29T04:18:09.778981Z",
                "vendor_data": {},
                "suspension": {"number": 0, "length": 0},
            },
        },
    }
    mock_penalty_response = MagicMock()
    mock_penalty_response.status_code = 200
    mock_penalty_response.json.return_value = {
        "status": "success",
        "data": {
            "player_games": [],
            "player_penalties": [],
            "rostered_players": [],
            "season_players": [],
        },
    }
    mock_session.get.side_effect = [mock_player_response, mock_penalty_response]
    report = get_player_penalty_report(mock_session, "15020", "8113805")
    assert "player_games" in report
    assert "player_penalties" in report
    assert mock_session.get.call_count == 2


def test_get_coach_penalty_report_api_error(mock_session: MagicMock) -> None:
    """Test coach penalty report when API returns error status."""
    from gamesheet_sdk.exceptions import GameSheetError

    mock_coach_response = MagicMock()
    mock_coach_response.status_code = 200
    mock_coach_response.json.return_value = {
        "data": {
            "id": "1879742",
            "type": "coaches",
            "attributes": {
                "external_id": PLAYER_EXTERNAL_ID_SECONDARY,
                "first_name": "SCOTTY",
                "last_name": "BOWMAN",
                "created_at": "2026-06-25T02:49:39.469641Z",
                "updated_at": "2026-06-29T04:18:09.831608Z",
                "vendor_data": {},
                "suspension": {"number": 0, "length": 0},
            },
        },
    }
    mock_penalty_response = MagicMock()
    mock_penalty_response.status_code = 200
    mock_penalty_response.json.return_value = {
        "status": "error",
        "message": "Coach not found",
    }
    mock_session.get.side_effect = [mock_coach_response, mock_penalty_response]
    with pytest.raises(GameSheetError, match="status: error"):
        get_coach_penalty_report(mock_session, "15020", "1879742")


def test_get_player_penalty_report_api_error(mock_session: MagicMock) -> None:
    """Test player penalty report when API returns error status."""
    from gamesheet_sdk.exceptions import GameSheetError

    mock_player_response = MagicMock()
    mock_player_response.status_code = 200
    mock_player_response.json.return_value = {
        "data": {
            "id": "8113805",
            "type": "players",
            "attributes": {
                "external_id": COACH_EXTERNAL_ID_TERTIARY,
                "first_name": "WAYNE",
                "last_name": "GRETZKY",
                "birthdate": None,
                "photo_url": "",
                "biography": "",
                "height": "",
                "weight": "",
                "shot_hand": "",
                "province": "",
                "hometown": "",
                "country": "",
                "drafted_by": "",
                "committed_to": "",
                "created_at": "2026-06-25T03:22:59.567319Z",
                "updated_at": "2026-06-29T04:18:09.778981Z",
                "vendor_data": {},
                "suspension": {"number": 0, "length": 0},
            },
        },
    }
    mock_penalty_response = MagicMock()
    mock_penalty_response.status_code = 200
    mock_penalty_response.json.return_value = {
        "status": "error",
        "message": "Player not found",
    }
    mock_session.get.side_effect = [mock_player_response, mock_penalty_response]
    with pytest.raises(GameSheetError, match="status: error"):
        get_player_penalty_report(mock_session, "15020", "8113805")
