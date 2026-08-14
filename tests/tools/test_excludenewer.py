# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for the syncdeps per-package ``exclude-newer`` subsystem.

``tools/`` sits outside ``[tool.coverage] run.source``, so these do not feed the 100% gate; they exist to pin
the decision logic that governs when a publication cutoff is relaxed for one package and when that relaxation
is retired.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:  # pragma: no cover - import side effect
    sys.path.insert(0, str(TOOLS_DIR))

from depsync.exceptions import ParseError, WriteError
from depsync.excludenewer import (
    apply_results,
    collect_versions,
    converge_exclude_newer,
    current_entries,
    parse_cutoff,
    parse_policy,
    update_pyproject_exclude_newer,
)

NOW = datetime(2026, 8, 12, 17, 0, tzinfo=UTC)

PYPROJECT = (
    "[project]\n"
    'name = "demo"\n'
    'requires-python = ">=3.11"\n'
    "dependencies = [\n"
    '  "requests==2.32.5",\n'
    '  "semgrep==1.172.0",\n'
    "]\n"
    "\n"
    "[tool.uv]\n"
    "override-dependencies = [\n"
    '  "mcp==1.29.0",\n'
    "]\n"
    'exclude-newer = "7 days"\n'
    'exclude-newer-package.semgrep = "1 days"\n'
    "package = true\n"
)


def _write(path: Path, text: str) -> Path:
    """Write *text* to *path* and return it.

    Args:
        path (Path): Destination file.
        text (str): Contents to write.

    Returns:
        Path: The written path, for chaining.

    """
    path.write_text(text, encoding="utf-8")
    return path


def _pyproject(tmp_path: Path, text: str = PYPROJECT) -> Path:
    """Write a pyproject.toml into *tmp_path*.

    Args:
        tmp_path (Path): Directory to write into.
        text (str): File contents.

    Returns:
        Path: Path to the written file.

    """
    return _write(tmp_path / "pyproject.toml", text)


def _ago(**delta: float) -> datetime:
    """Return an instant relative to the fixed test clock.

    Args:
        **delta (float): Keyword arguments for :class:`datetime.timedelta`.

    Returns:
        datetime: ``NOW`` minus the given offset.

    """
    return NOW - timedelta(**delta)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("7 days", timedelta(days=7)),
        ("1 day", timedelta(days=1)),
        ("0 days", timedelta()),
        ("36 hours", timedelta(hours=36)),
        ("1 week 2 hours", timedelta(weeks=1, hours=2)),
        ("P7D", timedelta(days=7)),
        ("PT0S", timedelta()),
    ],
)
def test_parse_cutoff_reads_spans(value: str, expected: timedelta) -> None:
    """Test that both the friendly and ISO 8601 duration notations are understood."""
    policy = parse_cutoff(value)

    assert policy is not None
    assert policy.span == expected
    assert policy.timestamp is None


def test_parse_cutoff_reads_absolute_timestamp() -> None:
    """Test that an RFC 3339 value is read as an absolute cutoff."""
    policy = parse_cutoff("2026-08-05T12:00:00Z")

    assert policy is not None
    assert policy.timestamp == datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    assert policy.span is None


def test_parse_cutoff_reads_bare_date_in_local_time() -> None:
    """Test that a bare date becomes local midnight, which is how uv reads one."""
    policy = parse_cutoff("2026-08-05")

    assert policy is not None
    assert policy.timestamp is not None
    assert policy.timestamp.tzinfo is not None
    assert policy.timestamp.date().isoformat() == "2026-08-05"


@pytest.mark.parametrize("value", ["3 months", "1 year", "banana", "", "P"])
def test_parse_cutoff_rejects_unusable_values(value: str) -> None:
    """Test that calendar units and nonsense yield None rather than a guessed span.

    A guessed month would move the cutoff silently; declining to interpret it leaves the table alone.
    """
    assert parse_cutoff(value) is None


def test_zero_span_is_not_confused_with_absence() -> None:
    """Test that ``0 days`` parses, since a falsy span is still a real answer."""
    policy = parse_cutoff("0 days")

    assert policy is not None
    assert policy.cutoff(NOW) == NOW


def test_render_span_floors_to_whole_days() -> None:
    """Test that a span policy renders the narrowest relaxation that still admits the release."""
    policy = parse_cutoff("7 days")

    assert policy is not None
    assert policy.render(_ago(days=5, hours=12), NOW) == "5 days"
    assert policy.render(_ago(hours=2), NOW) == "0 days"


