# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Completion command for the GameSheet admin CLI."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit
from rich_click import Choice

from gamesheet_sdk.common.cli.constants import SHELL_TYPES


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

    Raises:
        Exit: If the specified shell is unsupported.

    """
    from click import get_current_context  # noqa: PLC0415
    from click.shell_completion import get_completion_class  # noqa: PLC0415 # type: ignore[unresolved-import]

    cls = get_completion_class(shell)
    if cls is None:  # pragma: no cover
        click.secho(f"Unsupported shell: {shell}", fg="red", err=True)
        raise Exit(1)

    ctx = get_current_context()
    if ctx.parent:
        comp = cls(
            ctx.parent.command,
            ctx_args={},
            prog_name="gamesheet-admin",
            complete_var="_GAMESHEET_ADMIN_COMPLETE",
        )
        click.echo(comp.source())
