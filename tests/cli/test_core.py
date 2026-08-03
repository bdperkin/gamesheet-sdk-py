# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for core CLI functionality (main group, config options)."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli


def test_cli_help_shows_usage(runner: CliRunner) -> None:
    """Running the CLI with --help should show usage information."""
    result = runner.invoke(cli, ["--help"])
    assert not result.exit_code
    assert "gamesheet_sdk" in result.output.lower() or "usage" in result.output.lower()


def test_cli_version_shows_version_string(runner: CliRunner) -> None:
    """Running with --version should show a version string."""
    result = runner.invoke(cli, ["--version"])
    assert not result.exit_code
    # Should contain a digit somewhere
    assert any(c.isdigit() for c in result.output)


def test_cli_version_short_option(runner: CliRunner) -> None:
    """Running with -V should show a version string."""
    result = runner.invoke(cli, ["-V"])
    assert not result.exit_code
    # Should contain a digit somewhere
    assert any(c.isdigit() for c in result.output)


def test_login_command_exists(runner: CliRunner) -> None:
    """The 'login' command should be available."""
    result = runner.invoke(cli, ["login", "--help"])
    assert not result.exit_code
    assert "login" in result.output.lower()


def test_cli_with_base_url_override(runner: CliRunner) -> None:
    """CLI should accept --base-url override."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
    ):
        mock_list.return_value = []
        result = runner.invoke(
            cli,
            ["--base-url", "https://custom.example.com", "associations", "list"],
        )
        assert not result.exit_code
        # Should have been called, indicating config was created
        mock_list.assert_called_once()


def test_cli_with_no_headless_flag(runner: CliRunner) -> None:
    """CLI should accept --no-headless flag."""
    with (
        patch(
            "gamesheet_sdk.admin.cli.commands.associations._list_associations_action",
        ) as mock_list,
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_access_token",
            return_value="token",
        ),
        patch(
            "gamesheet_sdk.admin.cli.helpers.load_refresh_token",
            return_value="refresh",
        ),
    ):
        mock_list.return_value = []
        result = runner.invoke(cli, ["--no-headless", "associations", "list"])
        assert not result.exit_code
        mock_list.assert_called_once()


def test_resource_group_get_command_with_unknown_alias() -> None:
    """ResourceGroup.get_command should return None for unknown commands."""
