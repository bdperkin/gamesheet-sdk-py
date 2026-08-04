# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Style-preserving writers for pyproject.toml, pre-commit configs, and types-* sync."""

from __future__ import annotations

import io
import logging
from pathlib import Path
import re
from typing import Any

from depsync.exceptions import WriteError
from depsync.models import ConvergenceResult, UpdateTarget
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from shared import PROJECT_NAME
from tomlkit.toml_file import TOMLFile

logger = logging.getLogger(__name__)


def _create_yaml(*, wide: bool = False, explicit_start: bool = False) -> YAML:
    yml = YAML()
    yml.preserve_quotes = True
    yml.indent(mapping=2, sequence=4, offset=2)
    yml.default_flow_style = False
    if wide:
        yml.width = 4096
    if explicit_start:
        yml.explicit_start = True
    return yml


def _write_yaml(path: Path, yml: YAML, data: object) -> None:
    buf = io.StringIO()
    yml.dump(data, buf)
    cleaned = "\n".join(line.rstrip() for line in buf.getvalue().splitlines()) + "\n"
    with path.open("w", encoding="utf-8") as fh:
        fh.write(cleaned)


def _read_toml(path: Path) -> tuple[TOMLFile, Any]:
    """Read a TOML file and return the file handle and parsed document.

    :returns: Tuple of (TOMLFile, parsed document).
    :raises WriteError: If the file cannot be read.
    """
    try:
        toml_file = TOMLFile(str(path))
        doc = toml_file.read()
    except Exception as exc:
        msg = f"Failed to read {path}: {exc}"
        raise WriteError(msg) from exc
    return toml_file, doc


def _write_toml(path: Path, toml_file: TOMLFile, doc: Any) -> None:
    """Write a TOML document back to disk.

    :raises WriteError: If the file cannot be written.
    """
    try:
        toml_file.write(doc)
    except Exception as exc:
        msg = f"Failed to write {path}: {exc}"
        raise WriteError(msg) from exc


def _read_yaml_file(path: Path, yml: YAML) -> Any:
    """Read a YAML file and return the parsed data.

    :returns: Parsed YAML data.
    :raises WriteError: If the file cannot be read.
    """
    try:
        with path.open(encoding="utf-8") as f:
            return yml.load(f)
    except Exception as exc:
        msg = f"Failed to read {path}: {exc}"
        raise WriteError(msg) from exc


def _write_yaml_file(path: Path, yml: YAML, data: Any) -> None:
    """Write YAML data back to disk.

    :raises WriteError: If the file cannot be written.
    """
    try:
        _write_yaml(path, yml, data)
    except Exception as exc:
        msg = f"Failed to write {path}: {exc}"
        raise WriteError(msg) from exc


def _get_toml_key(doc: Any, keys: list[str], path: Path) -> Any:
    """Traverse nested keys in a TOML document.

    :returns: The value at the nested key path.
    :raises WriteError: If any key in the path is missing.
    """
    try:
        current = doc
        for key in keys:
            current = current[key]
    except KeyError as exc:
        dotted = ".".join(keys)
        msg = f"{path} is missing [{dotted}]"
        raise WriteError(msg) from exc
    return current


def _normalize_dep_name(dep_lower: str) -> str:
    """Extract and normalize the package name from a dependency string.

    :returns: Normalized name with separators replaced by hyphens.
    """
    name = dep_lower.split("==", maxsplit=1)[0].split("[", maxsplit=1)[0]
    return re.sub(r"[-_.]+", "-", name)


def _update_dep_in_list(
    dep_list: list,  # type: ignore[type-arg]
    result: ConvergenceResult,
) -> None:
    for i, entry in enumerate(dep_list):
        dep_str = str(entry)
        dep_lower = dep_str.lower()
        name_lower = result.package.lower()

        is_match = _normalize_dep_name(dep_lower) == name_lower

        if is_match:
            if "==" in dep_str:
                prefix = dep_str.split("==", maxsplit=1)[0]
                dep_list[i] = f"{prefix}=={result.new_version}"
            else:
                dep_list[i] = f"{dep_str}=={result.new_version}"

            logger.debug("  Updated %s in group", result.package)
            return


