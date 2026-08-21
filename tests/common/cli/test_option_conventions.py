# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Cross-CLI short-flag and option-name conventions.

These walk both shipped click trees rather than any one command, so a new command that reintroduces a
second name for "show me a subset of keys", or rebinds ``-f``, fails here rather than in review.
"""

from __future__ import annotations

import rich_click as click

from gamesheet_sdk.admin.cli.main import cli as admin_cli
from gamesheet_sdk.teams.cli.main import cli as teams_cli

#: Short flags whose meaning is fixed across every command in both CLIs, as ``option -> parameter dest``.
RESERVED_SHORT_FLAGS = {
    "-f": "force",
    "-F": "output_format",
    "-o": "output_path",
}

#: Option names that must never come back; each duplicated something that already existed.
BANNED_OPTIONS = ("--fields",)


def _leaf_commands() -> list[tuple[str, click.Command]]:
    """Collect every leaf command in both CLI trees.

    Returns:
        list[tuple[str, click.Command]]: ``(dotted path, command)`` pairs.

    """
    found: list[tuple[str, click.Command]] = []

    def walk(cmd: click.Command, path: list[str]) -> None:
        """Recurse into groups, collecting leaves.

        Args:
            cmd (click.Command): The command or group to walk.
            path (list[str]): The command path leading here.

        """
        if isinstance(cmd, click.Group):
            for name in sorted(cmd.commands):
                walk(cmd.commands[name], [*path, name])

            return

        found.append((" ".join(path), cmd))

    walk(admin_cli, ["gamesheet-admin"])
    walk(teams_cli, ["gamesheet-teams"])
    return found


def _option_map(cmd: click.Command) -> dict[str, str]:
    """Map every spelling a command accepts to the parameter it fills.

    Args:
        cmd (click.Command): The command to inspect.

    Returns:
        dict[str, str]: Option spelling to parameter name.

    """
    names: dict[str, str] = {}
    for param in cmd.params:
        for opt in [*param.opts, *param.secondary_opts]:
            names[opt] = str(param.name)

    return names


def test_there_are_leaf_commands_to_check() -> None:
    """Guard against the walk silently finding nothing and the checks below passing vacuously."""
    assert len(_leaf_commands()) > 50


def test_reserved_short_flags_never_change_meaning() -> None:
    """``-f`` is always ``--force``; it used to mean ``--fields`` on most commands."""
    offenders = [
        f"{path}: {flag} means {_option_map(cmd)[flag]!r}, expected {dest!r}"
        for path, cmd in _leaf_commands()
        for flag, dest in RESERVED_SHORT_FLAGS.items()
        if flag in _option_map(cmd) and _option_map(cmd)[flag] != dest
    ]
    assert not offenders, "\n".join(offenders)


def test_banned_options_are_gone() -> None:
    """``--fields`` was a second spelling of ``--columns``; only ``--columns`` remains."""
    offenders = [
        f"{path}: {banned}"
        for path, cmd in _leaf_commands()
        for banned in BANNED_OPTIONS
        if banned in _option_map(cmd)
    ]
    assert not offenders, "\n".join(offenders)


def test_force_always_offers_its_short_flag() -> None:
    """Every destructive command takes ``-f`` as well as ``--force``."""
    offenders = [
        path
        for path, cmd in _leaf_commands()
        if "--force" in _option_map(cmd) and "-f" not in _option_map(cmd)
    ]
    assert not offenders, "\n".join(offenders)


def test_columns_always_offers_its_short_flag() -> None:
    """Every command that can subset its output takes ``-c`` as well as ``--columns``."""
    offenders = [
        path
        for path, cmd in _leaf_commands()
        if "--columns" in _option_map(cmd) and "-c" not in _option_map(cmd)
    ]
    assert not offenders, "\n".join(offenders)
