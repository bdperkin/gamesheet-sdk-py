# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Delegate dependency version resolution to ``uv``.

Picking the latest release of each package independently produces pins that cannot co-exist: a package's own
requirements may cap a sibling below its newest release. Rather than reimplement a resolver, this module asks
``uv lock`` for the answer and harvests the versions it chose, so every version written back to
``pyproject.toml`` is guaranteed to lock.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

import tomlkit
from tomlkit.exceptions import TOMLKitError

from shared.exceptions import ToolError
from shared.toml import PROJECT_NAME, load_toml

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from tomlkit import TOMLDocument
    from tomlkit.items import Table

logger = logging.getLogger(__name__)

UV_RESOLVE_TIMEOUT = 300

# Matches only simple `name==version` / `name[extras]==version` requirements. Anything carrying an
# environment marker, a range, or a URL is left untouched so relaxation cannot corrupt it.
_SIMPLE_PIN = re.compile(r"^([A-Za-z0-9._-]+(?:\[[^\]]+\])?)==([^\s;,]+)$")

# Phrasings uv uses when a requirement can only be satisfied by a yanked release.
_YANKED_PATTERNS = (
    re.compile(r"all versions of ([A-Za-z0-9._-]+) were yanked"),
    re.compile(r"([A-Za-z0-9._-]+)==\S+ was yanked"),
    re.compile(r"([A-Za-z0-9._-]+) was yanked"),
)

# Bounds the restore-and-retry loop; each pass can only convert relaxed pins back to exact ones, so it
# terminates well before this in practice.
_MAX_RESOLVE_ATTEMPTS = 4


class UvResolveError(ToolError):
    """Version resolution via ``uv lock`` failed."""


