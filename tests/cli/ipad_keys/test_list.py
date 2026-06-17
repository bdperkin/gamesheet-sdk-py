"""Tests for ipad-keys command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

from gamesheet_sdk.cli import cli

if TYPE_CHECKING:
    from click.testing import CliRunner
