# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI interface for bidirectional dependency convergence."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click
from shared import PROJECT_NAME
from shared.http_client import get_session
from shared.log_config import configure_logging
from shared.pip_config import load_pip_config
from shared.uv_resolve import UvResolveError, resolve_project_versions

from depsync.config import (
    DEPENDABOT_CONFIG,
    GENPRECOMMIT_CONFIG,
    OVERRIDES_CONFIG,
    PRECOMMIT_CONFIG,
    PYPROJECT_TOML,
    UV_LOCK,
)
from depsync.engine import converge, resolve_pinned_packages
from depsync.exceptions import ResolveError, SyncDepsError
from depsync.models import (
    RunConfig,
)
from depsync.parsers import (
    parse_genprecommit_pinned_revs,
    parse_index_url,
    parse_precommit_config,
    parse_pyproject,
    parse_requires_python,
)
from depsync.stages import (
    apply_convergence,
    convergence_targets,
    find_capped_pins,
    run_dependabot_sync,
    run_exclude_newer,
    run_overrides,
    run_types_sync,
    types_targets,
)
from depsync.ui import (
    console,
    log_parsed_config,
)

if TYPE_CHECKING:
    from datetime import datetime


def _resolve_versions(
    config: RunConfig,
    pinned_revs: dict[str, str],
) -> dict[str, str]:
    """Ask uv which versions of the project's dependencies can co-exist.

    Revs pinned in ``.genprecommitconfig.yaml`` are passed through as hard constraints so the resolution bends
    around them instead of proposing versions that contradict the pre-commit config.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        pinned_revs (dict[str, str]): Repo URL → pinned rev from .genprecommitconfig.yaml.

    Returns:
        dict[str, str]: Package name → resolved version, or an empty dict when uv resolution is disabled.

    Raises:
        ResolveError: If uv is unavailable or finds no valid resolution.

    """
    if config.no_uv_resolve:
        console.print(
            "\n[bold yellow]uv resolution disabled[/] — using latest index release per package",
        )
        return {}

    console.print("\n[bold]Resolving co-installable versions with uv...[/]")

    pins = resolve_pinned_packages(pinned_revs)
    try:
        resolved = resolve_project_versions(config.pyproject_path, pins=pins)
    except UvResolveError as exc:
        raise ResolveError(str(exc)) from exc

    console.print(f"  uv resolved [cyan]{len(resolved)}[/] packages")
    if pins:
        pins_str = ", ".join(f"{name}=={ver}" for name, ver in sorted(pins.items()))
        console.print(f"  Held fixed by pre-commit pins: [magenta]{pins_str}[/]")

    return resolved


def _run(config: RunConfig) -> None:
    """Execute the convergence pipeline.

    Raises:
        SystemExit: If check mode is active and changes are needed.

    """
    console.print("[bold]Parsing configuration files...[/]")

    pip_config = load_pip_config()
    get_session(pip_config)

    pyproject_deps = parse_pyproject(config.pyproject_path)
    precommit_repos = parse_precommit_config(config.precommit_config_path)
    pinned_revs = parse_genprecommit_pinned_revs(config.genprecommit_config_path)

    index_url = parse_index_url(config.pyproject_path)
    min_python = parse_requires_python(config.pyproject_path)

    if index_url is None and pip_config.index_url:
        index_url = pip_config.index_url

    extra_index_urls = pip_config.extra_index_urls

    log_parsed_config(
        len(pyproject_deps),
        len(precommit_repos),
        len(pinned_revs),
        index_url,
        extra_index_urls,
        pip_config,
        min_python,
    )

    resolved = _resolve_versions(config, pinned_revs)

    console.print("\n[bold]Running convergence analysis...[/]")
    results = converge(
        pyproject_deps,
        precommit_repos,
        pinned_revs,
        resolved=resolved,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
        min_python=min_python,
    )

    has_changes = False
    upload_cache: dict[tuple[str, str], datetime | None] = {}

    if results:
        has_changes = apply_convergence(config, results)
    else:
        console.print("\n[bold green]All dependencies are already converged.[/]")

    if run_exclude_newer(
        config,
        convergence_targets(results),
        upload_cache,
        index_url,
        extra_index_urls,
        pip_config,
    ):
        has_changes = True

    types_result = (
        run_types_sync(config, index_url, min_python, extra_index_urls, pip_config)
        if config.sync_types
        else None
    )
    if types_result is not None:
        has_changes = True
        # A stub pin is chosen from the index, not from the resolution, so it too can land ahead of the
        # cutoff — and the next stage locks.
        run_exclude_newer(
            config,
            types_targets(types_result),
            upload_cache,
            index_url,
            extra_index_urls,
            pip_config,
        )

    overrides_changed, override_pins = run_overrides(config, resolve_pinned_packages(pinned_revs))
    if overrides_changed:
        has_changes = True

    capped_pins = find_capped_pins(
        pyproject_deps,
        resolved,
        index_url,
        extra_index_urls,
        pip_config,
        min_python,
    )

    dependabot_changed = run_dependabot_sync(config, pinned_revs, override_pins, capped_pins)
    if dependabot_changed:
        has_changes = True

    if config.check and has_changes:
        raise SystemExit(1)

    console.print("\n[bold green]Done.[/]")