def update_pyproject(
    path: Path,
    results: list[ConvergenceResult],
) -> int:
    """Update dependency versions in pyproject.toml, preserving formatting.

    :param path: Path to pyproject.toml.
    :type path: Path
    :param results: Convergence results targeting pyproject.toml.
    :type results: list[ConvergenceResult]
    :returns: Number of dependencies updated.
    :rtype: int
    :raises WriteError: If the file cannot be read or written.
    """
    pyproject_results = [
        r
        for r in results
        if r.target in {UpdateTarget.PYPROJECT, UpdateTarget.BOTH}
        and r.groups
        and r.old_version != r.new_version
    ]
    if not pyproject_results:
        return 0

    toml_file, doc = _read_toml(path)

    opt_deps = _get_toml_key(doc, ["project", "optional-dependencies"], path)

    updated_count = 0

    for result in pyproject_results:
        for group_name in result.groups:
            if group_name == "base":
                dep_list = _get_toml_key(doc, ["project", "dependencies"], path)
            else:
                if group_name not in opt_deps:
                    continue
                dep_list = opt_deps[group_name]

            _update_dep_in_list(dep_list, result)
            updated_count += 1

    _write_toml(path, toml_file, doc)

    logger.info("Updated %d dependency entries in %s", updated_count, path)
    return updated_count


def _update_additional_dep_list(
    ad_list: list,  # type: ignore[type-arg]
    pkg_to_result: dict[str, ConvergenceResult],
) -> int:
    count = 0
    for i, raw_ad_str in enumerate(ad_list):
        ad_value = str(raw_ad_str)
        if "==" in ad_value:
            name_part = ad_value.split("==", maxsplit=1)[0].strip().lower()
        else:
            name_part = ad_value.strip().lower()
        name_match = re.match(r"^([a-zA-Z0-9\-_]+)", name_part)
        if not name_match:
            continue
        normalized = re.sub(r"[-_.]+", "-", name_match.group(1)).lower()
        if normalized == _normalize_dep_name(PROJECT_NAME):
            continue
        if normalized in pkg_to_result:
            result = pkg_to_result[normalized]
            prefix = ad_value.split("==", maxsplit=1)[0] if "==" in ad_value else ad_value
            ad_list[i] = f"{prefix}=={result.new_version}"
            count += 1
    return count


def _update_repo_additional_deps(
    repo_entry: dict,  # type: ignore[type-arg]
    pkg_to_result: dict[str, ConvergenceResult],
) -> int:
    count = 0
    for hook_entry in repo_entry.get("hooks", []):
        for section_key in ("overrides", "appends"):
            section = hook_entry.get(section_key, {})
            ad_list = section.get("additional_dependencies")
            if not ad_list:
                continue
            count += _update_additional_dep_list(ad_list, pkg_to_result)
    return count


def update_genprecommit_additional_deps(
    path: Path,
    results: list[ConvergenceResult],
) -> int:
    """Update additional_dependencies versions in .genprecommitconfig.yaml.

    :param path: Path to .genprecommitconfig.yaml.
    :type path: Path
    :param results: Convergence results targeting additional_dependencies.
    :type results: list[ConvergenceResult]
    :returns: Number of additional_dependencies updated.
    :rtype: int
    :raises WriteError: If the file cannot be read or written.
    """
    ad_results = [
        r
        for r in results
        if r.is_additional_dep and r.target in {UpdateTarget.GENPRECOMMIT, UpdateTarget.BOTH}
    ]
    if not ad_results:
        return 0

    yml = _create_yaml(wide=True)
    data = _read_yaml_file(path, yml)

    pkg_to_result: dict[str, ConvergenceResult] = {r.package: r for r in ad_results}
    updated_count = 0

    for cat in (data.get("categories") or {}).values():
        if not cat:
            continue
        for repo_entry in cat.get("repos", []):
            updated_count += _update_repo_additional_deps(
                repo_entry,
                pkg_to_result,
            )

    if updated_count > 0:
        _write_yaml_file(path, yml, data)

    logger.info(
        "Updated %d additional_dependencies in %s",
        updated_count,
        path,
    )
    return updated_count


