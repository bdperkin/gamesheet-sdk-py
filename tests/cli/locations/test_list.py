# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for locations list command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.cli import cli
from gamesheet_sdk.games import Location


def test_locations_list_basic(runner: CliRunner) -> None:
    """The locations list command should retrieve all locations."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.locations._list_locations_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Location(
                id="loc-1",
                location_name="Arena A",
                surface_name="Ice 1",
                city="Toronto",
                province_state="ON",
                country="Canada",
            ),
        ]
        result = runner.invoke(cli, ["locations", "list"])
        assert not result.exit_code
        mock_list.assert_called_once()


def test_locations_list_json_output(runner: CliRunner) -> None:
    """The locations list command should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.locations._list_locations_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = [
            Location(
                id="loc-123",
                location_name="Test Arena",
                surface_name="Rink A",
                city="Montreal",
                province_state="QC",
                country="Canada",
            ),
        ]
        result = runner.invoke(cli, ["locations", "list", "--format", "json"])
        assert not result.exit_code
        assert '"id": "loc-123"' in result.output
        assert '"location_name": "Test Arena"' in result.output


def test_locations_list_alias_ls(runner: CliRunner) -> None:
    """The 'ls' alias should invoke the list command."""
    with (
        patch(
            "gamesheet_sdk.cli.commands.locations._list_locations_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["locations", "ls"])
        assert not result.exit_code
        mock_list.assert_called_once()
