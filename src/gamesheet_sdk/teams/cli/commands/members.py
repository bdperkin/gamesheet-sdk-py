# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Members CLI commands for GameSheet teams."""

from __future__ import annotations

import rich_click as click
from click.exceptions import Exit

from gamesheet_sdk.common.cli.core import ResourceGroup


@click.group(
    "members",
    cls=ResourceGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def members_group() -> None:
    """Manage team members, staff, followers, and invitations."""


@members_group.group(
    "invite",
    cls=ResourceGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def members_invite_group() -> None:
    """Invite staff or followers to the team."""


@members_invite_group.command("staff")
def members_invite_staff_command() -> None:
    r"""Invite team staff members.

    Send an invitation to join the team as a staff member.\f

    NOT YET IMPLEMENTED - Staff invitation support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: members invite staff is not yet implemented. "
        "Staff invitation support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)


@members_invite_group.command("follower")
def members_invite_follower_command() -> None:
    r"""Invite team followers.

    Send an invitation to follow the team.\f

    NOT YET IMPLEMENTED - Follower invitation support is planned for a future release.

    Raises:
        Exit: Always raised (exit code 1) because this command is not yet implemented.

    """
    click.secho(
        "Error: members invite follower is not yet implemented. "
        "Follower invitation support is planned for a future release.",
        fg="red",
        err=True,
    )
    raise Exit(1)
