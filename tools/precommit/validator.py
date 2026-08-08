# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Pre-commit validation runner."""

from __future__ import annotations

from contextlib import suppress
import logging
from pathlib import Path
import shutil
import subprocess  # noqa: S404 # nosec B404

from precommit.config import PRE_COMMIT_RUN_TIMEOUT
from precommit.exceptions import PreCommitValidationError, SubprocessError

logger = logging.getLogger(__name__)

_CONFIG_VALIDATION_HOOKS = ("check-hooks-apply", "check-useless-excludes")


def _find_pre_commit() -> str | None:
    """Locate the pre-commit executable.

    Returns:
        Path to pre-commit or None if not found.
    """
    return shutil.which("pre-commit")


def _run_pre_commit(
    pre_commit: str,
    *,
    hook_id: str | None = None,
    print_output: bool,
) -> None:
    """Execute pre-commit run --all-files, optionally for a single hook.

    Args:
        pre_commit: Path to pre-commit executable.
        hook_id: Optional specific hook ID to run.
        print_output: Whether to print stdout.

    Raises:
        PreCommitValidationError: If the run reports failures or skipped
            hooks.
        SubprocessError: If pre-commit cannot be executed.
    """
    cmd = [pre_commit, "run"]
    if hook_id:
        cmd.append(hook_id)

    cmd.extend(["--all-files", "--verbose"])

    try:
        result = subprocess.run(  # noqa: S603 # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=PRE_COMMIT_RUN_TIMEOUT,
        )
    except FileNotFoundError as exc:
        raise SubprocessError(str(exc), 127, "") from exc
    except subprocess.TimeoutExpired as exc:
        label = f" ({hook_id})" if hook_id else ""
        msg = f"pre-commit validation timed out after {PRE_COMMIT_RUN_TIMEOUT}s{label}"
        raise SubprocessError(msg, 124, "") from exc

    stdout = result.stdout
    stderr = result.stderr

    combined = stderr + stdout
    if hook_id and result.returncode and f"No hook with id `{hook_id}` in stage" in combined:
        logger.debug("Skipping %s: not in default stage", hook_id)
        return

    failed = bool(result.returncode)

    if print_output and stdout:
        logger.debug("%s", stdout.rstrip())

    if failed:
        detail = stderr or stdout.rstrip()
        label = f" ({hook_id})" if hook_id else ""
        msg = f"pre-commit validation failed{label} (exit {result.returncode})"
        if detail:
            msg = f"{msg}:\n{detail}"

        err = PreCommitValidationError(msg)
        err.exit_code = result.returncode or 1
        raise err


def _clear_backup(backup_path: Path) -> None:
    """Clear the backup file content so the next run always validates.

    Args:
        backup_path: Path to the backup file.
    """
    try:
        backup_path.write_text("", encoding="utf-8")
    except OSError:
        logger.debug("Could not clear backup file %s", backup_path)


def _config_unchanged(backup_path: Path, output_path: Path) -> bool:
    """Check whether the config file is identical to the backup.

    Args:
        backup_path: Path to the backup of the previous config.
        output_path: Path to the current config file.

    Returns:
        True if the files are identical, False otherwise.
    """
    if not (backup_path.exists() and output_path.exists()):
        return False

    with suppress(FileNotFoundError):
        result = subprocess.run(  # noqa: S603, S607 # nosec B603, B607
            ["diff", "-q", str(backup_path), str(output_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if not result.returncode:
            return True

    return False


def _diff_and_run(
    *,
    pre_commit: str,
    output_path: Path,
    backup_path: Path,
    hook_ids: list[str] | None,
    print_output: bool,
) -> None:
    """Compare current and previous configs, run pre-commit if they differ.

    Args:
        pre_commit: Path to pre-commit executable.
        output_path: Path to the current config file.
        backup_path: Path to the backup of the previous config.
        hook_ids: Optional hook IDs to run individually.
        print_output: Whether to print pre-commit stdout.
    """
    if _config_unchanged(backup_path, output_path):
        logger.debug("Config unchanged, skipping validation")
        return

    try:
        shutil.copy2(output_path, backup_path)
    except OSError:
        logger.warning(
            "Could not create backup of %s; skipping diff optimization",
            output_path,
        )

    if hook_ids:
        for meta_id in _CONFIG_VALIDATION_HOOKS:
            _run_pre_commit(pre_commit, hook_id=meta_id, print_output=print_output)

        for hook_id in hook_ids:
            _run_pre_commit(pre_commit, hook_id=hook_id, print_output=print_output)
    else:
        _run_pre_commit(pre_commit, print_output=print_output)

    if print_output:
        _clear_backup(backup_path)


def validate_config(
    output_path: Path,
    *,
    hook_ids: list[str] | None = None,
    print_output: bool = False,
) -> None:
    """Run pre-commit against all files to validate the generated config.

    Args:
        output_path (Path): Path to the .pre-commit-config.yaml file.
        hook_ids (list[str] | None): Optional list of hook IDs to
            validate individually. When None, all hooks are run.
        print_output (bool): Whether to print pre-commit stdout.

    Raises:
        PreCommitValidationError: If pre-commit reports failures or
            errors.
    """
    pre_commit = _find_pre_commit()
    if pre_commit is None:
        msg = "pre-commit executable not found"
        raise PreCommitValidationError(msg)

    backup_path = Path(f"{output_path}~")
    _diff_and_run(
        pre_commit=pre_commit,
        output_path=output_path,
        backup_path=backup_path,
        hook_ids=hook_ids,
        print_output=print_output,
    )
