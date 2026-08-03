# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for referees get command."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.referees import Referee
from tests.helpers import SEASON_ID, TEST_EMAIL_REFEREE


def test_referees_get_with_all_fields(runner: CliRunner) -> None:
    """The referees get command should retrieve a single referee."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._get_referee_action",
        ) as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Referee(
            id="1146197",
            season_id=SEASON_ID,
            first_name="WES",
            last_name="MCCAULEY",
            email=TEST_EMAIL_REFEREE,
            created_at=datetime(2026, 6, 15, 12, 4, 5, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 12, 4, 5, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "get",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146197",
            ],
        )
        assert not result.exit_code
        mock_get.assert_called_once()
        args = mock_get.call_args[0]
        assert args[1] == SEASON_ID
        assert args[2] == "1146197"


def test_referees_get_alias_show(runner: CliRunner) -> None:
    """The 'show' alias should invoke the get command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._get_referee_action",
        ) as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Referee(
            id="1146198",
            season_id=SEASON_ID,
            first_name="Test",
            last_name="Ref",
            created_at=datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "show",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146198",
            ],
        )
        assert not result.exit_code
        mock_get.assert_called_once()


def test_referees_get_alias_view(runner: CliRunner) -> None:
    """The 'view' alias should invoke the get command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._get_referee_action",
        ) as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Referee(
            id="1146199",
            season_id=SEASON_ID,
            first_name="Another",
            last_name="Test",
            created_at=datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "view",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146199",
            ],
        )
        assert not result.exit_code
        mock_get.assert_called_once()


def test_referees_get_missing_referee_id_shows_error(runner: CliRunner) -> None:
    """Calling 'referees get' without referee ID should show an error."""
    result = runner.invoke(
        cli,
        [
            "referees",
            "get",
            "--season-id",
            SEASON_ID,
        ],
    )
    assert result.exit_code == 2
    assert "referee-id" in result.output.lower() or "missing option" in result.output.lower()


def test_referees_get_json_output(runner: CliRunner) -> None:
    """The referees get command should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._get_referee_action",
        ) as mock_get,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_get.return_value = Referee(
            id="1146200",
            season_id=SEASON_ID,
            first_name="Json",
            last_name="Output",
            email="json@example.com",
            created_at=datetime(2026, 6, 15, 15, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 15, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "get",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146200",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert '"id": "1146200"' in result.output
        assert '"first_name": "Json"' in result.output
