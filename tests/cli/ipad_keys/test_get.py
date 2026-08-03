# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for ipad-keys get command."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli
from tests.helpers import SEASON_ID


def test_ipad_keys_get_alias_show_works(runner: CliRunner) -> None:
    """The ipad-keys show alias should work the same as get."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read", "write"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(cli, ["ipad-keys", "show", "--season-id", SEASON_ID])
        assert not result.exit_code
        assert "ipad-test-kw" in result.output


def test_ipad_keys_get_alias_view_works(runner: CliRunner) -> None:
    """The ipad-keys view alias should work the same as get."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read", "write"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(cli, ["ipad-keys", "view", "--season-id", SEASON_ID])
        assert not result.exit_code
        assert "ipad-test-kw" in result.output


def test_ipad_keys_default_command_is_get(runner: CliRunner) -> None:
    """Bare 'ipad-keys' with no args shows help mentioning get as default."""
    result = runner.invoke(cli, ["ipad-keys", "--help"])
    assert not result.exit_code
    # Help should mention that get is available
    assert "get" in result.output.lower() or "show" in result.output.lower()


def test_ipad_keys_get_json_output(runner: CliRunner) -> None:
    """Ipad-keys get should support JSON output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[{"title": "app"}],
                live_scoring_scopes=["read", "write"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["ipad-keys", "get", "--season-id", SEASON_ID, "-F", "json"],
        )
        assert not result.exit_code
        import json

        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "3567"
        assert data[0]["value"] == "ipad-test-kw"


def test_ipad_keys_get_yaml_output(runner: CliRunner) -> None:
    """Ipad-keys get should support YAML output."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["ipad-keys", "get", "--season-id", SEASON_ID, "-F", "yaml"],
        )
        assert not result.exit_code
        assert "id: '3567'" in result.output or 'id: "3567"' in result.output
        assert "ipad-test-kw" in result.output


def test_ipad_keys_get_columns_filter(runner: CliRunner) -> None:
    """Ipad-keys get should support column filtering."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read", "write"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["ipad-keys", "get", "--season-id", SEASON_ID, "-c", "id,value"],
        )
        assert not result.exit_code
        # Check that id and value are in the output
        assert "id" in result.output.lower() or "3567" in result.output
        assert "value" in result.output.lower() or "ipad-test-kw" in result.output


def test_ipad_keys_get_output_to_file(runner: CliRunner, tmp_path: Any) -> None:
    """Ipad-keys get should write to file when -o is specified."""
    output_file = tmp_path / "output.json"
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(
            cli,
            [
                "ipad-keys",
                "get",
                "--season-id",
                SEASON_ID,
                "-F",
                "json",
                "-o",
                str(output_file),
            ],
        )
        assert not result.exit_code
        assert output_file.exists()
        import json

        data = json.loads(output_file.read_text())
        assert len(data) == 1
        assert data[0]["id"] == "3567"


def test_ipad_keys_get_table_format(runner: CliRunner) -> None:
    """Ipad-keys get should output table format by default."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read", "write"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(cli, ["ipad-keys", "get", "--season-id", SEASON_ID])
        assert not result.exit_code
        # Table format should have column headers and the value
        assert "ipad-test-kw" in result.output


def test_ipad_keys_get_grid_format(runner: CliRunner) -> None:
    """Ipad-keys get should support grid table format."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["ipad-keys", "get", "--season-id", SEASON_ID, "-F", "grid"],
        )
        assert not result.exit_code
        # Grid format has border characters
        assert "+" in result.output or "|" in result.output


def test_ipad_keys_get_with_no_saved_tokens(runner: CliRunner) -> None:
    """Ipad-keys get should exit with error when no tokens are saved."""
    with (
        patch("gamesheet_sdk.admin.cli.helpers.load_access_token", return_value=None),
        patch("gamesheet_sdk.admin.cli.helpers.load_refresh_token", return_value=None),
    ):
        result = runner.invoke(cli, ["ipad-keys", "get", "--season-id", SEASON_ID])
        assert result.exit_code == 1
        assert "No saved session" in result.output or "login" in result.output.lower()


def test_ipad_keys_get_with_env_var(runner: CliRunner) -> None:
    """The season ID can be provided via GAMESHEET_SEASON_ID environment variable."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
        patch(
            "gamesheet_sdk.admin.cli.commands.ipad_keys._list_ipad_keys_action",
        ) as mock_action,
    ):
        from gamesheet_sdk.admin.ipad_keys import IPadKey

        mock_action.return_value = [
            IPadKey(
                id="3567",
                value="ipad-test-kw",
                description="Test Key",
                roles=[],
                live_scoring_scopes=["read", "write"],
                created_at="2026-05-15T17:42:34Z",
                updated_at="2026-05-15T17:42:34Z",
            ),
        ]
        result = runner.invoke(
            cli,
            ["ipad-keys", "get"],
            env={"GAMESHEET_SEASON_ID": SEASON_ID},
        )
        assert not result.exit_code
        mock_action.assert_called_once()
