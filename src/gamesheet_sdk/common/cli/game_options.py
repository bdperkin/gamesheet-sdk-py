# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""The unified game option set shared by ``gamesheet-admin games`` and ``gamesheet-teams schedule games``.

The two command trees drive different backends — a JSON:API season schedule for admin, the teams gateway's
``/api/schedule-game`` for teams — but expose one option vocabulary, so a command line written for either CLI
runs unchanged on the other.

The two backends disagree on how a game's two teams are named. admin names them **absolutely**, as
``--home-team-id`` / ``--visitor-team-id`` and their divisions. teams names them **relative to "my" team**,
as ``--team-id`` / ``--opposing-team-id`` plus a side flag — ``--home`` / ``--visitor``, spelled ``--away``
on ``update`` — saying which side that team is on.

Both spellings are accepted by both CLIs. :func:`resolve_game_sides` translates whichever was given into
:class:`GameSides`, which carries the absolute pair plus the ``home_flag`` each backend needs. These are
therefore equivalent everywhere::

    --home-team-id 10 --visitor-team-id 20
    --team-id 10 --opposing-team-id 20 --home
    --team-id 20 --opposing-team-id 10 --visitor

Naming the same side twice with different values is a usage error.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, TypeVar

import rich_click as click

from gamesheet_sdk.common.cli.game_constants import (
    ADMIN_ONLY_SUFFIX,
    BROADCASTER_HELP,
    DURATION_HELP,
    FLEXIBLE_DATETIME_HELP,
    GAME_TYPE_HELP,
    IANA_TIMEZONE_HELP_TEXT,
    LOCATION_HELP,
    SPLIT_DATE_HELP,
    SPLIT_TIME_HELP,
    TIMEZONE_OFFSET_HELP_TEXT,
)

F = TypeVar("F", bound=Callable[..., Any])

#: Absolute spelling of each side, and the relative spelling that fills the same slot.
_TEAM_NAMES: Final[dict[str, str]] = {
    "home": "--home-team-id",
    "visitor": "--visitor-team-id",
    "mine": "--team-id",
    "opposing": "--opposing-team-id",
}
_DIVISION_NAMES: Final[dict[str, str]] = {
    "home": "--home-division-id",
    "visitor": "--visitor-division-id",
    "mine": "--division-id",
    "opposing": "--opposing-division-id",
}

#: ``GameSides`` field to the pair of spellings that can fill it, for ``create``'s error message.
_REQUIRED_SIDE_FIELDS: Final[tuple[tuple[str, str], ...]] = (
    ("home_team_id", f"{_TEAM_NAMES['home']}/{_TEAM_NAMES['mine']}"),
    ("home_division_id", f"{_DIVISION_NAMES['home']}/{_DIVISION_NAMES['mine']}"),
    ("visitor_team_id", f"{_TEAM_NAMES['visitor']}/{_TEAM_NAMES['opposing']}"),
    ("visitor_division_id", f"{_DIVISION_NAMES['visitor']}/{_DIVISION_NAMES['opposing']}"),
)


@dataclass(frozen=True)
class RequiredGameSides:
    """A fully specified pair of sides, as ``create`` needs.

    Attributes:
        home_team_id (str): Home team identifier.
        home_division_id (str): Home team's division identifier.
        visitor_team_id (str): Visitor team identifier.
        visitor_division_id (str): Visitor team's division identifier.
        home_flag (bool): Whether the acting team (``--team-id``) is the home team.

    """

    home_team_id: str
    home_division_id: str
    visitor_team_id: str
    visitor_division_id: str
    home_flag: bool

    @property
    def team_id(self: RequiredGameSides) -> str:
        """The acting team's identifier.

        Returns:
            str: ``home_team_id`` when the acting team is home, else ``visitor_team_id``.

        """
        return self.home_team_id if self.home_flag else self.visitor_team_id

    @property
    def division_id(self: RequiredGameSides) -> str:
        """The acting team's division identifier.

        Returns:
            str: ``home_division_id`` when the acting team is home, else ``visitor_division_id``.

        """
        return self.home_division_id if self.home_flag else self.visitor_division_id

    @property
    def opposing_team_id(self: RequiredGameSides) -> str:
        """The opposing team's identifier.

        Returns:
            str: ``visitor_team_id`` when the acting team is home, else ``home_team_id``.

        """
        return self.visitor_team_id if self.home_flag else self.home_team_id

    @property
    def opposing_division_id(self: RequiredGameSides) -> str:
        """The opposing team's division identifier.

        Returns:
            str: ``visitor_division_id`` when the acting team is home, else ``home_division_id``.

        """
        return self.visitor_division_id if self.home_flag else self.home_division_id


