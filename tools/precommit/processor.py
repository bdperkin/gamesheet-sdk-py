# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Hook processing: filtering, blacklisting, overrides, and appends."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from precommit.config import HOOK_TARGETING_KEYS
from precommit.exceptions import ProcessingError

if TYPE_CHECKING:
    from precommit.models import HookConfig, RepoConfig

logger = logging.getLogger(__name__)


def _discover_meta_hooks() -> list[str]:
    """Discover available meta hook IDs from the installed pre-commit package.

    Returns:
        list[str]: List of meta hook IDs in definition order.

    Raises:
        ProcessingError: If pre-commit is not installed.
    """
    try:
        from pre_commit.clientlib import (
            _meta,
        )
    except ImportError as exc:
        msg = "pre-commit package not installed — cannot discover meta hooks"
        raise ProcessingError(msg) from exc

    hook_ids = [hook_id for hook_id, _ in _meta]
    logger.debug("Discovered meta hooks: %s", hook_ids)
    return hook_ids


def _apply_modifications(hook: dict[str, Any], cfg: HookConfig) -> None:
    """Apply overrides, appends, and prepends to a hook dict in-place.

    Args:
        hook (dict[str, Any]): Hook dict to modify.
        cfg (HookConfig): Hook configuration with overrides, appends, and prepends.
    """
    hook.update(cfg.overrides)

    for key, values in cfg.appends.items():
        if key not in hook:
            hook[key] = []

        if not isinstance(hook[key], list):
            logger.warning(
                "Cannot append to non-list field '%s' on hook '%s'",
                key,
                hook["id"],
            )
            continue

        hook[key].extend(values)

    for key, values in cfg.prepends.items():
        if key not in hook:
            hook[key] = values.copy()
            continue

        if not isinstance(hook[key], list):
            logger.warning(
                "Cannot prepend to non-list field '%s' on hook '%s'",
                key,
                hook["id"],
            )
            continue

        for i, val in enumerate(values):
            hook[key].insert(i, val)


def process_meta_hooks(
    repo_config: RepoConfig,
    blacklisted_hooks: list[str],
) -> list[dict[str, Any]]:
    """Build hook entries for a meta repository.

    When hooks are explicitly listed in the config, only those are included (with overrides applied).  When no
    hooks are listed, all available meta hooks are discovered from the installed pre-commit package and
    included unless blacklisted.

    Args:
        repo_config (RepoConfig): Repository configuration with hook definitions.
        blacklisted_hooks (list[str]): Hook IDs to exclude.

    Returns:
        list[dict[str, Any]]: List of hook dicts ready for YAML output.
    """
    overrides_map = {h.id: h for h in repo_config.hooks} if repo_config.hooks else {}

    available = _discover_meta_hooks()
    explicit_ids = {h.id for h in repo_config.hooks}

    hooks: list[dict[str, Any]] = []
    for hook_id in available:
        if hook_id in blacklisted_hooks:
            logger.debug("Skipping meta hook %s: blacklisted", hook_id)
            continue

        hook: dict[str, Any] = {"id": hook_id}

        override_cfg = overrides_map.get(hook_id)
        if override_cfg is not None:
            _apply_modifications(hook, override_cfg)

        hooks.append(hook)

    for hook_id in explicit_ids - set(available):
        logger.warning("Unknown meta hook '%s' — including as-is", hook_id)
        hook = {"id": hook_id}
        override_cfg = overrides_map[hook_id]
        _apply_modifications(hook, override_cfg)
        hooks.append(hook)

    return hooks


def _process_single_hook(
    hook: dict[str, Any],
    repo_url: str,
    override_cfg: HookConfig | None,
    allowed_languages: list[str],
    blacklisted_hooks: list[str],
) -> dict[str, Any] | None:
    """Process a single hook definition.

    Args:
        hook (dict[str, Any]): Raw hook definition dict.
        repo_url (str): Repository URL for error messages.
        override_cfg (HookConfig | None): Optional override/append configuration for this hook.
        allowed_languages (list[str]): Allowed hook languages.
        blacklisted_hooks (list[str]): Blacklisted hook IDs.

    Returns:
        dict[str, Any] | None: Processed hook dict or None if the hook should be excluded.

    Raises:
        ProcessingError: If required fields are missing.
    """
    hook_id = hook.get("id")
    if not hook_id:
        msg = f"Hook missing 'id' field in {repo_url}"
        raise ProcessingError(msg)

    language = hook.get("language")
    if not language:
        msg = f"Hook '{hook_id}' missing 'language' field in {repo_url}"
        raise ProcessingError(msg)

    if language not in allowed_languages:
        logger.debug("Skipping %s: language '%s' not allowed", hook_id, language)
        return None

    if hook_id in blacklisted_hooks:
        logger.debug("Skipping %s: blacklisted", hook_id)
        return None

    if not any(key in hook for key in HOOK_TARGETING_KEYS):
        logger.debug(
            "Hook %s has no targeting metadata; including with pre-commit defaults",
            hook_id,
        )

    result = hook.copy()

    if override_cfg is not None:
        _apply_modifications(result, override_cfg)

    return result


def process_remote_hooks(
    fetched_hooks: list[dict[str, Any]],
    repo_config: RepoConfig,
    allowed_languages: list[str],
    blacklisted_hooks: list[str],
) -> list[dict[str, Any]]:
    """Filter and configure hooks fetched from a remote repository.

    Args:
        fetched_hooks (list[dict[str, Any]]): Raw hook definitions from the remote .pre-commit-hooks.yaml.
        repo_config (RepoConfig): Repository configuration with overrides and appends.
        allowed_languages (list[str]): List of allowed hook languages.
        blacklisted_hooks (list[str]): List of hook IDs to exclude.

    Returns:
        list[dict[str, Any]]: List of processed hook dicts ready for YAML output.
    """
    overrides_map = {h.id: h for h in repo_config.hooks}
    processed: list[dict[str, Any]] = []

    for hook in fetched_hooks:
        result = _process_single_hook(
            hook=hook,
            repo_url=repo_config.repo,
            override_cfg=overrides_map.get(hook.get("id", "")),
            allowed_languages=allowed_languages,
            blacklisted_hooks=blacklisted_hooks,
        )
        if result is not None:
            processed.append(result)

    return processed


def get_hook_comment(repo_config: RepoConfig, hook_id: str) -> str | None:
    """Get the comment string for a specific hook if configured.

    Args:
        repo_config (RepoConfig): Repository configuration.
        hook_id (str): Hook identifier.

    Returns:
        str | None: Comment string or None.
    """
    for hook_cfg in repo_config.hooks:
        if hook_cfg.id == hook_id and hook_cfg.comment:
            return hook_cfg.comment

    return None
