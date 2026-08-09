# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""YAML output rendering for .pre-commit-config.yaml."""

from __future__ import annotations

import io
import logging
from pathlib import Path
import re
from typing import Any

from precommit.config import (
    CI_PROPERTY_DESCRIPTIONS,
    CI_SECTION_COMMENT,
    GLOBALS_PROPERTY_DESCRIPTIONS,
    GLOBALS_SECTION_COMMENT,
    HEADER_COMMENT,
    REPOS_SECTION_COMMENT,
)
from precommit.exceptions import RenderError
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from shared.yaml_format import format_yaml

logger = logging.getLogger(__name__)

_SUBSEP = "----------------------------------------------------------------------------\n"


def _build_hook_map(hook: dict[str, Any]) -> CommentedMap:
    """Convert a plain hook dict to a CommentedMap with ``id`` first.

    Args:
        hook (dict[str, Any]): Hook configuration dict.

    Returns:
        CommentedMap: CommentedMap with ordered keys.
    """
    hook_map = CommentedMap()
    if "id" in hook:
        hook_map["id"] = hook["id"]

    for key, value in hook.items():
        if key == "id":
            continue

        if isinstance(value, list):
            hook_map[key] = CommentedSeq(value)
        elif isinstance(value, dict):
            hook_map[key] = CommentedMap(value)
        else:
            hook_map[key] = value

    return hook_map


def _build_ci_map(ci: dict[str, Any]) -> CommentedMap:
    """Convert the ci config dict to a CommentedMap with property comments.

    Args:
        ci (dict[str, Any]): Raw ci configuration dict.

    Returns:
        CommentedMap: CommentedMap with description comments on documented properties.
    """
    ci_map = CommentedMap()
    for key, value in ci.items():
        if isinstance(value, list):
            ci_map[key] = CommentedSeq(value)
        elif isinstance(value, dict):
            ci_map[key] = CommentedMap(value)
        else:
            ci_map[key] = value

        if key in CI_PROPERTY_DESCRIPTIONS:
            ci_map.yaml_set_comment_before_after_key(
                key,
                before=CI_PROPERTY_DESCRIPTIONS[key],
                indent=2,
            )

    return ci_map


def _build_repo_map(repo: dict[str, Any]) -> CommentedMap:
    """Convert a plain repo dict to a CommentedMap with proper structure.

    Args:
        repo (dict[str, Any]): Repository dict with repo, rev, and hooks keys.

    Returns:
        CommentedMap: CommentedMap with ordered keys.
    """
    repo_map = CommentedMap()
    repo_map["repo"] = repo["repo"]

    if "rev" in repo:
        repo_map["rev"] = repo["rev"]

    if "hooks" in repo:
        hooks_seq = CommentedSeq()
        for hook in repo["hooks"]:
            hooks_seq.append(_build_hook_map(hook))

        repo_map["hooks"] = hooks_seq

    return repo_map


def _add_global_comment(doc: CommentedMap, key: str) -> None:
    """Add a description comment before a top-level global key if one is defined.

    Args:
        doc (CommentedMap): The document CommentedMap.
        key (str): The key to annotate.
    """
    if key in GLOBALS_PROPERTY_DESCRIPTIONS:
        doc.yaml_set_comment_before_after_key(
            key,
            before=GLOBALS_PROPERTY_DESCRIPTIONS[key],
        )


def _add_globals_section(
    doc: CommentedMap,
    *,
    default_language_version: dict[str, str],
    default_stages: list[str],
    fail_fast: bool,
    files: str | None,
    exclude: str | None,
    minimum_pre_commit_version: str | None,
) -> None:
    """Populate the globals section of the document with banner and property comments.

    Args:
        doc (CommentedMap): The document CommentedMap to populate.
        default_language_version (dict[str, str]): Default language version mapping.
        default_stages (list[str]): Default stages list.
        fail_fast (bool): Whether to fail fast.
        files (str | None): Optional global files regex pattern.
        exclude (str | None): Optional global exclude regex pattern.
        minimum_pre_commit_version (str | None): Optional minimum pre-commit version.
    """
    if minimum_pre_commit_version is not None:
        doc["minimum_pre_commit_version"] = minimum_pre_commit_version
        doc.yaml_set_comment_before_after_key(
            "minimum_pre_commit_version",
            before=GLOBALS_SECTION_COMMENT
            + "\n"
            + GLOBALS_PROPERTY_DESCRIPTIONS["minimum_pre_commit_version"],
        )
        globals_banner_placed = True
    else:
        globals_banner_placed = False

    lang_ver = CommentedMap(default_language_version)
    doc["default_language_version"] = lang_ver
    if not globals_banner_placed:
        doc.yaml_set_comment_before_after_key(
            "default_language_version",
            before=GLOBALS_SECTION_COMMENT + "\n" + GLOBALS_PROPERTY_DESCRIPTIONS["default_language_version"],
        )
    else:
        _add_global_comment(doc, "default_language_version")

    doc["default_stages"] = CommentedSeq(default_stages)
    _add_global_comment(doc, "default_stages")

    doc["fail_fast"] = fail_fast
    _add_global_comment(doc, "fail_fast")

    if files is not None:
        doc["files"] = files
        _add_global_comment(doc, "files")

    if exclude is not None:
        doc["exclude"] = exclude
        _add_global_comment(doc, "exclude")


