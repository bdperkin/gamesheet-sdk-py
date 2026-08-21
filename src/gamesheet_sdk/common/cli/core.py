# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Core CLI framework components.

Contains the ResourceGroup class, decorators, and helper functions used across all CLI commands.

This module provides the foundational infrastructure for building resource-oriented CLI interfaces:

- :class:`ResourceGroup` — A click.RichGroup subclass with alias support and default sub-commands
- :func:`confirm_destructive` — Decorator adding confirmation prompts to destructive operations
- Logging configuration with color support
- Column specification parsing for tabular output
- Exit code resolution for click exceptions

**Example: **

.. code-block:: python

    from gamesheet_sdk.common.cli.core import (
        ResourceGroup,
        confirm_destructive,
    )


    # Create a resource group with aliases and a default command
    @cli.group(
        "users",
        cls=ResourceGroup,
        default="list",
        aliases={
            "list": ("ls",),
            "delete": ("rm", "remove"),
        },
    )
    def users_group():
        pass


    # Add a destructive command with confirmation
    @users_group.command("delete")
    @click.argument("user_id")
    @confirm_destructive("this user")
    def delete_user(user_id):
        # Implementation here
        pass
"""

from __future__ import annotations

import functools
import logging
import os
import sys
from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar, cast

import colorlog
import rich_click as click
from click.exceptions import Abort, Exit, UsageError
from click.shell_completion import CompletionItem  # type: ignore[unresolved-import]
from rich_click import Command, Context, HelpFormatter

F = TypeVar("F", bound=Callable[..., Any])


class ResourceGroup(click.RichGroup):
    """A :class:`click.RichGroup` for resource-oriented sub-command trees.

    Adds two pieces of architectural plumbing on top of the stock group:

    **Aliases:**
        Pass ``aliases={"list": ("ls",), "delete": ("rm", "remove")}`` and ``ls`` resolves to the same
        callback as ``list`` without re-binding it. The canonical name is what shows up in tracebacks and
        ``--help`` output; aliases appear in parentheses next to it.

    **Default sub-command:**
        Pass ``default="list"`` and a bare invocation of the group implicitly runs ``list``. Explicit
        sub-command calls still flow through normally.

    Constructs a :class:`click.RichGroup` and configures command aliases and a default sub-command behavior.
    The alias mapping is flattened at construction time from ``{canonical: (alias1, alias2, ...)}`` into
    ``{alias1: canonical, alias2: canonical, ...}`` for O(1) lookup during command resolution.

    Args:
        *args (Any): Positional arguments forwarded to the decorated function.
        default (str | None): Name of the sub-command to invoke when the group is called with no arguments.
            For example, ``default="list"`` makes a bare ``gamesheet-admin associations`` implicitly run
            ``associations list``.
        aliases (Mapping[str, Iterable[str]] | None): Mapping of canonical command names to their aliases. For
            example, ``{"list": ("ls",), "delete": ("rm", "remove")}`` allows ``ls`` to resolve to ``list``
            and both ``rm`` and ``remove`` to resolve to ``delete``. Aliases appear in parentheses next to the
            canonical name in ``--help`` output and are included in tab-completion results.
        **kwargs (Any): Keyword arguments forwarded to the decorated function.

    """

    def __init__(
        self: ResourceGroup,
        *args: Any,
        default: str | None = None,
        aliases: Mapping[str, Iterable[str]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a ResourceGroup instance.

        Args:
            *args (Any): Positional arguments passed to superclass.
            default (str | None): Default sub-command name.
            aliases (Mapping[str, Iterable[str]] | None): Mapping of command names to aliases.
            **kwargs (Any): Keyword arguments passed to superclass.

        """
        super().__init__(*args, **kwargs)
        self.default_cmd_name = default
        # Flatten {canonical: (alt, ...)} into {alt: canonical} for O(1)
        # lookup in get_command.
        self._aliases: dict[str, str] = {}
        if aliases:
            for target, alts in aliases.items():
                for alt in alts:
                    self._aliases[alt] = target

    def get_command(self: ResourceGroup, ctx: Context, cmd_name: str) -> Command | None:
        """Resolve ``cmd_name`` against the canonical commands.

        Falls back to aliases if no canonical match is found.

        Args:
            ctx (Context): The click context.
            cmd_name (str): The command name to resolve.

        Returns:
            Command | None: The resolved Command object, or ``None`` if not found.

        """
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd

        target = self._aliases.get(cmd_name)
        if target is None:
            return None

        return super().get_command(ctx, target)

    def parse_args(self: ResourceGroup, ctx: Context, args: list[str]) -> list[str]:
        """Inject the default sub-command when invoked bare, then delegate to click.

        When the group is invoked with no further args, inject the configured default sub-command so the rest
        of click's parsing machinery treats it exactly like an explicit call. Skip the injection when click is
        parsing for shell completion (``resilient_parsing=True``). Otherwise click's completion walker would
        silently descend into the default sub-command, and a bare ``gamesheet-admin associations <TAB>`` would
        yield the leaf command's options instead of the group's verbs.

        Args:
            ctx (Context): The click context.
            args (list[str]): The command-line arguments to parse.

        Returns:
            list[str]: Parsed argument list.

        """
        if not args and self.default_cmd_name is not None and not ctx.resilient_parsing:
            args = [self.default_cmd_name]

        result: list[str] = super().parse_args(ctx, args)
        return result

    def _command_row(
        self: ResourceGroup,
        name: str,
        cmd: Command,
    ) -> tuple[str, str]:
        """Build the ``"list (ls)"`` label + short-help pair for one command.

        Args:
            name (str): Canonical command name.
            cmd (Command): The Command object.

        Returns:
            tuple[str, str]: Return value.

        """
        alts = sorted(a for a, t in self._aliases.items() if t == name)
        alts_str = ", ".join(alts)
        label = f"{name} ({alts_str})" if alts else name
        return label, cmd.get_short_help_str(limit=80)

    def _visible_command_rows(
        self: ResourceGroup,
        ctx: Context,
    ) -> Iterable[tuple[str, str]]:
        """Yield ``(label, short_help)`` for each non-hidden canonical command.

        Args:
            ctx (Context): The click context for resolving commands.

        Yields:
            tuple[str, str]: Tuples of ``(label, short_help)`` for visible commands.

        """
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue

            yield self._command_row(name, cmd)

    def format_commands(
        self: ResourceGroup,
        ctx: Context,
        formatter: HelpFormatter,
    ) -> None:
        """Render the command list with aliases in parentheses.

        Args:
            ctx (Context): The click context
            formatter (HelpFormatter): The help formatter to write to

        """
        rows = list(self._visible_command_rows(ctx))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)

    def _alias_item_if_visible(
        self: ResourceGroup,
        alias: str,
        target: str,
        incomplete: str,
        seen: set[str],
    ) -> CompletionItem | None:
        """Return a CompletionItem for ``alias`` if it should surface, else ``None``.

        Args:
            alias (str): The alias name to check.
            target (str): The canonical command name that the alias points to.
            incomplete (str): The partial command string being completed.
            seen (set[str]): Set of already seen command names or aliases.

        Returns:
            CompletionItem | None: Return value.

        """
        if alias in seen or not alias.startswith(incomplete):
            return None

        cmd = self.commands.get(target)
        if cmd is None or cmd.hidden:
            return None

        short = cmd.get_short_help_str()
        help_text = f"(alias for {target}) {short}".rstrip()
        return CompletionItem(alias, help=help_text)

    def _alias_completion_items(
        self: ResourceGroup,
        incomplete: str,
        seen: set[str],
    ) -> list[CompletionItem]:
        """Build the alias-only completion items not already in ``seen``.

        Args:
            incomplete (str): The partial command string being completed.
            seen (set[str]): Set of already seen command names or aliases.

        Returns:
            list[CompletionItem]: List of results.

        """
        items: list[CompletionItem] = []
        for alias, target in self._aliases.items():
            item = self._alias_item_if_visible(alias, target, incomplete, seen)
            if item is None:
                continue

            items.append(item)
            seen.add(alias)

        return items

    def shell_complete(
        self: ResourceGroup,
        ctx: Context,
        incomplete: str,
    ) -> list[CompletionItem]:
        """Tab-completion candidates for this group.

        Augments click's stock list (canonical sub-commands, plus options inherited from parent groups via the
        chained-completion walk) with any registered aliases whose underlying command is visible. Hidden
        commands and aliases pointing at hidden commands are skipped, matching click's default visibility
        rules.

        Args:
            ctx (Context): The click context
            incomplete (str): The partial command string being completed

        Returns:
            list[CompletionItem]: List of results.

        """
        # Look up the super method safely
        super_shell_complete = getattr(super(), "shell_complete", None)
        results = list(super_shell_complete(ctx, incomplete)) if super_shell_complete is not None else []

        seen = {item.value for item in results}
        results.extend(self._alias_completion_items(incomplete, seen))
        return results


