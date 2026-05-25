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
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_session_path() -> Path:
    """Return the XDG-compliant default path for persisted session state."""
    xdg = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(xdg).expanduser() / "gamesheet-sdk-py" / "session.json"


def _default_browser_state_path() -> Path:
    """Return the XDG-compliant default path for Playwright storage state."""
    xdg = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(xdg).expanduser() / "gamesheet-sdk-py" / "browser-state.json"


class Config(BaseSettings):
    """Resolved configuration for an SDK session."""

    model_config = SettingsConfigDict(
        env_prefix="GAMESHEET_",
        extra="ignore",
    )

    base_url: str = Field(
        default="https://gamesheet.com",
        description="Root URL of the GameSheet WebUI.",
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
