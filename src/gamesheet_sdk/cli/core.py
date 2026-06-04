"""Core CLI framework components.

Contains the ResourceGroup class, decorators, and helper functions used across all CLI commands.
"""

from __future__ import annotations

import functools
import logging
import os
import sys
from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar

import click
import click.shell_completion
import colorlog

F = TypeVar("F", bound=Callable[..., Any])


class ResourceGroup(click.Group):
    """A :class:`click.Group` for resource-oriented sub-command trees.

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

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
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

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Inject the default sub-command when invoked bare, then delegate to click.

        When the group is invoked with no further args, inject the configured default sub-command so the rest
        of click's parsing machinery treats it exactly like an explicit call. Skip the injection when click is
        parsing for shell completion (``resilient_parsing=True``). Otherwise click's completion walker would
        silently descend into the default sub-command, and a bare ``gamesheet- sdk-py associations <TAB>``
        would yield the leaf command's options instead of the group's verbs.
        """
        if not args and self.default_cmd_name is not None and not ctx.resilient_parsing:

            args = [self.default_cmd_name]
        return super().parse_args(ctx, args)

    def _command_row(self, name: str, cmd: click.Command) -> tuple[str, str]:
        """Build the ``"list (ls)"`` label + short-help pair for one command."""
        alts = sorted(a for a, t in self._aliases.items() if t == name)
        label = f"{name} ({', '.join(alts)})" if alts else name
        return label, cmd.get_short_help_str(limit=80)

    def _visible_command_rows(self, ctx: click.Context) -> Iterable[tuple[str, str]]:
        """Yield ``(label, short_help)`` for each non-hidden canonical command."""
        for name in self.list_commands(ctx):

            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:  # pragma: no cover

                continue
            yield self._command_row(name, cmd)

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Render the command list with aliases in parentheses."""
        rows = list(self._visible_command_rows(ctx))
        if rows:

            with formatter.section("Commands"):
                formatter.write_dl(rows)

    def _alias_item_if_visible(
        self,
        alias: str,
        target: str,
        incomplete: str,
        seen: set[str],
    ) -> click.shell_completion.CompletionItem | None:
        """Return a CompletionItem for ``alias`` if it should surface, else ``None``."""
        if alias in seen or not alias.startswith(incomplete):

            return None

        cmd = self.commands.get(target)
        if cmd is None or cmd.hidden:

            return None

        short = cmd.get_short_help_str()
        help_text = f"(alias for {target}) {short}".rstrip()
        return click.shell_completion.CompletionItem(alias, help=help_text)

    def _alias_completion_items(
        self,
        incomplete: str,
        seen: set[str],
    ) -> list[click.shell_completion.CompletionItem]:
        """Build the alias-only completion items not already in ``seen``."""
        items: list[click.shell_completion.CompletionItem] = []
        for alias, target in self._aliases.items():

            item = self._alias_item_if_visible(alias, target, incomplete, seen)
            if item is None:

                continue
            items.append(item)
            seen.add(alias)  # noqa: PD005
        return items

    def shell_complete(
        self,
        ctx: click.Context,
        incomplete: str,
    ) -> list[click.shell_completion.CompletionItem]:
        """Tab-completion candidates for this group.

        Augments click's stock list (canonical sub-commands, plus options inherited from parent groups via the
        chained-completion walk) with any registered aliases whose underlying command is visible. Hidden
        commands and aliases pointing at hidden commands are skipped, matching click's default visibility
        rules.
        """
        results = list(super().shell_complete(ctx, incomplete))
        seen = {item.value for item in results}
        results.extend(self._alias_completion_items(incomplete, seen))
        return results


def confirm_destructive(target: str = "this resource") -> Callable[[F], F]:
    """Add ``--force/-f`` flag and confirmation prompt to destructive commands.

    Decorated commands gain a ``--force`` flag. When not set, the user is prompted ``"Delete {target}?
    [y/N]"``. Answering anything other than ``y`` or ``yes`` aborts with ``Exit(1)``.
    :param target: The resource name shown in the prompt (e.g., ``"this association"``).
    """

    def decorator(f: F) -> F:

        @click.option(
            "--force",
            "-f",
            is_flag=True,
            help=f"Skip the confirmation prompt and delete {target} immediately.",
        )
        @functools.wraps(f)
        def wrapper(*args: Any, force: bool = False, **kwargs: Any) -> Any:

            if not force:

                confirmed = click.confirm(f"Delete {target}?", default=False)
                if not confirmed:

                    click.echo("Aborted.", err=True)
                    raise click.exceptions.Exit(1)
            # Remove force from kwargs before calling the original function
            return f(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def _should_color(handler: logging.StreamHandler[Any]) -> bool:  # pragma: no cover
    """Return True if the handler's stream supports color."""
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
    if verbose == 0:

        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    handler = logging.StreamHandler(sys.stderr)
    if _should_color(handler):  # pragma: no cover

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

    :param spec: e.g., ``"id,title,created_at"`` or ``None``.
    :returns: A list of column names, or ``None`` if ``spec`` is ``None``.
    """
    if spec is None:

        return None

    stripped = spec.strip()
    if not stripped:  # pragma: no cover - edge case: all whitespace

        return None

    return [col.strip() for col in stripped.split(",") if col.strip()]


def resolve_system_exit(exc: BaseException) -> int:  # pragma: no cover - edge case handling
    """Mirror Python's :class:`SystemExit` code-to-int convention."""
    code = getattr(exc, "code", None)
    if code is None:

        return 0

    if isinstance(code, int):

        return code

    return 1


def resolve_exit(exc: BaseException) -> int:  # pragma: no cover - exception handling
    """Map a click/Python exit-style exception to its conventional exit code."""
    if isinstance(exc, click.exceptions.Exit):

        return int(exc.exit_code)

    if isinstance(exc, click.exceptions.UsageError):

        exc.show()  # pyright: ignore[reportUnknownMemberType]
        return 2

    if isinstance(exc, click.exceptions.Abort):

        click.echo("Aborted.", err=True)
        return 1

    return resolve_system_exit(exc)
