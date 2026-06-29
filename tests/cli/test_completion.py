# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for shell completion command."""

from __future__ import annotations

from click.testing import CliRunner

from gamesheet_sdk.cli import cli
from gamesheet_sdk.cli.commands import completion_command


def test_completion_command_exists(runner: CliRunner) -> None:
    """The 'completion' command should be available."""
    result = runner.invoke(cli, ["completion", "--help"])
    assert not result.exit_code
    assert "completion" in result.output.lower()


def test_completion_bash(runner: CliRunner) -> None:
    """The 'completion bash' should generate bash completion script."""
    result = runner.invoke(cli, ["completion", "bash"])
    assert not result.exit_code
    # Should contain bash completion markers
    assert "complete" in result.output or "_GAMESHEET_SDK_PY_COMPLETE" in result.output


def test_completion_zsh(runner: CliRunner) -> None:
    """The 'completion zsh' should generate zsh completion script."""
    result = runner.invoke(cli, ["completion", "zsh"])
    assert not result.exit_code
    # Should contain zsh completion markers
    assert "compdef" in result.output or "_GAMESHEET_SDK_PY_COMPLETE" in result.output


def test_completion_fish(runner: CliRunner) -> None:
    """The 'completion fish' should generate fish completion script."""
    result = runner.invoke(cli, ["completion", "fish"])
    assert not result.exit_code
    # Should contain fish completion markers
    assert "complete" in result.output or "_GAMESHEET_SDK_PY_COMPLETE" in result.output


# Error path tests
def test_completion_command_without_parent_context(runner: CliRunner) -> None:
    """The completion command invoked without parent context should exit cleanly."""
    # Invoke the completion command directly (not through cli group)
    # This tests the edge case where ctx.parent is None (line 38->exit)
    result = runner.invoke(completion_command, ["bash"])
    # When there's no parent context, the command exits without output
    assert not result.exit_code
    # Should not produce completion output since there's no parent CLI to complete
    assert not result.output
