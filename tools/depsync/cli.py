# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI interface for bidirectional dependency convergence."""

from __future__ import annotations

import difflib
import logging
from pathlib import Path
import shutil
import subprocess  # noqa: S404 # nosec B404

from depsync.config import (
    DEPENDABOT_CONFIG,
    GENPRECOMMIT_CONFIG,
    PRECOMMIT_CONFIG,
    PYPROJECT_TOML,
    UV_LOCK,
    UV_LOCK_TIMEOUT,
)
from depsync.engine import converge, resolve_pinned_packages
from depsync.exceptions import LockfileError, ResolveError, SyncDepsError
from depsync.models import ConvergenceResult, RunConfig, TypesSyncResult, UpdateTarget
from depsync.parsers import (
    parse_genprecommit_pinned_revs,
    parse_index_url,
    parse_precommit_config,
    parse_pyproject,
    parse_requires_python,
    parse_uv_lock,
)
from depsync.typestubs import sync_types
from depsync.writers import (
    apply_types_sync,
    update_dependabot_ignores,
    update_genprecommit_additional_deps,
    update_precommit_config,
    update_pyproject,
)
from packaging.version import Version
from rich.console import Console
from rich.table import Table
import rich_click as click
from shared import PROJECT_NAME
from shared.http_client import get_session
from shared.log_config import configure_logging
from shared.pip_config import PipConfig, load_pip_config
from shared.uv_resolve import UvResolveError, resolve_project_versions

console = Console()
logger = logging.getLogger(__name__)


def _snapshot_files(paths: list[Path]) -> dict[Path, bytes]:
    """Read and store the content of each file that exists.

    Returns:
        dict[Path, bytes]: Mapping of path to original bytes for files that exist.
    """
    snapshots: dict[Path, bytes] = {}
    for path in paths:
        if path.exists():
            snapshots[path] = path.read_bytes()

    return snapshots


def _create_backups(snapshots: dict[Path, bytes]) -> None:
    """Create .bak copies of snapshotted files."""
    for path in snapshots:
        backup_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup_path)
        console.print(f"  Created backup: [dim]{backup_path}[/]")


def _restore_files(snapshots: dict[Path, bytes]) -> None:
    """Restore original file contents from snapshots."""
    for path, content in snapshots.items():
        path.write_bytes(content)


def _print_colored_diff(diff_lines: list[str]) -> None:
    """Print diff lines with colorized output based on line prefix.

    Args:
        diff_lines (list[str]): Lines from a unified diff.
    """
    for line in diff_lines:
        text = line.rstrip("\n")
        if line.startswith(("---", "+++")):
            console.print(f"[bold]{text}[/]")
        elif line.startswith("@@"):
            console.print(f"[cyan]{text}[/]")
        elif line.startswith("+"):
            console.print(f"[green]{text}[/]")
        elif line.startswith("-"):
            console.print(f"[red]{text}[/]")
        else:
            console.print(f"[dim]{text}[/]")


def _show_diffs(snapshots: dict[Path, bytes], paths: list[Path]) -> None:
    """Show colorized unified diffs between snapshots and current file contents."""
    for path in paths:
        if path not in snapshots:
            continue

        original = snapshots[path].decode("utf-8", errors="replace").splitlines(keepends=True)
        current = path.read_text(encoding="utf-8").splitlines(keepends=True)
        diff = list(
            difflib.unified_diff(
                original,
                current,
                fromfile=str(path),
                tofile=str(path),
                n=3,
            ),
        )
        if not diff:
            continue

        _print_colored_diff(diff)


def _print_result_warnings(results: list[ConvergenceResult]) -> None:
    """Print summary warnings for pinned and stale results."""
    pinned_results = [r for r in results if r.is_pinned]
    if pinned_results:
        noun = "dependency is" if len(pinned_results) == 1 else "dependencies are"
        console.print(
            f"\n[bold yellow]Warning:[/] {len(pinned_results)} "
            f"{noun} "
            f"pinned in .genprecommitconfig.yaml — rev values will not be modified",
        )

    stale_results = [r for r in results if r.needs_regeneration]
    if stale_results:
        noun = "repo has a" if len(stale_results) == 1 else "repos have"
        console.print(
            f"[bold yellow]Warning:[/] {len(stale_results)} {noun} stale rev in .pre-commit-config.yaml",
        )


