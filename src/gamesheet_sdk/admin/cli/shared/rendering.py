# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Rendering utilities for CLI commands."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from gamesheet_sdk.common.cli.core import parse_columns_spec
from gamesheet_sdk.common.output import render, write_output


def render_get_command(
    data: dict[str, Any] | BaseModel,
    output_format: str,
    output_path: str | None,
    fields_spec: str | None = None,
) -> None:
    """Render get command output (single object as key-value pairs).

    Args:
        data (dict[str, Any] | BaseModel): The object to render (dict or pydantic model)
        output_format (str): Output format (json, yaml, csv, tsv, or tabulate format)
        output_path (str | None): Optional file path to write output to
        fields_spec (str | None): Optional comma-separated field names to include
    """
    # Convert pydantic model to dict if needed
    data_dict = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
    # Filter fields if specified
    if fields_spec:
        fields = parse_columns_spec(fields_spec)
        if fields:
            data_dict = {k: v for k, v in data_dict.items() if k in fields}
    # Render as key-value rows for tabular formats
    if output_format not in ("json", "yaml"):
        rows = [{"field": k, "value": v} for k, v in data_dict.items()]
        rendered = render(rows, fmt=output_format, columns=None)
    else:
        rendered = render([data_dict], fmt=output_format, columns=None)

    write_output(rendered, output_path, fmt=output_format)


def render_list_command(
    items: list[Any],
    output_format: str,
    output_path: str | None,
    columns_spec: str | None = None,
) -> None:
    """Render list command output (table of objects).

    Args:
        items (list[Any]): List of objects to render (dicts or pydantic models)
        output_format (str): Output format (json, yaml, csv, tsv, or tabulate format)
        output_path (str | None): Optional file path to write output to
        columns_spec (str | None): Optional comma-separated column names to include
    """
    # Convert pydantic models to dicts
    rows = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in items]
    # Parse columns spec
    columns = parse_columns_spec(columns_spec) if columns_spec else None
    # Render and write
    rendered = render(rows, fmt=output_format, columns=columns)
    write_output(rendered, output_path, fmt=output_format)


def render_penalty_report(
    report: dict[str, Any],
    output_format: str,
    output_path: str | None,
) -> None:
    """Render penalty report output.

    Args:
        report (dict[str, Any]): The penalty report dictionary to render
        output_format (str): Output format (json or yaml)
        output_path (str | None): Optional file path to write output to
    """
    import json

    if output_format == "json":
        output_text = json.dumps(report, indent=2)
    elif output_format == "yaml":
        import yaml

        output_text = yaml.dump(report, default_flow_style=False)
    else:
        output_text = json.dumps(report, indent=2)

    write_output(output_text, output_path, fmt=output_format)
