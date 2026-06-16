"""Configuration for an SDK session.

Values are resolved by `pydantic-settings`_ in the following precedence:
1. Keyword arguments passed to :class:`Config`.
2. ``GAMESHEET_``-prefixed environment variables.
3. Built-in defaults defined on the model below.
A TOML config-file source is not loaded yet; it can be added later by
overriding ``settings_customise_sources`` without changing the public API.
.. _pydantic-settings:
    https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from gamesheet_sdk.constants import DEFAULT_BASE_URL


def _default_session_path() -> Path:
    """Return the XDG-compliant default path for persisted session state.

    :returns: Path to session.json under XDG_CACHE_HOME or ~/.cache
    :rtype: Path
    """
    xdg = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(xdg).expanduser() / "gamesheet-sdk-py" / "session.json"


def _default_browser_state_path() -> Path:
    """Return the XDG-compliant default path for Playwright storage state.

    :returns: Path to browser-state.json under XDG_CACHE_HOME or ~/.cache
    :rtype: Path
    """
    xdg = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(xdg).expanduser() / "gamesheet-sdk-py" / "browser-state.json"


class Config(BaseSettings, env_prefix="GAMESHEET_", extra="ignore"):
    """Resolved configuration for an SDK session.

    This class extends :class:`pydantic_settings.BaseSettings` to provide
    layered configuration resolution. Values are resolved in the following
    precedence order:

    1. Keyword arguments passed to the :class:`Config` constructor
    2. Environment variables prefixed with ``GAMESHEET_``
    3. Field defaults defined on the model

    All fields have sensible defaults, so you can instantiate an empty
    :class:`Config` for testing or override only the specific values you need.

    :var base_url: Root URL of the GameSheet WebUI (the dashboard app)
    :vartype base_url: str
    :var username: GameSheet account username/email
    :vartype username: str | None
    :var password: GameSheet account password (stored as SecretStr)
    :vartype password: SecretStr | None
    :var session_path: Where to persist cookie state between runs
    :vartype session_path: Path
    :var timeout: Default per-request HTTP timeout in seconds (must be > 0)
    :vartype timeout: float
    :var user_agent: Override the default User-Agent header sent by the Session
    :vartype user_agent: str | None
    :var verify_ssl: Whether to verify TLS certificates on outgoing requests
    :vartype verify_ssl: bool
    :var request_retries: Automatic retries on 5xx responses and connection errors
    :vartype request_retries: int
    :var browser_state_path: Where to persist Playwright storage state between runs
    :vartype browser_state_path: Path
    :var browser_headless: Launch the Playwright browser in headless mode
    :vartype browser_headless: bool

    **Examples:**

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
        export GAMESHEET_PASSWORD="secret"
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
