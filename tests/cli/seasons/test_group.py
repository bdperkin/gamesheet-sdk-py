"""Tests for seasons command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.cli import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_seasons_group_has_help_option(runner: CliRunner) -> None:
    """The seasons group should accept -h and --help."""
    result_short = runner.invoke(cli, ["seasons", "-h"])
    assert not result_short.exit_code
    assert "seasons" in result_short.output.lower()
    result_long = runner.invoke(cli, ["seasons", "--help"])
    assert not result_long.exit_code
    assert "seasons" in result_long.output.lower()