def _apply_hook_comments(
    repo_map: CommentedMap,
    repo_idx: int,
    hook_comments: dict[tuple[int, int], str],
) -> None:
    """Attach per-hook comments to hooks inside a repo entry.

    Args:
        repo_map (CommentedMap): The CommentedMap for a single repo.
        repo_idx (int): Index of this repo in the repos sequence.
        hook_comments (dict[tuple[int, int], str]): Mapping of (repo_index, hook_index) to comment text.
    """
    hooks_list = repo_map.get("hooks")
    if not isinstance(hooks_list, CommentedSeq):
        return

    for hook_idx in range(len(hooks_list)):
        comment_key = (repo_idx, hook_idx)
        if comment_key in hook_comments:
            hooks_list.yaml_set_comment_before_after_key(
                hook_idx,
                before=hook_comments[comment_key],
            )


def _build_repos_seq(
    repos: list[dict[str, Any]],
    hook_comments: dict[tuple[int, int], str] | None,
    category_comments: dict[int, str] | None,
) -> CommentedSeq:
    """Build the repos CommentedSeq with hook and category comments.

    Args:
        repos (list[dict[str, Any]]): List of repo dicts.
        hook_comments (dict[tuple[int, int], str] | None): Optional hook-level comments.
        category_comments (dict[int, str] | None): Optional category description comments.

    Returns:
        CommentedSeq: CommentedSeq ready for insertion into the document.
    """
    repos_seq = CommentedSeq()
    for repo_idx, repo in enumerate(repos):
        repo_map = _build_repo_map(repo)

        if hook_comments:
            _apply_hook_comments(repo_map, repo_idx, hook_comments)

        repos_seq.append(repo_map)

        if category_comments and repo_idx in category_comments:
            repos_seq.yaml_set_comment_before_after_key(
                repo_idx,
                before="\n" + _SUBSEP + category_comments[repo_idx] + "\n" + _SUBSEP,
                indent=2,
            )

    return repos_seq


def _build_document(
    *,
    default_language_version: dict[str, str],
    default_stages: list[str],
    fail_fast: bool,
    repos: list[dict[str, Any]],
    ci: dict[str, Any] | None = None,
    files: str | None = None,
    exclude: str | None = None,
    minimum_pre_commit_version: str | None = None,
    hook_comments: dict[tuple[int, int], str] | None = None,
    category_comments: dict[int, str] | None = None,
) -> CommentedMap:
    """Build the ruamel.yaml document structure with comments.

    Args:
        default_language_version (dict[str, str]): Default language version mapping.
        default_stages (list[str]): Default stages list.
        fail_fast (bool): Whether to fail fast.
        repos (list[dict[str, Any]]): List of repo dicts.
        ci (dict[str, Any] | None): Optional pre-commit.ci service configuration.
        files (str | None): Optional global files regex pattern.
        exclude (str | None): Optional global exclude regex pattern.
        minimum_pre_commit_version (str | None): Optional minimum pre-commit version.
        hook_comments (dict[tuple[int, int], str] | None): Optional hook-level comments.
        category_comments (dict[int, str] | None): Optional mapping of repo_index to category description.

    Returns:
        CommentedMap: CommentedMap ready for YAML serialization.
    """
    doc = CommentedMap()
    doc.yaml_set_start_comment(HEADER_COMMENT)

    if ci is not None:
        doc["ci"] = _build_ci_map(ci)
        doc.yaml_set_comment_before_after_key("ci", before=CI_SECTION_COMMENT)

    _add_globals_section(
        doc,
        default_language_version=default_language_version,
        default_stages=default_stages,
        fail_fast=fail_fast,
        files=files,
        exclude=exclude,
        minimum_pre_commit_version=minimum_pre_commit_version,
    )

    doc["repos"] = _build_repos_seq(repos, hook_comments, category_comments)
    doc.yaml_set_comment_before_after_key("repos", before=REPOS_SECTION_COMMENT)

    return doc


