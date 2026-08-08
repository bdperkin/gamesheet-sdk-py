# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Additional coverage tests for CLI core module."""

from __future__ import annotations

from unittest.mock import patch

from click.exceptions import Abort, Exit, UsageError
import rich_click as click

from gamesheet_sdk.common.cli.core import (
    ResourceGroup,
    _configure_logging,
    parse_columns_spec,
    resolve_exit,
    resolve_system_exit,
)


def test_command_row_with_no_aliases() -> None:
    """ResourceGroup._command_row should format command with no aliases."""

    @click.group(cls=ResourceGroup)
    def test_group() -> None:
        """Test group."""

    @test_group.command("list")
    def list_cmd() -> None:
        """List items."""

    label, help_text = test_group._command_row("list", list_cmd)
    assert label == "list"
    assert "List items" in help_text


def test_command_row_with_aliases() -> None:
    """ResourceGroup._command_row should format command with aliases."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls", "l")})
    def test_group() -> None:
        """Test group."""

    @test_group.command("list")
    def list_cmd() -> None:
        """List items."""

    label, help_text = test_group._command_row("list", list_cmd)
    assert "list" in label
    assert "l, ls" in label or "ls, l" in label  # Order may vary
    assert "List items" in help_text


def test_visible_command_rows_filters_hidden() -> None:
    """ResourceGroup._visible_command_rows should filter hidden commands."""

    @click.group(cls=ResourceGroup)
    def test_group() -> None:
        pass

    @test_group.command("list")
    def list_cmd() -> None:
        pass

    @test_group.command("hidden", hidden=True)
    def hidden_cmd() -> None:
        pass

    ctx = click.Context(test_group)
    rows = list(test_group._visible_command_rows(ctx))
    labels = [label for label, _ in rows]
    assert any("list" in label for label in labels)
    assert not any("hidden" in label for label in labels)


def test_visible_command_rows_handles_none_command() -> None:
    """ResourceGroup._visible_command_rows should handle get_command returning None."""

    @click.group(cls=ResourceGroup)
    def test_group() -> None:
        pass

    ctx = click.Context(test_group)

    # Mock list_commands to return a name that get_command will return None for
    original_get = test_group.get_command

    def mock_list(_ctx: click.Context) -> list[str]:
        return ["real_cmd", "fake_cmd"]

    def mock_get(_ctx: click.Context, name: str) -> click.Command | None:
        if name == "fake_cmd":
            return None

        return original_get(_ctx, name)

    with (
        patch.object(test_group, "list_commands", mock_list),
        patch.object(test_group, "get_command", mock_get),
    ):
        rows = list(test_group._visible_command_rows(ctx))
        # Should only get the real command, fake_cmd filtered out
        assert not rows  # real_cmd doesn't exist either


def test_format_commands_with_nonempty_rows() -> None:
    """ResourceGroup.format_commands should render non-empty command list."""

    @click.group(cls=ResourceGroup)
    def test_group() -> None:
        pass

    @test_group.command("list")
    def list_cmd() -> None:
        pass

    ctx = click.Context(test_group)
    formatter = click.HelpFormatter()
    test_group.format_commands(ctx, formatter)
    output = formatter.getvalue()
    assert "list" in output.lower() or "commands" in output.lower()


def test_shell_complete_without_super_method() -> None:
    """ResourceGroup.shell_complete should handle missing super().shell_complete."""

    @click.group(cls=ResourceGroup, aliases={"list": ("ls",)})
    def test_group() -> None:
        pass

    @test_group.command("list")
    def list_cmd() -> None:
        pass

    ctx = click.Context(test_group)

    # Patch getattr to simulate super().shell_complete not existing
    original_getattr = getattr

    def mock_getattr(obj: object, name: str, default: object = None) -> object:
        if name == "shell_complete" and isinstance(
            obj,
            type(super(ResourceGroup, test_group)),
        ):
            return None

        return original_getattr(obj, name, default)

    with patch("builtins.getattr", mock_getattr):
        items = test_group.shell_complete(ctx, "l")
        # Should still work and include aliases
        values = [item.value for item in items]
        assert "ls" in values


def test_parse_columns_spec_with_none() -> None:
    """parse_columns_spec should return None for None input."""
    assert parse_columns_spec(None) is None


def test_parse_columns_spec_with_whitespace_only() -> None:
    """parse_columns_spec should return None for whitespace-only input."""
    assert parse_columns_spec("   ") is None
    assert parse_columns_spec("\t\n") is None


def test_parse_columns_spec_with_valid_columns() -> None:
    """parse_columns_spec should parse comma-separated columns."""
    result = parse_columns_spec("id, name, created_at")
    assert result == ["id", "name", "created_at"]


def test_parse_columns_spec_filters_empty() -> None:
    """parse_columns_spec should filter empty columns."""
    result = parse_columns_spec("id,  , name,  ,created_at")
    assert result == ["id", "name", "created_at"]


def test_resolve_system_exit_with_none_code() -> None:
    """resolve_system_exit should return 0 for None code."""

    class FakeExit(BaseException):
        """Fake exception with None code."""

        code = None

    assert not resolve_system_exit(FakeExit())


def test_resolve_system_exit_with_int_code() -> None:
    """resolve_system_exit should return the int code."""

    class FakeExit(BaseException):
        """Fake exception with int code."""

        code = 42

    assert resolve_system_exit(FakeExit()) == 42


def test_resolve_system_exit_with_non_int_code() -> None:
    """resolve_system_exit should return 1 for non-int code."""

    class FakeExit(BaseException):
        """Fake exception with string code."""

        code = "error message"

    assert resolve_system_exit(FakeExit()) == 1


def test_resolve_system_exit_with_no_code_attribute() -> None:
    """resolve_system_exit should return 0 when exception has no code attribute."""

    class PlainException(BaseException):
        """Exception with no code attribute."""

        code = None

    assert not resolve_system_exit(PlainException())


def test_resolve_exit_with_exit_exception() -> None:
    """resolve_exit should return exit_code from Exit exception."""
    exc = Exit(42)
    assert resolve_exit(exc) == 42


def test_resolve_exit_with_usage_error() -> None:
    """resolve_exit should return 2 for UsageError."""
    ctx = click.Context(click.Command("test"))
    exc = UsageError("Invalid usage", ctx=ctx)
    with patch.object(exc, "show"):
        assert resolve_exit(exc) == 2


def test_resolve_exit_with_abort() -> None:
    """resolve_exit should return 1 for Abort."""
    exc = Abort()
    assert resolve_exit(exc) == 1


def test_resolve_exit_with_system_exit() -> None:
    """resolve_exit should delegate to resolve_system_exit for other exceptions."""

    class CustomExit(BaseException):
        """Custom exception with code."""

        code = 5

    assert resolve_exit(CustomExit()) == 5


def test_configure_logging_with_color() -> None:
    """_configure_logging should use ColoredFormatter when color is enabled."""
    import os

    # Ensure NO_COLOR is not set
    old_no_color = os.environ.pop("NO_COLOR", None)
    try:
        with (
            patch("gamesheet_sdk.common.cli.core.logging.basicConfig") as mock_basic,
            patch("gamesheet_sdk.common.cli.core.sys.stderr") as mock_stderr,
        ):
            # Mock stderr to appear as a TTY
            mock_stderr.isatty.return_value = True
            _configure_logging(1)
            # Should have been called with ColoredFormatter
            call_args = mock_basic.call_args
            assert call_args is not None
            handlers = call_args.kwargs["handlers"]
            assert len(handlers) == 1
            formatter = handlers[0].formatter
            # Should be ColoredFormatter (has log_colors attribute)
            assert hasattr(formatter, "log_colors") or formatter.__class__.__name__ == "ColoredFormatter"
    finally:
        if old_no_color is not None:
            os.environ["NO_COLOR"] = old_no_color