def confirm_destructive(target: str = "this resource") -> Callable[[F], F]:
    """Add ``--force/-f`` flag and confirmation prompt to destructive commands.

    Decorated commands gain a ``--force`` flag. When not set, the user is prompted ``"Delete {target}?
    [y/N]"``. Answering anything other than ``y`` or ``yes`` aborts with ``Exit(1)``. Example::
        @cli.command("delete")
        @click.argument("resource_id")
        @confirm_destructive("this association")
        def delete_association(resource_id: str):
            # Deletion logic here
            pass

    Args:
        target (str): The resource name shown in the prompt (e.g., ``"this association"``).

    Returns:
        Callable[[F], F]: A decorator that wraps the command function with confirmation logic.

    """

    def decorator(f: F) -> F:
        """Actual decorator that adds the --force option and confirmation logic.

        Args:
            f (F): The command function to decorate.

        Returns:
            F: Decorated command function.

        """

        @click.option(
            "--force",
            "-f",
            is_flag=True,
            help=f"Skip the confirmation prompt and delete {target} immediately.",
        )
        @functools.wraps(f)
        def wrapper(*args: Any, force: bool = False, **kwargs: Any) -> object:
            """Execute the decorated function with optional confirmation.

            Args:
                *args (Any): Positional arguments forwarded to the decorated function.
                force (bool): If True, skip confirmation and proceed immediately.
                **kwargs (Any): Keyword arguments forwarded to the decorated function.

            Returns:
                object: Result of calling decorated function.

            Raises:
                Exit: With code 1 if the user declines confirmation.

            """
            if not force:
                confirmed = click.confirm(f"Delete {target}?", default=False)
                if not confirmed:
                    click.echo("Aborted.", err=True)
                    raise Exit(1)
            # Remove force from kwargs before calling the original function
            return f(*args, **kwargs)

        return cast("F", wrapper)

    return decorator


