# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Transitive-dependency overrides.

``syncdeps`` converges *declared* dependencies. A transitive package whose version is dictated by an upstream
requirement is not declared anywhere, so there is no pin to converge and bumping the parent cannot move it.
This module handles that case: policy is declared in ``.syncdepsoverrides.yaml``, the resolved exact pin is
written to ``[tool.uv] override-dependencies`` in ``pyproject.toml``.

Resolution is delegated to ``uv`` for the same reason the rest of the tool delegates it — the newest release
inside the declared bounds is whatever ``uv`` picks when handed those bounds, so the pin is lockable by
construction.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from typing import TYPE_CHECKING, cast

import tomlkit
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from tomlkit.exceptions import TOMLKitError

from depsync.exceptions import ParseError, VerifyError, WriteError
from depsync.models import OverridePolicy, OverrideResult

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from tomlkit import TOMLDocument
    from tomlkit.items import Array

logger = logging.getLogger(__name__)

VERIFY_TIMEOUT = 600


def parse_overrides(path: Path) -> list[OverridePolicy]:
    """Read override policies from ``.syncdepsoverrides.yaml``.

    A missing file is not an error: a project with no transitive overrides simply has nothing to declare.

    Args:
        path (Path): Path to the overrides policy file.

    Returns:
        list[OverridePolicy]: Declared policies, empty if the file is absent or declares none.

    Raises:
        ParseError: If the file cannot be read, is not valid YAML, or an entry is missing required fields.
    """
    if not path.exists():
        logger.debug("%s not found, no transitive overrides declared", path)
        return []

    yaml = YAML()
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.load(handle)
    except (OSError, YAMLError) as exc:
        msg = f"Cannot parse {path}: {exc}"
        raise ParseError(msg) from exc

    entries = (data or {}).get("overrides") or []
    try:
        policies = [OverridePolicy.model_validate(dict(entry)) for entry in entries]
    except ValidationError as exc:
        msg = f"Invalid override entry in {path}: {exc}"
        raise ParseError(msg) from exc

    _validate_bounds(policies, path)
    logger.debug("Parsed %d override policies from %s", len(policies), path)
    return policies


def _validate_bounds(policies: Sequence[OverridePolicy], path: Path) -> None:
    """Reject bounds that are not parseable PEP 440 specifiers.

    Catching this here means a typo surfaces as a clear error rather than as a resolution that silently
    excludes every candidate.

    Args:
        policies (Sequence[OverridePolicy]): Parsed policies to check.
        path (Path): Policy file path, for the error message.

    Raises:
        ParseError: If any policy's floor or ceiling is not a valid specifier.
    """
    for policy in policies:
        bounds = policy.floor if policy.ceiling is None else f"{policy.floor},{policy.ceiling}"
        try:
            SpecifierSet(bounds)
        except InvalidSpecifier as exc:
            msg = f"Invalid bounds for {policy.package} in {path}: {bounds} ({exc})"
            raise ParseError(msg) from exc


def current_overrides(pyproject_path: Path) -> dict[str, str]:
    """Read the exact override pins currently written to ``pyproject.toml``.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.

    Returns:
        dict[str, str]: Mapping of package name to pinned version, for entries written as ``name==version``.
            Anything not in that form is ignored, since only exact pins are managed.

    Raises:
        ParseError: If the file cannot be read or is invalid TOML.
    """
    try:
        doc = tomlkit.parse(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, TOMLKitError) as exc:
        msg = f"Cannot read {pyproject_path}: {exc}"
        raise ParseError(msg) from exc

    declared = (doc.get("tool") or {}).get("uv", {}).get("override-dependencies") or []

    pins: dict[str, str] = {}
    for entry in declared:
        name, separator, version = str(entry).partition("==")
        if separator and version:
            pins[name.strip()] = version.strip()

    return pins


def _satisfies_floor(version: str, floor: str) -> bool:
    """Check whether *version* meets a policy's floor.

    Args:
        version (str): Candidate version string.
        floor (str): Floor as a PEP 440 specifier.

    Returns:
        bool: True if the version satisfies the floor. An unparseable version is treated as not satisfying it,
            which is the conservative reading — it keeps the override in place rather than retiring it on the
            strength of something we cannot compare.
    """
    try:
        return Version(version) in SpecifierSet(floor)
    except (InvalidVersion, InvalidSpecifier):
        logger.warning("Cannot compare %s against floor %s; treating floor as unmet", version, floor)
        return False


