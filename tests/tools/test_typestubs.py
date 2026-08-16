# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for the removal side of ``types-*`` stub synchronization.

``tools/`` sits outside ``[tool.coverage] run.source``, so these do not feed the 100% gate. They pin what
``--sync-types`` is allowed to delete: a stub the ``type-stubs`` group needs must survive a sync, because
``ty`` in CI runs against exactly that group.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:  # pragma: no cover - import side effect
    sys.path.insert(0, str(TOOLS_DIR))

from depsync.typestubs import _removal_reason


@pytest.fixture
def _no_removal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Report every base distribution as still imported."""
    monkeypatch.setattr("depsync.typestubs.is_orphaned", lambda *_args: False)


@pytest.mark.usefixtures("_no_removal")
def test_stub_is_removed_when_base_package_leaves_the_tree() -> None:
    """Test that a stub for a dependency no longer in uv.lock is removed."""
    assert _removal_reason("pywin32", {"requests"}, set()) == "base package not in dependency tree"


def test_stub_is_removed_when_module_stops_being_imported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a stub whose module nothing imports any more is removed."""
    monkeypatch.setattr("depsync.typestubs.is_orphaned", lambda *_args: True)

    assert _removal_reason("tabulate", {"tabulate"}, set()) == "no file imports the stubbed module any more"


@pytest.mark.usefixtures("_no_removal")
def test_live_stub_is_kept() -> None:
    """Test that a stub whose base package is present and imported is left alone."""
    assert _removal_reason("tabulate", {"tabulate"}, {"tabulate"}) is None
