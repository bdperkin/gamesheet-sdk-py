# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for capped-pin detection.

``tools/`` sits outside ``[tool.coverage] run.source``, so these do not feed the 100% gate. They pin the
decision that governs whether a package is suppressed in Dependabot — a suppression also applies to security
updates, so over-reporting here has a real cost.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:  # pragma: no cover - import side effect
    sys.path.insert(0, str(TOOLS_DIR))

from depsync.caps import detect_capped_pins  # noqa: E402
from depsync.exceptions import FetchError  # noqa: E402


def _stub_index(monkeypatch: pytest.MonkeyPatch, available: dict[str, list[str]]) -> None:
    """Replace the PyPI fetch with a fixed index.

    Args:
        monkeypatch (pytest.MonkeyPatch): Patcher.
        available (dict[str, list[str]]): Package name to the versions the index offers.
    """

    def _fetch(name: str, **_kwargs: object) -> dict[str, str | None]:
        if name not in available:
            msg = f"no such package {name}"
            raise FetchError(msg)

        return dict.fromkeys(available[name])

    monkeypatch.setattr("depsync.caps.fetch_pypi_versions", _fetch)


def test_capped_pin_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a pin below the newest release is reported at its resolved version."""
    _stub_index(monkeypatch, {"rich": ["14.3.4", "15.0.0"]})

    assert detect_capped_pins(["rich"], {"rich": "14.3.4"}) == {"rich": "14.3.4"}


def test_uncapped_pin_is_not_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a pin already at the newest release is left alone.

    This is the case that must not be suppressed: Dependabot should stay free to propose future releases,
    including security ones.
    """
    _stub_index(monkeypatch, {"rich": ["14.3.4"]})

    assert detect_capped_pins(["rich"], {"rich": "14.3.4"}) == {}


def test_resolution_ahead_of_index_is_not_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a resolution newer than anything on the index is not treated as capped."""
    _stub_index(monkeypatch, {"rich": ["14.0.0"]})

    assert detect_capped_pins(["rich"], {"rich": "14.3.4"}) == {}


def test_packages_absent_from_resolution_are_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a package uv did not resolve is ignored rather than guessed at."""
    _stub_index(monkeypatch, {"rich": ["14.3.4", "15.0.0"]})

    assert detect_capped_pins(["rich"], {}) == {}


def test_fetch_failure_omits_the_package(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an unreachable package is omitted rather than suppressed on a guess."""
    _stub_index(monkeypatch, {})

    assert detect_capped_pins(["ghost"], {"ghost": "1.0.0"}) == {}


def test_mixed_set_reports_only_the_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a realistic mix reports exactly the capped subset."""
    _stub_index(
        monkeypatch,
        {
            "rich": ["14.3.4", "15.0.0"],
            "tomlkit": ["0.13.3", "0.15.1"],
            "click": ["8.4.2"],
        },
    )
    resolved = {"rich": "14.3.4", "tomlkit": "0.13.3", "click": "8.4.2"}

    assert detect_capped_pins(resolved, resolved) == {"rich": "14.3.4", "tomlkit": "0.13.3"}


def test_empty_input_does_no_work(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that no packages means no index traffic at all."""

    def _explode(*_args: object, **_kwargs: object) -> dict[str, str | None]:
        msg = "should not fetch"
        raise AssertionError(msg)

    monkeypatch.setattr("depsync.caps.fetch_pypi_versions", _explode)

    assert detect_capped_pins([], {}) == {}


def test_unparseable_version_is_not_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a version that cannot be compared never manufactures a suppression."""
    _stub_index(monkeypatch, {"weird": ["not-a-version"]})

    assert detect_capped_pins(["weird"], {"weird": "1.0.0"}) == {}


@pytest.mark.parametrize(
    ("resolved", "newest", "expected"),
    [
        ("1.0.0", "1.0.1", True),
        ("1.0.0", "1.0.0", False),
        ("1.0.0", "0.9.9", False),
        ("1.0.0", "2.0.0", True),
    ],
)
def test_cap_boundary(
    monkeypatch: pytest.MonkeyPatch,
    resolved: str,
    newest: str,
    expected: bool,
) -> None:
    """Test the comparison at, above, and below the resolved version.

    Args:
        monkeypatch (pytest.MonkeyPatch): Patcher.
        resolved (str): Version uv resolved.
        newest (str): Newest version the index offers.
        expected (bool): Whether that should count as capped.
    """
    _stub_index(monkeypatch, {"pkg": [resolved, newest]})

    result = detect_capped_pins(["pkg"], {"pkg": resolved})

    assert bool(result) is expected
