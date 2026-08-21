# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""UI and rendering helpers for depsync."""

from __future__ import annotations

import difflib
import shutil
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from depsync.models import (
    ConvergenceResult,
    ExcludeNewerResult,
    OverrideResult,
    RunConfig,
    TypesSyncResult,
    UpdateTarget,
)
from depsync.typedness import PY_TYPED_REASON

if TYPE_CHECKING:
    from pathlib import Path

    from packaging.version import Version
    from shared.pip_config import PipConfig

console = Console()

_SCOPE_LABELS: dict[UpdateTarget, str] = {
    UpdateTarget.PYPROJECT: "pyproject",
    UpdateTarget.GENPRECOMMIT: "pre-commit",
    UpdateTarget.BOTH: "both",
}

_EXCLUDE_NEWER_ACTIONS: dict[str, str] = {
    "add": "[green]add[/]",
    "update": "[blue]update[/]",
    "remove": "[red]remove[/]",
}


def snapshot_files(paths: list[Path]) -> dict[Path, bytes]:
    """Read and store the content of each file that exists.

    Returns:
        dict[Path, bytes]: Mapping of path to original bytes for files that exist.

    """
    snapshots: dict[Path, bytes] = {}
    for path in paths:
        if path.exists():
            snapshots[path] = path.read_bytes()

    return snapshots


def create_backups(snapshots: dict[Path, bytes]) -> None:
    """Create .bak copies of snapshotted files."""
    for path in snapshots:
        backup_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup_path)
        console.print(f"  Created backup: [dim]{backup_path}[/]")


def restore_files(snapshots: dict[Path, bytes]) -> None:
    """Restore original file contents from snapshots."""
    for path, content in snapshots.items():
        path.write_bytes(content)


def print_colored_diff(diff_lines: list[str]) -> None:
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


def show_diffs(snapshots: dict[Path, bytes], paths: list[Path]) -> None:
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

        print_colored_diff(diff)


def print_result_warnings(results: list[ConvergenceResult]) -> None:
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


def result_status(r: ConvergenceResult) -> str:
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


def display_results(results: list[ConvergenceResult]) -> None:
    """Display convergence results in a rich table."""
    print_result_warnings(results)

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
            result_status(r),
            detail,
        )

    console.print(table)


def display_types_results(types_result: TypesSyncResult) -> None:
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


def display_types_skipped(types_result: TypesSyncResult) -> None:
    """Summarize stub candidates a gate rejected, so the narrowing is never silent.

    Counts rather than names: the unimported bucket routinely holds ~200 transitive packages. Every entry is
    logged individually at debug level, which the message points at.
    """
    if not types_result.skipped:
        return

    shadowing = sum(1 for _, reason in types_result.skipped if reason == PY_TYPED_REASON)
    console.print(
        f"  Gated out [yellow]{len(types_result.skipped)}[/] stub candidate(s): "
        f"[dim]{len(types_result.skipped) - shadowing} module not imported, "
        f"{shadowing} ship py.typed — --log-level debug lists them[/]",
    )


def preview_label(config: RunConfig) -> str:
    """Name the non-writing mode currently in effect.

    Returns:
        str: ``Check mode`` or ``Dry run``.

    """
    return "Check mode" if config.check else "Dry run"


def display_exclude_newer_results(results: list[ExcludeNewerResult]) -> None:
    """Render per-package cutoff relaxations as a table.

    Args:
        results (list[ExcludeNewerResult]): Converged changes to display.

    """
    table = Table(title="uv exclude-newer Relaxations", show_lines=False)
    table.add_column("Package", style="cyan")
    table.add_column("Pinned", style="yellow")
    table.add_column("Current", style="red")
    table.add_column("Target", style="green")
    table.add_column("Action")

    for result in results:
        table.add_row(
            result.package,
            result.version or "—",
            result.old_value or "—",
            result.new_value or "—",
            _EXCLUDE_NEWER_ACTIONS[result.action],
        )

    console.print()
    console.print(table)


def display_override_results(results: list[OverrideResult]) -> None:
    """Render converged override pins as a table.

    Args:
        results (list[OverrideResult]): Override results to display.

    """
    table = Table(title="Transitive Overrides", show_lines=False)
    table.add_column("Package", style="cyan")
    table.add_column("Current", style="yellow")
    table.add_column("Target", style="green")
    table.add_column("Without override", style="magenta")

    for result in results:
        table.add_row(
            result.package,
            result.old_version or "—",
            result.new_version,
            result.unpinned_version or "—",
        )

    console.print()
    console.print(table)


def report_retirable(results: list[OverrideResult]) -> None:
    """Point out overrides that are no longer doing any work.

    Nothing is removed automatically: dropping an override silently would reintroduce whatever it was added to
    fix, so retirement stays a human decision.

    Args:
        results (list[OverrideResult]): Override results to inspect.

    """
    for result in (r for r in results if r.retirable):
        console.print(
            f"  [bold yellow]{result.package}[/] resolves to "
            f"[green]{result.unpinned_version}[/] without the override — "
            "the override is retirable and can be deleted from .syncdepsoverrides.yaml",
        )


def log_parsed_config(
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


def report_dependabot_changes(added: int, removed: int) -> None:
    """Print changes to dependabot ignores."""
    if added:
        noun = "entry" if added == 1 else "entries"
        console.print(f"  Added [cyan]{added}[/] ignore {noun} in .github/dependabot.yml")

    if removed:
        noun = "entry" if removed == 1 else "entries"
        console.print(
            f"  Removed [cyan]{removed}[/] stale ignore {noun} from .github/dependabot.yml",
        )
