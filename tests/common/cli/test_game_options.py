# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the unified game option set shared by both game command trees."""

from __future__ import annotations

from typing import Any

import pytest
import rich_click as click
from click.testing import CliRunner

from gamesheet_sdk.common.cli.game_options import (
    GameSides,
    explicit_side_flag,
    game_detail_options,
    parse_game_args,
    requiredness,
    resolve_side_flag,
    sides_from_params,
    warn_unsupported_options,
)

_SIDE_KEYS = (
    "home_team_id",
    "home_division_id",
    "visitor_team_id",
    "visitor_division_id",
    "team_id",
    "division_id",
    "opposing_team_id",
    "opposing_division_id",
    "home_flag",
)


def _sides(**overrides: Any) -> GameSides:
    """Resolve sides from the default-empty option set with the given overrides.

    Args:
        **overrides (Any): Option values to set.

    Returns:
        GameSides: The resolved sides.

    """
    params: dict[str, Any] = dict.fromkeys(_SIDE_KEYS)
    params.update(overrides)
    return sides_from_params(params)


def test_the_three_spellings_describe_the_same_game() -> None:
    """Absolute and relative naming resolve to the same home/visitor pair."""
    absolute = _sides(home_team_id="10", visitor_team_id="20")
    relative_home = _sides(team_id="10", opposing_team_id="20", home_flag=True)
    relative_visitor = _sides(team_id="20", opposing_team_id="10", home_flag=False)

    for sides in (absolute, relative_home, relative_visitor):
        assert sides.home_team_id == "10"
        assert sides.visitor_team_id == "20"

    assert relative_visitor.home_flag is False
    assert relative_visitor.team_id == "20"
    assert relative_visitor.opposing_team_id == "10"


def test_divisions_map_the_same_way_as_teams() -> None:
    """``--division-id``/``--opposing-division-id`` fill the home/visitor division slots by side."""
    sides = _sides(division_id="81419", opposing_division_id="81420", home_flag=False)
    assert sides.visitor_division_id == "81419"
    assert sides.home_division_id == "81420"
    assert sides.division_id == "81419"
    assert sides.opposing_division_id == "81420"


def test_naming_the_same_side_twice_with_different_values_is_a_usage_error() -> None:
    """Two spellings of one slot must agree."""
    with pytest.raises(click.UsageError, match="both name the same team but disagree"):
        _sides(home_team_id="10", team_id="99")


def test_naming_the_same_side_twice_with_equal_values_is_allowed() -> None:
    """Redundant but consistent naming is harmless."""
    assert _sides(home_team_id="10", team_id="10").home_team_id == "10"


def test_side_flag_defaults_and_conflicts() -> None:
    """``--away`` is an alias for ``--visitor`` and cannot be combined with ``--home``."""
    assert resolve_side_flag(home_flag=None, away_flag=False) is True
    assert resolve_side_flag(home_flag=None, away_flag=False, default=False) is False
    assert resolve_side_flag(home_flag=False, away_flag=False) is False
    assert resolve_side_flag(home_flag=None, away_flag=True) is False

    with pytest.raises(click.UsageError, match="Cannot combine --home with --away"):
        resolve_side_flag(home_flag=True, away_flag=True)


def test_away_alias_flips_the_side() -> None:
    """``--away`` reaches the resolver through the params mapping too."""
    sides = sides_from_params({"team_id": "20", "opposing_team_id": "10", "away_flag": True})
    assert sides.home_flag is False
    assert sides.home_team_id == "10"
    assert sides.visitor_team_id == "20"


def test_explicit_side_flag_reports_only_what_was_named() -> None:
    """``update`` needs to know whether the user restated the side at all."""
    assert explicit_side_flag({}) is None
    assert explicit_side_flag({"home_flag": True}) is True
    assert explicit_side_flag({"home_flag": False}) is False
    assert explicit_side_flag({"away_flag": True}) is False


def test_require_reports_every_missing_side() -> None:
    """``create`` names both accepted spellings of each missing identifier."""
    with pytest.raises(click.UsageError) as exc:
        _sides().require()

    message = str(exc.value)
    for expected in (
        "--home-team-id/--team-id",
        "--home-division-id/--division-id",
        "--visitor-team-id/--opposing-team-id",
        "--visitor-division-id/--opposing-division-id",
    ):
        assert expected in message


def test_require_narrows_a_complete_set() -> None:
    """A fully specified set narrows without error and keeps the relative view."""
    sides = _sides(
        home_team_id="10",
        home_division_id="1",
        visitor_team_id="20",
        visitor_division_id="2",
        home_flag=False,
    ).require()
    assert sides.team_id == "20"
    assert sides.division_id == "2"
    assert sides.opposing_team_id == "10"
    assert sides.opposing_division_id == "1"


def test_parse_game_args_defaults_missing_keys() -> None:
    """A sparse params mapping still yields a fully populated view."""
    args = parse_game_args({})
    assert args.season_id is None
    assert args.output_format == "simple"
    assert args.times.duration is None
    assert args.sides.home_flag is True


def test_warn_unsupported_options_reports_only_supplied_values() -> None:
    """Falsy values are silent; supplied ones warn on stderr without failing."""

    @click.command("x")
    def command() -> None:
        """Emit warnings for the sample option map."""
        warn_unsupported_options(
            "gamesheet-teams",
            {"--home-label": "Blue", "--visitor-label": None, "--other": ""},
        )

    result = CliRunner().invoke(command, [])
    assert result.exit_code == 0
    assert "--home-label is not supported by `gamesheet-teams`" in result.output
    assert "--visitor-label" not in result.output
    assert "--other" not in result.output


def test_requiredness_omits_default_when_required() -> None:
    """Click 8.4 ignores ``required=True`` when ``default=None`` is passed alongside it."""
    assert requiredness(required=True) == {"required": True}
    assert requiredness(required=False) == {"required": False, "default": None}


def test_required_detail_options_are_actually_enforced() -> None:
    """The requiredness helper is wired up, so a missing --game-type is a usage error."""

    @click.command("x")
    @game_detail_options(required=True)
    def command(**_params: Any) -> None:
        """Accept the detail option set."""

    result = CliRunner().invoke(command, ["--number", "1"])
    assert result.exit_code == 2

    result = CliRunner().invoke(command, ["--number", "1", "--game-type", "playoff"])
    assert result.exit_code == 0
