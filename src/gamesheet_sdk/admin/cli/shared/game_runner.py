# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Admin-side execution of the unified game option set.

The ``gamesheet-admin games`` commands are thin: they declare the shared option set from
:mod:`gamesheet_sdk.common.cli.game_options` and hand their collected parameters here, which translates them
into the season-schedule JSON:API calls in :mod:`gamesheet_sdk.admin.games`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from rich_click import Context

from gamesheet_sdk.admin.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.admin.cli.shared.rendering import (
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.admin.games import (
    create_scheduled_game as _create_scheduled_game_action,
)
from gamesheet_sdk.admin.games import (
    delete_scheduled_game as _delete_scheduled_game_action,
)
from gamesheet_sdk.admin.games import (
    get_scheduled_game as _get_scheduled_game_action,
)
from gamesheet_sdk.admin.games import (
    list_scheduled as _list_scheduled_action,
)
from gamesheet_sdk.admin.games import (
    update_scheduled_game as _update_scheduled_game_action,
)
from gamesheet_sdk.common.cli.game_options import (
    GameArgs,
    parse_game_args,
    warn_unsupported_options,
)
from gamesheet_sdk.common.cli.game_times import (
    resolve_game_window,
    resolve_game_window_update,
    resolve_time_zone,
    validate_game_time_inputs,
)

if TYPE_CHECKING:
    from gamesheet_sdk.admin.games.models import ScheduledGame, ScheduledGameAttributes
    from gamesheet_sdk.common.auth.session import AuthenticatedSession
    from gamesheet_sdk.common.config import Config

CLI_NAME = "gamesheet-admin"


def _config(ctx: Context) -> Config:
    """Return the :class:`Config` the ``games`` group stashed in the context.

    Args:
        ctx (Context): Click context object.

    Returns:
        Config: The active configuration.

    """
    obj: Any = ctx.obj
    return obj["config"] if isinstance(obj, dict) else obj


def resolve_season_id(ctx: Context, season_id: str | None) -> str:
    """Resolve the season from the sub-command's own option or the ``games`` group's.

    ``--season-id`` is accepted in both positions so that a command line written for
    ``gamesheet-teams schedule games``, which only has the sub-command spelling, runs unchanged here.

    Args:
        ctx (Context): Click context object.
        season_id (str | None): The sub-command's ``--season-id``, if given.

    Returns:
        str: The season identifier.

    Raises:
        UsageError: If neither position supplied one.

    """
    if season_id:
        return season_id

    obj: Any = ctx.obj
    inherited = obj.get("season_id") if isinstance(obj, dict) else None
    if inherited:
        return str(inherited)

    msg = "Missing required option: --season-id (or the GAMESHEET_SEASON_ID environment variable)."
    raise click.UsageError(msg)


def _non_default_month(month: str | None) -> str | None:
    """Return ``month`` only when it narrows the result set.

    Args:
        month (str | None): The ``--month`` value.

    Returns:
        str | None: The value, or ``None`` when it is absent or the ``'all'`` default.

    """
    return None if month in {None, "", "all"} else month


def _warn_teams_only(params: dict[str, Any]) -> None:
    """Warn about teams-gateway options this backend cannot act on.

    Args:
        params (dict[str, Any]): The command's collected parameters.

    """
    warn_unsupported_options(
        CLI_NAME,
        {
            "--team-id": params.get("team_id"),
            "--month": _non_default_month(params.get("month")),
            "--event-data": params.get("include_event_data"),
            "--availability": params.get("include_availability"),
        },
    )


def _validate_times(args: GameArgs) -> None:
    """Reject conflicting time options before any authenticated work happens.

    Args:
        args (GameArgs): The parsed option set.

    """
    times = args.times
    validate_game_time_inputs(
        times.start_datetime,
        times.start_date,
        times.start_time,
        times.end_datetime,
        times.end_date,
        times.end_time,
    )


def _text(value: str | None) -> str:
    """Coerce an unsupplied optional string to the empty string the JSON:API payload expects.

    Args:
        value (str | None): The supplied value.

    Returns:
        str: The value, or ``''``.

    """
    return value if value is not None else ""


def _pick(new: str | None, current: str) -> str:
    """Choose between a newly supplied value and the one the API currently holds.

    ``None`` means the option was not given, so the current value stands. An explicitly empty string is a
    real value and clears the field.

    Args:
        new (str | None): The value from the command line.
        current (str): The value the API currently holds.

    Returns:
        str: The value to send.

    """
    return current if new is None else new


def _session(ctx: Context) -> AuthenticatedSession:
    """Build an authenticated admin session from the context config.

    Args:
        ctx (Context): Click context object.

    Returns:
        AuthenticatedSession: A session ready to use.

    """
    return build_authenticated_session(_config(ctx))


def run_create(ctx: Context, params: dict[str, Any]) -> None:
    """Create a scheduled game from the unified option set.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    sides = args.sides.require()
    times = args.times
    start, end = resolve_game_window(
        times.start_datetime,
        times.start_date,
        times.start_time,
        times.end_datetime,
        times.end_date,
        times.end_time,
        times.duration,
    )
    tz_name, tz_offset = resolve_time_zone(args.time_zone_name, args.time_zone_offset)
    season_id = resolve_season_id(ctx, args.season_id)

    game = run_action_or_exit(
        _session(ctx),
        _create_scheduled_game_action,
        season_id,
        start,
        end,
        sides.home_team_id,
        sides.home_division_id,
        sides.visitor_team_id,
        sides.visitor_division_id,
        _text(args.location),
        _text(args.scorekeeper_name),
        _text(args.scorekeeper_phone),
        str(args.game_type),
        tz_name,
        tz_offset,
        str(args.number),
        _text(args.broadcaster),
        _text(args.home_label),
        _text(args.visitor_label),
    )
    render_get_command(game, args.output_format, args.output_path, args.fields_spec)


def _current_game(
    session: AuthenticatedSession,
    season_id: str,
    game_id: str,
) -> ScheduledGame:
    """Fetch the game an update is about to modify.

    Args:
        session (AuthenticatedSession): Authenticated session.
        season_id (str): Season identifier.
        game_id (str): Game identifier.

    Returns:
        ScheduledGame: The current state of the game.

    """
    return run_action_or_exit(session, _get_scheduled_game_action, season_id, game_id)


def _updated_window(args: GameArgs, current: ScheduledGame) -> tuple[str, str]:
    """Resolve the game's new start/end pair, preserving the current one when untouched.

    Args:
        args (GameArgs): The parsed option set.
        current (ScheduledGame): The game's current state.

    Returns:
        tuple[str, str]: The ``(start, end)`` pair to send.

    """
    attrs = current.data.attributes
    times = args.times
    start, end = resolve_game_window_update(
        times.start_datetime,
        times.start_date,
        times.start_time,
        times.end_datetime,
        times.end_date,
        times.end_time,
        times.duration,
        attrs.scheduled_start_time,
        attrs.scheduled_end_time,
    )
    return start or attrs.scheduled_start_time, end or attrs.scheduled_end_time


def _updated_sides(args: GameArgs, current: ScheduledGame) -> tuple[str, str, str, str]:
    """Resolve the four team/division identifiers, keeping the current ones where unnamed.

    Args:
        args (GameArgs): The parsed option set.
        current (ScheduledGame): The game's current state.

    Returns:
        tuple[str, str, str, str]: ``(home team, home division, visitor team, visitor division)``.

    """
    sides = args.sides
    rels = current.data.relationships
    return (
        _pick(sides.home_team_id, rels.home_team.data.id),
        _pick(sides.home_division_id, rels.home_division.data.id),
        _pick(sides.visitor_team_id, rels.visitor_team.data.id),
        _pick(sides.visitor_division_id, rels.visitor_division.data.id),
    )


def _updated_details(args: GameArgs, attrs: ScheduledGameAttributes) -> tuple[str, str, str, str]:
    """Resolve the venue, scorekeeper, and game type, keeping the current ones where unnamed.

    Args:
        args (GameArgs): The parsed option set.
        attrs (ScheduledGameAttributes): The game's current attributes.

    Returns:
        tuple[str, str, str, str]: ``(location, scorekeeper name, scorekeeper phone, game type)``.

    """
    return (
        _pick(args.location, attrs.location),
        _pick(args.scorekeeper_name, attrs.scorekeeper.name),
        _pick(args.scorekeeper_phone, attrs.scorekeeper.phone),
        _pick(args.game_type, attrs.game_type),
    )


def run_update(ctx: Context, params: dict[str, Any]) -> None:
    """Update a scheduled game from the unified option set.

    Unspecified fields keep the values the API currently holds.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    # Validate before authenticating, so a bad option combination reports as a usage error rather than as a
    # login failure.
    _validate_times(args)
    season_id = resolve_season_id(ctx, args.season_id)
    game_id = str(args.game_id)
    session = _session(ctx)
    current = _current_game(session, season_id, game_id)
    start, end = _updated_window(args, current)
    attrs = current.data.attributes
    home_team, home_division, visitor_team, visitor_division = _updated_sides(args, current)
    location, scorekeeper_name, scorekeeper_phone, game_type = _updated_details(args, attrs)
    tz_name, tz_offset = resolve_time_zone(
        _pick(args.time_zone_name, attrs.time_zone_name),
        args.time_zone_offset,
    )

    updated = run_action_or_exit(
        session,
        _update_scheduled_game_action,
        season_id,
        game_id,
        start,
        end,
        home_team,
        home_division,
        visitor_team,
        visitor_division,
        location,
        scorekeeper_name,
        scorekeeper_phone,
        game_type,
        tz_name,
        tz_offset,
        _pick(args.number, attrs.number),
        attrs.status,
        _pick(args.broadcaster, attrs.data.broadcaster),
        _pick(args.home_label, attrs.data.home_label),
        _pick(args.visitor_label, attrs.data.visitor_label),
    )
    render_get_command(updated, args.output_format, args.output_path, args.fields_spec)


def run_get(ctx: Context, params: dict[str, Any]) -> None:
    """Show one scheduled game.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    _warn_teams_only(params)
    season_id = resolve_season_id(ctx, args.season_id)
    game = run_action_or_exit(
        _session(ctx),
        _get_scheduled_game_action,
        season_id,
        str(args.game_id),
    )
    render_get_command(game, args.output_format, args.output_path, args.fields_spec)


def run_list(ctx: Context, params: dict[str, Any]) -> None:
    """List the season's scheduled games.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    _warn_teams_only(params)
    season_id = resolve_season_id(ctx, args.season_id)
    games = run_action_or_exit(
        _session(ctx),
        _list_scheduled_action,
        season_id,
    )
    render_list_command(games, args.output_format, args.output_path, args.columns_spec)


def run_delete(ctx: Context, params: dict[str, Any]) -> None:
    """Delete a scheduled game and report the outcome.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    game_id = str(args.game_id)
    season_id = resolve_season_id(ctx, args.season_id)
    run_action_or_exit(
        _session(ctx),
        _delete_scheduled_game_action,
        season_id,
        game_id,
    )
    if args.output_format in {"json", "yaml"}:
        result = {"success": True, "id": game_id, "message": f"Successfully deleted game {game_id}"}
        render_get_command(result, args.output_format, args.output_path, args.fields_spec)
    else:
        click.secho(f"Successfully deleted scheduled game {game_id}", fg="green")


__all__ = [
    "resolve_season_id",
    "run_create",
    "run_delete",
    "run_get",
    "run_list",
    "run_update",
]
