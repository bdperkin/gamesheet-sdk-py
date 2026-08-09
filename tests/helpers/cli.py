# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI test helper functions."""

from __future__ import annotations

from click.testing import Result


def assert_no_session_error(result: Result) -> None:
    """Assert that CLI output contains a 'no saved session' or 'login' message.

    This is a common assertion pattern for CLI tests that verify behavior when authentication tokens are
    missing.

    Args:
        result (Result): Click CLI test result to check.
    """
    assert "No saved session" in result.output or "login" in result.output.lower()


def assert_output_contains_id(result: Result) -> None:
    """Assert that CLI output contains an 'id' field.

    This checks for the presence of an ID field in the output, accepting both "id:" and "id :" formats (with
    or without space after colon).

    Args:
        result (Result): Click CLI test result to check.
    """
    assert "id:" in result.output or "id :" in result.output