@dataclass(frozen=True)
class GameSides:
    """A game's two teams, held absolutely, plus which side is the acting team.

    Attributes:
        home_team_id (str | None): Home team identifier.
        home_division_id (str | None): Home team's division identifier.
        visitor_team_id (str | None): Visitor team identifier.
        visitor_division_id (str | None): Visitor team's division identifier.
        home_flag (bool): Whether the acting team (``--team-id``) is the home team.

    """

    home_team_id: str | None
    home_division_id: str | None
    visitor_team_id: str | None
    visitor_division_id: str | None
    home_flag: bool

    @property
    def team_id(self: GameSides) -> str | None:
        """The acting team's identifier.

        Returns:
            str | None: ``home_team_id`` when the acting team is home, else ``visitor_team_id``.

        """
        return self.home_team_id if self.home_flag else self.visitor_team_id

    @property
    def division_id(self: GameSides) -> str | None:
        """The acting team's division identifier.

        Returns:
            str | None: ``home_division_id`` when the acting team is home, else ``visitor_division_id``.

        """
        return self.home_division_id if self.home_flag else self.visitor_division_id

    @property
    def opposing_team_id(self: GameSides) -> str | None:
        """The opposing team's identifier.

        Returns:
            str | None: ``visitor_team_id`` when the acting team is home, else ``home_team_id``.

        """
        return self.visitor_team_id if self.home_flag else self.home_team_id

    @property
    def opposing_division_id(self: GameSides) -> str | None:
        """The opposing team's division identifier.

        Returns:
            str | None: ``visitor_division_id`` when the acting team is home, else ``home_division_id``.

        """
        return self.visitor_division_id if self.home_flag else self.home_division_id

    def require(self: GameSides) -> RequiredGameSides:
        """Narrow to a :class:`RequiredGameSides`, rejecting any side left unspecified.

        Returns:
            RequiredGameSides: The same sides with every identifier known to be present.

        """
        _require_sides(self)
        return RequiredGameSides(
            home_team_id=str(self.home_team_id),
            home_division_id=str(self.home_division_id),
            visitor_team_id=str(self.visitor_team_id),
            visitor_division_id=str(self.visitor_division_id),
            home_flag=self.home_flag,
        )


def resolve_side_flag(*, home_flag: bool | None, away_flag: bool, default: bool = True) -> bool:
    """Collapse ``--home/--visitor`` and the ``--away`` alias into one boolean.

    Args:
        home_flag (bool | None): ``True`` for ``--home``, ``False`` for ``--visitor``, ``None`` if neither.
        away_flag (bool): Whether ``--away`` was given.
        default (bool): Value to use when neither flag was given. ``create`` leaves this at ``True``;
            ``update`` passes the game's current side so the absolute option names keep their meaning.

    Returns:
        bool: Whether the acting team is the home team.

    Raises:
        UsageError: If ``--home`` and ``--away`` are both given.

    """
    if away_flag and home_flag:
        msg = "Cannot combine --home with --away/--visitor."
        raise click.UsageError(msg)

    if away_flag:
        return False

    return default if home_flag is None else home_flag