_SCOPE_LABELS: dict[UpdateTarget, str] = {
    UpdateTarget.PYPROJECT: "pyproject",
    UpdateTarget.GENPRECOMMIT: "pre-commit",
    UpdateTarget.BOTH: "both",
}


def _result_status(r: ConvergenceResult) -> str:
    """Compute the rich-markup status string for a convergence result.

    Returns:
        str: Rich-markup status label.
    """
    if r.is_pinned and r.old_version == r.new_version:
        status = "[magenta]pinned (up to date)[/]"
    elif r.is_pinned:
        status = "[magenta]pinned[/]"
    elif r.old_version != r.new_version:
        status = "[green]update[/]"
    else:
        status = ""

    if r.needs_regeneration:
        if status:
            status += " [yellow](stale rev)[/]"
        else:
            status = "[yellow]stale rev[/]"

    return status


def _display_results(results: list[ConvergenceResult]) -> None:
    """Display convergence results in a rich table."""
    _print_result_warnings(results)

    table = Table(title="Dependency Convergence Results", show_lines=True)
    table.add_column("Package", style="cyan")
    table.add_column("Current", style="red")
    table.add_column("Target", style="green")
    table.add_column("Scope", style="yellow")
    table.add_column("Status")
    table.add_column("Groups / Hooks")

    for r in results:
        scope = _SCOPE_LABELS[r.target]

        detail_parts = []
        if r.groups:
            groups_str = ", ".join(r.groups)
            detail_parts.append(f"groups: {groups_str}")

        if r.hook_ids:
            hooks_str = ", ".join(r.hook_ids)
            detail_parts.append(f"hooks: {hooks_str}")

        detail = "; ".join(detail_parts) if detail_parts else "-"

        label = f"{r.package} (additional_dep)" if r.is_additional_dep else r.package

        table.add_row(
            label,
            r.old_version or "-",
            r.new_version,
            scope,
            _result_status(r),
            detail,
        )

    console.print(table)


def _write_all_convergence(
    config: RunConfig,
    results: list,  # type: ignore[type-arg]
) -> int:
    """Write convergence results to all three managed files.

    Args:
        config (RunConfig): Run configuration containing file paths.
        results (list): Convergence results to apply.

    Returns:
        int: Total number of entries written across all files.
    """
    pyproject_count = update_pyproject(config.pyproject_path, results)
    genprecommit_ad_count = update_genprecommit_additional_deps(
        config.genprecommit_config_path,
        results,
    )
    precommit_count = update_precommit_config(config.precommit_config_path, results)

    return pyproject_count + genprecommit_ad_count + precommit_count


def _commit_convergence(
    config: RunConfig,
    results: list,  # type: ignore[type-arg]
    target_files: list[Path],
) -> None:
    """Apply convergence results to disk for real.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        results (list): Convergence results to apply.
        target_files (list[Path]): Files the results may touch.
    """
    snapshots = _snapshot_files(target_files)
    if config.backup:
        _create_backups(snapshots)

    console.print("\n[bold]Applying updates...[/]")
    pyproject_count = update_pyproject(config.pyproject_path, results)
    genprecommit_ad_count = update_genprecommit_additional_deps(
        config.genprecommit_config_path,
        results,
    )
    precommit_count = update_precommit_config(config.precommit_config_path, results)

    console.print(f"  Updated [cyan]{pyproject_count}[/] entries in pyproject.toml")
    console.print(
        f"  Updated [cyan]{genprecommit_ad_count}[/] additional_deps in .genprecommitconfig.yaml",
    )
    console.print(
        f"  Updated [cyan]{precommit_count}[/] entries in .pre-commit-config.yaml",
    )

    if config.diff:
        _show_diffs(snapshots, target_files)


