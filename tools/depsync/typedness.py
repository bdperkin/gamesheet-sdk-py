# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Gates deciding whether a ``types-*`` stub belongs in the ``type-stubs`` group.

``--sync-types`` used to add ``types-<pkg>`` for every resolved dependency whose stub merely *exists* on
PyPI, which is how the group reached 34 entries: 30 of them stubbed modules nothing in the tree imports, and
one (``types-click``) described a major version older than the one the project runs, shadowing click's own
inline types so ``click.shell_completion`` read as unresolved. An unused or shadowing stub is not inert — it
is a second, staler definition of a package waiting to be checked against instead of the real one.

Two rules therefore gate an addition.

**Rule 1, imported.** Some file under ``src/``, ``tests/``, ``tools/`` or ``docs/`` must import a top-level
module the distribution provides. A stub for a module no file imports can only ever shadow, never help.

**Rule 2, no inline types.** The runtime distribution must not ship ``py.typed``. A distribution with inline
types needs no stub, and a stub for it *shadows* those types — PEP 561 puts stubs ahead of inline annotations.

The rules are deliberately asymmetric between adding and removing, and the asymmetry is the load-bearing part.

For an **addition**, an undeterminable answer rejects. Not adding is cheap: ``ty`` reports the unresolved
import and the stub gets added deliberately, which is the documented workflow.

For a **removal**, an undeterminable answer keeps. ``resolve_top_level`` returns None when the distribution is
not installed in the environment ``syncdeps`` runs in, and guessing a module name from a distribution name is
unreliable — ``pyyaml`` provides ``yaml``, ``python-dateutil`` provides ``dateutil``. Removing a load-bearing
stub on a guess would break ``ty`` in CI.

