# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Test mock helpers for common API responses."""

from __future__ import annotations

import tempfile
from typing import Any

import responses

from tests.fixtures.constants import TEST_FAKE_IMAGE_CONTENT
from tests.helpers.constants import BFF_ASSETS_UPLOAD_URL_PATH, TEST_BFF_BASE_URL


def setup_photo_upload_mocks(
    *,
    upload_status: int = 200,
    upload_response: dict[str, Any] | None = None,
) -> str:
    """Set up mock responses for photo upload and return temp file path.

    Creates a temporary image file and sets up the mock responses needed for photo upload via the BFF API and
    Cloudflare upload endpoint.

    Args:
        upload_status (int): HTTP status code for the upload request (default 200).
        upload_response (dict[str, Any] | None): JSON response for the upload request (default {"success":
            True}).

    Returns:
        str: Path to the temporary image file.

    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jpg",
        delete=False,
    ) as temp_file:
        temp_file.write(TEST_FAKE_IMAGE_CONTENT)
        temp_path = temp_file.name
    # Mock upload URL request
    responses.add(
        responses.POST,
        f"{TEST_BFF_BASE_URL}{BFF_ASSETS_UPLOAD_URL_PATH}",
        json={
            "status": "success",
            "data": {
                "uploadURL": "https://upload.example.com/test",
                "id": "test-image-id",
            },
        },
        status=200,
    )
    # Mock upload request
    responses.add(
        responses.POST,
        "https://upload.example.com/test",
        json=upload_response if upload_response is not None else {"success": True},
        status=upload_status,
    )
    return temp_path


def setup_team_roster_update_mocks(
    base_url: str,
    season_id: str,
    team_id: str,
    team_data: dict[str, Any],
) -> None:
    """Set up mock responses for team roster update operations.

    Mocks the GET team endpoint to fetch current roster and PATCH endpoint to update team roster.

    Args:
        base_url (str): Base API URL.
        season_id (str): Season ID.
        team_id (str): Team ID.
        team_data (dict[str, Any]): Team payload data.

    """
    # Mock GET team to fetch current roster
    responses.add(
        responses.GET,
        f"{base_url}/api/seasons/{season_id}/teams/{team_id}",
        json={"data": team_data},
        status=200,
    )
    # Mock PATCH to update team roster
    responses.add(
        responses.PATCH,
        f"{base_url}/api/seasons/{season_id}/teams-v2/{team_id}",
        json={"data": team_data},
        status=200,
    )


def setup_update_player_mocks(
    endpoint: str,
    current_player: dict[str, Any],
    updated_player: dict[str, Any],
) -> None:
    """Set up mock responses for player update operations.

    Mocks the GET player endpoint to fetch current player and PATCH endpoint to update player.

    Args:
        endpoint (str): Player endpoint URL.
        current_player (dict[str, Any]): Current player payload data.
        updated_player (dict[str, Any]): Updated player payload data.

    """
    # Mock GET player to fetch current data
    responses.add(
        responses.GET,
        endpoint,
        json={"data": current_player},
        status=200,
    )
    # Mock PATCH to update player
    responses.add(
        responses.PATCH,
        endpoint,
        json={"data": updated_player},
        status=200,
    )


def setup_update_coach_mocks(
    endpoint: str,
    current_coach: dict[str, Any],
    updated_coach: dict[str, Any],
) -> None:
    """Set up mock responses for coach update operations.

    Mocks the GET coach endpoint to fetch current coach and PATCH endpoint to update coach.

    Args:
        endpoint (str): Coach endpoint URL.
        current_coach (dict[str, Any]): Current coach payload data.
        updated_coach (dict[str, Any]): Updated coach payload data.

    """
    # Mock GET coach to fetch current data
    responses.add(
        responses.GET,
        endpoint,
        json={"data": current_coach},
        status=200,
    )
    # Mock PATCH to update coach
    responses.add(
        responses.PATCH,
        endpoint,
        json={"data": updated_coach},
        status=200,
    )


def setup_get_team_roster_mocks(
    endpoint: str,
    team_id: str,
    roster_data: dict[str, Any],
    included: list[dict[str, Any]],
) -> None:
    """Set up mock response for getting team with roster data.

    Mocks the GET team endpoint which returns team data with roster and included player/coach resources.

    Args:
        endpoint (str): Team GET endpoint URL.
        team_id (str): Team ID.
        roster_data (dict[str, Any]): Team roster attributes (players and coaches arrays).
        included (list[dict[str, Any]]): List of included player/coach resource objects.

    """
    responses.add(
        responses.GET,
        endpoint,
        json={
            "data": {
                "type": "teams",
                "id": team_id,
                "attributes": {"roster": roster_data},
            },
            "included": included,
        },
        status=200,
    )