def explicit_side_flag(params: Mapping[str, Any]) -> bool | None:
    """Return the side the user actually named, or ``None`` if they named none.

    ``update`` sends ``home_flag`` to the teams gateway only when it was explicitly given, so an update that
    does not mention a side leaves the game's existing side alone.

    Args:
        params (Mapping[str, Any]): The command's collected parameters.

    Returns:
        bool | None: ``True`` for ``--home``, ``False`` for ``--visitor``/``--away``, ``None`` for neither.

    """
    if params.get("away_flag"):
        return False

    home_flag = params.get("home_flag")
    return bool(home_flag) if home_flag is not None else None


def _merge_slot(
    absolute: str | None,
    relative: str | None,
    absolute_name: str,
    relative_name: str,
) -> str | None:
    """Reconcile the absolute and relative spellings of one side.

    Args:
        absolute (str | None): Value from the ``--home-*`` / ``--visitor-*`` spelling.
        relative (str | None): Value from the ``--team-id`` / ``--opposing-*`` spelling.
        absolute_name (str): Option name behind ``absolute``, for the error message.
        relative_name (str): Option name behind ``relative``, for the error message.

    Returns:
        str | None: The agreed value, or ``None`` if neither spelling was used.

    Raises:
        UsageError: If both spellings were used with different values.

    """
    if absolute is not None and relative is not None and absolute != relative:
        msg = (
            f"{absolute_name} ({absolute}) and {relative_name} ({relative}) both name the same team "
            "but disagree. Supply only one of them."
        )
        raise click.UsageError(msg)

    return absolute if absolute is not None else relative


def _resolve_pair(
    home_value: str | None,
    visitor_value: str | None,
    mine_value: str | None,
    opposing_value: str | None,
    names: Mapping[str, str],
    *,
    is_home: bool,
) -> tuple[str | None, str | None]:
    """Map the relative pair onto the absolute pair according to which side is acting.

    Args:
        home_value (str | None): Value from the ``--home-*`` option.
        visitor_value (str | None): Value from the ``--visitor-*`` option.
        mine_value (str | None): Value from the acting team's relative option.
        opposing_value (str | None): Value from the opposing team's relative option.
        names (Mapping[str, str]): Option names keyed ``home``/``visitor``/``mine``/``opposing``.
        is_home (bool): Whether the acting team is the home team.

    Returns:
        tuple[str | None, str | None]: The resolved ``(home, visitor)`` pair.

    """
    if is_home:
        home = _merge_slot(home_value, mine_value, names["home"], names["mine"])
        visitor = _merge_slot(visitor_value, opposing_value, names["visitor"], names["opposing"])
    else:
        home = _merge_slot(home_value, opposing_value, names["home"], names["opposing"])
        visitor = _merge_slot(visitor_value, mine_value, names["visitor"], names["mine"])

    return home, visitor


def _require_sides(sides: GameSides) -> None:
    """Reject a create whose home/visitor teams or divisions were not fully specified.

    Args:
        sides (GameSides): The resolved sides.

    Raises:
        UsageError: If any of the four identifiers is missing.

    """
    missing = [label for field, label in _REQUIRED_SIDE_FIELDS if getattr(sides, field) is None]
    if missing:
        msg = f"Missing required option(s): {', '.join(missing)}."
        raise click.UsageError(msg)