def update_precommit_config(
    path: Path,
    results: list[ConvergenceResult],
) -> int:
    """Update revs and additional_dependencies in .pre-commit-config.yaml.

    :param path: Path to .pre-commit-config.yaml.
    :type path: Path
    :param results: All convergence results.
    :type results: list[ConvergenceResult]
    :returns: Number of entries updated.
    :rtype: int
    :raises WriteError: If the file cannot be read or written.
    """
    rev_results = {r.repo_url: r for r in results if r.needs_regeneration and r.rev_tag}
    ad_results = {
        r.package: r
        for r in results
        if r.is_additional_dep and r.target in {UpdateTarget.GENPRECOMMIT, UpdateTarget.BOTH}
    }

    if not rev_results and not ad_results:
        return 0

    yml = _create_yaml(explicit_start=True)
    data = _read_yaml_file(path, yml)

    updated_count = 0

    for repo_entry in data.get("repos", []):
        url = repo_entry.get("repo", "")

        if url in rev_results:
            repo_entry["rev"] = rev_results[url].rev_tag
            updated_count += 1
            logger.debug("  Updated rev for %s", url)

        if ad_results:
            for hook_entry in repo_entry.get("hooks", []):
                ad_list = hook_entry.get("additional_dependencies")
                if ad_list:
                    updated_count += _update_additional_dep_list(ad_list, ad_results)

    if updated_count > 0:
        _write_yaml_file(path, yml, data)

    logger.info("Updated %d entries in %s", updated_count, path)
    return updated_count


def _find_pip_ecosystem(data: Any) -> Any | None:
    for update in data.get("updates") or []:
        if update.get("package-ecosystem") == "pip":
            return update
    return None