def test_render_timestamp_rounds_up_to_the_second() -> None:
    """Test that a rendered timestamp never lands before the upload it exists to admit."""
    policy = parse_cutoff("2026-08-05")
    upload = datetime(2026, 8, 12, 14, 22, 31, 500000, tzinfo=UTC)

    assert policy is not None
    assert policy.render(upload, NOW) == "2026-08-12T14:22:32Z"


def test_parse_policy_reads_declared_cutoff(tmp_path: Path) -> None:
    """Test that the project-wide cutoff is read from ``[tool.uv]``."""
    policy = parse_policy(_pyproject(tmp_path))

    assert policy is not None
    assert policy.raw == "7 days"


def test_parse_policy_absent_cutoff_is_not_an_error(tmp_path: Path) -> None:
    """Test that a project declaring no cutoff simply has nothing to manage."""
    assert parse_policy(_pyproject(tmp_path, "[project]\nname = 'x'\n")) is None


def test_parse_policy_unusable_cutoff_is_not_an_error(tmp_path: Path) -> None:
    """Test that a cutoff we cannot interpret disables the stage instead of failing the run."""
    text = '[tool.uv]\nexclude-newer = "3 months"\n'

    assert parse_policy(_pyproject(tmp_path, text)) is None


def test_parse_policy_rejects_unreadable_file(tmp_path: Path) -> None:
    """Test that invalid TOML raises ParseError."""
    with pytest.raises(ParseError, match="Cannot read"):
        parse_policy(_pyproject(tmp_path, "[tool.uv\n"))


def test_current_entries_normalizes_names(tmp_path: Path) -> None:
    """Test that entry keys are read in the normalized form uv matches on."""
    text = '[tool.uv]\nexclude-newer-package.Types_Setuptools = "0 days"\n'

    assert current_entries(_pyproject(tmp_path, text)) == {"types-setuptools": "0 days"}


def test_current_entries_absent_table_is_empty(tmp_path: Path) -> None:
    """Test that a project with no relaxations yields no entries."""
    assert current_entries(_pyproject(tmp_path, "[project]\nname = 'x'\n")) == {}


def test_collect_versions_covers_pins_and_overrides(tmp_path: Path) -> None:
    """Test that declared pins, override pins, and this run's targets are all judged."""
    versions = collect_versions(
        _pyproject(tmp_path),
        tmp_path / "absent.lock",
        {},
        {"semgrep": "1.173.0"},
    )

    assert versions["requests"] == "2.32.5"
    assert versions["mcp"] == "1.29.0"
    assert versions["semgrep"] == "1.173.0"


def test_collect_versions_judges_unmanaged_entries_by_the_lockfile(tmp_path: Path) -> None:
    """Test that an entry the project does not pin is judged against the locked version."""
    lock = _write(
        tmp_path / "uv.lock",
        '[[package]]\nname = "rich"\nversion = "14.3.4"\n',
    )

    versions = collect_versions(_pyproject(tmp_path), lock, {"rich": "1 days", "gone": "0 days"}, {})

    assert versions["rich"] == "14.3.4"
    assert versions["gone"] is None


def test_collect_versions_without_a_lockfile_leaves_unmanaged_entries_alone(tmp_path: Path) -> None:
    """Test that an invisible graph is not treated as evidence that an entry is dead."""
    versions = collect_versions(
        _pyproject(tmp_path),
        tmp_path / "absent.lock",
        {"rich": "1 days"},
        {},
    )

    assert "rich" not in versions


def test_converge_adds_entry_for_a_release_inside_the_cutoff() -> None:
    """Test that a pin younger than the cutoff gains the narrowest relaxation that admits it."""
    policy = parse_cutoff("7 days")
    assert policy is not None

    results = converge_exclude_newer(
        policy,
        {},
        {"semgrep": "1.172.0"},
        {"semgrep": _ago(days=1, hours=20)},
        NOW,
    )

    assert [(r.package, r.action, r.new_value) for r in results] == [("semgrep", "add", "1 days")]


def test_converge_leaves_an_old_release_alone() -> None:
    """Test that a pin the global cutoff already admits gets no entry."""
    policy = parse_cutoff("7 days")
    assert policy is not None

    assert converge_exclude_newer(policy, {}, {"requests": "2.32.5"}, {"requests": _ago(days=90)}, NOW) == []


def test_converge_retires_an_entry_once_its_release_ages_out() -> None:
    """Test that a relaxation is dropped once the global cutoff admits the release on its own.

    Leaving it would exempt the package from every future cooldown without saying so.
    """
    policy = parse_cutoff("7 days")
    assert policy is not None

    results = converge_exclude_newer(
        policy,
        {"semgrep": "1 days"},
        {"semgrep": "1.172.0"},
        {"semgrep": _ago(days=8)},
        NOW,
    )

    assert [(r.package, r.action, r.new_value) for r in results] == [("semgrep", "remove", None)]


