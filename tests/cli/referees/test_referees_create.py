"""Tests for referees create command."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

from gamesheet_sdk.cli import cli
from gamesheet_sdk.referees import Referee

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_referees_create_with_all_fields(runner: CliRunner) -> None:
    """The referees create command should accept all fields."""
    with (
        patch("gamesheet_sdk.cli.commands.referees._create_referee_action") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = Referee(
            id="1146197",
            season_id="15020",
            first_name="Wes",
            last_name="McCauley",
            email="Wes.McCauley@example.com",
            created_at=datetime(2026, 6, 15, 12, 4, 5, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 12, 4, 5, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "create",
                "--season-id",
                "15020",
                "--first-name",
                "Wes",
                "--last-name",
                "McCauley",
                "--email-address",
                "Wes.McCauley@example.com",
                "--external-id",
                "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A",
            ],
        )
        assert result.exit_code == 0
        mock_create.assert_called_once()
        args = mock_create.call_args[0]
        assert args[1] == "15020"
        assert args[2] == "Wes"
        assert args[3] == "McCauley"
        assert args[4] == "Wes.McCauley@example.com"
        assert args[5] == "0EB978DD-66B8-4CA1-AAA8-D855EED39D6A"


def test_referees_create_required_fields_only(runner: CliRunner) -> None:
    """The referees create command should work with only required fields."""
    with (
        patch("gamesheet_sdk.cli.commands.referees._create_referee_action") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = Referee(
            id="1146198",
            season_id="15020",
            first_name="Jane",
            last_name="Doe",
            created_at=datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "create",
                "--season-id",
                "15020",
                "--first-name",
                "Jane",
                "--last-name",
                "Doe",
            ],
        )
        assert result.exit_code == 0
        mock_create.assert_called_once()
        args = mock_create.call_args[0]
        assert args[1] == "15020"
        assert args[2] == "Jane"
        assert args[3] == "Doe"
        assert args[4] is None
        assert args[5] is None


def test_referees_create_alias_add(runner: CliRunner) -> None:
    """The 'add' alias should invoke the create command."""
    with (
        patch("gamesheet_sdk.cli.commands.referees._create_referee_action") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = Referee(
            id="1146199",
            season_id="15020",
            first_name="Test",
            last_name="Ref",
            created_at=datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "add",
                "--season-id",
                "15020",
                "--first-name",
                "Test",
                "--last-name",
                "Ref",
            ],
        )
        assert result.exit_code == 0
        mock_create.assert_called_once()


def test_referees_create_alias_new(runner: CliRunner) -> None:
    """The 'new' alias should invoke the create command."""
    with (
        patch("gamesheet_sdk.cli.commands.referees._create_referee_action") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = Referee(
            id="1146200",
            season_id="15020",
            first_name="Another",
            last_name="Test",
            created_at=datetime(2026, 6, 15, 15, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 15, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "new",
                "--season-id",
                "15020",
                "--first-name",
                "Another",
                "--last-name",
                "Test",
            ],
        )
        assert result.exit_code == 0
        mock_create.assert_called_once()


def test_referees_create_missing_first_name_shows_error(runner: CliRunner) -> None:
    """Calling 'referees create' without first name should show an error."""
    result = runner.invoke(
        cli,
        [
            "referees",
            "create",
            "--season-id",
            "15020",
            "--last-name",
            "Doe",
        ],
    )
    assert result.exit_code == 2
    assert "first-name" in result.output.lower() or "missing option" in result.output.lower()


def test_referees_create_missing_last_name_shows_error(runner: CliRunner) -> None:
    """Calling 'referees create' without last name should show an error."""
    result = runner.invoke(
        cli,
        [
            "referees",
            "create",
            "--season-id",
            "15020",
            "--first-name",
            "Jane",
        ],
    )
    assert result.exit_code == 2
    assert "last-name" in result.output.lower() or "missing option" in result.output.lower()


def test_referees_create_json_output(runner: CliRunner) -> None:
    """The referees create command should support JSON output."""
    with (
        patch("gamesheet_sdk.cli.commands.referees._create_referee_action") as mock_create,
        patch(
            "gamesheet_sdk.cli.helpers.load_refresh_token",
            return_value="refresh-tok",
        ),
        patch("gamesheet_sdk.cli.helpers.load_access_token", return_value="bearer-tok"),
    ):
        mock_create.return_value = Referee(
            id="1146201",
            season_id="15020",
            first_name="Json",
            last_name="Test",
            email="json@example.com",
            created_at=datetime(2026, 6, 15, 16, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 15, 16, 0, 0, tzinfo=timezone.utc),
        )
        result = runner.invoke(
            cli,
            [
                "referees",
                "create",
                "--season-id",
                "15020",
                "--first-name",
                "Json",
                "--last-name",
                "Test",
                "--email-address",
                "json@example.com",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert '"id": "1146201"' in result.output
        assert '"first_name": "Json"' in result.output
