# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for divisions command group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.admin.cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_divisions_group_has_help_option(runner: CliRunner) -> None:
    """The divisions group should accept -h and --help."""
    result_short = runner.invoke(cli, ["divisions", "-h"])
    assert not result_short.exit_code
    assert "divisions" in result_short.output.lower()
    result_long = runner.invoke(cli, ["divisions", "--help"])
    assert not result_long.exit_code
    assert "divisions" in result_long.output.lower()