def resolve_game_sides(
    *,
    home_team_id: str | None,
    home_division_id: str | None,
    visitor_team_id: str | None,
    visitor_division_id: str | None,
    team_id: str | None,
    division_id: str | None,
    opposing_team_id: str | None,
    opposing_division_id: str | None,
    home_flag: bool | None,
    away_flag: bool = False,
    default_home: bool = True,
) -> GameSides:
    """Translate whichever team-naming spelling was used into a single :class:`GameSides`.

    Args:
        home_team_id (str | None): ``--home-team-id``.
        home_division_id (str | None): ``--home-division-id``.
        visitor_team_id (str | None): ``--visitor-team-id``.
        visitor_division_id (str | None): ``--visitor-division-id``.
        team_id (str | None): ``--team-id``, the acting team.
        division_id (str | None): ``--division-id``, the acting team's division.
        opposing_team_id (str | None): ``--opposing-team-id``.
        opposing_division_id (str | None): ``--opposing-division-id`` / ``--opposing-division``.
        home_flag (bool | None): ``--home`` / ``--visitor``.
        away_flag (bool): ``--away``, an alias for ``--visitor``.
        default_home (bool): Which side to assume when no side flag was given.

    Returns:
        GameSides: The resolved sides.

    """
    is_home = resolve_side_flag(home_flag=home_flag, away_flag=away_flag, default=default_home)
    resolved_home_team, resolved_visitor_team = _resolve_pair(
        home_team_id,
        visitor_team_id,
        team_id,
        opposing_team_id,
        _TEAM_NAMES,
        is_home=is_home,
    )
    resolved_home_division, resolved_visitor_division = _resolve_pair(
        home_division_id,
        visitor_division_id,
        division_id,
        opposing_division_id,
        _DIVISION_NAMES,
        is_home=is_home,
    )
    return GameSides(
        home_team_id=resolved_home_team,
        home_division_id=resolved_home_division,
        visitor_team_id=resolved_visitor_team,
        visitor_division_id=resolved_visitor_division,
        home_flag=is_home,
    )


@dataclass(frozen=True)
class GameTimeArgs:
    """The seven start/end/duration inputs, straight off the command line.

    Attributes:
        start_datetime (str | None): ``--start-datetime`` / ``--start-date-time`` / ``--start``.
        start_date (str | None): ``--start-date`` / ``--date``.
        start_time (str | None): ``--start-time``.
        end_datetime (str | None): ``--end-datetime`` / ``--end-date-time`` / ``--end``.
        end_date (str | None): ``--end-date``.
        end_time (str | None): ``--end-time``.
        duration (str | None): ``--duration``, in any accepted spelling.

    """

    start_datetime: str | None
    start_date: str | None
    start_time: str | None
    end_datetime: str | None
    end_date: str | None
    end_time: str | None
    duration: str | None


@dataclass(frozen=True)
class GameArgs:
    """A typed view over the unified game option set.

    The game commands take ``**params`` rather than three dozen named parameters, and turn it into one of
    these. Every field is optional at this level; ``create`` enforces its own requirements via
    :meth:`GameSides.require` and click's ``required=``.

    Attributes:
        sides (GameSides): The resolved home/visitor pair.
        times (GameTimeArgs): The raw start/end/duration inputs.
        season_id (str | None): ``--season-id``.
        game_id (str | None): ``--game-id`` / ``-g`` / ``--id``.
        number (str | None): ``--number`` / ``--game-number``.
        game_type (str | None): ``--game-type``.
        location (str | None): ``--location``.
        scorekeeper_name (str | None): ``--scorekeeper-name``.
        scorekeeper_phone (str | None): ``--scorekeeper-phone``.
        broadcaster (str | None): ``--broadcaster`` / ``--broadcast-provider``.
        time_zone_name (str | None): ``--time-zone-name`` / ``--timezone``.
        time_zone_offset (int | None): ``--time-zone-offset``.
        home_label (str | None): ``--home-label``; admin-only.
        visitor_label (str | None): ``--visitor-label``; admin-only.
        output_format (str): ``--format`` / ``-F``.
        output_path (str | None): ``--output`` / ``-o``.
        columns_spec (str | None): ``--columns`` / ``-c``.

    """

    sides: GameSides
    times: GameTimeArgs
    season_id: str | None
    game_id: str | None
    number: str | None
    game_type: str | None
    location: str | None
    scorekeeper_name: str | None
    scorekeeper_phone: str | None
    broadcaster: str | None
    time_zone_name: str | None
    time_zone_offset: int | None
    home_label: str | None
    visitor_label: str | None
    output_format: str
    output_path: str | None
    columns_spec: str | None