def _preview_convergence(
    config: RunConfig,
    results: list,  # type: ignore[type-arg]
    target_files: list[Path],
) -> None:
    """Show the diff convergence would produce, then roll the files back.

    Previewing a diff means really writing the files and undoing them, so the restore has to survive an
    exception or a SIGPIPE from a truncated pager — otherwise a preview silently becomes a commit.

    Args:
        config (RunConfig): Run configuration containing file paths.
        results (list): Convergence results to preview.
        target_files (list[Path]): Files the results may touch.
    """
    snapshots = _snapshot_files(target_files)
    try:
        _write_all_convergence(config, results)
        _show_diffs(snapshots, target_files)
    finally:
        _restore_files(snapshots)


def _apply_convergence(
    config: RunConfig,
    results: list,  # type: ignore[type-arg]
) -> bool:
    """Apply or preview convergence results.

    Returns:
        bool: True if actual file changes are needed.
    """
    _display_results(results)

    actual_changes = [r for r in results if r.old_version != r.new_version or r.needs_regeneration]
    if not actual_changes:
        return False

    target_files = [
        config.pyproject_path,
        config.genprecommit_config_path,
        config.precommit_config_path,
    ]

    if not (config.dry_run or config.check):
        _commit_convergence(config, results, target_files)
    elif config.diff:
        _preview_convergence(config, results, target_files)

    if config.check:
        console.print("\n[bold yellow]Check mode — files would be modified.[/]")
    elif config.dry_run:
        console.print("\n[bold yellow]Dry run — no convergence files modified.[/]")

    return True


def _check_lockfile_staleness(config: RunConfig) -> str | None:
    """Check whether the lockfile is missing or stale relative to pyproject.toml.

    Args:
        config (RunConfig): Run configuration containing file paths.

    Returns:
        str | None: A reason string if the lockfile needs regeneration, or None if it is up to date.

    Raises:
        LockfileError: If stat calls fail unexpectedly.
    """
    if not config.uv_lock_path.exists():
        return "missing"

    try:
        lock_mtime = config.uv_lock_path.stat().st_mtime
        pyproject_mtime = config.pyproject_path.stat().st_mtime
    except OSError as exc:
        msg = f"Cannot stat lockfile or pyproject.toml: {exc}"
        raise LockfileError(msg) from exc

    if lock_mtime < pyproject_mtime:
        return "stale (older than pyproject.toml)"

    return None


def _ensure_uv_lock(config: RunConfig) -> None:
    """Regenerate uv.lock if it is missing or stale relative to pyproject.toml.

    Raises:
        LockfileError: If uv is not found, the subprocess fails, times out, or the lockfile is still absent
            after generation.
    """
    reason = _check_lockfile_staleness(config)

    if reason is None:
        return

    if shutil.which("uv") is None:
        msg = f"uv.lock is {reason} but 'uv' is not on PATH; install uv or run 'uv lock' manually"
        raise LockfileError(msg)

    console.print(
        f"  [yellow]uv.lock is {reason}; running 'uv lock' to regenerate...[/]",
    )

    try:
        subprocess.run(  # noqa: S603, S607 # nosec B603, B607
            ["uv", "lock"],
            capture_output=True,
            text=True,
            check=True,
            timeout=UV_LOCK_TIMEOUT,
            cwd=config.pyproject_path.parent,
        )
    except subprocess.CalledProcessError as exc:
        msg = f"'uv lock' failed (exit {exc.returncode}): {exc.stderr.strip()}"
        raise LockfileError(msg) from exc
    except subprocess.TimeoutExpired as exc:
        msg = f"'uv lock' timed out after {UV_LOCK_TIMEOUT}s"
        raise LockfileError(msg) from exc
    except OSError as exc:
        msg = f"Failed to run 'uv lock': {exc}"
        raise LockfileError(msg) from exc

    if not config.uv_lock_path.exists():
        msg = (
            f"'uv lock' completed but {config.uv_lock_path} was not created; "
            f"check that pyproject.toml is in {config.pyproject_path.parent}"
        )
        raise LockfileError(msg)

    console.print("  [green]uv.lock regenerated successfully.[/]")


