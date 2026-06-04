"""Tests for CLI helper functions and ResourceGroup internals."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import click
from click.testing import CliRunner

from gamesheet_sdk.cli import ResourceGroup, confirm_destructive
from gamesheet_sdk.cli.core import _configure_logging, _should_color


# Tests for ResourceGroup edge cases and helper functions
def test_resource_group_with_no_aliases() -> None:
    """ResourceGroup should work with no aliases provided."""

    @click.group(cls=ResourceGroup, default="list")
    def test_group() -> None:

        pass

    @test_group.command("list")
    def list_cmd() -> None:

        click.echo("listing")

    runner = CliRunner()
    result = runner.invoke(test_group, ["list"])  # noqa: FURB184
    assert result.exit_code == 0
    assert "listing" in result.output


def test_resource_group_format_commands_with_empty_rows() -> None:
    """ResourceGroup.format_commands should handle empty command rows."""

    @click.group(cls=ResourceGroup)
    def test_group() -> None:

        pass

    # Group with no commands
    ctx = click.Context(test_group)
    formatter = click.HelpFormatter()
    test_group.format_commands(ctx, formatter)
    # Should not crash, output will just be empty


def test_resource_group_shell_complete_includes_aliases() -> None:
    """ResourceGroup.shell_complete should include aliases in completion."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",)})
    def test_group() -> None:

        pass

    @test_group.command("list")
    def list_cmd() -> None:

        pass

    ctx = click.Context(test_group)
    items = test_group.shell_complete(ctx, "l")
    # Should include both 'list' and 'ls'
    values = [item.value for item in items]
    assert "list" in values
    assert "ls" in values


def test_resource_group_shell_complete_filters_by_incomplete() -> None:
    """ResourceGroup.shell_complete should filter by incomplete prefix."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",), "get": ("show",)})
    def test_group() -> None:

        pass

    @test_group.command("list")
    def list_cmd() -> None:

        pass

    @test_group.command("get")
    def get_cmd() -> None:

        pass

    ctx = click.Context(test_group)
    items = test_group.shell_complete(ctx, "l")
    values = [item.value for item in items]
    # Should only include items starting with 'l'
    assert "list" in values
    assert "ls" in values
    assert "get" not in values
    assert "show" not in values


def test_should_color_with_no_color_env() -> None:
    """_should_color should return False when NO_COLOR is set."""
    handler = Mock()
    handler.stream = Mock()
    handler.stream.isatty.return_value = True
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        assert _should_color(handler) is False


def test_should_color_with_tty() -> None:
    """_should_color should return True for TTY without NO_COLOR."""
    handler = Mock()
    handler.stream = Mock()
    handler.stream.isatty.return_value = True
    with patch.dict(os.environ, {}, clear=True):
        # Remove NO_COLOR if it exists
        os.environ.pop("NO_COLOR", None)
        assert _should_color(handler) is True


def test_should_color_with_non_tty() -> None:
    """_should_color should return False for non-TTY."""
    handler = Mock()
    handler.stream = Mock()
    handler.stream.isatty.return_value = False
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("NO_COLOR", None)
        assert _should_color(handler) is False


def test_should_color_with_no_stream() -> None:
    """_should_color should return False when handler has no stream."""
    handler = Mock(spec=[])  # No stream attribute
    assert _should_color(handler) is False


def test_configure_logging_verbose_0() -> None:
    """_configure_logging with verbose=0 should set WARNING level."""
    with patch("gamesheet_sdk.cli.core.logging.basicConfig") as mock_basic:
        _configure_logging(0)
        # Should be called with WARNING level
        call_args = mock_basic.call_args
        assert call_args is not None
        import logging

        assert call_args.kwargs["level"] == logging.WARNING


def test_configure_logging_verbose_1() -> None:
    """_configure_logging with verbose=1 should set INFO level."""
    with patch("gamesheet_sdk.cli.core.logging.basicConfig") as mock_basic:
        _configure_logging(1)
        call_args = mock_basic.call_args
        assert call_args is not None
        import logging

        assert call_args.kwargs["level"] == logging.INFO


def test_configure_logging_verbose_2() -> None:
    """_configure_logging with verbose=2 should set DEBUG level."""
    with patch("gamesheet_sdk.cli.core.logging.basicConfig") as mock_basic:
        _configure_logging(2)
        call_args = mock_basic.call_args
        assert call_args is not None
        import logging

        assert call_args.kwargs["level"] == logging.DEBUG


def test_confirm_destructive_with_force() -> None:
    """confirm_destructive decorator with --force should skip confirmation."""

    @click.command()
    @confirm_destructive("test item")
    def delete_cmd() -> None:

        click.echo("deleted")

    runner = CliRunner()
    result = runner.invoke(delete_cmd, ["--force"])  # noqa: FURB184
    assert result.exit_code == 0
    assert "deleted" in result.output
    assert "Really delete" not in result.output


def test_confirm_destructive_without_force_confirmed() -> None:
    """confirm_destructive decorator without --force should prompt and accept y."""

    @click.command()
    @confirm_destructive("test item")
    def delete_cmd() -> None:

        click.echo("deleted")

    runner = CliRunner()
    result = runner.invoke(delete_cmd, input="y\n")  # noqa: FURB184
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_confirm_destructive_without_force_aborted() -> None:
    """confirm_destructive decorator without --force should prompt and abort on n."""

    @click.command()
    @confirm_destructive("test item")
    def delete_cmd() -> None:

        click.echo("deleted")

    runner = CliRunner()
    result = runner.invoke(delete_cmd, input="n\n")  # noqa: FURB184
    assert result.exit_code == 1
    assert "deleted" not in result.output
    assert "Aborted" in result.output or result.exit_code != 0


def test_resource_group_get_command_with_unknown_alias() -> None:
    """ResourceGroup.get_command should return None for unknown commands."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",)})
    def test_group() -> None:

        pass

    @test_group.command("list")
    def list_cmd() -> None:

        pass

    ctx = click.Context(test_group)
    # Try to get a command that doesn't exist
    cmd = test_group.get_command(ctx, "nonexistent")
    assert cmd is None


def test_resource_group_alias_item_if_visible_with_hidden_command() -> None:
    """ResourceGroup should not surface aliases for hidden commands."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",)})
    def test_group() -> None:

        pass

    @test_group.command("list", hidden=True)
    def list_cmd() -> None:

        pass

    ctx = click.Context(test_group)
    items = test_group.shell_complete(ctx, "l")
    values = [item.value for item in items]
    # Hidden commands and their aliases should not appear
    assert "list" not in values
    assert "ls" not in values
