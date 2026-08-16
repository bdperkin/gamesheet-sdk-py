# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for the ``types-*`` stub gates.

``tools/`` sits outside ``[tool.coverage] run.source``, so these do not feed the 100% gate. They pin the two
rules that decide whether ``--sync-types`` may add a stub — an unused stub is not inert, it is a second,
staler definition of a package waiting to shadow the real one — and, just as importantly, they pin the
asymmetry that stops the same rules from *removing* a stub that is deliberately kept.
"""

from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:  # pragma: no cover - import side effect
    sys.path.insert(0, str(TOOLS_DIR))

from depsync.typedness import (
    NOT_IMPORTED_REASON,
    PY_TYPED_REASON,
    collect_imported_modules,
    filter_stub_candidates,
    is_orphaned,
    rejection_reason,
    resolve_top_level,
    ships_py_typed,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest


class _FakeDistribution:
    """Minimal stand-in for :class:`importlib.metadata.Distribution`."""

    def __init__(self, files: Sequence[str] | None, top_level: str | None = None) -> None:
        self.files = None if files is None else [PurePosixPath(name) for name in files]
        self._top_level = top_level

    def read_text(self, filename: str) -> str | None:
        """Return the recorded ``top_level.txt`` content.

        Returns:
            str | None: Declared top-level names, or None when the metadata file is absent.

        """
        return self._top_level if filename == "top_level.txt" else None


def _install(monkeypatch: pytest.MonkeyPatch, installed: dict[str, _FakeDistribution]) -> None:
    """Replace metadata lookup with a fixed set of installed distributions.

    Args:
        monkeypatch (pytest.MonkeyPatch): Patcher.
        installed (dict[str, _FakeDistribution]): Distribution name to its fake metadata.

    """
    from importlib.metadata import PackageNotFoundError

    def _distribution(name: str) -> _FakeDistribution:
        if name not in installed:
            raise PackageNotFoundError(name)

        return installed[name]

    monkeypatch.setattr("depsync.typedness.distribution", _distribution)


def test_imports_are_collected_across_roots(tmp_path: Path) -> None:
    """Test that every configured root is scanned, at any nesting depth."""
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "mod.py").write_text("import requests.adapters\n")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "helper.py").write_text("from ruamel.yaml import YAML\n")

    imported = collect_imported_modules(tmp_path)

    assert {"requests", "ruamel"} <= imported


def test_function_level_import_counts(tmp_path: Path) -> None:
    """Test that an import nested inside a function is still seen.

    ``tools/precommit/processor.py`` imports ``pre_commit`` inside a function body, so a module-level-only
    scan would wrongly declare the module unimported.
    """
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_text("def f():\n    from pre_commit.clientlib import x\n")

    assert "pre_commit" in collect_imported_modules(tmp_path)


def test_relative_imports_are_ignored(tmp_path: Path) -> None:
    """Test that a relative import contributes nothing, since it can never name a distribution."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_text("from . import sibling\nfrom .pkg import thing\n")

    assert collect_imported_modules(tmp_path) == set()


def test_unparsable_file_is_skipped(tmp_path: Path) -> None:
    """Test that a file with a syntax error does not abort the scan."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "broken.py").write_text("def (:\n")
    (tmp_path / "src" / "fine.py").write_text("import tabulate\n")

    assert collect_imported_modules(tmp_path) == {"tabulate"}


def test_missing_root_is_skipped(tmp_path: Path) -> None:
    """Test that a project without one of the configured roots scans the rest."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("import yaml\n")

    assert collect_imported_modules(tmp_path) == {"yaml"}


def test_top_level_txt_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that declared top-level names are used when the distribution ships them."""
    _install(monkeypatch, {"pyyaml": _FakeDistribution(["yaml/__init__.py"], top_level="yaml\n_yaml\n")})

    assert resolve_top_level("pyyaml") == {"yaml", "_yaml"}


def test_top_level_falls_back_to_file_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that names are derived from the file list when top_level.txt is absent."""
    _install(
        monkeypatch,
        {
            "python-dateutil": _FakeDistribution(
                [
                    "dateutil/__init__.py",
                    "dateutil/tz/tz.py",
                    "six.py",
                    "python_dateutil-2.9.0.dist-info/METADATA",
                    "../../bin/script",
                ],
            ),
        },
    )

    assert resolve_top_level("python-dateutil") == {"dateutil", "six"}