def _parse_time_args(params: Mapping[str, Any]) -> GameTimeArgs:
    """Collect the time options out of the raw click params.

    Args:
        params (Mapping[str, Any]): The command's collected parameters.

    Returns:
        GameTimeArgs: The time inputs.

    """
    return GameTimeArgs(
        start_datetime=params.get("start_datetime"),
        start_date=params.get("start_date"),
        start_time=params.get("start_time"),
        end_datetime=params.get("end_datetime"),
        end_date=params.get("end_date"),
        end_time=params.get("end_time"),
        duration=params.get("duration"),
    )


def sides_from_params(params: Mapping[str, Any], *, default_home: bool = True) -> GameSides:
    """Collect and resolve the side options out of the raw click params.

    Args:
        params (Mapping[str, Any]): The command's collected parameters.
        default_home (bool): Which side to assume when no side flag was given.

    Returns:
        GameSides: The resolved sides.

    """
    return resolve_game_sides(
        home_team_id=params.get("home_team_id"),
        home_division_id=params.get("home_division_id"),
        visitor_team_id=params.get("visitor_team_id"),
        visitor_division_id=params.get("visitor_division_id"),
        team_id=params.get("team_id"),
        division_id=params.get("division_id"),
        opposing_team_id=params.get("opposing_team_id"),
        opposing_division_id=params.get("opposing_division_id"),
        home_flag=params.get("home_flag"),
        away_flag=bool(params.get("away_flag")),
        default_home=default_home,
    )


def parse_game_args(params: Mapping[str, Any]) -> GameArgs:
    """Turn a game command's collected click parameters into a :class:`GameArgs`.

    Args:
        params (Mapping[str, Any]): The command's collected parameters.

    Returns:
        GameArgs: The typed view.

    """
    return GameArgs(
        sides=sides_from_params(params),
        times=_parse_time_args(params),
        season_id=params.get("season_id"),
        game_id=params.get("game_id"),
        number=params.get("number"),
        game_type=params.get("game_type"),
        location=params.get("location"),
        scorekeeper_name=params.get("scorekeeper_name"),
        scorekeeper_phone=params.get("scorekeeper_phone"),
        broadcaster=params.get("broadcaster"),
        time_zone_name=params.get("time_zone_name"),
        time_zone_offset=params.get("time_zone_offset"),
        home_label=params.get("home_label"),
        visitor_label=params.get("visitor_label"),
        output_format=params.get("output_format", "simple"),
        output_path=params.get("output_path"),
        columns_spec=params.get("columns_spec"),
    )


def warn_unsupported_options(cli_name: str, ignored: Mapping[str, object]) -> None:
    """Warn on stderr for options this backend cannot send, then carry on.

    The unified option set is deliberately wider than either backend's payload so that a command line stays
    portable. Anything the receiving backend has no field for is dropped with a warning rather than an error,
    and the exit status is unaffected.

    Args:
        cli_name (str): The CLI the caller is running as, e.g. ``'gamesheet-teams'``.
        ignored (Mapping[str, object]): Option name to supplied value. Falsy values are not reported.

    """
    for name, value in ignored.items():
        if value:
            click.secho(
                f"Warning: {name} is not supported by `{cli_name}` and was ignored.",
                fg="yellow",
                err=True,
            )


def requiredness(*, required: bool) -> dict[str, Any]:
    """Build the ``required``/``default`` keyword pair for an option.

    **Gotcha worth preserving:** click 8.4.2 silently ignores ``required=True`` when ``default=None`` is also
    passed explicitly — the option simply arrives as ``None`` and the body runs. Passing no ``default`` at
    all is not the same thing as passing ``default=None``, even though click's implicit default *is*
    ``None``. So a required option must omit the key entirely.

    Args:
        required (bool): Whether the option is mandatory.

    Returns:
        dict[str, Any]: Keyword arguments to splat into :func:`click.option`.

    """
    return {"required": True} if required else {"required": False, "default": None}


def _apply(func: F, options: Sequence[Callable[[F], F]]) -> F:
    """Apply option decorators so their declaration order is their ``--help`` order.

    Args:
        func (F): The command function to decorate.
        options (Sequence[Callable[[F], F]]): Option decorators, in the desired help order.

    Returns:
        F: The decorated command function.

    """
    for option in reversed(options):
        func = option(func)

    return func


