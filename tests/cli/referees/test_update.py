# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for referees update command."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli
from gamesheet_sdk.admin.referees import Referee
from tests.helpers import REFEREE_EXTERNAL_ID_SECONDARY, SEASON_ID


def test_referees_update_with_all_fields(runner: CliRunner) -> None:
    """The referees update command should accept all fields."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._update_referee_action",
        ) as mock_update,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_update.return_value = Referee(
            id="1146196",
            season_id=SEASON_ID,
            first_name="WES",
            last_name="MCCAULEY",
            email="McCauley.Wes@example.com",
            created_at=datetime(2026, 6, 15, 12, 1, 41, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 12, 6, 46, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "update",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146196",
                "--first-name",
                "WES",
                "--last-name",
                "MCCAULEY",
                "--email-address",
                "McCauley.Wes@example.com",
                "--external-id",
                REFEREE_EXTERNAL_ID_SECONDARY,
            ],
        )
        assert not result.exit_code
        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        assert args[1] == SEASON_ID
        assert args[2] == "1146196"
        assert args[3] == "WES"
        assert args[4] == "MCCAULEY"
        assert args[5] == "McCauley.Wes@example.com"
        assert args[6] == REFEREE_EXTERNAL_ID_SECONDARY


def test_referees_update_partial_fields(runner: CliRunner) -> None:
    """The referees update command should work with partial fields."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._update_referee_action",
        ) as mock_update,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_update.return_value = Referee(
            id="1146197",
            season_id=SEASON_ID,
            first_name="Updated",
            last_name="Original",
            created_at=datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "update",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146197",
                "--first-name",
                "Updated",
            ],
        )
        assert not result.exit_code
        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        assert args[1] == SEASON_ID
        assert args[2] == "1146197"
        assert args[3] == "Updated"
        assert args[4] is None
        assert args[5] is None
        assert args[6] is None


def test_referees_update_alias_set(runner: CliRunner) -> None:
    """The 'set' alias should invoke the update command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._update_referee_action",
        ) as mock_update,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_update.return_value = Referee(
            id="1146198",
            season_id=SEASON_ID,
            first_name="Test",
            last_name="Ref",
            created_at=datetime(2026, 6, 15, 15, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 15, 30, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "set",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146198",
                "--first-name",
                "Test",
            ],
        )
        assert not result.exit_code
        mock_update.assert_called_once()


def test_referees_update_alias_edit(runner: CliRunner) -> None:
    """The 'edit' alias should invoke the update command."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._update_referee_action",
        ) as mock_update,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_update.return_value = Referee(
            id="1146199",
            season_id=SEASON_ID,
            first_name="Another",
            last_name="Test",
            created_at=datetime(2026, 6, 15, 16, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 16, 15, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "edit",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146199",
                "--last-name",
                "Test",
            ],
        )
        assert not result.exit_code
        mock_update.assert_called_once()


def test_referees_update_missing_referee_id_shows_error(runner: CliRunner) -> None:
    """Calling 'referees update' without referee ID should show an error."""
    result = runner.invoke(
        cli,
        [
            "referees",
            "update",
            "--season-id",
            SEASON_ID,
            "--first-name",
            "Test",
        ],
    )
    assert result.exit_code == 2
    assert "referee-id" in result.output.lower() or "missing option" in result.output.lower()


def test_referees_update_no_fields_shows_error(runner: CliRunner) -> None:
    """Calling 'referees update' without any update fields should show an error."""
    result = runner.invoke(
        cli,
        [
            "referees",
            "update",
            "--season-id",
            SEASON_ID,
            "--referee-id",
            "1146200",
        ],
    )
    assert result.exit_code == 2
    assert "at least one field" in result.output.lower()


def test_referees_update_json_output(runner: CliRunner) -> None:
    """The referees update command should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.referees._update_referee_action",
        ) as mock_update,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="bearer-tok",
        ),
    ):
        mock_update.return_value = Referee(
            id="1146200",
            season_id=SEASON_ID,
            first_name="Json",
            last_name="Updated",
            email="updated@example.com",
            created_at=datetime(2026, 6, 15, 17, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 17, 30, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "update",
                "--season-id",
                SEASON_ID,
                "--referee-id",
                "1146200",
                "--last-name",
                "Updated",
                "--format",
                "json",
            ],
        )
        assert not result.exit_code
        assert '"id": "1146200"' in result.output
        assert '"last_name": "Updated"' in result.output
