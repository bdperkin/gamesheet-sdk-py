"""Multi-format rendering of tabular data for CLI workflows.

Every SDK workflow that produces a list of rows (associations, leagues,
teams, ...) flows through :func:`render` to get a string. Supported
formats fall into two groups.

**Data formats** (machine-friendly, not via tabulate): ``json``,
``yaml``, ``csv``, ``tsv``.

**Tabulate formats** (human-readable or markup-embeddable; every
``tablefmt`` value tabulate accepts): ``plain``, ``simple``, ``grid``,
``fancy_grid``, ``pipe``, ``orgtbl``, ``rst``, ``mediawiki``, ``html``,
``latex``, ``latex_raw``, ``latex_booktabs``, ``latex_longtable``.

The default format is ``simple``.

:func:`write_output` complements :func:`render` by writing the rendered
text to a file path (when one is given) or to stdout (with optional
``rich``-driven syntax highlighting when stdout is a TTY and the format
is ``json`` or ``yaml``).
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

import tabulate as _tabulate
import yaml
from rich.console import Console
from rich.syntax import Syntax

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
"""Every ``tablefmt`` value :func:`render` accepts from tabulate."""

DATA_FORMATS: tuple[str, ...] = ("json", "yaml", "csv", "tsv")
"""Machine-friendly formats :func:`render` renders without tabulate."""

ALL_FORMATS: tuple[str, ...] = DATA_FORMATS + TABULATE_FORMATS
"""Union of every format :func:`render` understands."""

DEFAULT_FORMAT = "simple"
"""Format used when the caller does not specify one."""


def render(
    rows: list[dict[str, Any]],
    fmt: str = DEFAULT_FORMAT,
    *,
    columns: list[str] | None = None,
) -> str:
    """Render ``rows`` as a string in the requested format.

    :param rows: A list of mappings -- each becomes one row.
    :param fmt: One of :data:`ALL_FORMATS`. Defaults to
        :data:`DEFAULT_FORMAT`.
    :param columns: Restrict and order the column set. If ``None`` and
        ``rows`` is non-empty, the first row's keys are used in their
        natural order.
    :raises ValueError: If ``fmt`` is not in :data:`ALL_FORMATS`.
    """
    if fmt not in ALL_FORMATS:
        raise ValueError(
            f"Unknown format: {fmt!r}. Expected one of " f"{', '.join(ALL_FORMATS)}."
        )
    effective_columns = columns if columns is not None else _derive_columns(rows)

    if fmt == "json":
        return json.dumps(rows, indent=2, sort_keys=True, default=str)
    if fmt == "yaml":
        return yaml.safe_dump(rows, sort_keys=True, default_flow_style=False).rstrip()
    if fmt == "csv":
        return _render_dsv(rows, effective_columns, delimiter=",")
    if fmt == "tsv":
        return _render_dsv(rows, effective_columns, delimiter="\t")
    # fmt is in TABULATE_FORMATS by virtue of the ALL_FORMATS check above.
    table_rows = [[row.get(col, "") for col in effective_columns] for row in rows]
    return _tabulate.tabulate(
        table_rows,
        headers=effective_columns,
        tablefmt=fmt,
    )


def write_output(
    text: str,
    path: str | Path | None,
    *,
    fmt: str,
) -> None:
    """Write ``text`` to ``path`` or to stdout.

    When ``path`` is ``None`` and stdout is a TTY, JSON and YAML output
    is syntax-highlighted via :class:`rich.syntax.Syntax`. Other
    formats and any non-TTY destination receive ``text`` verbatim with
    a trailing newline if it does not already have one.
    """
    if path is not None:
        Path(path).write_text(_ensure_trailing_newline(text), encoding="utf-8")
        return

    if sys.stdout.isatty() and fmt in ("json", "yaml"):
        Console().print(
            Syntax(
                text,
                fmt,
                theme="ansi_dark",
                background_color="default",
                word_wrap=True,
            )
        )
        return

    sys.stdout.write(_ensure_trailing_newline(text))


def _derive_columns(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return list(rows[0].keys())


def _render_dsv(
    rows: list[dict[str, Any]],
    columns: list[str],
    *,
    delimiter: str,
) -> str:
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
            {key: ("" if value is None else value) for key, value in row.items()}
        )
    return buf.getvalue().rstrip("\n")


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"
