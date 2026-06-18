"""Tests for :mod:`gamesheet_sdk.output`."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import yaml

from gamesheet_sdk import render
from gamesheet_sdk.output import (
    ALL_FORMATS,
    DATA_FORMATS,
    DEFAULT_FORMAT,
    TABULATE_FORMATS,
    write_output,
)

if TYPE_CHECKING:
    from pathlib import Path
_ROWS = [
    {"id": "11", "title": "Hockey Time", "logo": ""},
    {"id": "40", "title": "SuperSeries AAA", "logo": "https://x/logo.png"},
]


# ---------- format catalog ------------------------------------------------
def test_format_constants_are_disjoint() -> None:
    """Test that DATA_FORMATS and TABULATE_FORMATS have no overlap."""
    assert set(DATA_FORMATS).isdisjoint(set(TABULATE_FORMATS))


def test_all_formats_is_union() -> None:
    """Test that ALL_FORMATS is the union of DATA_FORMATS and TABULATE_FORMATS."""
    assert set(ALL_FORMATS) == set(DATA_FORMATS) | set(TABULATE_FORMATS)


def test_default_format_is_in_all_formats() -> None:
    """Test that DEFAULT_FORMAT is a valid format in ALL_FORMATS."""
    assert DEFAULT_FORMAT in ALL_FORMATS


# ---------- render() per format ------------------------------------------
def test_render_unknown_format_raises_value_error() -> None:
    """Test that render raises ValueError for unknown format."""
    with pytest.raises(ValueError, match="Unknown format"):
        render(_ROWS, fmt="not-a-format")


def test_render_json_is_sorted_keys_pretty_indented() -> None:
    """Test that JSON rendering produces sorted, pretty-printed output."""
    out = render(_ROWS, fmt="json")
    data = json.loads(out)
    assert data == _ROWS
    # Keys within each row are sorted alphabetically by json.dumps(sort_keys=True).
    assert '"id": "11"' in out


def test_render_yaml_round_trips() -> None:
    """Test that YAML rendering round-trips correctly."""
    out = render(_ROWS, fmt="yaml")
    data = yaml.safe_load(out)
    assert data == _ROWS


def test_render_csv_header_and_rows() -> None:
    """Test that CSV rendering includes header and data rows."""
    lines = render(_ROWS, fmt="csv").splitlines()
    assert lines[0] == "id,title,logo"
    assert lines[1] == "11,Hockey Time,"
    assert lines[2] == "40,SuperSeries AAA,https://x/logo.png"


def test_render_tsv_uses_tab_delimiter() -> None:
    """Test that TSV rendering uses tab delimiters."""
    out = render(_ROWS, fmt="tsv")
    assert "\t" in out.splitlines()[0]
    # commas in titles would be quoted; no titles have them
    assert "," not in out.splitlines()[0]


@pytest.mark.parametrize("fmt", list(TABULATE_FORMATS))
def test_render_every_tabulate_format_returns_non_empty_string(fmt: str) -> None:
    """Test that all tabulate formats produce non-empty output."""
    out = render(_ROWS, fmt=fmt)
    assert isinstance(out, str)
    assert out, f"tabulate format {fmt!r} produced an empty string"
    # Tabulate output for non-empty rows must contain a title token somewhere.
    assert "Hockey Time" in out or "Hockey" in out


def test_render_columns_restricts_and_orders() -> None:
    """Test that columns parameter restricts and orders output columns."""
    out = render(_ROWS, fmt="csv", columns=["title", "id"])
    lines = out.splitlines()
    assert lines[0] == "title,id"
    assert lines[1] == "Hockey Time,11"
    assert "logo" not in out


def test_render_empty_rows_yields_clean_output() -> None:
    """Test that rendering empty rows produces clean output."""
    assert render([], fmt="json") == "[]"
    assert not render([], fmt="csv")
    assert not render([], fmt="simple")


def test_render_handles_none_in_values_for_csv() -> None:
    """Test that None values are handled correctly in CSV output."""
    rows = [{"a": 1, "b": None}]
    out = render(rows, fmt="csv")
    # None becomes empty string
    assert out.splitlines() == ["a,b", "1,"]


# ---------- write_output() ------------------------------------------------
def test_write_output_to_file_creates_text_with_trailing_newline(
    tmp_path: Path,
) -> None:
    """Test that writing to file adds trailing newline."""
    out = tmp_path / "out.json"
    write_output('{"x": 1}', out, fmt="json")
    assert out.read_text() == '{"x": 1}\n'


def test_write_output_to_file_does_not_double_newline(tmp_path: Path) -> None:
    """Test that writing to file doesn't add double newlines."""
    out = tmp_path / "out.txt"
    write_output("already-has-newline\n", out, fmt="simple")
    assert out.read_text() == "already-has-newline\n"


def test_write_output_to_stdout_non_tty_writes_verbatim(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that stdout non-TTY output writes text verbatim."""
    # capsys redirects stdout, .isatty() returns False in this context.
    write_output("plain text", None, fmt="simple")
    captured = capsys.readouterr()
    assert captured.out == "plain text\n"


def test_write_output_to_stdout_non_tty_does_not_invoke_rich(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that non-TTY output doesn't use rich formatting."""
    with patch("gamesheet_sdk.output.Console") as mock_console:
        write_output('{"x": 1}', None, fmt="json")
    mock_console.assert_not_called()
    assert '{"x": 1}' in capsys.readouterr().out


def test_write_output_json_to_tty_uses_rich_syntax(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that JSON output to TTY uses rich syntax highlighting."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    with (
        patch("gamesheet_sdk.output.Console") as mock_console,
        patch("gamesheet_sdk.output.Syntax") as mock_syntax,
    ):
        write_output('{"x": 1}', None, fmt="json")
    mock_console.assert_called_once_with()
    mock_console.return_value.print.assert_called_once()
    args, kwargs = mock_syntax.call_args
    assert args[0] == '{"x": 1}'
    assert args[1] == "json"
    assert kwargs.get("theme") == "ansi_dark"


def test_write_output_yaml_to_tty_uses_rich_syntax(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that YAML output to TTY uses rich syntax highlighting."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    with (
        patch("gamesheet_sdk.output.Console") as mock_console,
        patch("gamesheet_sdk.output.Syntax") as mock_syntax,
    ):
        write_output("a: 1\n", None, fmt="yaml")
    mock_console.assert_called_once_with()
    args, _ = mock_syntax.call_args
    assert args[1] == "yaml"


def test_write_output_tabulate_to_tty_does_not_use_rich(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Tabulate formats are already nicely shaped; no syntax highlighting."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    with patch("gamesheet_sdk.output.Console") as mock_console:
        write_output("simple table text", None, fmt="simple")
    mock_console.assert_not_called()
    assert "simple table text" in capsys.readouterr().out


def test_write_output_to_file_skips_rich_even_on_tty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When a path is given, we never engage rich even if stdout is a TTY."""
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    out = tmp_path / "out.json"
    with patch("gamesheet_sdk.output.Console") as mock_console:
        write_output('{"x": 1}', out, fmt="json")
    mock_console.assert_not_called()
    assert out.read_text() == '{"x": 1}\n'


# ---------- types / values regression checks -----------------------------
def test_render_datetime_in_json_is_iso() -> None:
    """Test that datetime values are rendered as ISO format in JSON."""
    rows = [{"when": datetime(2024, 1, 1, tzinfo=timezone.utc)}]
    out = render(rows, fmt="json")
    assert "2024-01-01" in out
