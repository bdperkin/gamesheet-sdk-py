# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Completion command for the GameSheet admin CLI."""

from __future__ import annotations

import rich_click as click
from rich_click import Choice

from gamesheet_sdk.common.cli.constants import SHELL_TYPES
from gamesheet_sdk.common.cli.helpers import emit_shell_completion


@click.command("completion")
@click.argument(
    "shell",
    type=Choice(SHELL_TYPES, case_sensitive=False),
)
def completion_command(shell: str) -> None:
    r"""Emit shell completion script for the specified shell.

    Source the output to enable tab-completion::

        eval "$(gamesheet-admin completion bash)"\f

    Args:
        shell (str): Target shell (bash, zsh, or fish).

    """
    emit_shell_completion(
        shell,
        prog_name="gamesheet-admin",
        complete_var="_GAMESHEET_ADMIN_COMPLETE",
    )
