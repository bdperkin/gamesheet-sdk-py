# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for CLI shared utilities."""

from __future__ import annotations

from pathlib import Path
import tempfile

from pydantic import BaseModel
import rich_click as click

from gamesheet_sdk.cli.shared import (
    common_output_options,
    get_fields_option,
    list_columns_option,
    render_get_command,
    render_list_command,
)
from tests.helpers import ASSOCIATION_ID, LEAGUE_ID


class SampleModel(BaseModel):
    """Sample pydantic model for testing."""

    id: str
    name: str


def test_common_output_options_decorator() -> None:
    """Test that common_output_options adds --format and --output options."""

    @common_output_options
    @click.command()
    def dummy_command(output_format: str, output_path: str | None) -> None:
        del output_format, output_path

    # Check that the command has the expected parameters
    params = {p.name for p in dummy_command.params}
    assert "output_format" in params
    assert "output_path" in params


def test_list_columns_option_decorator() -> None:
    """Test that list_columns_option adds --columns option."""

    @list_columns_option
    @click.command()
    def dummy_command(columns_spec: str | None) -> None:
        del columns_spec

    # Check that the command has the columns_spec parameter
    params = {p.name for p in dummy_command.params}
    assert "columns_spec" in params


def test_get_fields_option_decorator() -> None:
    """Test that get_fields_option adds --fields option."""

    @get_fields_option
    @click.command()
    def dummy_command(fields_spec: str | None) -> None:
        del fields_spec

    # Check that the command has the fields_spec parameter
    params = {p.name for p in dummy_command.params}
    assert "fields_spec" in params


def test_render_get_command_with_dict() -> None:
    """Test render_get_command with a dict."""
    output_file = Path(tempfile.gettempdir()) / "output.json"
    data = {"id": ASSOCIATION_ID, "name": "Test"}
    render_get_command(data, "json", str(output_file), None)
    content = output_file.read_text()
    assert ASSOCIATION_ID in content
    assert "Test" in content


def test_render_get_command_with_fields_filter() -> None:
    """Test render_get_command with fields filter."""
    output_file = Path(tempfile.gettempdir()) / "output.json"
    data = {"id": ASSOCIATION_ID, "name": "Test", "extra": "Should be filtered"}
    render_get_command(data, "json", str(output_file), "id,name")
    content = output_file.read_text()
    assert ASSOCIATION_ID in content
    assert "Test" in content
    assert "extra" not in content


def test_render_list_command_with_dicts() -> None:
    """Test render_list_command with list of dicts."""
    output_file = Path(tempfile.gettempdir()) / "output.json"
    items = [
        {"id": "1", "name": "First"},
        {"id": "2", "name": "Second"},
    ]
    render_list_command(items, "json", str(output_file), None)
    content = output_file.read_text()
    assert "First" in content
    assert "Second" in content


def test_render_list_command_with_columns_filter() -> None:
    """Test render_list_command with columns filter."""
    output_file = Path(tempfile.gettempdir()) / "output.csv"
    items = [
        {"id": "1", "name": "First", "extra": "Data"},
        {"id": "2", "name": "Second", "extra": "More"},
    ]
    render_list_command(items, "csv", str(output_file), "id,name")
    content = output_file.read_text()
    # CSV should have id and name columns, not extra
    assert "id" in content
    assert "name" in content
    assert "First" in content
    assert "Second" in content


def test_render_get_command_with_pydantic_model() -> None:
    """Test render_get_command with a pydantic model."""
    output_file = Path(tempfile.gettempdir()) / "output.json"
    model = SampleModel(id=LEAGUE_ID, name="Pydantic Test", extra="Extra data")
    render_get_command(model, "json", str(output_file), None)
    content = output_file.read_text()
    assert LEAGUE_ID in content
    assert "Pydantic Test" in content


def test_render_get_command_with_pydantic_model_tabular() -> None:
    """Test render_get_command with pydantic model in tabular format."""
    output_file = Path(tempfile.gettempdir()) / "output.txt"
    model = SampleModel(id="789", name="Tabular Test")
    render_get_command(model, "plain", str(output_file), None)
    content = output_file.read_text()
    assert "789" in content
    assert "Tabular Test" in content


def test_render_list_command_with_pydantic_models() -> None:
    """Test render_list_command with pydantic models."""
    output_file = Path(tempfile.gettempdir()) / "output.json"
    items = [
        SampleModel(id="1", name="Model One"),
        SampleModel(id="2", name="Model Two"),
    ]
    render_list_command(items, "json", str(output_file), None)
    content = output_file.read_text()
    assert "Model One" in content
    assert "Model Two" in content


def test_render_get_command_with_whitespace_fields_spec() -> None:
    """Test render_get_command with whitespace-only fields_spec (no filtering)."""
    output_file = Path(tempfile.gettempdir()) / "output.json"
    data = {"id": "999", "name": "Test", "extra": "Should appear"}
    # Whitespace-only fields_spec should not filter (parse_columns_spec returns None)
    render_get_command(data, "json", str(output_file), "   ")
    content = output_file.read_text()
    assert "999" in content
    assert "Test" in content
    assert "Should appear" in content
