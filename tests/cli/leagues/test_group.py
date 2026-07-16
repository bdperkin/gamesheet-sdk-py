# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for leagues command group."""

from __future__ import annotations

from click.testing import CliRunner

from gamesheet_sdk.admin.cli.main import cli


def test_leagues_group_has_help_option(runner: CliRunner) -> None:
    """The leagues group should accept -h and --help."""
    result_short = runner.invoke(cli, ["leagues", "-h"])
    assert not result_short.exit_code
    assert "leagues" in result_short.output.lower()
    result_long = runner.invoke(cli, ["leagues", "--help"])
    assert not result_long.exit_code
    assert "leagues" in result_long.output.lower()
