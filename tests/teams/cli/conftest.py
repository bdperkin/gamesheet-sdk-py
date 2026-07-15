# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures for teams CLI tests."""

from __future__ import annotations

from click.testing import CliRunner
import pytest


@pytest.fixture
def runner() -> CliRunner:
    """Return a Click CLI test runner."""
    return CliRunner()
