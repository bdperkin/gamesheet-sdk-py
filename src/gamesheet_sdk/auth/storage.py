# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Browser storage state file manipulation.

This module provides utilities for reading and writing Playwright browser
storage state files, which store cookies, localStorage, and sessionStorage
data in JSON format.

The storage state file format is:

.. code-block:: json

    {
        "cookies": [...],
        "origins": [
            {
                "origin": "https://example.com",
                "localStorage": [
                    {"name": "key", "value": "value"}
                ]
            }
        ]
    }

**Example usage:**
.. code-block:: python
    from pathlib import Path
    from gamesheet_sdk.config import Config
    from gamesheet_sdk.auth.storage import (
        load_local_storage_value,
        read_state_or_empty,
        origin_entry_for,
        apply_local_storage_updates,
    )

    # Load a localStorage value
    config = Config()
    access_token = load_local_storage_value(config, "access_token")
    # Create/update localStorage entries
    state_path = Path.home() / ".gamesheet" / "browser_state.json"
    state = read_state_or_empty(state_path)
    origin = origin_entry_for(state, APP_GAMESHEET_COM)
    apply_local_storage_updates(
        origin["localStorage"],
        {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
        },
    )
    state_path.write_text(json.dumps(state, indent=2))
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from gamesheet_sdk.config import Config

_LOGGER = logging.getLogger(__name__)


def read_state_file(path: Path) -> dict[str, Any] | None:
    """Parse the browser storage state JSON, or return None on miss/error.

    Reads and parses a Playwright browser storage state file. Returns ``None`` if
    the file does not exist or cannot be parsed.

    .. note:: This function logs a warning (not an error) if the file exists but
        cannot be read or parsed, allowing graceful fallback to fresh login
        flows.

    :param path: Path to the browser storage state JSON file.
    :type path: Path
    :returns: Parsed storage state dictionary, or ``None`` if file is missing or cannot be parsed.
    :rtype: dict[str, Any] | None
    """
    if not path.exists():
        return None
    try:
        loaded: dict[str, Any] = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        _LOGGER.warning("Failed to read browser storage state from %s.", path)
        return None
    return loaded


def lookup_local_storage(state: dict[str, Any], base_url: str, name: str) -> Any:
    """Return the named localStorage value for base_url, or None.

    Searches the storage state dictionary for a localStorage entry matching
    the given origin (base_url) and key name.

    .. note:: The value returned is untyped (``Any``) — callers should validate the type
        before use. See :func:`load_local_storage_value` for a string-validated
        variant.

    :param state: Parsed browser storage state dictionary (from :func:`read_state_file` or
        :func:`read_state_or_empty`).
    :type state: dict[str, Any]
    :param base_url: Origin URL to search for (e.g., ``APP_GAMESHEET_COM``).
    :type base_url: str
    :param name: localStorage key name to look up.
    :type name: str
    :returns: The value associated with the key, or ``None`` if the origin or key is not found.
    :rtype: Any
    """
    for origin in state.get("origins", []):
        if origin.get("origin") != base_url:
            continue
        for kv in origin.get("localStorage", []):
            if kv.get("name") == name:
                return kv.get("value")
    return None


def load_local_storage_value(config: Config, name: str) -> str | None:
    """Read one localStorage entry for config.base_url from the saved state.

    High-level helper that reads the browser storage state file from
    ``config.browser_state_path``, looks up the localStorage value for
    ``config.base_url``, and validates that it is a non-empty string.

    .. note:: Returns ``None`` if the file does not exist, cannot be parsed, the origin
        is not found, the key is not found, or the value is not a non-empty
        string.

    **Example:**
    .. code-block:: python
        from gamesheet_sdk.config import Config
        from gamesheet_sdk.auth.storage import load_local_storage_value

        config = Config()
        access_token = load_local_storage_value(config, "access_token")
        if access_token:
            print(f"Found token: {access_token[:10]}...")
        else:
            print("No token found, need to log in")
    :param config: Configuration object containing the browser state path and base URL.
    :type config: Config
    :param name: localStorage key name to retrieve (e.g., ``"access_token"``).
    :type name: str
    :returns: The string value if found and non-empty, otherwise None.
    :rtype: str | None
    """
    state = read_state_file(config.browser_state_path)
    if state is None:
        return None
    value = lookup_local_storage(state, config.base_url, name)
    return value if isinstance(value, str) and value else None