def game_time_options(func: F) -> F:
    """Add the seven start/end/duration options both CLIs accept.

    Args:
        func (F): The command function to decorate.

    Returns:
        F: The decorated command function.

    """
    return _apply(
        func,
        [
            click.option(
                "--start-datetime",
                "--start-date-time",
                "--start",
                "start_datetime",
                type=str,
                default=None,
                help=(
                    f"Start date and time. {FLEXIBLE_DATETIME_HELP} "
                    "Mutually exclusive with --start-date/--start-time."
                ),
            ),
            click.option(
                "--end-datetime",
                "--end-date-time",
                "--end",
                "end_datetime",
                type=str,
                default=None,
                help=(
                    f"End date and time. {FLEXIBLE_DATETIME_HELP} "
                    "Mutually exclusive with --end-date/--end-time."
                ),
            ),
            click.option(
                "--start-date",
                "--date",
                "start_date",
                type=str,
                default=None,
                help=f"Start {SPLIT_DATE_HELP} Also supplies the end date unless --end-date is given.",
            ),
            click.option(
                "--start-time",
                "start_time",
                type=str,
                default=None,
                help=f"Start {SPLIT_TIME_HELP} Use with --start-date/--date.",
            ),
            click.option(
                "--end-date",
                "end_date",
                type=str,
                default=None,
                help=f"End {SPLIT_DATE_HELP} Defaults to the start date.",
            ),
            click.option(
                "--end-time",
                "end_time",
                type=str,
                default=None,
                help=f"End {SPLIT_TIME_HELP} Lands on the start date unless --end-date is given.",
            ),
            click.option(
                "--duration",
                type=str,
                default=None,
                help=DURATION_HELP,
            ),
        ],
    )


def _absolute_side_options() -> list[Callable[[F], F]]:
    """Build the ``--home-*`` / ``--visitor-*`` option decorators.

    Returns:
        list[Callable[[F], F]]: Option decorators in help order.

    """
    return [
        click.option(
            "--home-team-id",
            type=str,
            default=None,
            help="Home team identifier.",
        ),
        click.option(
            "--home-division-id",
            type=str,
            default=None,
            help="Home team division identifier.",
        ),
        click.option(
            "--visitor-team-id",
            type=str,
            default=None,
            help="Visitor team identifier.",
        ),
        click.option(
            "--visitor-division-id",
            type=str,
            default=None,
            help="Visitor team division identifier.",
        ),
    ]


def _relative_side_options() -> list[Callable[[F], F]]:
    """Build the ``--team-id`` / ``--opposing-*`` option decorators and the side flags.

    Returns:
        list[Callable[[F], F]]: Option decorators in help order.

    """
    return [
        click.option(
            "--team-id",
            "-t",
            type=str,
            envvar="GAMESHEET_TEAM_ID",
            default=None,
            help="Acting team identifier. Home unless --visitor/--away is given.",
        ),
        click.option(
            "--division-id",
            type=str,
            envvar="GAMESHEET_DIVISION_ID",
            default=None,
            help="Acting team's division identifier.",
        ),
        click.option(
            "--opposing-team-id",
            type=str,
            default=None,
            help="Opposing team identifier.",
        ),
        click.option(
            "--opposing-division-id",
            "--opposing-division",
            "opposing_division_id",
            type=str,
            default=None,
            help="Opposing team's division identifier.",
        ),
        click.option(
            "--home/--visitor",
            "home_flag",
            default=None,
            help="Which side --team-id is on.  [default: --home]",
        ),
        click.option(
            "--away",
            "away_flag",
            is_flag=True,
            default=False,
            help="Alias for --visitor.",
        ),
    ]


def game_side_options(func: F) -> F:
    """Add both spellings of the home/visitor team and division options.

    Requiredness is enforced by :func:`resolve_game_sides`, not by click, because each side has two accepted
    spellings and click can only require one option at a time.

    Args:
        func (F): The command function to decorate.

    Returns:
        F: The decorated command function.

    """
    return _apply(func, [*_absolute_side_options(), *_relative_side_options()])