def test_uninstalled_distribution_resolves_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an absent distribution yields None rather than a guessed module name."""
    _install(monkeypatch, {})

    assert resolve_top_level("pywin32") is None


def test_py_typed_is_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a PEP 561 marker anywhere in the file list is found."""
    _install(monkeypatch, {"click": _FakeDistribution(["click/__init__.py", "click/py.typed"])})

    assert ships_py_typed("click") is True


def test_py_typed_absence_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a distribution without the marker reports False, not None."""
    _install(monkeypatch, {"tabulate": _FakeDistribution(["tabulate/__init__.py"])})

    assert ships_py_typed("tabulate") is False


def test_py_typed_is_unknown_when_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an uninstalled distribution answers None, distinct from a real False."""
    _install(monkeypatch, {})

    assert ships_py_typed("pywin32") is None


def test_unimported_module_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that rule 1 rejects a stub nothing in the tree would consult.

    This is the rule that keeps the group from drifting back to 34 entries.
    """
    _install(monkeypatch, {"zipp": _FakeDistribution(["zipp/__init__.py"])})

    assert rejection_reason("zipp", {"requests"}) == NOT_IMPORTED_REASON.format(
        roots="src/tests/tools/docs",
        modules="zipp",
    )


def test_py_typed_distribution_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that rule 2 rejects an imported distribution that carries inline types.

    ``types-click==7.1.8`` described click 7 while the project ran click 8, so the stub shadowed
    ``click.shell_completion`` out of existence. Rule 2 is what stops that stub being proposed again.
    """
    _install(monkeypatch, {"click": _FakeDistribution(["click/__init__.py", "click/py.typed"])})

    assert rejection_reason("click", {"click"}) == PY_TYPED_REASON


def test_imported_untyped_distribution_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a stub is warranted when the module is imported and has no inline types."""
    _install(monkeypatch, {"tabulate": _FakeDistribution(["tabulate/__init__.py"])})

    assert rejection_reason("tabulate", {"tabulate"}) is None


def test_uninstalled_candidate_is_rejected_on_the_guessed_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an undeterminable candidate is rejected rather than added.

    Not adding is the cheap direction: ``ty`` reports the unresolved import and the stub is then added
    deliberately.
    """
    _install(monkeypatch, {})

    assert rejection_reason("some-unused-pkg", {"requests"}) == NOT_IMPORTED_REASON.format(
        roots="src/tests/tools/docs",
        modules="some_unused_pkg",
    )


def test_candidates_are_split_and_prefixed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that survivors come back bare and rejects come back as types-* with a reason."""
    _install(
        monkeypatch,
        {
            "tabulate": _FakeDistribution(["tabulate/__init__.py"]),
            "click": _FakeDistribution(["click/__init__.py", "click/py.typed"]),
            "zipp": _FakeDistribution(["zipp/__init__.py"]),
        },
    )

    keep, skipped = filter_stub_candidates({"tabulate", "click", "zipp"}, {"tabulate", "click"})

    assert keep == {"tabulate"}
    assert [name for name, _ in skipped] == ["types-click", "types-zipp"]
    assert dict(skipped)["types-click"] == PY_TYPED_REASON


def test_stub_for_unimported_module_is_orphaned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an installed distribution nobody imports is reported as orphaned."""
    _install(monkeypatch, {"zipp": _FakeDistribution(["zipp/__init__.py"])})

    assert is_orphaned("zipp", {"requests"}) is True


def test_stub_for_py_typed_distribution_is_not_orphaned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that shipping py.typed never makes an existing stub removable.

    ``types-requests`` is kept on purpose: typeshed types ``Session.headers`` as
    ``CaseInsensitiveDict[str | bytes]`` where requests itself says ``CaseInsensitiveDict[str]``, and the
    wider view is the accurate one. Rule 2 gates additions only, so this stub survives a sync.
    """
    _install(monkeypatch, {"requests": _FakeDistribution(["requests/__init__.py", "requests/py.typed"])})

    assert is_orphaned("requests", {"requests"}) is False


def test_uninstalled_distribution_is_never_orphaned(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a removal is not proposed from a guessed module name.

    ``pyyaml`` provides ``yaml`` and ``python-dateutil`` provides ``dateutil``, so a name-derived guess would
    delete load-bearing stubs and break ``ty`` in CI.
    """
    _install(monkeypatch, {})

    assert is_orphaned("pyyaml", {"yaml"}) is False


def test_file_list_absent_resolves_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a distribution with no recorded files is treated as undeterminable."""
    _install(monkeypatch, {"ghost": _FakeDistribution(None)})

    assert resolve_top_level("ghost") is None
    assert is_orphaned("ghost", set()) is False
