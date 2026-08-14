# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Main pipeline orchestrator for pre-commit configuration generation."""

from __future__ import annotations

import io
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any

from depsync.config import UV_LOCK
from depsync.parsers import parse_index_url, parse_requires_python
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from shared.concurrency import PARALLEL_WORKERS
from shared.http_client import get_session
from shared.pip_config import PipConfig, load_pip_config
from shared.uv_resolve import UvResolveError, versions_from_lock

from precommit.config import (
    DEFAULT_ALLOWED_LANGUAGES,
    DEFAULT_FAIL_FAST,
    DEFAULT_LANGUAGE_VERSION,
    DEFAULT_STAGES,
)
from precommit.discovery import RevisionResult, resolve_revision
from precommit.exceptions import (
    ConfigError,
    DiscoveryError,
    FetchError,
    PreCommitValidationError,
)
from precommit.fetcher import fetch_hooks
from precommit.models import GlobalConfig, RepoConfig, RunConfig, ToolConfig
from precommit.processor import (
    get_hook_comment,
    process_meta_hooks,
    process_remote_hooks,
)
from precommit.renderer import render_config
from precommit.validator import validate_config

if TYPE_CHECKING:
    from packaging.version import Version


logger = logging.getLogger(__name__)


def _reset_working_tree(*, exclude: str | None = None) -> None:
    """Reset any dirty files left by a crashing formatter hook."""
    cmd = ["git", "checkout", "--", "."]
    if exclude:
        cmd.append(f":(exclude){exclude}")

    try:
        subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("git checkout -- . failed; files may still be dirty")