Only rule 1 drives removals at all. Rule 2 is add-time only, because a stub that shadows ``py.typed`` is
sometimes the one that is right: ``types-requests`` is kept on purpose, since typeshed types
``Session.headers`` as ``CaseInsensitiveDict[str | bytes]`` where requests itself says
``CaseInsensitiveDict[str]``, and the wider view is the accurate one. "Stub shadows ``py.typed``" is a prompt
to verify, not an automatic removal — so it may block an unreviewed addition but never undo a reviewed keep.
"""

from __future__ import annotations

import ast
import logging
import re
from importlib.metadata import PackageNotFoundError, distribution
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from pathlib import Path, PurePath

logger = logging.getLogger(__name__)

# Directories scanned for imports. A stub only earns its place if one of these imports the module.
SOURCE_ROOTS: tuple[str, ...] = ("src", "tests", "tools", "docs")

# Rule 2's reason, as a constant so callers can group reasons without parsing prose.
PY_TYPED_REASON = "ships py.typed; a stub would shadow its inline types"

# Rule 1's reason, formatted per candidate with the modules the stub would have covered.
NOT_IMPORTED_REASON = "nothing under {roots} imports {modules}"


def _iter_python_files(project_root: Path, roots: Sequence[str]) -> Iterator[Path]:
    """Yield every ``*.py`` file under the given roots that exist.

    Yields:
        Path: Python source files, in directory-walk order.

    """
    for root in roots:
        directory = project_root / root
        if not directory.is_dir():
            logger.debug("Import scan: %s does not exist; skipping", directory)
            continue

        yield from sorted(directory.rglob("*.py"))


def _module_names(node: ast.AST) -> set[str]:
    """Extract top-level module names imported by a single statement.

    Relative imports resolve inside the project, never to a distribution, so they are ignored.

    Returns:
        set[str]: Top-level names, empty for statements that are not imports.

    """
    if isinstance(node, ast.Import):
        return {alias.name.split(".", maxsplit=1)[0] for alias in node.names}

    if isinstance(node, ast.ImportFrom) and not node.level and node.module:
        return {node.module.split(".", maxsplit=1)[0]}

    return set()


def collect_imported_modules(
    project_root: Path,
    roots: Sequence[str] = SOURCE_ROOTS,
) -> set[str]:
    """Collect every top-level module name imported anywhere under *roots*.

    Args:
        project_root (Path): Directory holding ``pyproject.toml``.
        roots (Sequence[str]): Directories to scan, relative to *project_root*.

    Returns:
        set[str]: Top-level module names, including stdlib and first-party ones. Callers intersect against a
            distribution's own modules, so the extra names are harmless.

    """
    imported: set[str] = set()
    for path in _iter_python_files(project_root, roots):
        try:
            tree = ast.parse(path.read_bytes(), filename=str(path))
        except (SyntaxError, ValueError, OSError):
            logger.warning("Import scan: cannot parse %s; skipping", path)
            continue

        for node in ast.walk(tree):
            imported |= _module_names(node)

    logger.debug("Import scan: %d distinct top-level modules imported", len(imported))
    return imported


def _names_from_record(dist_files: Iterable[PurePath]) -> set[str]:
    """Derive importable top-level names from a distribution's file list.

    Returns:
        set[str]: Package directory names and top-level module stems, ignoring metadata directories.

    """
    names: set[str] = set()
    for path in dist_files:
        parts = path.parts
        if parts[0].endswith((".dist-info", ".egg-info")) or parts[0] == "..":
            continue

        if len(parts) > 1:
            names.add(parts[0])
        elif path.suffix == ".py":
            names.add(path.stem)

    return names


def resolve_top_level(dist_name: str) -> set[str] | None:
    """Resolve the top-level modules a distribution provides, from installed metadata.

    Args:
        dist_name (str): Distribution (PyPI) name.

    Returns:
        set[str] | None: Module names, or None when the distribution is not installed here and the answer
            would only be a guess.

    """
    try:
        dist = distribution(dist_name)
    except PackageNotFoundError:
        logger.debug("%s is not installed; top-level modules unknown", dist_name)
        return None

    declared = dist.read_text("top_level.txt")
    if declared:
        return {line.strip() for line in declared.splitlines() if line.strip()}

    return _names_from_record(dist.files or ()) or None


def ships_py_typed(dist_name: str) -> bool | None:
    """Report whether a distribution ships a PEP 561 ``py.typed`` marker.

    Args:
        dist_name (str): Distribution (PyPI) name.

    Returns:
        bool | None: True/False from installed metadata, or None when the distribution is not installed here.

    """
    try:
        dist = distribution(dist_name)
    except PackageNotFoundError:
        logger.debug("%s is not installed; cannot inspect for py.typed", dist_name)
        return None

    return any(path.name == "py.typed" for path in dist.files or ())


def _fallback_name(dist_name: str) -> str:
    """Guess the import name of a distribution from its PyPI name.

    Returns:
        str: PEP 503 name with separators turned into underscores.

    """
    return re.sub(r"[-.]+", "_", dist_name).lower()


def rejection_reason(dist_name: str, imported: Iterable[str]) -> str | None:
    """Explain why *dist_name* should not gain a ``types-*`` stub, if it should not.

    Args:
        dist_name (str): Base distribution name (no ``types-`` prefix).
        imported (Iterable[str]): Top-level module names imported anywhere in the tree.

    Returns:
        str | None: Human-readable reason, or None when a stub is warranted.

    """
    modules = resolve_top_level(dist_name) or {_fallback_name(dist_name)}
    if not modules & set(imported):
        return NOT_IMPORTED_REASON.format(
            roots="/".join(SOURCE_ROOTS),
            modules=", ".join(sorted(modules)),
        )

    if ships_py_typed(dist_name):
        return PY_TYPED_REASON

    return None


def filter_stub_candidates(
    candidates: Iterable[str],
    imported: Iterable[str],
) -> tuple[set[str], list[tuple[str, str]]]:
    """Split stub candidates into those worth checking on the index and those to skip.

    Args:
        candidates (Iterable[str]): Base distribution names under consideration.
        imported (Iterable[str]): Top-level module names imported anywhere in the tree.

    Returns:
        tuple[set[str], list[tuple[str, str]]]: Candidates to keep, and (name, reason) pairs for the rest.

    """
    imported = set(imported)
    keep: set[str] = set()
    skipped: list[tuple[str, str]] = []
    for name in sorted(candidates):
        reason = rejection_reason(name, imported)
        if reason is None:
            keep.add(name)
        else:
            skipped.append((f"types-{name}", reason))
            logger.debug("  Skip types-%s: %s", name, reason)

    return keep, skipped


def is_orphaned(dist_name: str, imported: Iterable[str]) -> bool:
    """Report whether an existing stub's base distribution is no longer imported anywhere.

    Answers False when the distribution is not installed, so a removal is never proposed on a guessed module
    name. See the module docstring for why adding and removing are gated asymmetrically.

    Args:
        dist_name (str): Base distribution name (no ``types-`` prefix).
        imported (Iterable[str]): Top-level module names imported anywhere in the tree.

    Returns:
        bool: True only when the provided modules are known and none of them is imported.

    """
    modules = resolve_top_level(dist_name)
    if modules is None:
        return False

    return not modules & set(imported)