def _normalize_name(name: str) -> str:
    """Normalize a package name to its PEP 503 form.

    Args:
        name (str): Raw package name.

    Returns:
        str: Lower-cased name with runs of separators collapsed to hyphens.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def versions_from_lock(lock_path: Path) -> dict[str, str]:
    """Read package name to version pairs from a ``uv`` lockfile.

    Args:
        lock_path (Path): Path to a ``uv.lock`` file.

    Returns:
        dict[str, str]: Mapping of normalized package name to locked version. Entries without a version (such
            as the root project when it is unversioned) are skipped.

    Raises:
        UvResolveError: If the lockfile cannot be read or contains invalid TOML.
    """
    try:
        data = load_toml(lock_path)
    except ToolError as exc:
        raise UvResolveError(str(exc)) from exc

    versions: dict[str, str] = {}
    for pkg in data.get("package", []):
        name = pkg.get("name", "")
        version = pkg.get("version")
        if name and version:
            versions[_normalize_name(name)] = str(version)

    logger.debug("Read %d locked versions from %s", len(versions), lock_path)
    return versions


def _relax_entry(entry: str, pins: Mapping[str, str]) -> str | None:
    """Compute the relaxed form of a single dependency string.

    A managed ``==`` pin becomes a bare requirement so ``uv`` is free to pick the highest co-installable
    release. Packages in *pins* keep an exact pin instead, because those versions are dictated by
    ``.genprecommitconfig.yaml`` and must constrain the resolution rather than float with it.

    Args:
        entry (str): Dependency string as written in ``pyproject.toml``.
        pins (Mapping[str, str]): Normalized package name to version that must be held fixed.

    Returns:
        str | None: The replacement string, or None if the entry must be left exactly as written.
    """
    if entry.startswith(f"{PROJECT_NAME}["):
        return None

    match = _SIMPLE_PIN.match(entry.strip())
    if not match:
        return None

    name_part = match.group(1)
    normalized = _normalize_name(name_part.split("[", maxsplit=1)[0])
    pinned = pins.get(normalized)

    return f"{name_part}=={pinned}" if pinned else name_part


def _relax_dep_list(
    dep_list: list,  # type: ignore[type-arg]
    pins: Mapping[str, str],
    loosened: dict[str, str],
) -> None:
    """Relax every managed pin in a dependency array in place.

    Args:
        dep_list (list): TOML array of dependency strings.
        pins (Mapping[str, str]): Normalized package name to version that must be held fixed.
        loosened (dict[str, str]): Collects package name to the original version each relaxed entry had, so a
            pin can be restored if it turns out to be unrelaxable.
    """
    for i, entry in enumerate(dep_list):
        original = str(entry)
        relaxed = _relax_entry(original, pins)
        if relaxed is None:
            continue

        if "==" not in relaxed:
            name, _, version = original.strip().partition("==")
            loosened[_normalize_name(name.split("[", maxsplit=1)[0])] = version

        dep_list[i] = relaxed


def _ensure_uv_table(doc: TOMLDocument) -> Table:
    """Return the ``[tool.uv]`` table, creating it and its parent if absent.

    Args:
        doc (TOMLDocument): Parsed pyproject document.

    Returns:
        Table: The ``[tool.uv]`` table, ready to mutate.
    """
    tool = doc.get("tool")
    if tool is None:
        tool = tomlkit.table()
        doc["tool"] = tool

    uv_table = tool.get("uv")
    if uv_table is None:
        uv_table = tomlkit.table()
        tool["uv"] = uv_table

    return cast("Table", uv_table)


def _apply_overrides(doc: TOMLDocument, overrides: Sequence[str] | None) -> None:
    """Rewrite ``[tool.uv] override-dependencies`` in the scratch copy.

    Args:
        doc (TOMLDocument): Parsed pyproject document, mutated in place.
        overrides (Sequence[str] | None): Requirement strings to install as the override list. ``None`` leaves
            whatever the file already declares untouched; an *empty* sequence removes the overrides entirely,
            which is how a caller asks what the resolution looks like without them.
    """
    if overrides is None:
        return

    uv_table = _ensure_uv_table(doc)
    if overrides:
        uv_table["override-dependencies"] = list(overrides)
    else:
        uv_table.pop("override-dependencies", None)


def _relaxed_pyproject(
    pyproject_path: Path,
    pins: Mapping[str, str],
    overrides: Sequence[str] | None = None,
) -> tuple[str, dict[str, str]]:
    """Render ``pyproject.toml`` with managed pins relaxed.

    Args:
        pyproject_path (Path): Path to the real ``pyproject.toml``.
        pins (Mapping[str, str]): Normalized package name to version that must be held fixed.
        overrides (Sequence[str] | None): Override requirements for the scratch copy. See
            :func:`_apply_overrides` for the None-versus-empty distinction.

    Returns:
        tuple[str, dict[str, str]]: Serialized TOML for the relaxed copy, and the package name to original
            version map for every pin that was loosened.

    Raises:
        UvResolveError: If the file cannot be read, is invalid TOML, or has no ``[project]`` table.
    """
    try:
        doc = tomlkit.parse(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, TOMLKitError) as exc:
        msg = f"Cannot read {pyproject_path}: {exc}"
        raise UvResolveError(msg) from exc

    project = doc.get("project")
    if project is None:
        msg = f"{pyproject_path} has no [project] table"
        raise UvResolveError(msg)

    loosened: dict[str, str] = {}
    _relax_dep_list(project.get("dependencies") or [], pins, loosened)
    for group in (project.get("optional-dependencies") or {}).values():
        _relax_dep_list(group, pins, loosened)

    _apply_overrides(doc, overrides)

    return tomlkit.dumps(doc), loosened


def _run_uv_lock(directory: Path, timeout: int) -> str:
    """Run ``uv lock`` inside *directory*.

    Args:
        directory (Path): Working directory containing the ``pyproject.toml`` to resolve.
        timeout (int): Subprocess timeout in seconds.

    Returns:
        str: Captured stderr when resolution fails, or an empty string on success.

    Raises:
        UvResolveError: If uv is missing, times out, or cannot be executed.
    """
    if shutil.which("uv") is None:
        msg = "'uv' is not on PATH; install uv or pass --no-uv-resolve"
        raise UvResolveError(msg)

    try:
        result = subprocess.run(
            ["uv", "lock"],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            cwd=directory,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"'uv lock' timed out after {timeout}s"
        raise UvResolveError(msg) from exc
    except OSError as exc:
        msg = f"Failed to run 'uv lock': {exc}"
        raise UvResolveError(msg) from exc

    return "" if not result.returncode else result.stderr.strip()


def _unrelaxable_pins(stderr: str, loosened: Mapping[str, str]) -> dict[str, str]:
    """Identify loosened pins that uv rejected because every candidate release is yanked.

    A yanked release is reachable only through an exact pin, so loosening one makes the whole resolution
    unsatisfiable. Those pins are restored verbatim and the resolution retried, which is strictly
    conservative: it reinstates what ``pyproject.toml`` already said.

    Args:
        stderr (str): Captured ``uv lock`` error output.
        loosened (Mapping[str, str]): Package name to original version for pins that were relaxed.

    Returns:
        dict[str, str]: Package name to original version for pins that must be restored.
    """
    # uv hard-wraps its error output, so collapse whitespace before matching across line breaks.
    flat = " ".join(stderr.split())

    restore: dict[str, str] = {}
    for pattern in _YANKED_PATTERNS:
        for match in pattern.finditer(flat):
            name = _normalize_name(match.group(1))
            original = loosened.get(name)
            if original:
                restore[name] = original

    return restore


def _stage_pyproject(directory: Path, content: str) -> None:
    """Write the relaxed pyproject copy into the scratch directory.

    Args:
        directory (Path): Scratch directory.
        content (str): Serialized TOML to write.

    Raises:
        UvResolveError: If the file cannot be written.
    """
    try:
        (directory / "pyproject.toml").write_text(content, encoding="utf-8")
    except OSError as exc:
        msg = f"Cannot stage relaxed pyproject.toml in {directory}: {exc}"
        raise UvResolveError(msg) from exc


def resolve_project_versions(
    pyproject_path: Path,
    *,
    pins: Mapping[str, str] | None = None,
    overrides: Sequence[str] | None = None,
    timeout: int = UV_RESOLVE_TIMEOUT,
) -> dict[str, str]:
    """Resolve every project dependency to the version ``uv`` would lock.

    Copies ``pyproject.toml`` into a scratch directory with managed ``==`` pins relaxed, resolves it with ``uv
    lock``, and returns the chosen versions. The real project directory is never touched, and no existing
    lockfile is copied in, so the resolution is unbiased by previous choices.

    Args:
        pyproject_path (Path): Path to the project's ``pyproject.toml``.
        pins (Mapping[str, str] | None): Normalized package name to version that must be held fixed (typically
            revs pinned in ``.genprecommitconfig.yaml``).
        overrides (Sequence[str] | None): Override requirements to apply to the scratch copy instead of the
            ones the file declares. Passing the declared *bounds* lets uv pick the newest release inside them,
            which is how override pins are discovered; passing an empty sequence strips the overrides and
            answers what the resolution would be without them.
        timeout (int): Subprocess timeout in seconds.

    Returns:
        dict[str, str]: Mapping of normalized package name to resolved version.

    Raises:
        UvResolveError: If the relaxed copy cannot be built or ``uv lock`` fails.
    """
    effective_pins = dict(pins or {})

    with tempfile.TemporaryDirectory(prefix="uv-resolve-") as tmp:
        tmp_dir = Path(tmp)
        for _attempt in range(_MAX_RESOLVE_ATTEMPTS):
            content, loosened = _relaxed_pyproject(pyproject_path, effective_pins, overrides)
            _stage_pyproject(tmp_dir, content)

            stderr = _run_uv_lock(tmp_dir, timeout)
            if not stderr:
                versions = versions_from_lock(tmp_dir / "uv.lock")
                logger.info("uv resolved %d packages", len(versions))
                return versions

            restore = _unrelaxable_pins(stderr, loosened)
            if not restore:
                msg = f"'uv lock' found no valid resolution:\n{stderr}"
                raise UvResolveError(msg)

            for name, version in sorted(restore.items()):
                logger.warning(
                    "Holding %s==%s: every other release is yanked, so the pin cannot be relaxed",
                    name,
                    version,
                )

            effective_pins.update(restore)

    msg = f"'uv lock' did not converge after {_MAX_RESOLVE_ATTEMPTS} attempts"
    raise UvResolveError(msg)
