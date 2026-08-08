# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Multi-format rendering of tabular data for CLI workflows.

Every SDK workflow that produces a list of rows (associations, leagues, teams, ...) flows through
:func:`render` to get a string. Supported formats fall into two groups. **Data formats** (machine-friendly,
not via tabulate): ``json``, ``yaml``, ``csv``, ``tsv``. **Tabulate formats** (human-readable or markup-
embeddable; every ``tablefmt`` value tabulate accepts): ``plain``, ``simple``, ``grid``, ``fancy_grid``,
``pipe``, ``orgtbl``, ``rst``, ``mediawiki``, ``html``, ``latex``, ``latex_raw``, ``latex_booktabs``,
``latex_longtable``. The default format is ``simple``. :func:`write_output` complements :func:`render` by
writing the rendered text to a file path (when one is given) or to stdout (with optional ``rich``-driven
syntax highlighting when stdout is a TTY and the format is ``json`` or ``yaml``).
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.syntax import Syntax
import tabulate as _tabulate
import yaml

from gamesheet_sdk.common.constants import (
    DEFAULT_OUTPUT_FORMAT,
    ENCODING_UTF8,
    JSON_INDENT_SPACES,
    SYNTAX_BG_COLOR,
    SYNTAX_THEME,
)

if TYPE_CHECKING:
    from collections.abc import Callable
# Every ``tablefmt`` value :func:`render` accepts from tabulate.
TABULATE_FORMATS: tuple[str, ...] = (
    "plain",
    "simple",
    "grid",
    "fancy_grid",
    "pipe",
    "orgtbl",
    "rst",
    "mediawiki",
    "html",
    "latex",
    "latex_raw",
    "latex_booktabs",
    "latex_longtable",
)
# Machine-friendly formats :func:`render` renders without tabulate.
DATA_FORMATS: tuple[str, ...] = ("json", "yaml", "csv", "tsv")
# Union of every format :func:`render` understands.
ALL_FORMATS: tuple[str, ...] = DATA_FORMATS + TABULATE_FORMATS
# Format used when the caller does not specify one.
DEFAULT_FORMAT = DEFAULT_OUTPUT_FORMAT


def _render_json(
    rows: list[dict[str, Any]],
    _columns: list[str],
) -> str:
    """Render rows as indented, sorted JSON.

    Args:
        rows (list[dict[str, Any]]): List of row dictionaries to
            serialize.
        _columns (list[str]): Column names list (unused for JSON
            format).

    Returns:
        str: JSON string with 2-space indentation and sorted keys.

    Example output::

        [{"id": 123, "name": "Example"}]
    """
    return json.dumps(rows, indent=JSON_INDENT_SPACES, sort_keys=True, default=str)


def _render_yaml(
    rows: list[dict[str, Any]],
    _columns: list[str],
) -> str:
    """Render rows as block-style YAML.

    Args:
        rows (list[dict[str, Any]]): List of row dictionaries to
            serialize.
        _columns (list[str]): Column names list (unused for YAML
            format).

    Returns:
        str: YAML string in block style with sorted keys, trailing
        whitespace stripped.

    Example output::

        - id: 123
            name: Example
        - id: 456
            name: Another
    """
    return yaml.safe_dump(rows, sort_keys=True, default_flow_style=False).rstrip()


def _render_dsv(
    rows: list[dict[str, Any]],
    columns: list[str],
    *,
    delimiter: str,
) -> str:
    r"""Render rows as delimiter-separated values (CSV, TSV, etc.).

    Args:
        rows (list[dict[str, Any]]): List of row dictionaries to
            serialize.
        columns (list[str]): Column names in display order; keys not in
            this list are ignored.
        delimiter (str): Single-character separator (e.g. ``,`` for CSV,
            ``\t`` for TSV).

    Returns:
        DSV string with header row, LF line endings, trailing newline
        stripped.
    None values are converted to empty strings. Extra keys in each row beyond
    ``columns`` are silently ignored (``extrasaction="ignore"``).
    Example (delimiter=``,``)::
        id, name
        123, Example
        456, Another
    """
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=columns,
        delimiter=delimiter,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {key: ("" if value is None else value) for key, value in row.items()},
        )

    return buf.getvalue().rstrip("\n")


def _render_csv(rows: list[dict[str, Any]], columns: list[str]) -> str:
    """Render rows as comma-separated values.

    Thin wrapper around :func:`_render_dsv` with ``delimiter=","``.

    Args:
        rows (list[dict[str, Any]]): List of row dictionaries to
            serialize.
        columns (list[str]): Column names in display order.

    Returns:
        str: CSV string with header row and comma delimiters.
    """
    return _render_dsv(rows, columns, delimiter=",")


def _render_tsv(rows: list[dict[str, Any]], columns: list[str]) -> str:
    r"""Render rows as tab-separated values.

    Thin wrapper around :func:`_render_dsv` with ``delimiter="\t"``.

    Args:
        rows (list[dict[str, Any]]): List of row dictionaries to
            serialize.
        columns (list[str]): Column names in display order.

    Returns:
        str: TSV string with header row and tab delimiters.
    """
    return _render_dsv(rows, columns, delimiter="\t")


def _render_tabulate(rows: list[dict[str, Any]], columns: list[str], fmt: str) -> str:
    """Render rows using the tabulate library.

    Missing keys in a row default to an empty string. The ``fmt`` parameter controls alignment, borders, and
    markup dialect.

    Args:
        rows (list[dict[str, Any]]): List of row dictionaries to render.
        columns (list[str]): Column names in display order; used as
            table headers.
        fmt (str): A ``tablefmt`` value tabulate accepts (e.g.
            ``"simple"``, ``"grid"``, ``"rst"``). See
            :data:`TABULATE_FORMATS` for the full list of accepted
            formats.

    Returns:
        str: Formatted table string.
    """
    table_rows = [[row.get(col, "") for col in columns] for row in rows]
    return _tabulate.tabulate(table_rows, headers=columns, tablefmt=fmt)