def _display_types_results(types_result: TypesSyncResult) -> None:
    """Display types-* sync results in a rich table."""
    table = Table(title="Types Stub Sync Results", show_lines=True)
    table.add_column("Package", style="cyan")
    table.add_column("Action", style="yellow")
    table.add_column("Version", style="green")

    for name, version in types_result.added:
        table.add_row(name, "[green]add[/]", version)

    for name in types_result.removed:
        table.add_row(name, "[red]remove[/]", "-")

    for name, old_ver, new_ver in types_result.updated:
        table.add_row(name, "[blue]update[/]", f"{old_ver} → {new_ver}")

    console.print(table)


def _commit_types_sync(
    config: RunConfig,
    types_result: TypesSyncResult,
    target_files: list[Path],
) -> None:
    """Apply types-* stub changes to disk for real.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        types_result (TypesSyncResult): Stub additions, removals, and updates to apply.
        target_files (list[Path]): Files the changes may touch.
    """
    snapshots = _snapshot_files(target_files)
    if config.backup:
        _create_backups(snapshots)

    change_count = apply_types_sync(
        config.pyproject_path,
        types_result.added,
        types_result.removed,
        types_result.updated,
    )
    console.print(
        f"  Applied [cyan]{change_count}[/] types-* changes in pyproject.toml",
    )

    if config.diff:
        _show_diffs(snapshots, target_files)


def _preview_types_sync(
    config: RunConfig,
    types_result: TypesSyncResult,
    target_files: list[Path],
) -> None:
    """Show the diff the types-* sync would produce, then roll the file back.

    Args:
        config (RunConfig): Run configuration containing file paths.
        types_result (TypesSyncResult): Stub additions, removals, and updates to preview.
        target_files (list[Path]): Files the changes may touch.
    """
    snapshots = _snapshot_files(target_files)
    try:
        apply_types_sync(
            config.pyproject_path,
            types_result.added,
            types_result.removed,
            types_result.updated,
        )
        _show_diffs(snapshots, target_files)
    finally:
        _restore_files(snapshots)


def _run_types_sync(
    config: RunConfig,
    index_url: str | None,
    min_python: Version | None,
    extra_index_urls: tuple[str, ...],
    pip_config: PipConfig,
) -> bool:
    """Run the types-* stub synchronization phase.

    Returns:
        bool: True if changes are needed (or were applied), False otherwise.
    """
    console.print("\n[bold]Syncing types-* stub packages...[/]")

    _ensure_uv_lock(config)

    base_packages, all_packages = parse_uv_lock(config.uv_lock_path)
    console.print(f"  Found [cyan]{len(all_packages)}[/] packages in uv.lock")

    types_result = sync_types(
        base_packages,
        all_packages,
        config.pyproject_path,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
        min_python=min_python,
    )

    if not types_result.added and not types_result.removed and not types_result.updated:
        console.print("\n[bold green]All types-* stubs are already in sync.[/]")
        return False

    _display_types_results(types_result)

    target_files = [config.pyproject_path]

    if not (config.dry_run or config.check):
        _commit_types_sync(config, types_result, target_files)
    elif config.diff:
        _preview_types_sync(config, types_result, target_files)
    elif config.check:
        console.print("\n[bold yellow]Check mode — types-* stubs would be modified.[/]")
    else:
        console.print("\n[bold yellow]Dry run — no types-* changes applied.[/]")

    return True


def _log_parsed_config(
    dep_count: int,
    repo_count: int,
    pin_count: int,
    index_url: str | None,
    extra_index_urls: tuple[str, ...],
    pip_config: PipConfig,
    min_python: Version | None,
) -> None:
    """Print a summary of parsed configuration to the console."""
    console.print(
        f"  Found [cyan]{dep_count}[/] packages in pyproject.toml, "
        f"[cyan]{repo_count}[/] repos in pre-commit config, "
        f"[cyan]{pin_count}[/] pinned revs",
    )
    if index_url:
        console.print(f"  Using package index: [cyan]{index_url}[/]")

    if extra_index_urls:
        console.print(f"  Extra index URLs: [cyan]{len(extra_index_urls)}[/]")

    if pip_config.trusted_hosts:
        hosts_str = ", ".join(pip_config.trusted_hosts)
        console.print(f"  Trusted hosts: [cyan]{hosts_str}[/]")

    if min_python:
        console.print(f"  Python compatibility floor: [cyan]{min_python}[/]")


