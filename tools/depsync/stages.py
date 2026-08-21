# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Sync stage runners for depsync."""

from __future__ import annotations

import logging
import shutil
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from shared.uv_resolve import UvResolveError, resolve_project_versions

from depsync.caps import detect_capped_pins
from depsync.config import UV_LOCK_TIMEOUT
from depsync.engine import resolve_pinned_packages
from depsync.exceptions import LockfileError, ResolveError, VerifyError
from depsync.excludenewer import (
    apply_results,
    collect_versions,
    converge_exclude_newer,
    current_entries,
    parse_policy,
    prefetch_upload_times,
    update_pyproject_exclude_newer,
)
from depsync.models import (
    ConvergenceResult,
    OverridePolicy,
    OverrideResult,
    PyProjectDependency,
    RunConfig,
    TypesSyncResult,
    UpdateTarget,
)
from depsync.overrides import (
    converge_overrides,
    current_overrides,
    parse_overrides,
    run_verify,
    update_pyproject_overrides,
)
from depsync.parsers import parse_uv_lock
from depsync.typestubs import sync_types
from depsync.ui import (
    console,
    create_backups,
    display_exclude_newer_results,
    display_override_results,
    display_results,
    display_types_results,
    display_types_skipped,
    preview_label,
    report_dependabot_changes,
    report_retirable,
    restore_files,
    show_diffs,
    snapshot_files,
)
from depsync.writers import (
    apply_types_sync,
    update_dependabot_ignores,
    update_genprecommit_additional_deps,
    update_precommit_config,
    update_pyproject,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from packaging.version import Version
    from shared.pip_config import PipConfig

logger = logging.getLogger(__name__)


def write_all_convergence(
    config: RunConfig,
    results: list[Any],
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


def commit_convergence(
    config: RunConfig,
    results: list[Any],
    target_files: list[Path],
) -> None:
    """Apply convergence results to disk for real.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        results (list): Convergence results to apply.
        target_files (list[Path]): Files the results may touch.

    """
    snapshots = snapshot_files(target_files)
    if config.backup:
        create_backups(snapshots)

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
        show_diffs(snapshots, target_files)


def preview_convergence(
    config: RunConfig,
    results: list[Any],
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
    snapshots = snapshot_files(target_files)
    try:
        write_all_convergence(config, results)
        show_diffs(snapshots, target_files)
    finally:
        restore_files(snapshots)


def apply_convergence(
    config: RunConfig,
    results: list[Any],
) -> bool:
    """Apply or preview convergence results.

    Returns:
        bool: True if actual file changes are needed.

    """
    display_results(results)

    actual_changes = [r for r in results if r.old_version != r.new_version or r.needs_regeneration]
    if not actual_changes:
        return False

    target_files = [
        config.pyproject_path,
        config.genprecommit_config_path,
        config.precommit_config_path,
    ]

    if not (config.dry_run or config.check):
        commit_convergence(config, results, target_files)
    elif config.diff:
        preview_convergence(config, results, target_files)

    if config.check:
        console.print("\n[bold yellow]Check mode — files would be modified.[/]")
    elif config.dry_run:
        console.print("\n[bold yellow]Dry run — no convergence files modified.[/]")

    return True


def check_lockfile_staleness(config: RunConfig) -> str | None:
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


def ensure_uv_lock(config: RunConfig) -> None:
    """Regenerate uv.lock if it is missing or stale relative to pyproject.toml.

    Raises:
        LockfileError: If uv is not found, the subprocess fails, times out, or the lockfile is still absent
            after generation.

    """
    reason = check_lockfile_staleness(config)

    if reason is None:
        return

    if shutil.which("uv") is None:
        msg = f"uv.lock is {reason} but 'uv' is not on PATH; install uv or run 'uv lock' manually"
        raise LockfileError(msg)

    console.print(
        f"  [yellow]uv.lock is {reason}; running 'uv lock' to regenerate...[/]",
    )

    try:
        subprocess.run(
            ["uv", "lock"],  # noqa: S607
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


def commit_types_sync(
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
    snapshots = snapshot_files(target_files)
    if config.backup:
        create_backups(snapshots)

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
        show_diffs(snapshots, target_files)


def preview_types_sync(
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
    snapshots = snapshot_files(target_files)
    try:
        apply_types_sync(
            config.pyproject_path,
            types_result.added,
            types_result.removed,
            types_result.updated,
        )
        show_diffs(snapshots, target_files)
    finally:
        restore_files(snapshots)


def run_types_sync(
    config: RunConfig,
    index_url: str | None,
    min_python: Version | None,
    extra_index_urls: tuple[str, ...],
    pip_config: PipConfig,
) -> TypesSyncResult | None:
    """Run the types-* stub synchronization phase.

    Returns:
        TypesSyncResult | None: The stub changes needed (or applied), or None when the stubs are already in
            sync. The result rather than a flag, because the stage writes pins that the exclude-newer stage
            then has to account for.

    """
    console.print("\n[bold]Syncing types-* stub packages...[/]")

    ensure_uv_lock(config)

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

    display_types_skipped(types_result)

    if not types_result.added and not types_result.removed and not types_result.updated:
        console.print("\n[bold green]All types-* stubs are already in sync.[/]")
        return None

    display_types_results(types_result)

    target_files = [config.pyproject_path]

    if not (config.dry_run or config.check):
        commit_types_sync(config, types_result, target_files)
    elif config.diff:
        preview_types_sync(config, types_result, target_files)
    elif config.check:
        console.print("\n[bold yellow]Check mode — types-* stubs would be modified.[/]")
    else:
        console.print("\n[bold yellow]Dry run — no types-* changes applied.[/]")

    return types_result


def convergence_targets(results: Sequence[ConvergenceResult]) -> dict[str, str]:
    """Extract the pins convergence is about to write to pyproject.toml.

    Targets are read from the results rather than from disk so ``--check`` and ``--dry-run`` judge the end
    state, which is the whole point of those modes.

    Args:
        results (Sequence[ConvergenceResult]): Convergence results.

    Returns:
        dict[str, str]: Package name to target version.

    """
    return {
        r.package: r.new_version
        for r in results
        if r.target in {UpdateTarget.PYPROJECT, UpdateTarget.BOTH} and r.groups
    }


def types_targets(types_result: TypesSyncResult) -> dict[str, str]:
    """Extract the stub pins the types-* sync is about to write.

    Args:
        types_result (TypesSyncResult): Stub additions, removals, and updates.

    Returns:
        dict[str, str]: Package name to target version.

    """
    targets = dict(types_result.added)
    targets.update({name: new_version for name, _, new_version in types_result.updated})

    return targets


def commit_exclude_newer(
    config: RunConfig,
    desired: dict[str, str],
    target_files: list[Path],
) -> None:
    """Write the converged relaxation table to disk.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        desired (dict[str, str]): The complete table to write.
        target_files (list[Path]): Files the change may touch.

    """
    snapshots = snapshot_files(target_files)
    if config.backup:
        create_backups(snapshots)

    written = update_pyproject_exclude_newer(config.pyproject_path, desired)
    console.print(f"  Wrote [cyan]{written}[/] exclude-newer-package entries in pyproject.toml")

    if config.diff:
        show_diffs(snapshots, target_files)


def preview_exclude_newer(
    config: RunConfig,
    desired: dict[str, str],
    target_files: list[Path],
) -> None:
    """Show the diff the relaxation sync would produce, then roll the file back.

    Args:
        config (RunConfig): Run configuration containing file paths.
        desired (dict[str, str]): The complete table that would be written.
        target_files (list[Path]): Files the change may touch.

    """
    snapshots = snapshot_files(target_files)
    try:
        update_pyproject_exclude_newer(config.pyproject_path, desired)
        show_diffs(snapshots, target_files)
    finally:
        restore_files(snapshots)


def apply_exclude_newer(config: RunConfig, desired: dict[str, str]) -> None:
    """Apply or preview the converged relaxation table.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        desired (dict[str, str]): The complete table to write.

    """
    target_files = [config.pyproject_path]

    if not (config.dry_run or config.check):
        commit_exclude_newer(config, desired, target_files)
    elif config.diff:
        preview_exclude_newer(config, desired, target_files)
    else:
        console.print(
            f"\n[bold yellow]{preview_label(config)} — exclude-newer-package entries would be modified.[/]",
        )


def run_exclude_newer(
    config: RunConfig,
    targets: dict[str, str],
    cache: dict[tuple[str, str], datetime | None],
    index_url: str | None,
    extra_index_urls: tuple[str, ...],
    pip_config: PipConfig,
) -> bool:
    """Keep ``[tool.uv] exclude-newer-package`` in step with the pins this run writes.

    Runs once after convergence and again after the types-* sync, because both write pins and either can land
    a release younger than the cutoff — after which every ``uv lock`` in the project fails, including the one
    the next stage is about to run.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        targets (dict[str, str]): Package name to the version this pass is about to pin.
        cache (dict[tuple[str, str], datetime | None]): Publication times already looked up this run.
        index_url (str | None): Optional PEP 503 index URL.
        extra_index_urls (tuple[str, ...]): Additional PEP 503 index URLs.
        pip_config (PipConfig): Pip configuration for SSL settings.

    Returns:
        bool: True if file changes are needed (or were applied).

    """
    if not config.sync_exclude_newer:
        return False

    policy = parse_policy(config.pyproject_path)
    if policy is None:
        return False

    console.print("\n[bold]Syncing uv exclude-newer relaxations...[/]")

    entries = current_entries(config.pyproject_path)
    versions = collect_versions(config.pyproject_path, config.uv_lock_path, entries, targets)
    uploads = prefetch_upload_times(
        versions,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
        cache=cache,
    )

    results = converge_exclude_newer(policy, entries, versions, uploads, datetime.now(tz=UTC))
    if not results:
        console.print(f"  [green]Cutoff [cyan]{policy.raw}[/] needs no per-package relaxation.[/]")
        return False

    display_exclude_newer_results(results)
    apply_exclude_newer(config, apply_results(entries, results))

    return True


def run_dependabot_write(
    config: RunConfig,
    pinned_packages: dict[str, str],
) -> bool:
    """Write dependabot ignore entries.

    Args:
        config (RunConfig): Run configuration.
        pinned_packages (dict[str, str]): Pinned packages mapping.

    Returns:
        bool: True if dependabot config was modified, False otherwise.

    """
    target_files = [config.dependabot_path]
    snapshots = snapshot_files(target_files)
    if config.backup:
        create_backups(snapshots)

    added, removed = update_dependabot_ignores(config.dependabot_path, pinned_packages)
    if not (added or removed):
        return False

    report_dependabot_changes(added, removed)
    if config.diff:
        show_diffs(snapshots, target_files)

    return True


def run_dependabot_preview(
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
    snapshots = snapshot_files(target_files)

    try:
        added, removed = update_dependabot_ignores(config.dependabot_path, pinned_packages)
        if config.diff:
            show_diffs(snapshots, target_files)
    finally:
        restore_files(snapshots)

    if not (added or removed):
        return False

    if not config.diff:
        label = "Check mode" if config.check else "Dry run"
        console.print(f"  [bold yellow]{label} — dependabot.yml would be modified.[/]")

    return True


def find_capped_pins(
    pyproject_deps: dict[str, list[PyProjectDependency]],
    resolved: dict[str, str],
    index_url: str | None,
    extra_index_urls: Sequence[str],
    pip_config: PipConfig,
    min_python: Version | None,
) -> dict[str, str]:
    """Identify managed pins that another dependency holds below the newest release.

    Args:
        pyproject_deps (dict[str, list[PyProjectDependency]]): Parsed pyproject dependencies by group.
        resolved (dict[str, str]): Package name to the version uv resolved. Empty when uv resolution is off,
            in which case there is nothing to compare against and the check is skipped.
        index_url (str | None): Optional PEP 503 index URL.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs.
        pip_config (PipConfig): Pip configuration for SSL settings.
        min_python (Version | None): Minimum Python version to filter candidate releases against.

    Returns:
        dict[str, str]: Package name to resolved version for capped pins, empty when none are capped.

    """
    if not resolved:
        return {}

    names = {dep.name for deps in pyproject_deps.values() for dep in deps}
    capped = detect_capped_pins(
        names,
        resolved,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
        min_python=min_python,
    )
    if capped:
        listed = ", ".join(f"{name}=={version}" for name, version in sorted(capped.items()))
        console.print(f"  Capped by another dependency: [magenta]{listed}[/]")

    return capped


def run_dependabot_sync(
    config: RunConfig,
    pinned_revs: dict[str, str],
    override_pins: dict[str, str] | None = None,
    capped_pins: dict[str, str] | None = None,
) -> bool:
    """Sync dependabot.yml ignore list with pinned revs, override pins, and capped pins.

    An overridden package needs the same protection as a rev-pinned one, and arguably more: syncdeps owns its
    version, and for a security override an unattended Dependabot bump past the declared ceiling is the very
    breakage the ceiling exists to prevent. Overrides win over a rev pin for the same package, since the
    override is what actually governs what gets installed.

    Capped pins are those another dependency holds below the newest release, so a Dependabot proposal for that
    release could never be installed. Suppressing them stops a weekly PR that is unmergeable by construction.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        pinned_revs (dict[str, str]): Repo URL to pinned rev from .genprecommitconfig.yaml.
        override_pins (dict[str, str] | None): Package name to target version for transitive overrides.
        capped_pins (dict[str, str] | None): Package name to resolved version for pins another
            dependency holds below the newest release.

    Returns:
        bool: True if changes are needed (or were applied), False otherwise.

    """
    pinned_packages = resolve_pinned_packages(pinned_revs) | (capped_pins or {}) | (override_pins or {})

    if not config.dependabot_path.exists():
        logger.debug("dependabot.yml not found at %s, skipping", config.dependabot_path)
        return False

    console.print("\n[bold]Syncing dependabot ignore list...[/]")

    if not (config.dry_run or config.check):
        changed = run_dependabot_write(config, pinned_packages)
    else:
        changed = run_dependabot_preview(config, pinned_packages)

    if not changed:
        console.print("  [green]Dependabot ignore list already in sync.[/]")

    return changed


def resolve_override_versions(
    config: RunConfig,
    policies: list[OverridePolicy],
    pins: dict[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    """Resolve each override twice: within its bounds, and with overrides stripped.

    The bounded resolution supplies the target pin. The stripped resolution answers whether the override is
    still needed, which is the only way to tell that upstream has loosened its requirement.

    Args:
        config (RunConfig): Run configuration containing file paths.
        policies (list[OverridePolicy]): Declared override policies.
        pins (dict[str, str]): Packages held fixed by pre-commit pins.

    Returns:
        tuple[dict[str, str], dict[str, str]]: Versions resolved with bounds applied, and without overrides.

    Raises:
        ResolveError: If either resolution fails.

    """
    specifiers = [policy.specifier() for policy in policies]
    console.print(
        f"\n[bold]Resolving {len(specifiers)} transitive override(s) within declared bounds...[/]",
    )

    try:
        bounded = resolve_project_versions(config.pyproject_path, pins=pins, overrides=specifiers)
        unpinned = resolve_project_versions(config.pyproject_path, pins=pins, overrides=[])
    except UvResolveError as exc:
        raise ResolveError(str(exc)) from exc

    return bounded, unpinned


def commit_overrides(
    config: RunConfig,
    policies: list[OverridePolicy],
    results: list[OverrideResult],
) -> None:
    """Write override pins, relock, and verify — rolling back if verification fails.

    A failed verify must not leave the new pin behind, or the next run would treat a broken state as the
    starting point.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        policies (list[OverridePolicy]): Declared policies, for their verify commands.
        results (list[OverrideResult]): Override results to write.

    Raises:
        LockfileError: If relocking uv.lock fails after writing overrides.
        VerifyError: If a verify command fails once the new pin is in place.

    """
    target_files = [config.pyproject_path, config.uv_lock_path]
    snapshots = snapshot_files(target_files)
    if config.backup:
        create_backups(snapshots)

    console.print("\n[bold]Applying override pins...[/]")
    written = update_pyproject_overrides(config.pyproject_path, results)
    console.print(f"  Updated [cyan]{written}[/] override pin(s) in pyproject.toml")

    changed = {r.package for r in results if r.old_version != r.new_version}
    try:
        ensure_uv_lock(config)
        for policy in (p for p in policies if p.package in changed):
            run_verify(policy)
    except (LockfileError, VerifyError):
        restore_files(snapshots)
        console.print("  [bold red]Verification failed — override pins rolled back.[/]")
        raise

    if config.diff:
        show_diffs(snapshots, target_files)


def apply_overrides_stage(
    config: RunConfig,
    policies: list[OverridePolicy],
    results: list[OverrideResult],
) -> bool:
    """Apply or preview override pins.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        policies (list[OverridePolicy]): Declared policies.
        results (list[OverrideResult]): Converged override results.

    Returns:
        bool: True if actual file changes are needed.

    """
    display_override_results(results)
    report_retirable(results)

    if not [r for r in results if r.old_version != r.new_version]:
        console.print("  [green]All override pins are already current.[/]")
        return False

    if config.dry_run or config.check:
        console.print(
            "\n[bold yellow]Override pins would be updated — verify commands not run "
            "(they need the new pin on disk).[/]",
        )
        return True

    commit_overrides(config, policies, results)
    return True


def run_overrides(config: RunConfig, pins: dict[str, str]) -> tuple[bool, dict[str, str]]:
    """Converge transitive-dependency overrides declared in .syncdepsoverrides.yaml.

    Skipped entirely when no policies are declared, so a project without overrides pays nothing for this
    stage.

    Args:
        config (RunConfig): Run configuration containing file paths and flags.
        pins (dict[str, str]): Packages held fixed by pre-commit pins.

    Returns:
        tuple[bool, dict[str, str]]: Whether file changes are needed, and the package name to *target* version
            for every converged override. Targets rather than what is currently on disk, so the dependabot
            ignore list reflects the end state even under --check, where nothing is written.

    """
    policies = parse_overrides(config.overrides_path)
    if not policies:
        return False, {}

    if config.no_uv_resolve:
        console.print(
            "\n[bold yellow]uv resolution disabled[/] — transitive overrides left untouched",
        )
        return False, {}

    bounded, unpinned = resolve_override_versions(config, policies, pins)
    results = converge_overrides(
        policies,
        current_overrides(config.pyproject_path),
        bounded,
        unpinned,
    )
    if not results:
        return False, {}

    target_pins = {result.package: result.new_version for result in results}
    return apply_overrides_stage(config, policies, results), target_pins