def read_state_or_empty(path: Path) -> dict[str, Any]:
    """Like read_state_file but returns an empty skeleton on miss/error.

    Reads and parses a browser storage state file. Unlike
    :func:`read_state_file`, this function never returns ``None`` — if the file
    does not exist or cannot be parsed, it returns a minimal valid state
    structure.

    .. note:: This function does not log warnings on parse failures (unlike
        :func:`read_state_file`), making it suitable for write-path helpers
        where missing state is expected.

    :param path: Path to the browser storage state JSON file.
    :type path: Path
    :returns: Parsed storage state dictionary, or ``{"cookies": [], "origins": []}`` if the file is missing or
        cannot be parsed.
    :rtype: dict[str, Any]
    """
    empty: dict[str, Any] = {"cookies": [], "origins": []}
    if not path.exists():
        return empty
    try:
        loaded: dict[str, Any] = json.loads(path.read_text())
    except json.JSONDecodeError:
        return empty
    return loaded


def origin_entry_for(state: dict[str, Any], base_url: str) -> dict[str, Any]:
    """Return the origin entry for base_url, creating it if absent.

    Searches the ``origins`` list in the storage state for an entry matching
    the given URL. If not found, creates a new origin entry with an empty
    localStorage array and appends it to the list.

    .. warning:: This function **mutates** the ``state`` dictionary by adding a new
        origin entry if one does not exist. Ensure you write the modified state
        back to disk after calling this function.

    :param state: Browser storage state dictionary (typically from :func:`read_state_or_empty`).
    :type state: dict[str, Any]
    :param base_url: Origin URL (e.g., ``APP_GAMESHEET_COM``).
    :type base_url: str
    :returns: The origin entry dictionary containing ``"origin"`` and ``"localStorage"`` keys. The returned
        dict is a **live reference** — modifications to it will update the state.
    :rtype: dict[str, Any]
    """
    origins: list[dict[str, Any]] = state.setdefault("origins", [])
    for origin in origins:
        if origin.get("origin") == base_url:
            return origin
    new_entry: dict[str, Any] = {"origin": base_url, "localStorage": []}
    origins.append(new_entry)
    return new_entry


def apply_local_storage_updates(
    ls: list[dict[str, str]],
    updates: dict[str, str],
) -> None:
    """Upsert each name → value pair into the localStorage list.

    Updates existing localStorage entries in place or appends new entries for
    keys that do not exist.

    .. warning:: This function **mutates** the ``ls`` list in place. Ensure you write
        the parent state back to disk after calling this function.

    **Example:**
    .. code-block:: python
        from pathlib import Path
        import json
        from gamesheet_sdk.auth.storage import (
            read_state_or_empty,
            origin_entry_for,
            apply_local_storage_updates,
        )

        state_path = Path.home() / ".gamesheet" / "browser_state.json"
        state = read_state_or_empty(state_path)
        origin = origin_entry_for(state, APP_GAMESHEET_COM)
        # Upsert tokens
        apply_local_storage_updates(
            origin["localStorage"],
            {
                "access_token": "eyJ...",
                "refresh_token": "dGh...",
            },
        )
        # Write back to disk
        state_path.write_text(json.dumps(state, indent=2))
    :param ls: The ``localStorage`` array from an origin entry (typically ``origin["localStorage"]``). This
        list is **mutated in place**.
    :type ls: list[dict[str, str]]
    :param updates: Dictionary of key-value pairs to upsert.
    :type updates: dict[str, str]
    """
    by_name = {kv.get("name"): kv for kv in ls}
    for name, value in updates.items():
        existing = by_name.get(name)
        if existing is not None:
            existing["value"] = value
        else:
            ls.append({"name": name, "value": value})
