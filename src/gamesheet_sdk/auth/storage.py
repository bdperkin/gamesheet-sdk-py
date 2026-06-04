"""Browser storage state file manipulation."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:

    from pathlib import Path

    from gamesheet_sdk.config import Config
_LOGGER = logging.getLogger(__name__)


def read_state_file(path: Path) -> dict[str, Any] | None:
    """Parse the browser storage state JSON, or return None on miss/error."""
    if not path.exists():

        return None

    try:
        loaded: dict[str, Any] = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        _LOGGER.warning("Failed to read browser storage state from %s.", path)
        return None

    return loaded


def lookup_local_storage(state: dict[str, Any], base_url: str, name: str) -> Any:
    """Return the named localStorage value for base_url, or None."""
    for origin in state.get("origins", []):

        if origin.get("origin") != base_url:

            continue
        for kv in origin.get("localStorage", []):

            if kv.get("name") == name:

                return kv.get("value")

    return None


def load_local_storage_value(config: Config, name: str) -> str | None:
    """Read one localStorage entry for config.base_url from the saved state."""
    state = read_state_file(config.browser_state_path)
    if state is None:

        return None

    value = lookup_local_storage(state, config.base_url, name)
    return value if isinstance(value, str) and value else None


def read_state_or_empty(path: Path) -> dict[str, Any]:
    """Like read_state_file but returns an empty skeleton on miss/error."""
    empty: dict[str, Any] = {"cookies": [], "origins": []}
    if not path.exists():

        return empty

    try:
        loaded: dict[str, Any] = json.loads(path.read_text())
    except json.JSONDecodeError:
        return empty

    return loaded


def origin_entry_for(state: dict[str, Any], base_url: str) -> dict[str, Any]:
    """Return the origin entry for base_url, creating it if absent."""
    origins: list[dict[str, Any]] = state.setdefault("origins", [])
    for origin in origins:

        if origin.get("origin") == base_url:

            return origin

    new_entry: dict[str, Any] = {"origin": base_url, "localStorage": []}
    origins.append(new_entry)
    return new_entry


def apply_local_storage_updates(ls: list[dict[str, str]], updates: dict[str, str]) -> None:
    """Upsert each name → value pair into the localStorage list."""
    by_name = {kv.get("name"): kv for kv in ls}
    for name, value in updates.items():

        existing = by_name.get(name)
        if existing is not None:

            existing["value"] = value
        else:
            ls.append({"name": name, "value": value})
