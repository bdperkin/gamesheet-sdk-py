# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for rich-click CLI integration."""

from __future__ import annotations

import pytest

from gamesheet_sdk.admin.cli import main


def test_cli_help_renders_with_rich_click() -> None:
    """Test that --help renders using rich-click."""
    result = main(["--help"])
    # Should exit with 0 when showing help
    assert not result


def test_cli_version_renders_with_rich_click() -> None:
    """Test that --version renders using rich-click."""
    result = main(["--version"])
    # Should exit with 0 when showing version
    assert not result


def test_cli_version_short_option() -> None:
    """Test that -V short option works for version."""
    result = main(["-V"])
    # Should exit with 0 when showing version
    assert not result


def test_subcommand_help_renders() -> None:
    """Test that subcommand help works with rich-click."""
    result = main(["associations", "--help"])
    assert not result


def test_rich_click_configuration_applied() -> None:
    """Test that rich-click configuration is properly applied."""
    # Import after module loads to ensure config is applied
    import rich_click as click

    # Verify key configuration settings
    assert click.rich_click.TEXT_MARKUP == "rich"
    assert click.rich_click.SHOW_ARGUMENTS is True
    assert click.rich_click.GROUP_ARGUMENTS_OPTIONS
    assert click.rich_click.MAX_WIDTH == 100


def test_option_groups_configured() -> None:
    """Test that option groups are configured."""
    import rich_click as click

    # Verify option groups exist
    assert "gamesheet-admin" in click.rich_click.OPTION_GROUPS
    option_groups = click.rich_click.OPTION_GROUPS["gamesheet-admin"]
    assert any(g.get("name") == "Configuration Options" for g in option_groups)
    assert any(g.get("name") == "General Options" for g in option_groups)


def test_command_groups_configured() -> None:
    """Test that command groups are configured."""
    import rich_click as click

    # Verify command groups exist
    assert "gamesheet-admin" in click.rich_click.COMMAND_GROUPS
    command_groups = click.rich_click.COMMAND_GROUPS["gamesheet-admin"]
    assert any(g.get("name") == "Authentication" for g in command_groups)
    assert any(g.get("name") == "Utilities" for g in command_groups)
    assert any(g.get("name") == "Resources" for g in command_groups)


def test_login_command_help() -> None:
    """Test that login command help renders."""
    result = main(["login", "--help"])
    assert not result


def test_completion_command_help() -> None:
    """Test that completion command help renders."""
    result = main(["completion", "--help"])
    assert not result


@pytest.mark.parametrize(
    "resource",
    [
        "associations",
        "leagues",
        "seasons",
        "divisions",
        "teams",
        "referees",
        "ipad-keys",
        "games",
        "roster",
    ],
)
def test_resource_group_help(resource: str) -> None:
    """Test that all resource group help pages render."""
    result = main([resource, "--help"])
    assert not result


def test_resource_group_uses_rich_formatting() -> None:
    """Test that ResourceGroup properly uses rich formatting."""
    # Verify that ResourceGroup extends RichGroup
    from rich_click import RichGroup

    from gamesheet_sdk.common.cli.core import ResourceGroup

    assert issubclass(ResourceGroup, RichGroup)
