# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for locations get command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.games import Location


def test_locations_get_basic(runner: CliRunner) -> None:
    """The locations get command should retrieve a single location."""
    with (
        patch("gamesheet_sdk.admin.cli.commands.locations._get_location_action") as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Location(
            id="550e8400-e29b-41d4-a716-446655440000",
            location_name="Scotiabank Arena",
            surface_name="Main Ice",
            city="Toronto",
            province_state="ON",
            country="Canada",
        )
        result = runner.invoke(
            cli,
            [
                "locations",
                "get",
                "--location-id",
                "550e8400-e29b-41d4-a716-446655440000",
            ],
        )
        assert not result.exit_code
        mock_get.assert_called_once()
        args = mock_get.call_args[0]
        assert args[1] == "550e8400-e29b-41d4-a716-446655440000"


def test_locations_get_json_output(runner: CliRunner) -> None:
    """The locations get command should support JSON output."""
    with (
        patch("gamesheet_sdk.admin.cli.commands.locations._get_location_action") as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Location(
            id="loc-456",
            location_name="Bell Centre",
            surface_name="Ice",
            city="Montreal",
            province_state="QC",
            country="Canada",
        )
        result = runner.invoke(
            cli,
            ["locations", "get", "--location-id", "loc-456", "--format", "json"],
        )
        assert not result.exit_code
        assert '"id": "loc-456"' in result.output
        assert '"location_name": "Bell Centre"' in result.output


def test_locations_get_alias_show(runner: CliRunner) -> None:
    """The 'show' alias should invoke the get command."""
    with (
        patch("gamesheet_sdk.admin.cli.commands.locations._get_location_action") as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Location(
            id="loc-789",
            location_name="Rogers Arena",
            surface_name="Main",
            city="Vancouver",
            province_state="BC",
            country="Canada",
        )
        result = runner.invoke(
            cli,
            ["locations", "show", "--location-id", "loc-789"],
        )
        assert not result.exit_code
        mock_get.assert_called_once()


def test_locations_get_alias_view(runner: CliRunner) -> None:
    """The 'view' alias should invoke the get command."""
    with (
        patch("gamesheet_sdk.admin.cli.commands.locations._get_location_action") as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Location(
            id="loc-999",
            location_name="Canadian Tire Centre",
            surface_name="Rink",
            city="Ottawa",
            province_state="ON",
            country="Canada",
        )
        result = runner.invoke(
            cli,
            ["locations", "view", "--location-id", "loc-999"],
        )
        assert not result.exit_code
        mock_get.assert_called_once()
