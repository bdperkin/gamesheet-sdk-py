# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Teams-side execution of the unified game option set.

The ``gamesheet-teams schedule games`` commands are thin: they declare the shared option set from
:mod:`gamesheet_sdk.common.cli.game_options` — the same set ``gamesheet-admin games`` declares — and hand
their collected parameters here, which translates them into the teams gateway calls in
:mod:`gamesheet_sdk.teams.schedule`.

``--association-id`` and ``--league-id`` are deliberately absent from the option set even though the gateway
payload carries both: they are wholly determined by ``--season-id``, so this module derives them from
``GET /api/seasons`` rather than asking for values ``gamesheet-admin`` has no equivalent for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import rich_click as click
from rich_click import Context

from gamesheet_sdk.common.cli.game_options import (
    GameArgs,
    explicit_side_flag,
    parse_game_args,
    sides_from_params,
    warn_unsupported_options,
)
from gamesheet_sdk.common.cli.game_times import (
    resolve_game_window,
    resolve_time_zone,
    validate_game_time_inputs,
)
from gamesheet_sdk.common.cli.rendering import (
    render_get_command,
    render_list_command,
)
from gamesheet_sdk.teams.cli.commands.schedule.helpers import (
    format_teams_window,
    resolve_game_update_times,
)
from gamesheet_sdk.teams.cli.helpers import (
    build_authenticated_session,
    run_action_or_exit,
)
from gamesheet_sdk.teams.schedule import (
    _fetch_and_normalize_game_dict,
    validate_game_type,
)
from gamesheet_sdk.teams.schedule import (
    create_game as _create_game_action,
)
from gamesheet_sdk.teams.schedule import (
    delete_game as _delete_game_action,
)
from gamesheet_sdk.teams.schedule import (
    get_game as _get_game_action,
)
from gamesheet_sdk.teams.schedule import (
    list_games as _list_games_action,
)
from gamesheet_sdk.teams.schedule import (
    update_game as _update_game_action,
)
from gamesheet_sdk.teams.seasons import get_season_ownership as _get_season_ownership_action

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config
    from gamesheet_sdk.teams.seasons import SeasonOwnership
    from gamesheet_sdk.teams.session import TeamsAuthenticatedSession

CLI_NAME = "gamesheet-teams"


def _warn_admin_only(args: GameArgs) -> None:
    """Warn about admin-only options the teams gateway payload has no field for.

    Args:
        args (GameArgs): The parsed option set.

    """
    warn_unsupported_options(
        CLI_NAME,
        {"--home-label": args.home_label, "--visitor-label": args.visitor_label},
    )


def _ownership(
    session: TeamsAuthenticatedSession,
    season_id: str,
    timeout: float | None,
) -> SeasonOwnership:
    """Look up the association and league that own a season.

    Args:
        session (TeamsAuthenticatedSession): Authenticated session.
        season_id (str): Season identifier.
        timeout (float | None): Optional request timeout.

    Returns:
        SeasonOwnership: The season's association and league identifiers.

    """
    return run_action_or_exit(
        session,
        _get_season_ownership_action,
        season_id,
        timeout=timeout,
    )


