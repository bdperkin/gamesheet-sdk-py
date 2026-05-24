"""Smoke tests for gamesheet_sdk."""

from gamesheet_sdk import __version__
from gamesheet_sdk.cli import main


def test_version_is_string() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_cli_exits_zero_on_no_args() -> None:
    assert main([]) == 0
