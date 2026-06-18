"""Core CLI framework components.

Contains the ResourceGroup class, decorators, and helper functions used across all CLI commands.

This module provides the foundational infrastructure for building resource-oriented CLI interfaces:
- :class:`ResourceGroup`: A click.RichGroup subclass with alias support and default sub-commands
- :func:`confirm_destructive`: Decorator adding confirmation prompts to destructive operations
- Logging configuration with color support
- Column specification parsing for tabular output
- Exit code resolution for click exceptions
Example::
    from gamesheet_sdk.cli.core import ResourceGroup, confirm_destructive
    # Create a resource group with aliases and a default command
    @cli.group("users", cls=ResourceGroup, default="list", aliases={
        "list": ("ls",),
        "delete": ("rm", "remove"),
    })
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
from typing import TYPE_CHECKING, Any, TypeVar

import colorlog
import rich_click as click
from click.exceptions import Abort, Exit, UsageError
from click.shell_completion import CompletionItem

if TYPE_CHECKING:
    from rich_click import Command, Context, HelpFormatter
F = TypeVar("F", bound=Callable[..., Any])


class ResourceGroup(click.RichGroup):
    """A :class:`click.RichGroup` for resource-oriented sub-command trees.

    Adds two pieces of architectural plumbing on top of the stock group.
    **Aliases.** Pass ``aliases={"list": ("ls",), "delete": ("rm", "remove")}`` and ``ls`` resolves to the
    same callback as ``list`` without re-binding it. The canonical name is what shows up in tracebacks and
    ``--help`` output; aliases appear in parentheses next to it.
    **Default sub-command.** Pass ``default="list"`` and a bare invocation of the group implicitly runs
    ``list``. Explicit sub-command calls still flow through normally.
    """

    def __init__(
        self,
        *args: Any,
        default: str | None = None,
        aliases: Mapping[str, Iterable[str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.default_cmd_name = default
        # Flatten {canonical: (alt, ...)} into {alt: canonical} for O(1)
        # lookup in get_command.
        self._aliases: dict[str, str] = {}
        if aliases:
            for target, alts in aliases.items():
                for alt in alts:
                    self._aliases[alt] = target

    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        """Resolve ``cmd_name`` against the canonical commands.

        Falls back to aliases.
        """
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        target = self._aliases.get(cmd_name)
        if target is None:
            return None
        return super().get_command(ctx, target)

    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        """Inject the default sub-command when invoked bare, then delegate to click.

        When the group is invoked with no further args, inject the configured default sub-command so the rest
        of click's parsing machinery treats it exactly like an explicit call. Skip the injection when click is
        parsing for shell completion (``resilient_parsing=True``). Otherwise click's completion walker would
        silently descend into the default sub-command, and a bare ``gamesheet- sdk-py associations <TAB>``
        would yield the leaf command's options instead of the group's verbs.
        """
        if not args and self.default_cmd_name is not None and not ctx.resilient_parsing:
            args = [self.default_cmd_name]
        result: list[str] = super().parse_args(ctx, args)
        return result

    def _command_row(
        self,
        name: str,
        cmd: Command,
    ) -> tuple[str, str]:
        """Build the ``"list (ls)"`` label + short-help pair for one command.

        :param name: Canonical command name.
        :param cmd: The Command object.
        :returns: A tuple of (label, short_help) where label includes aliases in parentheses if any exist.
        """
        alts = sorted(a for a, t in self._aliases.items() if t == name)  # pragma: no cover
        label = f"{name} ({', '.join(alts)})" if alts else name  # pragma: no cover
        return label, cmd.get_short_help_str(limit=80)  # pragma: no cover

    def _visible_command_rows(
        self,
        ctx: Context,
    ) -> Iterable[tuple[str, str]]:
        """Yield ``(label, short_help)`` for each non-hidden canonical command.

        Args:
            ctx: The click context for resolving commands.

        Yields:
            tuple[str, str]: Tuples of (label, short_help) for visible commands.
        """
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)  # pragma: no cover
            if cmd is None or cmd.hidden:  # pragma: no cover
                continue  # pragma: no cover
            yield self._command_row(name, cmd)  # pragma: no cover

    def format_commands(
        self,
        ctx: Context,
        formatter: HelpFormatter,
    ) -> None:
        """Render the command list with aliases in parentheses."""
        rows = list(self._visible_command_rows(ctx))
        if rows:
            with formatter.section("Commands"):  # pragma: no cover
                formatter.write_dl(rows)  # pragma: no cover

    def _alias_item_if_visible(
        self,
        alias: str,
        target: str,
        incomplete: str,
        seen: set[str],
    ) -> CompletionItem | None:
        """Return a CompletionItem for ``alias`` if it should surface, else ``None``.

        :param alias: The alias name to check.
        :param target: The canonical command name that the alias points to.
        :param incomplete: The partial command string being completed.
        :param seen: Set of already-seen completion values to avoid duplicates.
        :returns: A CompletionItem for the alias if it's visible and matches, otherwise ``None``.
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
        self,
        incomplete: str,
        seen: set[str],
    ) -> list[CompletionItem]:
        """Build the alias-only completion items not already in ``seen``.

        :param incomplete: The partial command string being completed.
        :param seen: Set of already-seen completion values; mutated in-place to track new aliases.
        :returns: List of CompletionItems for visible aliases matching the incomplete string.
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
        self,
        ctx: Context,
        incomplete: str,
    ) -> list[CompletionItem]:
        """Tab-completion candidates for this group.

        Augments click's stock list (canonical sub-commands, plus options inherited from parent groups via the
        chained-completion walk) with any registered aliases whose underlying command is visible. Hidden
        commands and aliases pointing at hidden commands are skipped, matching click's default visibility
        rules.
        """
        # Look up the super method safely
        super_shell_complete = getattr(super(), "shell_complete", None)
        if super_shell_complete is not None:
            results = list(super_shell_complete(ctx, incomplete))
        else:
            results = []  # pragma: no cover
        seen = {item.value for item in results}
        results.extend(self._alias_completion_items(incomplete, seen))
        return results


def confirm_destructive(target: str = "this resource") -> Callable[[F], F]:
    """Add ``--force/-f`` flag and confirmation prompt to destructive commands.

    Decorated commands gain a ``--force`` flag. When not set, the user is prompted
    ``"Delete {target}? [y/N]"``. Answering anything other than ``y`` or ``yes`` aborts with ``Exit(1)``.
    :param target: The resource name shown in the prompt (e.g., ``"this association"``).
    :returns: A decorator that wraps the command function with confirmation logic.

    Example::
        @cli.command("delete")
        @click.argument("resource_id")
        @confirm_destructive("this association")
        def delete_association(resource_id: str):
            # Deletion logic here
            pass
    """

    def decorator(f: F) -> Any:
        """Actual decorator that adds the --force option and confirmation logic.

        :param f: The command function to decorate.
        :returns: The wrapped function with confirmation prompt and --force support.
        """

        @click.option(
            "--force",
            "-f",
            is_flag=True,
            help=f"Skip the confirmation prompt and delete {target} immediately.",
        )
        @functools.wraps(f)
        def wrapper(*args: Any, force: bool = False, **kwargs: Any) -> Any:
            """Execute the decorated function with optional confirmation.

            :param args: Positional arguments passed to the original function.
            :param force: If True, skip confirmation and proceed immediately.
            :param kwargs: Keyword arguments passed to the original function.
            :returns: The return value of the decorated function.
            :raises Exit: With code 1 if the user declines confirmation.
            """
            if not force:
                confirmed = click.confirm(f"Delete {target}?", default=False)
                if not confirmed:
                    click.echo("Aborted.", err=True)
                    raise Exit(1)
            # Remove force from kwargs before calling the original function
            return f(*args, **kwargs)

        return wrapper

    return decorator


def _should_color(handler: logging.StreamHandler[Any]) -> bool:
    """Return True if the handler's stream supports color.

    Checks for the ``NO_COLOR`` environment variable and whether the stream is a TTY.
    :param handler: The logging StreamHandler to check.
    :returns: True if color output is supported and not disabled, False otherwise.
    """
    if "NO_COLOR" in os.environ:
        return False
    try:
        stream = handler.stream
    except AttributeError:
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def _configure_logging(verbose: int) -> None:
    """Configure colored logging based on verbosity level.

    :param verbose: 0 = WARNING, 1 = INFO, 2+ = DEBUG.
    """
    if not verbose:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    handler = logging.StreamHandler(sys.stderr)
    if _should_color(handler):
        formatter: logging.Formatter = colorlog.ColoredFormatter(  # pragma: no cover
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
    :param spec: A comma-separated string of column names (e.g., ``"id,title,created_at"``) or ``None``.
    :returns: A list of column names, or ``None`` if ``spec`` is ``None`` or contains only whitespace.
    Example::
        >>> parse_columns_spec("id, name, created_at")
        ['id', 'name', 'created_at']
        >>> parse_columns_spec(None)
        None
        >>> parse_columns_spec("  ")
        None
    """
    if spec is None:  # pragma: no cover
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
    :param exc: A BaseException, typically a SystemExit.
    :returns: An integer exit code (0 for success, non-zero for failure).
    """
    code = getattr(exc, "code", None)  # pragma: no cover
    if code is None:  # pragma: no cover
        return 0  # pragma: no cover
    if isinstance(code, int):  # pragma: no cover
        return code  # pragma: no cover
    return 1  # pragma: no cover


def resolve_exit(exc: BaseException) -> int:
    """Map a click/Python exit-style exception to its conventional exit code.

    Handles click-specific exceptions and delegates to :func:`resolve_system_exit` for standard Python exits:
    - :class:`Exit` → the exception's exit_code
    - :class:`UsageError` → 2 (after showing the error)
    - :class:`Abort` → 1 (after printing "Aborted.")
    - Other exceptions → delegated to :func:`resolve_system_exit`
    :param exc: The exception to resolve.
    :returns: An integer exit code following Unix conventions (0 = success, 1 = general error, 2 = usage
        error).
    """
    if isinstance(exc, Exit):
        return int(exc.exit_code)  # pragma: no cover
    if isinstance(exc, UsageError):
        exc.show()
        return 2
    if isinstance(exc, Abort):  # pragma: no cover
        click.echo("Aborted.", err=True)  # pragma: no cover
        return 1  # pragma: no cover
    return resolve_system_exit(exc)  # pragma: no cover
