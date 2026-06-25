"""Completion command."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit
from rich_click import Choice

from gamesheet_sdk.cli.constants import SHELL_TYPES


@click.command("completion")
@click.argument(
    "shell",
    type=Choice(SHELL_TYPES, case_sensitive=False),
)
def completion_command(shell: str) -> None:
    """Emit shell completion script for the specified shell.

    Source the output to enable tab-completion:
    Bash::
        eval "$(gamesheet-sdk-py completion bash)"
    Zsh::
        eval "$(gamesheet-sdk-py completion zsh)"
    Fish::
        gamesheet-sdk-py completion fish | source
    """
    # click's built-in completion uses an env-var protocol. We mimic what
    # click.shell_completion does internally but surface it as a subcommand.
    from click import get_current_context
    from click.shell_completion import get_completion_class

    cls = get_completion_class(shell)
    if cls is None:  # pragma: no cover
        click.secho(f"Unsupported shell: {shell}", fg="red", err=True)
        raise Exit(1)
    # Create the completion instance and echo its source
    complete_var = "_GAMESHEET_SDK_PY_COMPLETE"
    cli = None
    ctx = get_current_context()
    if ctx.parent:
        cli = ctx.parent.command
        comp = cls(
            cli,
            ctx_args={},
            prog_name="gamesheet-sdk-py",
            complete_var=complete_var,
        )
        click.echo(comp.source())