def _report_dependabot_changes(added: int, removed: int) -> None:
    if added:
        noun = "entry" if added == 1 else "entries"
        console.print(f"  Added [cyan]{added}[/] ignore {noun} in .github/dependabot.yml")

    if removed:
        noun = "entry" if removed == 1 else "entries"
        console.print(
            f"  Removed [cyan]{removed}[/] stale ignore {noun} from .github/dependabot.yml",
        )


def _run_dependabot_write(
    config: RunConfig,
    pinned_packages: dict[str, str],
) -> bool:
    target_files = [config.dependabot_path]
    snapshots = _snapshot_files(target_files)
    if config.backup:
        _create_backups(snapshots)

    added, removed = update_dependabot_ignores(config.dependabot_path, pinned_packages)
    if not (added or removed):
        return False

    _report_dependabot_changes(added, removed)
    if config.diff:
        _show_diffs(snapshots, target_files)

    return True


def _run_dependabot_preview(
    config: RunConfig,
    pinned_packages: dict[str, str],
) -> bool:
    """Report what the dependabot ignore sync would change, leaving the file untouched.

    There is no pure "would change" query for the ignore list, so the write is performed and then rolled back
    unconditionally — a preview must never outlive the process that ran it.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        pinned_packages (dict[str, str]): PyPI package name to pinned version.

    Returns:
        bool: True if the file would be modified, False otherwise.
    """
    target_files = [config.dependabot_path]
    snapshots = _snapshot_files(target_files)
    added, removed = 0, 0

    try:
        added, removed = update_dependabot_ignores(config.dependabot_path, pinned_packages)
        if config.diff:
            _show_diffs(snapshots, target_files)
    finally:
        _restore_files(snapshots)

    if not (added or removed):
        return False

    if not config.diff:
        label = "Check mode" if config.check else "Dry run"
        console.print(f"  [bold yellow]{label} — dependabot.yml would be modified.[/]")

    return True


def _run_dependabot_sync(
    config: RunConfig,
    pinned_revs: dict[str, str],
) -> bool:
    """Sync dependabot.yml ignore list with pinned revs.

    Returns:
        bool: True if changes are needed (or were applied), False otherwise.
    """
    pinned_packages = resolve_pinned_packages(pinned_revs)

    if not config.dependabot_path.exists():
        logger.debug("dependabot.yml not found at %s, skipping", config.dependabot_path)
        return False

    console.print("\n[bold]Syncing dependabot ignore list...[/]")

    if not (config.dry_run or config.check):
        changed = _run_dependabot_write(config, pinned_packages)
    else:
        changed = _run_dependabot_preview(config, pinned_packages)

    if not changed:
        console.print("  [green]Dependabot ignore list already in sync.[/]")

    return changed


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

    _log_parsed_config(
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

    if results:
        has_changes = _apply_convergence(config, results)
    else:
        console.print("\n[bold green]All dependencies are already converged.[/]")

    if config.sync_types:
        types_changed = _run_types_sync(
            config,
            index_url,
            min_python,
            extra_index_urls,
            pip_config,
        )
        if types_changed:
            has_changes = True

    dependabot_changed = _run_dependabot_sync(config, pinned_revs)
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
    help="Path to dependabot.yml (ignore list synced with pinned revs).",
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
def app(  # pylint: disable=redefined-outer-name
    pyproject: str,
    precommit_config: str,
    genprecommit_config: str,
    dependabot: str,
    uv_lock: str,
    log_level: str,
    *,
    dry_run: bool,
    sync_types: bool,
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
        uv_lock (str): Path to uv.lock.
        log_level (str): Logging level string.
        dry_run (bool): If True, report changes without writing files.
        sync_types (bool): If True, synchronize types-* stub packages.
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
        uv_lock_path=Path(uv_lock),
        log_level=log_level,
        dry_run=dry_run,
        sync_types=sync_types,
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