def run_create(ctx: Context, params: dict[str, Any]) -> None:
    """Create a scheduled game from the unified option set.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    _warn_admin_only(args)
    sides = args.sides.require()
    times = args.times
    start_iso, end_iso = resolve_game_window(
        times.start_datetime,
        times.start_date,
        times.start_time,
        times.end_datetime,
        times.end_date,
        times.end_time,
        times.duration,
    )
    start, end = format_teams_window(start_iso, end_iso)
    tz_name, tz_offset = resolve_time_zone(args.time_zone_name, args.time_zone_offset)

    config: Config = ctx.obj
    session = build_authenticated_session(config)
    season_id = str(args.season_id)
    owner = _ownership(session, season_id, config.timeout)

    created = run_action_or_exit(
        session,
        _create_game_action,
        sides.team_id,
        season_id,
        sides.division_id,
        sides.opposing_team_id,
        start,
        end,
        home_flag=sides.home_flag,
        opposing_division=sides.opposing_division_id,
        association_id=owner.association_id,
        league_id=owner.league_id,
        game_number=str(args.number),
        game_type=str(args.game_type),
        location=args.location or "",
        scorekeeper_name=args.scorekeeper_name or "",
        scorekeeper_phone=args.scorekeeper_phone or "",
        broadcast_provider=args.broadcaster or "",
        time_zone_name=tz_name,
        time_zone_offset=tz_offset,
        timeout=config.timeout,
    )
    render_get_command(created, args.output_format, args.output_path, args.columns_spec)


def _current_game(
    session: TeamsAuthenticatedSession,
    game_id: str,
    timeout: float | None,
) -> dict[str, Any]:
    """Read the game an update is about to modify.

    Args:
        session (TeamsAuthenticatedSession): Authenticated session.
        game_id (str): Game identifier.
        timeout (float | None): Optional request timeout.

    Returns:
        dict[str, Any]: The gateway's normalized game dictionary.

    """
    return run_action_or_exit(
        session,
        _fetch_and_normalize_game_dict,
        game_id,
        timeout=timeout,
    )


def _current_window(game_dict: dict[str, Any]) -> tuple[str | None, str | None]:
    """Extract the game's current start and end.

    Args:
        game_dict (dict[str, Any]): The gateway's normalized game dictionary.

    Returns:
        tuple[str | None, str | None]: The current ``(start, end)`` pair as the gateway reports it.

    """
    start = game_dict.get("date_time") or game_dict.get("startDate")
    end = game_dict.get("end_time") or game_dict.get("endTime")
    return (
        str(start) if start is not None else None,
        str(end) if end is not None else None,
    )


def _current_team_id(game_dict: dict[str, Any]) -> str | None:
    """Extract the acting team the game is currently attached to.

    The gateway's ``PUT /api/schedule-game/{id}`` drops fields that are absent, so an update that does not
    name a team resends the current one rather than leaving the association to chance.

    Args:
        game_dict (dict[str, Any]): The gateway's normalized game dictionary.

    Returns:
        str | None: The current team identifier, or ``None`` if the gateway did not report one.

    """
    raw = game_dict.get("team_id") or game_dict.get("teamId")
    return None if raw is None else str(raw)


def _current_home_flag(game_dict: dict[str, Any]) -> bool:
    """Extract which side the acting team is currently on.

    This is what makes ``--home-team-id`` mean the right thing on an update that does not restate the side:
    the absolute names are mapped onto the gateway's relative ones using the game's existing orientation
    rather than a blanket "home" assumption.

    Args:
        game_dict (dict[str, Any]): The gateway's normalized game dictionary.

    Returns:
        bool: ``True`` when the acting team is currently the home team; ``True`` when unknown.

    """
    raw = game_dict.get("home_flag")
    if raw is None:
        return True

    return bool(raw)


def _update_time_zone(args: GameArgs) -> tuple[str | None, int | None]:
    """Resolve the time zone to send on update, leaving it untouched when unspecified.

    Args:
        args (GameArgs): The parsed option set.

    Returns:
        tuple[str | None, int | None]: The ``(name, offset)`` pair, or ``(None, None)``.

    """
    if args.time_zone_name is None and args.time_zone_offset is None:
        return None, None

    return resolve_time_zone(args.time_zone_name, args.time_zone_offset)


def _updated_owner_ids(
    session: TeamsAuthenticatedSession,
    args: GameArgs,
    timeout: float | None,
) -> tuple[str | None, str | None]:
    """Derive association and league for an update, only when a new season was given.

    Args:
        session (TeamsAuthenticatedSession): Authenticated session.
        args (GameArgs): The parsed option set.
        timeout (float | None): Optional request timeout.

    Returns:
        tuple[str | None, str | None]: The ``(association_id, league_id)`` pair, or ``(None, None)``.

    """
    if args.season_id is None:
        return None, None

    owner = _ownership(session, args.season_id, timeout)
    return owner.association_id, owner.league_id


def run_update(ctx: Context, params: dict[str, Any]) -> None:
    """Update a scheduled game from the unified option set.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    _warn_admin_only(args)
    # Validate before authenticating, so a bad option combination reports as a usage error rather than as a
    # login failure.
    times = args.times
    validate_game_time_inputs(
        times.start_datetime,
        times.start_date,
        times.start_time,
        times.end_datetime,
        times.end_date,
        times.end_time,
    )
    if args.game_type is not None:
        validate_game_type(args.game_type)

    config: Config = ctx.obj
    session = build_authenticated_session(config)
    game_id = str(args.game_id)
    game_dict = _current_game(session, game_id, config.timeout)
    current_start, current_end = _current_window(game_dict)
    sides = sides_from_params(params, default_home=_current_home_flag(game_dict))
    start, end = resolve_game_update_times(
        start_date_time=times.start_datetime,
        start_date=times.start_date,
        start_time=times.start_time,
        end_date_time=times.end_datetime,
        end_date=times.end_date,
        end_time=times.end_time,
        duration=times.duration,
        current_date_time=current_start,
        current_end_time=current_end,
    )
    tz_name, tz_offset = _update_time_zone(args)
    association_id, league_id = _updated_owner_ids(session, args, config.timeout)

    result = run_action_or_exit(
        session,
        _update_game_action,
        game_id,
        team_id=sides.team_id or _current_team_id(game_dict),
        season_id=args.season_id,
        division_id=sides.division_id,
        opposing_team_id=sides.opposing_team_id,
        opposing_division=sides.opposing_division_id,
        association_id=association_id,
        league_id=league_id,
        home_flag=explicit_side_flag(params),
        date_time=start,
        end_time=end,
        game_number=args.number,
        game_type=args.game_type,
        location=args.location,
        scorekeeper_name=args.scorekeeper_name,
        scorekeeper_phone=args.scorekeeper_phone,
        broadcast_provider=args.broadcaster,
        time_zone_name=tz_name,
        time_zone_offset=tz_offset,
        timeout=config.timeout,
    )
    render_get_command(result, args.output_format, args.output_path, args.columns_spec)


