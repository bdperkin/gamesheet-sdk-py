"""Smoke tests for gamesheet_sdk."""

from gamesheet_sdk import __version__
from gamesheet_sdk.cli import main


def test_version_is_string() -> None:
    """Test that __version__ is a non-empty string."""
    assert isinstance(__version__, str)
    assert __version__


def test_cli_exits_zero_on_no_args() -> None:
    """Test that CLI main() returns 0 when called with no arguments."""
    assert not main([])
