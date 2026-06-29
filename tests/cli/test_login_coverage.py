# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Coverage tests for login command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gamesheet_sdk.cli.commands.login import login_command
from tests.helpers import TEST_EMAIL_GENERIC


def test_login_command_success() -> None:
    """Test successful login flow."""
    runner = CliRunner()
    mock_config = MagicMock()

    with (
        patch("gamesheet_sdk.cli.commands.login.BrowserSession") as mock_browser_cls,
        patch("gamesheet_sdk.cli.commands.login._login_action") as mock_login,
    ):
        # Setup mocks
        mock_browser = MagicMock()
        mock_browser_cls.return_value.__enter__.return_value = mock_browser
        mock_browser_cls.return_value.__exit__.return_value = None

        result = runner.invoke(
            login_command,
            ["--email", TEST_EMAIL_GENERIC, "--password", "secret"],
            obj=mock_config,
        )

        # Verify success
        assert not result.exit_code
        assert "Login successful" in result.output
        assert "Tokens saved" in result.output

        # Verify login action was called
        mock_login.assert_called_once_with(
            mock_browser,
            email=TEST_EMAIL_GENERIC,
            password="secret",
            timeout=30000,
        )


def test_login_command_with_custom_timeout() -> None:
    """Test login command with custom timeout."""
    runner = CliRunner()
    mock_config = MagicMock()

    with (
        patch("gamesheet_sdk.cli.commands.login.BrowserSession") as mock_browser_cls,
        patch("gamesheet_sdk.cli.commands.login._login_action") as mock_login,
    ):
        mock_browser = MagicMock()
        mock_browser_cls.return_value.__enter__.return_value = mock_browser
        mock_browser_cls.return_value.__exit__.return_value = None

        result = runner.invoke(
            login_command,
            [
                "--email",
                TEST_EMAIL_GENERIC,
                "--password",
                "secret",
                "--timeout",
                "60000",
            ],
            obj=mock_config,
        )

        assert not result.exit_code
        mock_login.assert_called_once_with(
            mock_browser,
            email=TEST_EMAIL_GENERIC,
            password="secret",
            timeout=60000,
        )


def test_login_command_failure() -> None:
    """Test login command when login fails."""
    runner = CliRunner()
    mock_config = MagicMock()

    with (
        patch("gamesheet_sdk.cli.commands.login.BrowserSession") as mock_browser_cls,
        patch("gamesheet_sdk.cli.commands.login._login_action") as mock_login,
    ):
        mock_browser = MagicMock()
        mock_browser_cls.return_value.__enter__.return_value = mock_browser
        mock_browser_cls.return_value.__exit__.return_value = None

        # Simulate login failure
        mock_login.side_effect = Exception("Invalid credentials")

        result = runner.invoke(
            login_command,
            ["--email", TEST_EMAIL_GENERIC, "--password", "wrong"],
            obj=mock_config,
        )

        # Verify failure
        assert result.exit_code == 1
        assert "Login failed" in result.output
        assert "Invalid credentials" in result.output


def test_login_command_with_email_only() -> None:
    """Test login command with only email (password will be prompted)."""
    runner = CliRunner()
    mock_config = MagicMock()

    with (
        patch("gamesheet_sdk.cli.commands.login.BrowserSession") as mock_browser_cls,
        patch("gamesheet_sdk.cli.commands.login._login_action") as mock_login,
    ):
        mock_browser = MagicMock()
        mock_browser_cls.return_value.__enter__.return_value = mock_browser
        mock_browser_cls.return_value.__exit__.return_value = None

        result = runner.invoke(
            login_command,
            ["--email", TEST_EMAIL_GENERIC],
            obj=mock_config,
        )

        assert not result.exit_code
        # Verify login was called with None password (will be prompted)
        mock_login.assert_called_once()
        call_kwargs = mock_login.call_args.kwargs
        assert call_kwargs["email"] == TEST_EMAIL_GENERIC
        assert call_kwargs["password"] is None


def test_login_command_with_no_credentials() -> None:
    """Test login command with no credentials (both will be prompted/from env)."""
    runner = CliRunner()
    mock_config = MagicMock()

    with (
        patch("gamesheet_sdk.cli.commands.login.BrowserSession") as mock_browser_cls,
        patch("gamesheet_sdk.cli.commands.login._login_action") as mock_login,
    ):
        mock_browser = MagicMock()
        mock_browser_cls.return_value.__enter__.return_value = mock_browser
        mock_browser_cls.return_value.__exit__.return_value = None

        result = runner.invoke(
            login_command,
            [],
            obj=mock_config,
        )

        assert not result.exit_code
        # Verify login was called with None for both
        mock_login.assert_called_once()
        call_kwargs = mock_login.call_args.kwargs
        assert call_kwargs["email"] is None
        assert call_kwargs["password"] is None
