# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for seasons command group."""

from __future__ import annotations

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli


def test_seasons_group_has_help_option(runner: CliRunner) -> None:
    """The seasons group should accept -h and --help."""
    result_short = runner.invoke(cli, ["seasons", "-h"])
    assert not result_short.exit_code
    assert "seasons" in result_short.output.lower()
    result_long = runner.invoke(cli, ["seasons", "--help"])
    assert not result_long.exit_code
    assert "seasons" in result_long.output.lower()