def _should_color(handler: logging.StreamHandler[Any]) -> bool:
    """Return True if the handler's stream supports color.

    Checks for the ``NO_COLOR`` environment variable and whether the stream is a TTY.

    Args:
        handler (logging.StreamHandler[Any]): The logging StreamHandler to check.

    Returns:
        bool: Boolean result.

    """
    if "NO_COLOR" in os.environ:
        return False

    try:
        stream = handler.stream
    except AttributeError:
        return False

    return bool(hasattr(stream, "isatty") and stream.isatty())


def _configure_logging(verbose: int) -> None:
    """Configure colored logging based on verbosity level.

    Args:
        verbose (int): 0 = WARNING, 1 = INFO, 2+ = DEBUG.

    """
    if not verbose:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    handler = logging.StreamHandler(sys.stderr)
    if _should_color(handler):
        formatter: logging.Formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    else:
        formatter = logging.Formatter("%(levelname)-8s %(message)s")

    handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[handler], force=True)


def parse_columns_spec(spec: str | None) -> list[str] | None:
    """Parse a comma-separated column specification.

    Whitespace around column names is stripped. Empty strings and whitespace-only columns are filtered out.
    Example::
        >>> parse_columns_spec("id, name, created_at")
        ['id', 'name', 'created_at']
        >>> parse_columns_spec(None)
        None
        >>> parse_columns_spec("  ")
        None

    Args:
        spec (str | None): A comma-separated string of column names (e.g., ``"id,title,created_at"``) or
            ``None``.

    Returns:
        list[str] | None: A list of column names, or ``None`` if ``spec`` is ``None`` or contains only
            whitespace.

    """
    if spec is None:
        return None

    stripped = spec.strip()
    if not stripped:
        return None

    return [col.strip() for col in stripped.split(",") if col.strip()]


def resolve_system_exit(
    exc: BaseException,
) -> int:
    """Mirror Python's :class:`SystemExit` code-to-int convention.

    Extracts the exit code from a SystemExit exception following Python's standard behavior:
    - ``None`` code → 0 (success)
    - Integer code → the integer itself
    - Any other code → 1 (failure)

    Args:
        exc (BaseException): A BaseException, typically a SystemExit.

    Returns:
        int: Integer exit code.

    """
    code = getattr(exc, "code", None)
    if code is None:
        return 0

    if isinstance(code, int):
        return code

    return 1


def resolve_exit(exc: BaseException) -> int:
    """Map a click/Python exit-style exception to its conventional exit code.

    Handles click-specific exceptions and delegates to :func:`resolve_system_exit` for standard Python exits:
    - :class:`Exit` → the exception's exit_code
    - :class:`UsageError` → 2 (after showing the error)
    - :class:`Abort` → 1 (after printing "Aborted.")
    - Other exceptions → delegated to :func:`resolve_system_exit`

    Args:
        exc (BaseException): The exception to resolve.

    Returns:
        int: An integer exit code following Unix conventions (0 = success, 1 = general error, 2 = usage
            error).

    """
    if isinstance(exc, Exit):
        return int(exc.exit_code)

    if isinstance(exc, UsageError):
        exc.show()
        return 2

    if isinstance(exc, Abort):
        click.echo("Aborted.", err=True)
        return 1

    return resolve_system_exit(exc)
