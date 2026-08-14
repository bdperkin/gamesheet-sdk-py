# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Credential resolution for login flows.

Provides helpers that resolve an email address and password from explicit arguments, environment variables
(via :class:`~gamesheet_sdk.common.config.Config`), or interactive prompts.  Both
:mod:`~gamesheet_sdk.common.auth.login` (admin) and :mod:`~gamesheet_sdk.teams.login` (teams) delegate to
these functions so the fallback logic lives in one place.

The two resolvers are intentionally kept as separate functions — bundling email and password into a shared
return value trips CodeQL's data-flow analyzer into flagging downstream ``email`` log calls as clear-text
password logging.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gamesheet_sdk.common.exceptions import AuthenticationError

if TYPE_CHECKING:
    from gamesheet_sdk.common.config import Config


def resolve_email(cfg: Config, email: str | None) -> str:
    """Resolve the login email from explicit argument or config.

    Falls through: explicit ``email`` argument → ``GAMESHEET_USERNAME`` env var → ``Config.username``.

    Args:
        cfg (Config): Configuration object containing username from env/defaults.
        email (str | None): Explicit email address, or ``None`` to fall back to config.

    Returns:
        str: The resolved email address.

    Raises:
        AuthenticationError: If no email is available from any source.

    """
    if email is None:
        email = cfg.username

    if not email:
        _err_msg = "Login requires an email. Pass it explicitly or set GAMESHEET_USERNAME."
        raise AuthenticationError(_err_msg)

    return email


def resolve_password(cfg: Config, password: str | None) -> str:
    """Resolve the login password from explicit argument or config.

    Falls through: explicit ``password`` argument → ``GAMESHEET_PASSWORD`` env var → ``Config.password``.

    Args:
        cfg (Config): Configuration object containing password from env/defaults.
        password (str | None): Explicit password, or ``None`` to fall back to config.

    Returns:
        str: The resolved password string.

    Raises:
        AuthenticationError: If no password is available from any source.

    """
    if password is None and cfg.password is not None:
        password = cfg.password.get_secret_value()

    if not password:
        _err_msg = "Login requires a password. Pass it explicitly or set GAMESHEET_PASSWORD."
        raise AuthenticationError(_err_msg)

    return password