def converge_overrides(
    policies: Sequence[OverridePolicy],
    pinned: Mapping[str, str],
    bounded: Mapping[str, str],
    unpinned: Mapping[str, str],
) -> list[OverrideResult]:
    """Determine the target pin for each override policy.

    Args:
        policies (Sequence[OverridePolicy]): Declared override policies.
        pinned (Mapping[str, str]): Package name to version currently pinned in ``pyproject.toml``.
        bounded (Mapping[str, str]): Versions uv resolved with the declared bounds applied.
        unpinned (Mapping[str, str]): Versions uv resolved with the overrides stripped, used to decide whether
            an override is still doing any work.

    Returns:
        list[OverrideResult]: One result per policy whose package uv actually resolved. A policy uv did not
            resolve is skipped with a warning rather than guessed at.
    """
    results: list[OverrideResult] = []
    for policy in policies:
        target = bounded.get(policy.package)
        if target is None:
            logger.warning(
                "uv did not resolve %s within %s; leaving its override untouched",
                policy.package,
                policy.specifier(),
            )
            continue

        without = unpinned.get(policy.package)
        results.append(
            OverrideResult(
                package=policy.package,
                old_version=pinned.get(policy.package),
                new_version=target,
                retirable=without is not None and _satisfies_floor(without, policy.floor),
                unpinned_version=without,
            ),
        )

    return results


def run_verify(policy: OverridePolicy) -> None:
    """Run a policy's verify command, raising if it does not exit 0.

    The command runs only after the new pin is on disk and locked, so what it exercises is the real
    environment rather than a hypothetical one.

    Args:
        policy (OverridePolicy): Policy whose verify command should run.

    Raises:
        VerifyError: If the command exits non-zero, times out, or cannot be executed.
    """
    if policy.verify is None:
        logger.debug("No verify command declared for %s", policy.package)
        return

    logger.info("Verifying %s override: %s", policy.package, policy.verify)
    try:
        result = subprocess.run(
            shlex.split(policy.verify),
            capture_output=True,
            text=True,
            check=False,
            timeout=VERIFY_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"Verify command for {policy.package} timed out after {VERIFY_TIMEOUT}s"
        raise VerifyError(msg) from exc
    except OSError as exc:
        msg = f"Cannot run verify command for {policy.package}: {exc}"
        raise VerifyError(msg) from exc

    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        msg = f"Verify command for {policy.package} failed (exit {result.returncode}):\n{detail}"
        raise VerifyError(msg)


def _override_array(doc: TOMLDocument) -> Array:
    """Return the ``[tool.uv] override-dependencies`` array, creating what is missing.

    A project declaring its first override has no ``[tool.uv]`` table at all, so the tables and the array are
    materialized on demand rather than treated as an error.

    Args:
        doc (TOMLDocument): Parsed pyproject document, mutated in place.

    Returns:
        Array: The override array, ready to mutate.
    """
    tool = doc.get("tool")
    if tool is None:
        tool = tomlkit.table()
        doc["tool"] = tool

    uv_table = tool.get("uv")
    if uv_table is None:
        uv_table = tomlkit.table()
        tool["uv"] = uv_table

    declared = uv_table.get("override-dependencies")
    if declared is None:
        declared = tomlkit.array().multiline(multiline=True)
        uv_table["override-dependencies"] = declared

    return cast("Array", declared)


def update_pyproject_overrides(pyproject_path: Path, results: Sequence[OverrideResult]) -> int:
    """Write resolved override pins into ``[tool.uv] override-dependencies``.

    Only entries whose version actually changes are touched, and only for the managed package, so an unrelated
    hand-written override survives. A policy with no entry yet is appended.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.
        results (Sequence[OverrideResult]): Converged override results.

    Returns:
        int: Number of entries written.

    Raises:
        WriteError: If the file cannot be read or written.
    """
    changed = [r for r in results if r.old_version != r.new_version]
    if not changed:
        return 0

    try:
        doc = tomlkit.parse(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, TOMLKitError) as exc:
        msg = f"Cannot read {pyproject_path}: {exc}"
        raise WriteError(msg) from exc

    written = _rewrite_override_entries(_override_array(doc), changed)

    try:
        pyproject_path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    except OSError as exc:
        msg = f"Cannot write {pyproject_path}: {exc}"
        raise WriteError(msg) from exc

    logger.info("Updated %d override pins in %s", written, pyproject_path)
    return written


def _rewrite_override_entries(
    declared: Array,
    changed: Sequence[OverrideResult],
) -> int:
    """Replace matching entries in the override array in place, appending any that are absent.

    Args:
        declared (Array): TOML array of override requirement strings.
        changed (Sequence[OverrideResult]): Results whose pins need writing.

    Returns:
        int: Number of entries written, counting both replacements and additions.
    """
    targets = {r.package: r.new_version for r in changed}

    written = 0
    for index, entry in enumerate(declared):
        name = str(entry).partition("==")[0].strip()
        version = targets.pop(name, None)
        if version is not None:
            declared[index] = f"{name}=={version}"
            written += 1

    for name, version in sorted(targets.items()):
        declared.append(f"{name}=={version}")
        written += 1

    return written