def _add_repo_spacing(text: str) -> str:
    """Insert a blank line before each ``- repo:`` entry that lacks one.

    Returns:
        str: Text with blank lines inserted before repo entries.
    """
    lines = text.splitlines()
    result: list[str] = []
    for i, line in enumerate(lines):
        if (
            line.lstrip().startswith("- repo:")
            and i > 0
            and lines[i - 1].strip()
            and not lines[i - 1].strip().startswith("repos:")
        ):
            result.append("")

        result.append(line)

    return "\n".join(result)


def _single_to_double_quotes(text: str) -> str:
    """Replace single-quoted YAML scalar values with double-quoted equivalents.

    Strings containing backslashes are left single-quoted because YAML double-quoted strings interpret
    backslash escape sequences.

    Returns:
        str: Text with single quotes replaced by double quotes.
    """

    def _replace_match(m: re.Match[str]) -> str:
        inner = m.group(1)
        if "\\" in inner:
            return m.group(0)

        return '"' + inner + '"'

    def _replace_on_line(line: str) -> str:
        if line.lstrip().startswith("#"):
            return line

        return re.sub(r"'([^']*)'", _replace_match, line)

    return "\n".join(_replace_on_line(line) for line in text.splitlines())


def _write_yaml(output_path: Path, doc: CommentedMap) -> None:
    """Write a ruamel.yaml document to a file.

    Args:
        output_path (Path): Path to write to.
        doc (CommentedMap): Document to serialize.
    """
    yml = YAML()
    yml.indent(mapping=2, sequence=4, offset=2)
    yml.default_flow_style = False
    yml.explicit_start = True

    buf = io.StringIO()
    yml.dump(doc, buf)
    text = _add_repo_spacing(buf.getvalue())
    text = _single_to_double_quotes(text)
    cleaned = format_yaml("\n".join(line.rstrip() for line in text.splitlines()) + "\n")
    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(cleaned)


def render_config(
    output_path: Path,
    *,
    default_language_version: dict[str, str],
    default_stages: list[str],
    fail_fast: bool,
    repos: list[dict[str, Any]],
    ci: dict[str, Any] | None = None,
    files: str | None = None,
    exclude: str | None = None,
    minimum_pre_commit_version: str | None = None,
    hook_comments: dict[tuple[int, int], str] | None = None,
    category_comments: dict[int, str] | None = None,
) -> None:
    """Render the complete .pre-commit-config.yaml file.

    Args:
        output_path (Path): Path to write the output file.
        default_language_version (dict[str, str]): Default language version mapping.
        default_stages (list[str]): Default stages list.
        fail_fast (bool): Whether to fail fast on first hook failure.
        repos (list[dict[str, Any]]): List of repository dicts with hooks.
        ci (dict[str, Any] | None): Optional pre-commit.ci service configuration.
        files (str | None): Optional global files regex pattern.
        exclude (str | None): Optional global exclude regex pattern.
        minimum_pre_commit_version (str | None): Optional minimum pre- commit version.
        hook_comments (dict[tuple[int, int], str] | None): Optional mapping of (repo_index, hook_index) to
            comment.
        category_comments (dict[int, str] | None): Optional mapping of repo_index to category description.

    Raises:
        RenderError: If the file cannot be written.
    """
    doc = _build_document(
        default_language_version=default_language_version,
        default_stages=default_stages,
        fail_fast=fail_fast,
        repos=repos,
        ci=ci,
        files=files,
        exclude=exclude,
        minimum_pre_commit_version=minimum_pre_commit_version,
        hook_comments=hook_comments,
        category_comments=category_comments,
    )

    try:
        _write_yaml(output_path, doc)
    except RenderError:
        raise
    except Exception as exc:
        msg = f"Failed to render {output_path}: {exc}"
        raise RenderError(msg) from exc

    logger.debug("Wrote %s", output_path)
