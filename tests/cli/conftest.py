# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared fixtures for CLI tests."""

from __future__ import annotations

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Return a Click CLI test runner.

    Returns:
        CliRunner: Click CLI test runner instance.

    """
    return CliRunner()