def test_converge_retires_an_entry_whose_package_left_the_graph() -> None:
    """Test that an entry for a package no longer in the lockfile is removed."""
    policy = parse_cutoff("7 days")
    assert policy is not None

    results = converge_exclude_newer(policy, {"gone": "2 days"}, {"gone": None}, {}, NOW)

    assert [(r.package, r.action) for r in results] == [("gone", "remove")]


def test_converge_keeps_a_sufficient_existing_value() -> None:
    """Test that a still-valid entry is left exactly as written.

    Recomputing it from the release's age would grow the value by a day every day, so every run would rewrite
    the table and ``--check`` would fail daily on a project nobody had touched.
    """
    policy = parse_cutoff("7 days")
    assert policy is not None

    assert (
        converge_exclude_newer(
            policy,
            {"semgrep": "1 days"},
            {"semgrep": "1.172.0"},
            {"semgrep": _ago(days=4)},
            NOW,
        )
        == []
    )


def test_converge_tightens_an_insufficient_existing_value() -> None:
    """Test that a pin moving to a newer release rewrites an entry that no longer admits it."""
    policy = parse_cutoff("7 days")
    assert policy is not None

    results = converge_exclude_newer(
        policy,
        {"semgrep": "5 days"},
        {"semgrep": "1.173.0"},
        {"semgrep": _ago(hours=3)},
        NOW,
    )

    assert [(r.action, r.old_value, r.new_value) for r in results] == [("update", "5 days", "0 days")]


def test_converge_leaves_a_package_alone_when_its_release_date_is_unknown() -> None:
    """Test that a failed lookup changes nothing, rather than retiring a relaxation on no evidence."""
    policy = parse_cutoff("7 days")
    assert policy is not None

    assert converge_exclude_newer(policy, {"semgrep": "1 days"}, {"semgrep": "1.172.0"}, {}, NOW) == []


def test_converge_under_an_absolute_cutoff_writes_a_timestamp() -> None:
    """Test that an absolute cutoff yields per-package timestamps rather than spans."""
    policy = parse_cutoff("2026-08-05T00:00:00Z")
    assert policy is not None

    results = converge_exclude_newer(
        policy,
        {},
        {"semgrep": "1.172.0"},
        {"semgrep": datetime(2026, 8, 10, 9, 30, tzinfo=UTC)},
        NOW,
    )

    assert [r.new_value for r in results] == ["2026-08-10T09:30:00Z"]


def test_apply_results_carries_unmentioned_entries_through() -> None:
    """Test that packages this run could not see keep their entries."""
    policy = parse_cutoff("7 days")
    assert policy is not None

    results = converge_exclude_newer(policy, {}, {"semgrep": "1.172.0"}, {"semgrep": _ago(hours=1)}, NOW)

    assert apply_results({"unseen": "2 days"}, results) == {"unseen": "2 days", "semgrep": "0 days"}


def test_update_pyproject_writes_sorted_entries_beneath_the_cutoff(tmp_path: Path) -> None:
    """Test that the managed block stays sorted and attached to the ``exclude-newer`` line."""
    path = _pyproject(tmp_path)

    update_pyproject_exclude_newer(path, {"semgrep": "0 days", "attrs": "2 days"})

    body = path.read_text(encoding="utf-8")
    assert 'exclude-newer = "7 days"\n' in body
    assert body.index("exclude-newer-package.attrs") < body.index("exclude-newer-package.semgrep")
    assert body.index("exclude-newer-package.semgrep") < body.index("package = true")


def test_update_pyproject_round_trips_unrelated_content(tmp_path: Path) -> None:
    """Test that rewriting the table leaves the rest of the file byte-identical."""
    path = _pyproject(tmp_path)

    update_pyproject_exclude_newer(path, current_entries(path))

    assert path.read_text(encoding="utf-8") == PYPROJECT


def test_update_pyproject_removes_the_table_when_nothing_is_needed(tmp_path: Path) -> None:
    """Test that an empty table leaves no orphaned keys behind."""
    path = _pyproject(tmp_path)

    assert update_pyproject_exclude_newer(path, {}) == 0
    assert "exclude-newer-package" not in path.read_text(encoding="utf-8")


def test_update_pyproject_requires_a_uv_table(tmp_path: Path) -> None:
    """Test that writing into a project with no ``[tool.uv]`` table fails loudly."""
    path = _pyproject(tmp_path, "[project]\nname = 'x'\n")

    with pytest.raises(WriteError, match=r"has no \[tool\.uv\] table"):
        update_pyproject_exclude_newer(path, {"semgrep": "0 days"})