def run_get(ctx: Context, params: dict[str, Any]) -> None:
    """Show one scheduled game.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    game_detail = run_action_or_exit(
        session,
        _get_game_action,
        str(args.game_id),
        include_availability=bool(params.get("include_availability")),
        team_id=params.get("team_id"),
        timeout=config.timeout,
    )
    render_get_command(game_detail, args.output_format, args.output_path, args.columns_spec)


def run_list(ctx: Context, params: dict[str, Any]) -> None:
    """List a team's scheduled games.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    games = run_action_or_exit(
        session,
        _list_games_action,
        params.get("team_id"),
        month=params.get("month", "all"),
        include_event_data=bool(params.get("include_event_data")),
        timeout=config.timeout,
    )
    render_list_command(games, args.output_format, args.output_path, args.columns_spec)


def run_delete(ctx: Context, params: dict[str, Any]) -> None:
    """Delete a scheduled game and report the outcome.

    Args:
        ctx (Context): Click context object.
        params (dict[str, Any]): The command's collected parameters.

    """
    args = parse_game_args(params)
    config: Config = ctx.obj
    session = build_authenticated_session(config)
    game_id = str(args.game_id)
    result = run_action_or_exit(
        session,
        _delete_game_action,
        game_id,
        timeout=config.timeout,
    )
    if args.output_format in {"json", "yaml"}:
        render_get_command(result, args.output_format, args.output_path, args.columns_spec)
    else:
        click.echo(f"Successfully deleted game {game_id}")


__all__ = [
    "run_create",
    "run_delete",
    "run_get",
    "run_list",
    "run_update",
]
