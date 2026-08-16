# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Configuration for an SDK session.

Values are resolved by `pydantic-settings`_ in the following precedence:
1. Keyword arguments passed to :class:`Config`.
2. ``GAMESHEET_``-prefixed environment variables.
3. Built-in defaults defined on the model below.

A TOML config-file source is not loaded yet; it can be added later by overriding
``settings_customise_sources`` without changing the public API.

.. _pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from gamesheet_sdk.common.constants import DEFAULT_BASE_URL


def _default_session_path() -> Path:
    """Return the XDG-compliant default path for persisted session state."""
    xdg = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(xdg).expanduser() / "gamesheet-sdk-py" / "session.json"


def _default_browser_state_path() -> Path:
    """Return the XDG-compliant default path for Playwright storage state."""
    xdg = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(xdg).expanduser() / "gamesheet-sdk-py" / "browser-state.json"


class Config(BaseSettings, env_prefix="GAMESHEET_", extra="ignore"):
    """Resolved configuration for an SDK session.

    This class extends :class:`pydantic_settings.BaseSettings` to provide layered configuration resolution.
    Values are resolved in the following precedence order:

    1. Keyword arguments passed to the :class:`Config` constructor
    2. Environment variables prefixed with ``GAMESHEET_``
    3. Field defaults defined on the model

    All fields have sensible defaults, so you can instantiate an empty :class:`Config` for testing or override
    only the specific values you need.

    Attributes:
        base_url (str): Root URL of the GameSheet WebUI (the dashboard app)
        username (str | None): GameSheet account username/email
        password (SecretStr | None): GameSheet account password (stored as SecretStr)
        session_path (Path): Where to persist cookie state between runs
        timeout (float): Default per-request HTTP timeout in seconds (must be > 0)
        user_agent (str | None): Override the default User-Agent header sent by the Session
        verify_ssl (bool): Whether to verify TLS certificates on outgoing requests
        request_retries (int): Automatic retries on 5xx responses and connection errors
        browser_state_path (Path): Where to persist Playwright storage state between runs
        browser_headless (bool): Launch the Playwright browser in headless mode
    Examples:
        Create a default config that picks up environment variables:

        .. code-block:: python

            from gamesheet_sdk import Config

            # Reads GAMESHEET_USERNAME, GAMESHEET_PASSWORD, etc. if set
            config = Config()

        Override specific fields programmatically:

        .. code-block:: python

            from gamesheet_sdk import Config

            config = Config(
                username="user@example.com",
                timeout=60.0,
                browser_headless=False,
            )

        Use environment variables to configure the SDK:

        .. code-block:: bash

            export GAMESHEET_USERNAME="user@example.com"
            export GAMESHEET_PASSWORD="secret"  # pragma: allowlist secret
            export GAMESHEET_TIMEOUT="60.0"

        Then in Python:

        .. code-block:: python

            from gamesheet_sdk import Config

            config = Config()  # Picks up the env vars above
            print(config.username)  # "user@example.com"
            print(config.timeout)  # 60.0

    """

    base_url: str = Field(
        default=DEFAULT_BASE_URL,
        description="Root URL of the GameSheet WebUI (the dashboard app).",
    )
    username: str | None = Field(
        default=None,
        description="GameSheet account username/email.",
    )
    password: SecretStr | None = Field(
        default=None,
        description="GameSheet account password.",
    )
    session_path: Path = Field(
        default_factory=_default_session_path,
        description="Where to persist cookie state between runs.",
    )
    timeout: float = Field(
        default=30.0,
        description="Default per-request HTTP timeout in seconds.",
        gt=0,
    )
    user_agent: str | None = Field(
        default=None,
        description="Override the default User-Agent header sent by the Session.",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify TLS certificates on outgoing requests.",
    )
    request_retries: int = Field(
        default=3,
        description="Automatic retries on 5xx responses and connection errors.",
        ge=0,
    )
    browser_state_path: Path = Field(
        default_factory=_default_browser_state_path,
        description="Where to persist Playwright storage state between runs.",
    )
    browser_headless: bool = Field(
        default=True,
        description="Launch the Playwright browser in headless mode.",
    )
