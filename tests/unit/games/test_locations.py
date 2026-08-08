# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for location-related functions."""

from __future__ import annotations

import pytest
import responses

from gamesheet_sdk import Config, Session
from gamesheet_sdk.admin.games import (
    Location,
    get_location,
    list_locations,
    validate_location,
)
from gamesheet_sdk.common.constants import DEFAULT_BASE_URL
from gamesheet_sdk.common.exceptions import GameSheetError
from tests.fixtures.constants import (
    TEST_BEARER_TOKEN,
    TEST_CITY,
    TEST_COUNTRY,
    TEST_LOCATION_NAME,
    TEST_PROVINCE_STATE,
    TEST_SURFACE_NAME,
)
from tests.unit.games.conftest import add_mock_locations_response


def test_location_full_name() -> None:
    """Test Location.full_name() method."""
    loc = Location(
        id="loc-1",
        location_name="Scotiabank Arena",
        surface_name="Main Ice",
        city="Toronto",
        province_state="ON",
        country="Canada",
    )
    assert loc.full_name() == "Scotiabank Arena Main Ice"


# Lines 494-500: list_broadcasters()


@responses.activate
def test_list_locations() -> None:
    """Test list_locations function."""
    add_mock_locations_response()
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        locations = list_locations(session)

    assert len(locations) == 1
    assert locations[0].id == "loc-1"


# Lines 563-571: get_location()


@responses.activate
def test_get_location_found() -> None:
    """Test get_location with existing location."""
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={
            "data": [
                {
                    "id": "loc-123",
                    "location_name": TEST_LOCATION_NAME,
                    "surface_name": TEST_SURFACE_NAME,
                    "city": TEST_CITY,
                    "province_state": TEST_PROVINCE_STATE,
                    "country": TEST_COUNTRY,
                },
            ],
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        location = get_location(session, "loc-123")

    assert location.id == "loc-123"


@responses.activate
def test_get_location_not_found() -> None:
    """Test get_location with non-existent location."""
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={"data": []},
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        with pytest.raises(GameSheetError, match=r"Location.*not found"):
            get_location(session, "loc-999")


# Lines 588-604: validate_location()


@responses.activate
def test_validate_location_valid() -> None:
    """Test validate_location with valid location."""
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={
            "data": [
                {
                    "id": "loc-1",
                    "location_name": TEST_LOCATION_NAME,
                    "surface_name": TEST_SURFACE_NAME,
                    "city": TEST_CITY,
                    "province_state": TEST_PROVINCE_STATE,
                    "country": TEST_COUNTRY,
                },
            ],
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        # Test case-insensitive match
        result = validate_location(session, "arena a ice 1")

    assert result == "Arena A Ice 1"


@responses.activate
def test_validate_location_empty() -> None:
    """Test validate_location with empty string."""
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        result = validate_location(session, "")

    assert not result


@responses.activate
def test_validate_location_invalid() -> None:
    """Test validate_location with invalid location."""
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={
            "data": [
                {
                    "id": "loc-1",
                    "location_name": TEST_LOCATION_NAME,
                    "surface_name": TEST_SURFACE_NAME,
                    "city": TEST_CITY,
                    "province_state": TEST_PROVINCE_STATE,
                    "country": TEST_COUNTRY,
                },
            ],
        },
        status=200,
    )
    config = Config(base_url=DEFAULT_BASE_URL)
    with Session(config) as session:
        session.set_bearer_token(TEST_BEARER_TOKEN)
        with pytest.raises(GameSheetError, match=r"Invalid location.*Examples"):
            validate_location(session, "Invalid Location")


# Lines 614-616: validate_game_type()


@responses.activate
def test_get_location_empty_list() -> None:
    """Test get_location when locations list is empty (loop never enters)."""
    config = Config(base_url=DEFAULT_BASE_URL)
    session = Session(config)

    # Mock empty locations list
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={"data": []},
        status=200,
    )

    with pytest.raises(GameSheetError, match=r"Location 'loc-1' not found"):
        get_location(session, "loc-1")


@responses.activate
def test_get_location_not_in_list() -> None:
    """Test get_location when location is not in a non-empty list (loop enters but no match)."""
    config = Config(base_url=DEFAULT_BASE_URL)
    session = Session(config)

    # Mock non-empty locations list without the requested location
    responses.add(
        responses.GET,
        f"{DEFAULT_BASE_URL}/api/locations",
        json={
            "data": [
                {
                    "id": "loc-2",
                    "location_name": "Arena B",
                    "surface_name": "Ice 2",
                    "city": "Montreal",
                    "province_state": "QC",
                    "country": "Canada",
                },
                {
                    "id": "loc-3",
                    "location_name": "Arena C",
                    "surface_name": "Ice 3",
                    "city": "Vancouver",
                    "province_state": "BC",
                    "country": "Canada",
                },
            ],
        },
        status=200,
    )

    with pytest.raises(GameSheetError, match=r"Location 'loc-1' not found"):
        get_location(session, "loc-1")  # Request loc-1 which isn't in the list