def _extract_current_ignores(pip_entry: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for entry in pip_entry.get("ignore") or []:
        name = entry.get("dependency-name", "")
        versions = entry.get("versions", [])
        if name and versions:
            result[name] = str(versions[0])
    return result


def _build_ignore_list(desired_ignores: dict[str, str]) -> Any:
    ignore_list = CommentedSeq()
    ignore_list.yaml_set_start_comment(
        "Managed by syncdeps — do not edit manually",
        indent=6,
    )
    for name, constraint in sorted(desired_ignores.items()):
        entry = CommentedMap()
        entry["dependency-name"] = name
        versions_seq = CommentedSeq([constraint])
        versions_seq.fa.set_flow_style()
        entry["versions"] = versions_seq
        ignore_list.append(entry)
    return ignore_list


def _apply_ignore_list(pip_entry: Any, desired_ignores: dict[str, str]) -> None:
    if not desired_ignores:
        if "ignore" in pip_entry:
            del pip_entry["ignore"]
        return

    ignore_list = _build_ignore_list(desired_ignores)
    if "ignore" in pip_entry:
        del pip_entry["ignore"]
    keys = list(pip_entry.keys())
    insert_pos = keys.index("cooldown") if "cooldown" in keys else len(keys)
    pip_entry.insert(insert_pos, "ignore", ignore_list)


def update_dependabot_ignores(
    path: Path,
    pinned_packages: dict[str, str],
) -> tuple[int, int]:
    """Sync the ignore list under the pip ecosystem in dependabot.yml.

    :param path: Path to dependabot.yml.
    :type path: Path
    :param pinned_packages: Dict mapping PyPI package name to pinned version.
    :type pinned_packages: dict[str, str]
    :returns: Tuple of (added_count, removed_count).
    :rtype: tuple[int, int]
    """
    if not path.exists():
        logger.debug("dependabot.yml not found, skipping ignore sync")
        return 0, 0

    yml = _create_yaml(wide=True)
    data = _read_yaml_file(path, yml)

    pip_entry = _find_pip_ecosystem(data)
    if pip_entry is None:
        logger.debug("No pip ecosystem found in %s", path)
        return 0, 0

    current_ignores = _extract_current_ignores(pip_entry)
    desired_ignores: dict[str, str] = {
        name: f"> {version}" for name, version in sorted(pinned_packages.items())
    }

    if current_ignores == desired_ignores:
        return 0, 0

    added = set(desired_ignores) - set(current_ignores)
    removed = set(current_ignores) - set(desired_ignores)

    _apply_ignore_list(pip_entry, desired_ignores)
    _write_yaml_file(path, yml, data)

    logger.info(
        "Updated dependabot ignores in %s: +%d -%d",
        path,
        len(added),
        len(removed),
    )
    return len(added), len(removed)


def _sort_types_entries(mypy_list: list) -> None:  # type: ignore[type-arg]
    """Sort types-* entries alphabetically, preserving non-types entries in place."""
    types_indices: list[int] = []
    types_entries: list[str] = []
    for i, entry in enumerate(mypy_list):
        if str(entry).lower().startswith("types-"):
            types_indices.append(i)
            types_entries.append(str(entry))

    types_entries.sort(key=str.lower)
    for idx, entry in zip(types_indices, types_entries, strict=True):
        mypy_list[idx] = entry


def _apply_removes_and_updates(
    mypy_list: list[Any],
    remove_normalized: set[str],
    update_map: dict[str, str],
) -> int:
    """Remove and update entries in the type-stubs dependency list (reverse iteration).

    :returns: Number of entries changed.
    """
    change_count = 0
    i = len(mypy_list) - 1
    while i >= 0:
        entry = str(mypy_list[i])
        norm = _normalize_dep_name(entry.lower())
        if norm in remove_normalized:
            del mypy_list[i]
            change_count += 1
            logger.debug("  Removed %s from type-stubs group", entry)
        elif norm in update_map:
            prefix = entry.split("==", maxsplit=1)[0] if "==" in entry else entry
            mypy_list[i] = f"{prefix}=={update_map[norm]}"
            change_count += 1
            logger.debug("  Updated %s in type-stubs group", norm)
        i -= 1
    return change_count


def apply_types_sync(
    path: Path,
    to_add: list[tuple[str, str]],
    to_remove: list[str],
    to_update: list[tuple[str, str, str]],
) -> int:
    """Apply types-* stub changes to the type-stubs group in pyproject.toml.

    :param path: Path to pyproject.toml.
    :type path: Path
    :param to_add: (package_name, version) pairs to add.
    :type to_add: list[tuple[str, str]]
    :param to_remove: Package names to remove.
    :type to_remove: list[str]
    :param to_update: (package_name, old_version, new_version) tuples.
    :type to_update: list[tuple[str, str, str]]
    :returns: Total number of changes applied.
    :rtype: int
    :raises WriteError: If the file cannot be read or written.
    """
    if not to_add and not to_remove and not to_update:
        return 0

    toml_file, doc = _read_toml(path)

    mypy_list = _get_toml_key(
        doc,
        ["project", "optional-dependencies", "type-stubs"],
        path,
    )

    remove_normalized = {_normalize_dep_name(n) for n in to_remove}
    update_map = {_normalize_dep_name(name): new_ver for name, _, new_ver in to_update}

    change_count = _apply_removes_and_updates(mypy_list, remove_normalized, update_map)

    insert_before = len(mypy_list)
    for i, entry in enumerate(mypy_list):
        entry_str = str(entry).strip()
        is_self_ref = entry_str.startswith(f"{PROJECT_NAME}[")
        is_bare_non_types = not entry_str.lower().startswith("types-") and "==" not in entry_str
        if is_self_ref or is_bare_non_types:
            insert_before = i
            break

    for name, version in sorted(to_add, reverse=True):
        mypy_list.insert(insert_before, f"{name}=={version}")
        logger.debug("  Added %s==%s to type-stubs group", name, version)
    change_count += len(to_add)

    _sort_types_entries(mypy_list)

    _write_toml(path, toml_file, doc)

    logger.info("Applied %d types-* changes in %s", change_count, path)
    return change_count
