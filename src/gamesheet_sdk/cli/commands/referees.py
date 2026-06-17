"""Referees command group."""

from __future__ import annotations

import rich_click as click
from rich_click import Choice, Context, Path

from gamesheet_sdk.cli.core import (
    ResourceGroup,
    confirm_destructive,
    parse_columns_spec,
)
from gamesheet_sdk.cli.helpers import build_authenticated_session, run_action_or_exit
from gamesheet_sdk.config import Config
from gamesheet_sdk.output import ALL_FORMATS, DEFAULT_FORMAT, render, write_output
from gamesheet_sdk.referees import create_referee as _create_referee_action
from gamesheet_sdk.referees import delete_referee as _delete_referee_action
from gamesheet_sdk.referees import get_referee as _get_referee_action
from gamesheet_sdk.referees import get_referee_report as _get_referee_report_action
from gamesheet_sdk.referees import list_referees as _list_referees_action
from gamesheet_sdk.referees import update_referee as _update_referee_action


@click.group(
    "referees",
    cls=ResourceGroup,
    default="list",
    aliases={
        "get": ("show", "view"),
        "list": ("ls",),
        "create": ("add", "new"),
        "update": ("set", "edit"),
        "delete": ("rm", "remove"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
def referees_group() -> None:
    """Manage referees within a season.

    Invoking ``referees`` with no sub-command runs ``list`` by default.
    """


@referees_group.command("get")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to retrieve.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
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
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
def referees_get_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get a single referee by ID.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    referee = run_action_or_exit(session, _get_referee_action, season_id, referee_id)
    rendered = render([referee.model_dump(mode="json")], fmt=output_format)
    write_output(rendered, output_path, fmt=output_format)


@referees_group.command("report")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to retrieve report for.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
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
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
def referees_report_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
    output_format: str,
    output_path: str | None,
) -> None:
    """Get a comprehensive referee report with statistics and games.

    Retrieves career statistics, games officiated, and penalty details. Requires authentication (run
    'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    report = run_action_or_exit(
        session,
        _get_referee_report_action,
        season_id,
        referee_id,
    )
    rendered = render([report.model_dump(mode="json")], fmt=output_format)
    write_output(rendered, output_path, fmt=output_format)


@referees_group.command("create")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to create the referee in.",
)
@click.option(
    "--first-name",
    type=str,
    required=True,
    help="Referee's first name.",
)
@click.option(
    "--last-name",
    type=str,
    required=True,
    help="Referee's last name.",
)
@click.option(
    "--email-address",
    type=str,
    default=None,
    help="Optional email address for the referee.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="Optional external identifier for the referee.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
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
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
# pylint: disable-next=too-many-positional-arguments
def referees_create_command(
    ctx: Context,
    season_id: str,
    first_name: str,
    last_name: str,
    email_address: str | None,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Create a new referee in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    referee = run_action_or_exit(
        session,
        _create_referee_action,
        season_id,
        first_name,
        last_name,
        email_address,
        external_id,
    )
    rendered = render([referee.model_dump(mode="json")], fmt=output_format)
    write_output(rendered, output_path, fmt=output_format)


@referees_group.command("update")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to update.",
)
@click.option(
    "--first-name",
    type=str,
    default=None,
    help="Updated first name.",
)
@click.option(
    "--last-name",
    type=str,
    default=None,
    help="Updated last name.",
)
@click.option(
    "--email-address",
    type=str,
    default=None,
    help="Updated email address.",
)
@click.option(
    "--external-id",
    type=str,
    default=None,
    help="Updated external identifier.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
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
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.pass_context
# pylint: disable-next=too-many-positional-arguments
def referees_update_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
    first_name: str | None,
    last_name: str | None,
    email_address: str | None,
    external_id: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Update an existing referee in the specified season.

    At least one field must be provided to update. Requires authentication (run 'gamesheet-sdk-py login'
    first).
    """
    # Validate that at least one field is provided
    if not any([first_name, last_name, email_address, external_id]):
        msg = (
            "At least one field must be provided to update. "
            "Use --first-name, --last-name, --email-address, or --external-id."
        )
        raise click.UsageError(msg)
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    referee = run_action_or_exit(
        session,
        _update_referee_action,
        season_id,
        referee_id,
        first_name,
        last_name,
        email_address,
        external_id,
    )
    rendered = render([referee.model_dump(mode="json")], fmt=output_format)
    write_output(rendered, output_path, fmt=output_format)


@referees_group.command("delete")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID containing the referee.",
)
@click.option(
    "--referee-id",
    type=str,
    required=True,
    help="Referee ID to delete.",
)
@confirm_destructive("referee")
@click.pass_context
def referees_delete_command(
    ctx: Context,
    season_id: str,
    referee_id: str,
) -> None:
    """Delete a referee.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    run_action_or_exit(session, _delete_referee_action, season_id, referee_id)
    click.secho(f"Referee {referee_id} deleted successfully.", fg="green")


@referees_group.command("list")
@click.option(
    "--season-id",
    type=str,
    envvar="GAMESHEET_SEASON_ID",
    required=True,
    help="Season ID to list referees for.",
)
@click.option(
    "--format",
    "-F",
    "output_format",
    type=Choice(list(ALL_FORMATS), case_sensitive=False),
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
    type=Path(dir_okay=False, writable=True),
    default=None,
    help="Write to this file instead of stdout.",
)
@click.option(
    "--columns",
    "-c",
    "columns_spec",
    default=None,
    help=("Comma-separated list of column names to include (default: all columns the API returns)."),
)
@click.pass_context
def referees_list_command(
    ctx: Context,
    season_id: str,
    output_format: str,
    output_path: str | None,
    columns_spec: str | None,
) -> None:
    """List all referees in the specified season.

    Requires authentication (run 'gamesheet-sdk-py login' first).
    """
    config: Config = ctx.obj
    session = build_authenticated_session(ctx, config)
    referees = run_action_or_exit(session, _list_referees_action, season_id)
    rows = [referee.model_dump(mode="json") for referee in referees]
    rendered = render(rows, fmt=output_format, columns=parse_columns_spec(columns_spec))
    write_output(rendered, output_path, fmt=output_format)
