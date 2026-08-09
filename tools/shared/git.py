# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared git subprocess helpers for CLI tools."""

from __future__ import annotations

import shutil
import subprocess  # noqa: S404 # nosec B404

GIT_LS_REMOTE_TIMEOUT = 30


class GitCommandError(Exception):
    """A git subprocess command failed."""


def run_ls_remote(
    repo_url: str,
    *options: str,
    refspecs: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    """Run ``git ls-remote`` against a remote repository.

    Args:
        repo_url (str): Remote repository URL.
        *options (str): Flag arguments inserted before the repo URL
            (e.g. ``"--tags"``, ``"--quiet"``).
        refspecs (tuple[str, ...]): Ref patterns placed after the repo
            URL (e.g. ``("HEAD",)``).

    Returns:
        subprocess.CompletedProcess[str]: The completed process with
        captured stdout/stderr.

    Raises:
        GitCommandError: If git is not on PATH, the command fails, times
            out, or cannot be executed.
    """
    if shutil.which("git") is None:
        msg = "'git' is not on PATH; install git to enable tag discovery"
        raise GitCommandError(msg)

    cmd: list[str] = ["git", "ls-remote", *options, repo_url, *refspecs]

    try:
        return subprocess.run(  # noqa: S603 # nosec B603
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_LS_REMOTE_TIMEOUT,
        )
    except subprocess.CalledProcessError as exc:
        msg = f"git ls-remote failed for {repo_url}: {exc.stderr.strip()}"
        raise GitCommandError(msg) from exc
    except subprocess.TimeoutExpired as exc:
        msg = f"git ls-remote timed out for {repo_url}"
        raise GitCommandError(msg) from exc
    except OSError as exc:
        msg = f"Failed to run 'git ls-remote' for {repo_url}: {exc}"
        raise GitCommandError(msg) from exc