def _detail_options(*, required: bool) -> list[Callable[[F], F]]:
    """Build the detail option decorators.

    Args:
        required (bool): Whether ``--game-type`` and ``--number`` are mandatory.

    Returns:
        list[Callable[[F], F]]: Option decorators in help order.

    """
    return [
        click.option(
            "--number",
            "--game-number",
            "number",
            type=str,
            help="Game number.",
            **requiredness(required=required),
        ),
        click.option(
            "--game-type",
            type=str,
            help=GAME_TYPE_HELP,
            **requiredness(required=required),
        ),
        click.option("--location", type=str, default=None, help=LOCATION_HELP),
        click.option("--scorekeeper-name", type=str, default=None, help="Scorekeeper's full name."),
        click.option("--scorekeeper-phone", type=str, default=None, help="Scorekeeper's phone number."),
        click.option(
            "--broadcaster",
            "--broadcast-provider",
            "broadcaster",
            type=str,
            default=None,
            help=BROADCASTER_HELP,
        ),
        click.option(
            "--time-zone-name",
            "--timezone",
            "time_zone_name",
            type=str,
            default=None,
            help=f"{IANA_TIMEZONE_HELP_TEXT}. Defaults to the system timezone.",
        ),
        click.option(
            "--time-zone-offset",
            type=int,
            default=None,
            help=f"{TIMEZONE_OFFSET_HELP_TEXT}. Defaults to the system timezone offset.",
        ),
        click.option(
            "--home-label",
            type=str,
            default=None,
            help=f"Home team label override. {ADMIN_ONLY_SUFFIX}",
        ),
        click.option(
            "--visitor-label",
            type=str,
            default=None,
            help=f"Visitor team label override. {ADMIN_ONLY_SUFFIX}",
        ),
    ]


def game_detail_options(*, required: bool) -> Callable[[F], F]:
    """Build the decorator adding the non-time, non-side game options.

    Args:
        required (bool): Whether ``--game-type`` and ``--number`` are mandatory, as they are on ``create``.

    Returns:
        Callable[[F], F]: The option decorator.

    """

    def decorator(func: F) -> F:
        """Apply the detail options to ``func``.

        Args:
            func (F): The command function to decorate.

        Returns:
            F: The decorated command function.

        """
        return _apply(func, _detail_options(required=required))

    return decorator


def season_id_option(*, required: bool) -> Callable[[F], F]:
    """Build the ``--season-id`` decorator.

    Args:
        required (bool): Whether the option is mandatory. ``gamesheet-admin`` passes ``False`` because the
            value may instead come from the ``games`` group.

    Returns:
        Callable[[F], F]: The option decorator.

    """

    def decorator(func: F) -> F:
        """Apply the ``--season-id`` option to ``func``.

        Args:
            func (F): The command function to decorate.

        Returns:
            F: The decorated command function.

        """
        return click.option(
            "--season-id",
            type=str,
            envvar="GAMESHEET_SEASON_ID",
            help="Season identifier.",
            **requiredness(required=required),
        )(func)

    return decorator


def game_id_option(func: F) -> F:
    """Add the ``--game-id`` option under all three accepted spellings.

    Args:
        func (F): The command function to decorate.

    Returns:
        F: The decorated command function.

    """
    return click.option(
        "--game-id",
        "-g",
        "--id",
        "game_id",
        type=str,
        envvar="GAMESHEET_GAME_ID",
        required=True,
        help="Game identifier.",
    )(func)


__all__ = [
    "GameArgs",
    "GameSides",
    "GameTimeArgs",
    "RequiredGameSides",
    "explicit_side_flag",
    "game_detail_options",
    "game_id_option",
    "game_side_options",
    "game_time_options",
    "parse_game_args",
    "requiredness",
    "resolve_game_sides",
    "resolve_side_flag",
    "season_id_option",
    "sides_from_params",
    "warn_unsupported_options",
]