def _fix_resolved_rev_spacing(text: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    i = 0
    while i < len(lines):
        if not lines[i].strip() and i + 1 < len(lines) and lines[i + 1].strip().startswith("resolved_rev:"):
            i += 1
            continue

        result.append(lines[i])
        if lines[i].strip().startswith("resolved_rev:") and i + 1 < len(lines) and lines[i + 1].strip():
            result.append("")

        i += 1

    return "\n".join(result)


def _merge_globals(raw_globals: dict[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "default_language_version": DEFAULT_LANGUAGE_VERSION.copy(),
        "default_stages": DEFAULT_STAGES.copy(),
        "fail_fast": DEFAULT_FAIL_FAST,
        "allowed_languages": DEFAULT_ALLOWED_LANGUAGES.copy(),
    }
    defaults.update(raw_globals)
    return defaults


class PreCommitGenerator:
    """Orchestrates the full generation pipeline.

    Phases:
        1. CLI parsing (handled by cli.py before instantiation)
        2. Load static defaults
        3. Parse and validate configuration file
        4. Build hook configuration (discovery + fetch + process)
        5. Per-repo incremental validation
        6. Final validation

    Args:
            run_config (RunConfig): Runtime configuration for the generation pipeline.

    """

    def __init__(self: PreCommitGenerator, run_config: RunConfig) -> None:
        """Initialize PreCommitGenerator instance.

        Args:
            run_config (RunConfig): Runtime configuration.

        """
        self.run_config = run_config
        self.tool_config: ToolConfig | None = None
        self.repos: list[dict[str, Any]] = []
        self.hook_comments: dict[tuple[int, int], str] = {}
        self.category_comments: dict[int, str] = {}
        self.ci: dict[str, Any] | None = None
        self.index_url: str | None = None
        self.extra_index_urls: tuple[str, ...] = ()
        self.pip_config: PipConfig | None = None
        self.min_python: Version | None = None
        self.resolved: dict[str, str] = {}
        self._repo_cache: dict[str, tuple[RevisionResult, list[dict[str, Any]]]] = {}

    @staticmethod
    def _validate_tool_config(raw: dict[str, Any]) -> ToolConfig:
        """Validate a raw config dict into a ToolConfig model.

        Args:
            raw (dict[str, Any]): Parsed and merged configuration dictionary.

        Returns:
            ToolConfig: Validated ToolConfig instance.

        Raises:
            ConfigError: If the configuration data fails validation.

        """
        try:
            return ToolConfig.model_validate(raw)
        except Exception as exc:
            msg = f"Configuration validation failed: {exc}"
            raise ConfigError(msg) from exc

    def _load_config(self: PreCommitGenerator) -> ToolConfig:
        config_path = self.run_config.config_file
        logger.info("Loading configuration from %s", config_path)

        if not config_path.exists():
            logger.warning(
                "Configuration file not found: %s — using defaults only",
                config_path,
            )
            return ToolConfig.model_validate({"globals": _merge_globals({})})

        try:
            raw = YAML().load(config_path)
        except Exception as exc:
            msg = f"Failed to parse {config_path}: {exc}"
            raise ConfigError(msg) from exc

        if not isinstance(raw, dict):
            msg = f"Expected mapping in {config_path}, got {type(raw).__name__}"
            raise ConfigError(msg)

        raw_globals = raw.get("globals", {})
        merged_globals = _merge_globals(raw_globals)
        raw["globals"] = merged_globals

        return self._validate_tool_config(raw)

    def _resolve_output_path(
        self: PreCommitGenerator,
        globals_cfg: GlobalConfig,
    ) -> Path:
        if self.run_config.output_file is not None:
            return self.run_config.output_file

        return Path(globals_cfg.output_file)

    def _prefetch_repos(self: PreCommitGenerator, tool_config: ToolConfig) -> None:
        remote_configs: list[RepoConfig] = [
            rc for cat in tool_config.categories.values() for rc in cat.repos if rc.repo != "meta"
        ]

        if not remote_configs:
            return

        def _fetch_one(
            rc: RepoConfig,
        ) -> tuple[str, RevisionResult, list[dict[str, Any]]]:
            rev_result = resolve_revision(
                rc.repo,
                rc.rev,
                resolved=self.resolved,
                index_url=self.index_url,
                extra_index_urls=self.extra_index_urls,
                pip_config=self.pip_config,
                min_python=self.min_python,
            )
            hooks = fetch_hooks(rc.repo, rev_result.rev, pip_config=self.pip_config)
            return rc.repo, rev_result, hooks

        logger.info("Prefetching %d remote repos in parallel", len(remote_configs))

        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
            futures = {pool.submit(_fetch_one, rc): rc for rc in remote_configs}
            for future in as_completed(futures):
                rc = futures[future]
                try:
                    repo_url, rev_result, hooks = future.result()
                    self._repo_cache[repo_url] = (rev_result, hooks)
                except (DiscoveryError, FetchError):
                    logger.warning("Failed to prefetch %s; will retry inline", rc.repo)

    def _collect_hook_comments(
        self: PreCommitGenerator,
        repo_idx: int,
        repo_config: RepoConfig,
        repo_entry: dict[str, Any],
    ) -> None:
        for hook_idx, hook in enumerate(repo_entry.get("hooks", [])):
            hook_id = hook.get("id", "")
            comment = get_hook_comment(repo_config, hook_id)
            if comment:
                self.hook_comments[repo_idx, hook_idx] = comment

    def _render_and_validate(
        self: PreCommitGenerator,
        globals_cfg: GlobalConfig,
        output_path: Path,
        *,
        hook_ids: list[str] | None = None,
        print_output: bool,
    ) -> None:
        render_config(
            output_path,
            default_language_version=globals_cfg.default_language_version,
            default_stages=globals_cfg.default_stages,
            fail_fast=globals_cfg.fail_fast,
            repos=self.repos,
            ci=self.ci,
            files=globals_cfg.files,
            exclude=globals_cfg.exclude,
            minimum_pre_commit_version=globals_cfg.minimum_pre_commit_version,
            hook_comments=self.hook_comments or None,
            category_comments=self.category_comments or None,
        )

        if not self.run_config.dry_run:
            validate_config(output_path, hook_ids=hook_ids, print_output=print_output)

    @staticmethod
    def _update_resolved_rev_in_data(
        data: dict[str, Any],
        repo_url: str,
        resolved_rev: str | None,
    ) -> None:
        """Update or clear resolved_rev for *repo_url* inside parsed YAML *data*."""
        for cat in (data.get("categories") or {}).values():
            if not cat:
                continue

            for repo_entry in cat.get("repos", []):
                if repo_entry.get("repo") != repo_url:
                    continue

                if resolved_rev is not None:
                    repo_entry["resolved_rev"] = resolved_rev
                    logger.info("Wrote resolved_rev: %s for %s", resolved_rev, repo_url)
                elif "resolved_rev" in repo_entry:
                    del repo_entry["resolved_rev"]
                    logger.info("Cleared resolved_rev for %s", repo_url)

                break

    def _write_resolved_rev(
        self: PreCommitGenerator,
        repo_url: str,
        resolved_rev: str | None,
    ) -> None:
        """Write or clear resolved_rev in .genprecommitconfig.yaml."""
        config_path = self.run_config.config_file

        yml = YAML()
        yml.preserve_quotes = True
        yml.indent(mapping=2, sequence=4, offset=2)
        yml.default_flow_style = False
        yml.width = 4096

        try:
            with config_path.open(encoding="utf-8") as fh:
                data = yml.load(fh)
        except (OSError, YAMLError):
            logger.warning("Could not read %s to write resolved_rev", config_path)
            return

        if data is None:
            return

        self._update_resolved_rev_in_data(data, repo_url, resolved_rev)

        buf = io.StringIO()
        yml.dump(data, buf)
        cleaned = _fix_resolved_rev_spacing(buf.getvalue())
        cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines()) + "\n"
        with config_path.open("w", encoding="utf-8") as fh:
            fh.write(cleaned)

    def _try_downgrade_candidates(
        self: PreCommitGenerator,
        repo_config: RepoConfig,
        globals_cfg: GlobalConfig,
        output_path: Path,
        rev_result: RevisionResult,
        repo_idx: int,
        hook_ids: list[str],
        max_attempts: int,
    ) -> None:
        """Iterate through older revisions until one passes validation.

        Raises:
            PreCommitValidationError: If all candidates fail validation.

        """
        del hook_ids
        candidates = [c for c in rev_result.candidates if c != rev_result.rev]

        if repo_config.resolved_rev and repo_config.resolved_rev in candidates:
            candidates.remove(repo_config.resolved_rev)
            candidates.insert(0, repo_config.resolved_rev)

        if max_attempts > 0:
            candidates = candidates[:max_attempts]

        for candidate in candidates:
            logger.info(
                "Trying downgrade %s -> %s for %s",
                rev_result.rev,
                candidate,
                repo_config.name,
            )

            try:
                fetched = fetch_hooks(
                    repo_config.repo,
                    candidate,
                    pip_config=self.pip_config,
                )
            except FetchError:
                logger.warning(
                    "Failed to fetch hooks for %s at %s",
                    repo_config.repo,
                    candidate,
                )
                continue

            hooks = process_remote_hooks(
                fetched_hooks=fetched,
                repo_config=repo_config,
                allowed_languages=globals_cfg.allowed_languages,
                blacklisted_hooks=globals_cfg.blacklisted_hooks,
            )

            if not hooks:
                logger.warning(
                    "No hooks passed filtering for %s at %s",
                    repo_config.name,
                    candidate,
                )
                continue

            new_entry: dict[str, Any] = {
                "repo": repo_config.repo,
                "rev": candidate,
                "hooks": hooks,
            }

            self.repos[repo_idx] = new_entry
            self._collect_hook_comments(repo_idx, repo_config, new_entry)

            try:
                new_hook_ids = [h["id"] for h in hooks if "id" in h]
                self._render_and_validate(
                    globals_cfg,
                    output_path,
                    hook_ids=new_hook_ids,
                    print_output=False,
                )
            except PreCommitValidationError as exc:
                logger.warning(
                    "%s also failed at %s: %s",
                    repo_config.name,
                    candidate,
                    exc,
                )
                if self.run_config.reset_on_failure:
                    _reset_working_tree(exclude=str(self.run_config.config_file))

                continue

            logger.info(
                "Downgrade successful: %s -> %s for %s",
                rev_result.rev,
                candidate,
                repo_config.name,
            )
            self._write_resolved_rev(repo_config.repo, candidate)
            return

        msg = (
            f"All downgrade candidates exhausted for {repo_config.name}; "
            f"latest {rev_result.rev} and {len(candidates)} older versions all failed"
        )
        raise PreCommitValidationError(msg)

    def _get_max_downgrade_attempts(self: PreCommitGenerator) -> int:
        if self.run_config.max_downgrade_attempts is not None:
            return self.run_config.max_downgrade_attempts

        if self.tool_config is not None:
            return self.tool_config.global_config.max_downgrade_attempts

        return 3

    def _validate_with_downgrade(
        self: PreCommitGenerator,
        repo_config: RepoConfig,
        globals_cfg: GlobalConfig,
        output_path: Path,
        rev_result: RevisionResult,
        repo_idx: int,
        hook_ids: list[str],
    ) -> None:
        """Validate a repo, attempting older revisions on failure.

        Raises:
            PreCommitValidationError: If validation fails and downgrade is not possible or all candidates are
                exhausted.

        """
        try:
            self._render_and_validate(
                globals_cfg,
                output_path,
                hook_ids=hook_ids,
                print_output=False,
            )
        except PreCommitValidationError as exc:
            max_attempts = self._get_max_downgrade_attempts()
            can_downgrade = repo_config.rev is None and rev_result.candidates and max_attempts
            if not can_downgrade:
                raise

            logger.warning(
                "%s failed validation at %s: %s",
                repo_config.name,
                rev_result.rev,
                exc,
            )
            if self.run_config.reset_on_failure:
                _reset_working_tree(exclude=str(self.run_config.config_file))

            self._try_downgrade_candidates(
                repo_config,
                globals_cfg,
                output_path,
                rev_result,
                repo_idx,
                hook_ids,
                max_attempts,
            )
            return

        if repo_config.rev is None and repo_config.resolved_rev is not None:
            logger.info(
                "Latest %s now passes; clearing resolved_rev %s",
                rev_result.rev,
                repo_config.resolved_rev,
            )
            self._write_resolved_rev(repo_config.repo, None)

    @staticmethod
    def _build_meta_repo(
        repo_config: RepoConfig,
        globals_cfg: GlobalConfig,
    ) -> dict[str, Any]:
        hooks = process_meta_hooks(repo_config, globals_cfg.blacklisted_hooks)
        return {"repo": "meta", "hooks": hooks}

    def _build_remote_repo(
        self: PreCommitGenerator,
        repo_config: RepoConfig,
        globals_cfg: GlobalConfig,
    ) -> tuple[dict[str, Any] | None, RevisionResult]:
        cached = self._repo_cache.get(repo_config.repo)
        if cached:
            rev_result, fetched = cached
        else:
            rev_result = resolve_revision(
                repo_config.repo,
                repo_config.rev,
                resolved=self.resolved,
                index_url=self.index_url,
                extra_index_urls=self.extra_index_urls,
                pip_config=self.pip_config,
                min_python=self.min_python,
            )
            fetched = fetch_hooks(
                repo_config.repo,
                rev_result.rev,
                pip_config=self.pip_config,
            )

        hooks = process_remote_hooks(
            fetched_hooks=fetched,
            repo_config=repo_config,
            allowed_languages=globals_cfg.allowed_languages,
            blacklisted_hooks=globals_cfg.blacklisted_hooks,
        )

        if not hooks:
            logger.warning("No hooks passed filtering for %s", repo_config.name)
            return None, rev_result

        entry = {"repo": repo_config.repo, "rev": rev_result.rev, "hooks": hooks}
        return entry, rev_result

    def _process_single_repo(
        self: PreCommitGenerator,
        repo_config: RepoConfig,
        globals_cfg: GlobalConfig,
        output_path: Path,
    ) -> None:
        repo_entry: dict[str, Any] | None
        if repo_config.repo == "meta":
            repo_entry = self._build_meta_repo(repo_config, globals_cfg)
            if repo_entry is None:
                return

            repo_idx = len(self.repos)
            self._collect_hook_comments(repo_idx, repo_config, repo_entry)
            self.repos.append(repo_entry)
            return

        repo_entry, rev_result = self._build_remote_repo(repo_config, globals_cfg)

        if repo_entry is None:
            return

        repo_idx = len(self.repos)
        self._collect_hook_comments(repo_idx, repo_config, repo_entry)
        self.repos.append(repo_entry)

        if not self.run_config.dry_run and self.run_config.validate_incremental:
            hook_ids = [h["id"] for h in repo_entry.get("hooks", []) if "id" in h]
            logger.debug("Validating %s...", repo_config.name)
            self._validate_with_downgrade(
                repo_config,
                globals_cfg,
                output_path,
                rev_result,
                repo_idx,
                hook_ids,
            )

    def _build_all_repos(
        self: PreCommitGenerator,
        tool_config: ToolConfig,
        globals_cfg: GlobalConfig,
        output_path: Path,
    ) -> None:
        for category_name, cat in tool_config.categories.items():
            logger.debug("Processing category: %s", category_name)
            first_repo_idx = len(self.repos)

            for repo_config in cat.repos:
                logger.info("Processing %s (%s)...", repo_config.name, repo_config.repo)
                self._process_single_repo(repo_config, globals_cfg, output_path)

            if cat.description and len(self.repos) > first_repo_idx:
                self.category_comments[first_repo_idx] = cat.description

    @staticmethod
    def _load_locked_versions(lock_path: Path) -> dict[str, str]:
        """Read the project's locked versions, tolerating a missing or unreadable lockfile.

        The lockfile is an optimization for rev selection, not a prerequisite: without it the generator falls
        back to pure tag and index discovery, so a failure here must not abort generation.

        Args:
            lock_path (Path): Path to uv.lock.

        Returns:
            dict[str, str]: Package name to locked version, empty if unavailable.

        """
        if not lock_path.exists():
            logger.info("%s not found — using tag/index discovery only", lock_path)
            return {}

        try:
            locked = versions_from_lock(lock_path)
        except UvResolveError as exc:
            logger.warning("Could not read %s (%s) — using tag/index discovery only", lock_path, exc)
            return {}

        logger.info("Read %d locked versions from %s", len(locked), lock_path)
        return locked

    def generate(self: PreCommitGenerator) -> None:
        """Execute the full generation pipeline."""
        pip_config = load_pip_config()
        self.pip_config = pip_config
        get_session(pip_config)

        tool_config = self._load_config()
        self.tool_config = tool_config
        self.ci = tool_config.ci
        globals_cfg = tool_config.global_config

        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            self.index_url = parse_index_url(pyproject_path)
            self.min_python = parse_requires_python(pyproject_path)
        else:
            self.index_url = None
            self.min_python = None

        if self.index_url is None and pip_config.index_url:
            self.index_url = pip_config.index_url

        self.extra_index_urls = pip_config.extra_index_urls
        self.resolved = self._load_locked_versions(Path(UV_LOCK))

        output_path = self._resolve_output_path(globals_cfg)

        logger.info("Generating %s", output_path)

        self._prefetch_repos(tool_config)
        self._build_all_repos(tool_config, globals_cfg, output_path)

        logger.info("Final validation...")
        self._render_and_validate(globals_cfg, output_path, print_output=True)

        logger.info("Done. Wrote %s with %d repos.", output_path, len(self.repos))
