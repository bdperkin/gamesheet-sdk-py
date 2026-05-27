"""Command-line entry point for gamesheet_sdk.

Built on click. The pyproject.toml entry point is
``gamesheet_sdk.cli:main``; ``main`` is a thin int-returning wrapper
around the click group ``cli`` so the original
``main(argv: list[str] | None = None) -> int`` contract is preserved
for callers that imported it directly.

The CLI follows a resource-oriented (noun-first) layout: each resource
gets its own :class:`ResourceGroup` whose canonical verbs are
``create``, ``get``, ``list``, ``update``, and ``delete`` (with the
conventional aliases ``add/new``, ``show/view``, ``ls``, ``set/edit``,
and ``rm/remove`` respectively). Invoking a resource group with no
sub-command implicitly runs ``list``. ``login`` remains a root-level
global operation.
"""

from __future__ import annotations

import functools
import logging
import os
import sys
from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar, cast

import click
import colorlog

from gamesheet_sdk import __version__
from gamesheet_sdk.associations import list_associations as _list_associations_action
from gamesheet_sdk.auth import (
    AuthenticatedSession,
    load_access_token,
    load_refresh_token,
)
from gamesheet_sdk.auth import login as _login_action
from gamesheet_sdk.auth import (
    save_tokens,
)
from gamesheet_sdk.browser import BrowserSession
from gamesheet_sdk.config import Config
from gamesheet_sdk.exceptions import AuthenticationError, GameSheetError
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output

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
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        target = self._aliases.get(cmd_name)
        if target is None:
            return None
        return super().get_command(ctx, target)

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        # When the group is invoked with no further args, inject the
        # configured default sub-command so the rest of click's parsing
        # machinery treats it exactly like an explicit call.
        if not args and self.default_cmd_name is not None:
            args = [self.default_cmd_name]
        return super().parse_args(ctx, args)

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Render the command list with aliases in parentheses."""
        rows: list[tuple[str, str]] = []
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            alts = sorted(a for a, t in self._aliases.items() if t == name)
            label = f"{name} ({', '.join(alts)})" if alts else name
            rows.append((label, cmd.get_short_help_str(limit=80)))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


def confirm_destructive(target: str = "this resource") -> Callable[[F], F]:
    """Decorator: gate a click command with a ``[y/N]`` confirmation.

    Adds a ``--force/-f`` flag to the wrapped command. The flag skips
    the prompt (suitable for automation/CI); without it the command
    aborts unless the user confirms interactively. Intended for use on
    any ``delete``/``rm``/``remove`` sub-command across resource groups.
    """

    def decorator(f: F) -> F:
        @click.option(
            "--force",
            "-f",
            is_flag=True,
            default=False,
            help="Skip the interactive confirmation prompt.",
        )
        @functools.wraps(f)
        def wrapper(*args: Any, force: bool = False, **kwargs: Any) -> Any:
            if not force:
                click.confirm(
                    f"Really delete {target}?",
                    abort=True,
                    default=False,
                )
            return f(*args, **kwargs)

        return cast("F", wrapper)

    return decorator


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(__version__, prog_name="gamesheet-sdk-py")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase logging verbosity. -v sets INFO; -vv sets DEBUG.",
)
@click.option(
    "--base-url",
    metavar="URL",
    help="Override Config.base_url for this invocation.",
)
@click.option(
    "--no-headless",
    is_flag=True,
    help="Run browser-driven flows with a visible window (for debugging).",
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: int,
    base_url: str | None,
    no_headless: bool,
) -> None:
    """Unofficial CLI for the GameSheet Inc. platform.

    Each subcommand resolves its configuration in this order: CLI args >
    GAMESHEET_* environment variables > built-in defaults.
    """
    _configure_logging(verbose)
    overrides: dict[str, Any] = {}
    if base_url is not None:
        overrides["base_url"] = base_url
    if no_headless:
        overrides["browser_headless"] = False
    ctx.obj = Config(**overrides)
    # `invoke_without_command=True` lets us reach here with no subcommand;
    # in that case we print help and exit 0 (the canonical user-friendly
    # default) rather than letting click report a "Missing command" error.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _configure_logging(verbose: int) -> None:
    """Configure root logging based on the verbosity count (0, 1, 2+).

    Uses :class:`colorlog.ColoredFormatter` to add ANSI color codes to
    each log level when stderr is a TTY and the user has not set the
    ``NO_COLOR`` environment variable (https://no-color.org/). Falls
    back to a plain :class:`logging.Formatter` for non-interactive
    output (e.g. piped to a file or running in CI), so escape codes
    never leak into log files.
    """
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    handler = logging.StreamHandler()  # defaults to sys.stderr
    if _should_color(handler):
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(levelname)-8s%(reset)s %(message_log_color)s%(message)s",
                datefmt=None,
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
                secondary_log_colors={"message": {"ERROR": "red", "CRITICAL": "red"}},
                style="%",
            )
        )
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=level, handlers=[handler], force=True)


def _should_color(handler: logging.StreamHandler[Any]) -> bool:
    """Return True iff the handler's stream is a TTY and color is permitted."""
    if os.environ.get("NO_COLOR"):
        return False
    stream = getattr(handler, "stream", None)
    return bool(stream is not None and getattr(stream, "isatty", lambda: False)())


@cli.command("login")
@click.option(
    "--email",
    "-e",
    envvar="GAMESHEET_USERNAME",
    prompt="Email",
    help="GameSheet account email. Falls back to GAMESHEET_USERNAME, then prompts.",
)
@click.option(
    "--password",
    "-p",
    envvar="GAMESHEET_PASSWORD",
    prompt=True,
    hide_input=True,
    help="GameSheet account password. Falls back to GAMESHEET_PASSWORD, then prompts.",
)
@click.option(
    "--timeout",
    type=float,
    default=15.0,
    show_default=True,
    help="Seconds to wait for the post-submit redirect off the sign-in page.",
)
@click.pass_context
def login_command(
    ctx: click.Context,
    email: str,
    password: str,
    timeout: float,
) -> None:
    """Authenticate against the GameSheet dashboard and persist the session.

    On success the auth cookie and browser storage state are written to
    ``Config.browser_state_path`` so subsequent commands pick them up
    without re-authenticating.
    """
    config: Config = ctx.obj
    try:
        with BrowserSession(config) as session:
            _login_action(session, email=email, password=password, timeout=timeout)
    except AuthenticationError as exc:
        click.secho(f"Login failed: {exc}", fg="red", err=True)
        ctx.exit(1)  # raises; nothing after this point in the except runs
    click.secho("Login succeeded.", fg="green")


@cli.group(
    "associations",
    cls=ResourceGroup,
    default="list",
    aliases={
        "list": ("ls",),
        # The remaining canonical → alias mappings are listed here so the
        # next contributor adding create/get/update/delete sub-commands
        # gets the muscle-memory mapping for free. They have no effect
        # until matching @associations_group.command() callables exist.
        "create": ("add", "new"),
        "get": ("show", "view"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def associations_group() -> None:
    """Manage GameSheet associations.

    Invoking ``associations`` with no sub-command runs ``list`` by default.
    """


@associations_group.command("list")
@click.option(
    "--format",
    "-F",
    "output_format",
    type=click.Choice(list(ALL_FORMATS), case_sensitive=False),
    default=DEFAULT_FORMAT,
    show_default=True,
    help=(
        "Output format. Data formats: json, yaml, csv, tsv. Human-readable "
        "tabulate formats: plain, simple, grid, fancy_grid, pipe, orgtbl, "
        "rst, mediawiki, html, latex, latex_raw, latex_booktabs, "
        "latex_longtable."
    ),
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all " "columns the API returns)."),
)
@click.pass_context
def associations_list_command(
    ctx: click.Context,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List the associations the signed-in user can see.

    Requires a saved session from `gamesheet-sdk-py login` -- the bearer token is read
    out of the browser storage state on disk and attached to the HTTP request. No
    browser is launched.
    """
    config: Config = ctx.obj
    access = load_access_token(config)
    refresh = load_refresh_token(config)
    if access is None or refresh is None:
        click.secho(
            "No saved session. Run `gamesheet-sdk-py login` first.",
            fg="red",
            err=True,
        )
        ctx.exit(1)

    def persist(tokens: dict[str, str]) -> None:
        save_tokens(config, **tokens)

    try:
        with AuthenticatedSession(
            config,
            access_token=access or "",
            refresh_token=refresh or "",
            on_refresh=persist,
        ) as session:
            associations = _list_associations_action(session)
    except AuthenticationError as exc:
        click.secho(f"Authentication required: {exc}", fg="red", err=True)
        ctx.exit(1)  # raises; control does not return
    except GameSheetError as exc:
        click.secho(f"GameSheet error: {exc}", fg="red", err=True)
        ctx.exit(1)  # raises; control does not return

    rows = [assoc.model_dump(mode="json") for assoc in associations]
    columns = [c.strip() for c in columns_spec.split(",") if c.strip()] if columns_spec else None
    rendered = render(rows, fmt=output_format, columns=columns)
    write_output(rendered, output_path, fmt=output_format)


def main(  # pylint: disable=too-many-return-statements
    argv: list[str] | None = None,
) -> int:
    """Entry-point wrapper. Returns an int exit code.

    Calls into the click ``cli`` group with ``standalone_mode=False`` so
    click's control-flow exceptions are converted to integer returns
    rather than ``sys.exit()`` calls, preserving the original
    ``main(argv) -> int`` contract.
    """
    try:
        cli.main(
            args=argv,
            prog_name="gamesheet-sdk-py",
            standalone_mode=False,
        )
    except click.exceptions.Exit as exc:
        return int(exc.exit_code)
    except click.exceptions.UsageError as exc:
        exc.show()
        return 2
    except click.exceptions.Abort:
        click.echo("Aborted.", err=True)
        return 1
    except SystemExit as exc:
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