@click.command("syncdeps")
@click.option(
    "--pyproject",
    type=click.Path(exists=True),
    default=PYPROJECT_TOML,
    show_default=True,
    help="Path to pyproject.toml.",
)
@click.option(
    "--precommit-config",
    type=click.Path(exists=True),
    default=PRECOMMIT_CONFIG,
    show_default=True,
    help="Path to .pre-commit-config.yaml.",
)
@click.option(
    "--genprecommit-config",
    type=click.Path(exists=True),
    default=GENPRECOMMIT_CONFIG,
    show_default=True,
    help="Path to .genprecommitconfig.yaml.",
)
@click.option(
    "--dependabot",
    type=click.Path(),
    default=DEPENDABOT_CONFIG,
    show_default=True,
    help="Path to dependabot.yml (ignore list synced with pinned revs and override pins).",
)
@click.option(
    "--overrides",
    type=click.Path(),
    default=OVERRIDES_CONFIG,
    show_default=True,
    help="Path to the transitive-dependency override policy file.",
)
@click.option(
    "--uv-lock",
    type=click.Path(),
    default=UV_LOCK,
    show_default=True,
    help="Path to uv.lock (used with --sync-types).",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    show_default=True,
    help="Logging verbosity level.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without modifying files.",
)
@click.option(
    "--sync-types",
    is_flag=True,
    default=False,
    help="Sync types-* stub packages in the type-stubs group against the dependency tree.",
)
@click.option(
    "--sync-exclude-newer/--no-sync-exclude-newer",
    "sync_exclude_newer",
    default=True,
    show_default=True,
    help="Keep [tool.uv] exclude-newer-package in step with the pins written.",
)
@click.option(
    "--no-uv-resolve",
    is_flag=True,
    default=False,
    help="Skip uv resolution and pin each package to its latest index release (may not lock).",
)
@click.option(
    "--backup",
    is_flag=True,
    default=False,
    help="Create backup before modifying any files.",
)
@click.option(
    "--check",
    "check_mode",
    is_flag=True,
    default=False,
    help="Check if any files would be modified (exit 1 if changes would be made).",
)
@click.option(
    "--diff",
    "show_diff",
    is_flag=True,
    default=False,
    help="Show unified diff of changes.",
)
@click.version_option(package_name=PROJECT_NAME)
def app(
    pyproject: str,
    precommit_config: str,
    genprecommit_config: str,
    dependabot: str,
    overrides: str,
    uv_lock: str,
    log_level: str,
    *,
    dry_run: bool,
    sync_types: bool,
    sync_exclude_newer: bool,
    no_uv_resolve: bool,
    backup: bool,
    check_mode: bool,
    show_diff: bool,
) -> None:
    """Bidirectional dependency convergence between pyproject.toml and pre-commit.

    Synchronizes dependency versions across pyproject.toml, .genprecommitconfig.yaml, and .pre-commit-
    config.yaml by querying PyPI and git tags for the latest stable versions.

    Args:
        pyproject (str): Path to pyproject.toml.
        precommit_config (str): Path to .pre-commit-config.yaml.
        genprecommit_config (str): Path to .genprecommitconfig.yaml.
        dependabot (str): Path to dependabot.yml.
        overrides (str): Path to overrides policy YAML.
        uv_lock (str): Path to uv.lock.
        log_level (str): Logging level string.
        dry_run (bool): If True, report changes without writing files.
        sync_types (bool): If True, synchronize types-* stub packages.
        sync_exclude_newer (bool): If True, keep [tool.uv] exclude-newer-package in step with the pins.
        no_uv_resolve (bool): If True, skip uv resolution and use the latest index release per package.
        backup (bool): If True, create backup files before writing.
        check_mode (bool): If True, exit 1 when changes would be made.
        show_diff (bool): If True, show unified diff of changes.

    Raises:
        SystemExit: If a SyncDepsError occurs during execution.

    """
    configure_logging(log_level, console)

    run_config = RunConfig(
        pyproject_path=Path(pyproject),
        precommit_config_path=Path(precommit_config),
        genprecommit_config_path=Path(genprecommit_config),
        dependabot_path=Path(dependabot),
        overrides_path=Path(overrides),
        uv_lock_path=Path(uv_lock),
        log_level=log_level,
        dry_run=dry_run,
        sync_types=sync_types,
        sync_exclude_newer=sync_exclude_newer,
        no_uv_resolve=no_uv_resolve,
        backup=backup,
        check=check_mode,
        diff=show_diff,
    )

    try:
        _run(run_config)
    except SyncDepsError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise SystemExit(exc.exit_code) from exc
