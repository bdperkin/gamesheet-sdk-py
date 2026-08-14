# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared yamlfix formatting for CLI tools that emit YAML."""

from __future__ import annotations

import logging
import re

from yamlfix import fix_code
from yamlfix.model import YamlfixConfig

from shared.toml import PYPROJECT_PATH, load_toml

logger = logging.getLogger(__name__)


def _load_yamlfix_config() -> YamlfixConfig:
    """Build a :class:`YamlfixConfig` from ``[tool.yamlfix]`` in pyproject.toml.

    Keys that are not ``YamlfixConfig`` fields are dropped: the table also carries settings for the yamlfix
    CLI (``check``, ``diff``, ``recursive``, ``exclude``) and options this yamlfix release does not define,
    none of which the formatter accepts.

    Returns:
        YamlfixConfig: Formatter configuration for :func:`yamlfix.fix_code`.

    Raises:
        ToolError: If pyproject.toml cannot be read or parsed.

    """
    fields = frozenset(YamlfixConfig.model_fields)
    table = load_toml(PYPROJECT_PATH).get("tool", {}).get("yamlfix", {})
    known = {key: value for key, value in table.items() if key in fields}
    logger.debug("Loaded %d yamlfix option(s) from %s", len(known), PYPROJECT_PATH)
    return YamlfixConfig(**known)


def _apply_yamlfix(text: str) -> str:
    """Format *text* with yamlfix using the project's configuration.

    Returns:
        str: The yamlfix-formatted YAML.

    Raises:
        SystemExit: If yamlfix cannot format the text.

    """
    try:
        formatted: str = fix_code(text, _load_yamlfix_config())
    except Exception as exc:
        logger.exception("yamlfix failed to format output")
        raise SystemExit(2) from exc

    return formatted


def _postprocess(text: str) -> str:
    """Re-attach merge-key comments and strip trailing whitespace.

    Returns:
        str: Cleaned YAML text.

    """
    text = re.sub(
        r"^(\s*<<:[^\n]*\S)\s*\n\s*(#[^\n]*)",
        r"\1  \2",
        text,
        flags=re.MULTILINE,
    )
    return re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)


def format_yaml(text: str) -> str:
    """Run yamlfix over rendered YAML, then repair what it breaks.

    The post-pass has to run after yamlfix, not before: both ruamel and yamlfix push a comment that trails a
    ``<<:`` merge key down onto its own line, where it reads as a comment on the following key instead.

    Args:
        text (str): Rendered YAML to format.

    Returns:
        str: Formatted YAML, ready to write.

    Raises:
        SystemExit: If yamlfix cannot format the text.

    """
    return _postprocess(_apply_yamlfix(text))