# Dispatch table for the non-tabulate ("data") formats. Keeps :func:`render`
# branchless across the format axis; tabulate formats fall through to
# :func:`_render_tabulate`.
_DATA_RENDERERS: dict[str, Callable[[list[dict[str, Any]], list[str]], str]] = {
    "json": _render_json,
    "yaml": _render_yaml,
    "csv": _render_csv,
    "tsv": _render_tsv,
}


def _derive_columns(rows: list[dict[str, Any]]) -> list[str]:
    """Derive column names from the first row's keys.

    Used by :func:`render` when the caller does not provide an explicit column list. Column order is the
    natural iteration order of the first row's keys (insertion order in Python 3.7+).

    Args:
        rows (list[dict[str, Any]]): List of row dictionaries.

    Returns:
        list[str]: Keys from the first row, or an empty list if ``rows``
        is empty.
    """
    if not rows:
        return []

    return list(rows[0].keys())


def render(
    rows: list[dict[str, Any]],
    fmt: str = DEFAULT_FORMAT,
    *,
    columns: list[str] | None = None,
) -> str:
    """Render ``rows`` as a string in the requested format.

    Args:
        rows (list[dict[str, Any]]): A list of mappings -- each becomes
            one row.
        fmt (str): One of :data:`ALL_FORMATS`. Defaults to
            :data:`DEFAULT_FORMAT` (``"simple"``).
        columns (list[str] | None): Restrict and order the column set.
            If ``None`` and ``rows`` is non-empty, the first row's keys
            are used in their natural order.

    Returns:
        str: Rendered string in the requested format.

    Raises:
        ValueError: If ``fmt`` is not in :data:`ALL_FORMATS`.
    **Example usage:**

    .. code-block:: python

        from gamesheet_sdk.common.output import render

        rows = [{"id": 123, "name": "Example"}, {"id": 456, "name": "Another"}]

        # Simple table format
        print(render(rows, fmt="simple"))
        # Output:
        #   id   name
        # ---  -------
        # 123  Example
        # 456  Another

        # JSON format
        print(render(rows, fmt="json"))
        # Output:
        # [
        #     {
        #         "id": 123,
        #         "name": "Example"
        #     },
        #     {
        #         "id": 456,
        #         "name": "Another"
        #     }
        # ]

        # CSV format
        print(render(rows, fmt="csv"))
        # Output:
        # id,name
        # 123,Example
        # 456,Another
    """
    if fmt not in ALL_FORMATS:
        _fmt_list = ", ".join(ALL_FORMATS)
        _err_msg = f"Unknown format: {fmt!r}. Expected one of {_fmt_list}."
        raise ValueError(_err_msg)

    effective_columns = columns if columns is not None else _derive_columns(rows)
    renderer = _DATA_RENDERERS.get(fmt)
    if renderer is not None:
        return renderer(rows, effective_columns)

    return _render_tabulate(rows, effective_columns, fmt)


def _ensure_trailing_newline(text: str) -> str:
    """Append a newline to ``text`` if it does not already end with one.

    Used by :func:`write_output` to ensure file writes and stdout prints end with a newline, which most
    terminals expect.

    Args:
        text (str): Input string.

    Returns:
        str: Text string with a guaranteed trailing newline.
    """
    return text if text.endswith("\n") else f"{text}\n"


def write_output(
    text: str,
    path: str | Path | None,
    *,
    fmt: str,
) -> None:
    """Write ``text`` to ``path`` or to stdout.

    When ``path`` is ``None`` and stdout is a TTY, JSON and YAML output is syntax-highlighted via
    :class:`rich.syntax.Syntax`. Other formats and any non-TTY destination receive ``text`` verbatim with a
    trailing newline if it does not already have one.

    **File output example**::

        >>> from gamesheet_sdk.common.output import render, write_output
        >>> rows = [{"id": 123, "name": "Example"}]
        >>> text = render(rows, fmt="json")
        >>> write_output(text, "output.json", fmt="json")
        # Writes to output.json with trailing newline

    **TTY stdout example** (JSON/YAML only)::

        >>> from gamesheet_sdk.common.output import write_output
        >>> write_output(text, None, fmt="json")
        # Syntax-highlighted output to terminal if stdout is a TTY

    **Non-TTY / other formats**::

        >>> from gamesheet_sdk.common.output import write_output
        >>> write_output(text, None, fmt="csv")
        # Plain text to stdout with trailing newline

    Args:
        text (str): Rendered output string to write.
        path (str | Path | None): Destination file path (str or
            :class:`pathlib.Path`), or ``None`` for stdout.
        fmt (str): Format name (e.g. ``"json"``, ``"yaml"``, ``"csv"``);
            controls syntax highlighting on TTY stdout.
    """
    if path is not None:
        Path(path).write_text(_ensure_trailing_newline(text), encoding=ENCODING_UTF8)
        return

    if sys.stdout.isatty() and fmt in ("json", "yaml"):
        Console().print(
            Syntax(
                text,
                fmt,
                theme=SYNTAX_THEME,
                background_color=SYNTAX_BG_COLOR,
                word_wrap=True,
            ),
        )
        return

    sys.stdout.write(_ensure_trailing_newline(text))
