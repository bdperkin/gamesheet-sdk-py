# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Unit tests for the syncdeps transitive-dependency override subsystem.

``tools/`` sits outside ``[tool.coverage] run.source``, so these do not feed the 100% gate; they exist to pin
the decision logic that governs whether a security override is written, retired, or rolled back.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS_DIR) not in sys.path:  # pragma: no cover - import side effect
    sys.path.insert(0, str(TOOLS_DIR))

from depsync.exceptions import ParseError, VerifyError, WriteError  # noqa: E402
from depsync.models import OverridePolicy, OverrideResult  # noqa: E402
from depsync.overrides import (  # noqa: E402
    converge_overrides,
    current_overrides,
    parse_overrides,
    run_verify,
    update_pyproject_overrides,
)

POLICY_YAML = (
    "---\n"
    "overrides:\n"
    "  - package: mcp\n"
    "    pinned_by: semgrep\n"
    '    floor: ">=1.28.1"\n'
    '    ceiling: "<2"\n'
    "    reason: semgrep hard-pins a vulnerable mcp.\n"
    '    verify: python -c "import sys"\n'
    "    review: 2026-11-09\n"
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


def _policy(**overrides: object) -> OverridePolicy:
    """Build an OverridePolicy with sensible defaults.

    Args:
        **overrides (object): Fields to override on the default policy.

    Returns:
        OverridePolicy: The constructed policy.
    """
    fields: dict[str, object] = {
        "package": "mcp",
        "pinned_by": "semgrep",
        "floor": ">=1.28.1",
        "ceiling": "<2",
        "reason": "because",
        "review": "2026-11-09",
    }
    fields.update(overrides)
    return OverridePolicy.model_validate(fields)


def test_parse_overrides_missing_file_is_not_an_error(tmp_path: Path) -> None:
    """A project with no override policy file simply declares no overrides."""
    assert parse_overrides(tmp_path / "absent.yaml") == []


def test_parse_overrides_reads_policy(tmp_path: Path) -> None:
    """Test that a well-formed policy file round-trips into an OverridePolicy."""
    policies = parse_overrides(_write(tmp_path / "o.yaml", POLICY_YAML))

    assert len(policies) == 1
    policy = policies[0]
    assert policy.package == "mcp"
    assert policy.pinned_by == "semgrep"
    assert policy.review.isoformat() == "2026-11-09"
    assert policy.specifier() == "mcp>=1.28.1,<2"


def test_specifier_without_ceiling_is_floor_only() -> None:
    """Test that omitting the ceiling yields a floor-only requirement."""
    assert _policy(ceiling=None).specifier() == "mcp>=1.28.1"


def test_parse_overrides_rejects_missing_required_field(tmp_path: Path) -> None:
    """Test that an entry lacking a required field is a ParseError, not a silent skip."""
    text = '---\noverrides:\n  - package: mcp\n    floor: ">=1"\n'

    with pytest.raises(ParseError, match="Invalid override entry"):
        parse_overrides(_write(tmp_path / "o.yaml", text))


def test_parse_overrides_rejects_unparseable_bounds(tmp_path: Path) -> None:
    """Test that a malformed specifier fails loudly instead of excluding every candidate."""
    text = (
        "---\noverrides:\n  - package: mcp\n    pinned_by: semgrep\n"
        '    floor: "=>1.28.1"\n    reason: typo\n    review: 2026-11-09\n'
    )

    with pytest.raises(ParseError, match="Invalid bounds"):
        parse_overrides(_write(tmp_path / "o.yaml", text))


def test_parse_overrides_rejects_invalid_yaml(tmp_path: Path) -> None:
    """Test that unparseable YAML raises ParseError."""
    with pytest.raises(ParseError, match="Cannot parse"):
        parse_overrides(_write(tmp_path / "o.yaml", "overrides:\n  - [unclosed\n"))


def test_current_overrides_reads_exact_pins_only(tmp_path: Path) -> None:
    """Test that only ``name==version`` entries are treated as managed pins."""
    text = '[tool.uv]\noverride-dependencies = [\n  "mcp==1.29.0",\n  "other>=2",\n]\n'

    assert current_overrides(_write(tmp_path / "pyproject.toml", text)) == {"mcp": "1.29.0"}


def test_current_overrides_absent_section_is_empty(tmp_path: Path) -> None:
    """Test that a pyproject with no override list yields no pins."""
    assert current_overrides(_write(tmp_path / "pyproject.toml", "[project]\nname = 'x'\n")) == {}


def test_converge_overrides_targets_bounded_resolution() -> None:
    """Test that the bounded resolution supplies the target pin."""
    results = converge_overrides(
        [_policy()],
        {"mcp": "1.28.1"},
        {"mcp": "1.29.0"},
        {"mcp": "1.23.3"},
    )

    assert len(results) == 1
    assert results[0].old_version == "1.28.1"
    assert results[0].new_version == "1.29.0"


def test_converge_overrides_declines_retirement_below_floor() -> None:
    """Test that an override stays when the unpinned resolution misses the floor."""
    results = converge_overrides([_policy()], {}, {"mcp": "1.29.0"}, {"mcp": "1.23.3"})

    assert results[0].retirable is False
    assert results[0].unpinned_version == "1.23.3"


def test_converge_overrides_flags_retirement_at_floor() -> None:
    """Test that an override is retirable once upstream satisfies the floor on its own."""
    results = converge_overrides([_policy()], {}, {"mcp": "1.29.0"}, {"mcp": "1.28.1"})

    assert results[0].retirable is True


def test_converge_overrides_skips_unresolved_package() -> None:
    """Test that a package uv did not resolve is skipped rather than guessed at."""
    assert converge_overrides([_policy()], {}, {}, {}) == []


def test_converge_overrides_unparseable_unpinned_version_is_not_retirable() -> None:
    """Test that a version we cannot compare keeps the override in place."""
    results = converge_overrides([_policy()], {}, {"mcp": "1.29.0"}, {"mcp": "not-a-version"})

    assert results[0].retirable is False


def test_update_pyproject_overrides_rewrites_existing_entry(tmp_path: Path) -> None:
    """Test that an existing pin is rewritten and unmanaged entries survive."""
    path = _write(
        tmp_path / "pyproject.toml",
        '[tool.uv]\noverride-dependencies = [\n  "mcp==1.28.1",\n  "keepme>=1",\n]\n',
    )
    result = OverrideResult(package="mcp", old_version="1.28.1", new_version="1.29.0")

    assert update_pyproject_overrides(path, [result]) == 1
    body = path.read_text(encoding="utf-8")
    assert "mcp==1.29.0" in body
    assert "keepme>=1" in body


def test_update_pyproject_overrides_appends_new_entry(tmp_path: Path) -> None:
    """Test that a newly declared policy is appended rather than dropped."""
    path = _write(tmp_path / "pyproject.toml", "[tool.uv]\npackage = true\n")
    result = OverrideResult(package="mcp", old_version=None, new_version="1.29.0")

    assert update_pyproject_overrides(path, [result]) == 1
    assert "mcp==1.29.0" in path.read_text(encoding="utf-8")


def test_update_pyproject_overrides_creates_missing_tables(tmp_path: Path) -> None:
    """Test that a project declaring its first override gets the tables materialized."""
    path = _write(tmp_path / "pyproject.toml", '[project]\nname = "x"\n')
    result = OverrideResult(package="mcp", old_version=None, new_version="1.29.0")

    assert update_pyproject_overrides(path, [result]) == 1
    body = path.read_text(encoding="utf-8")
    assert "[tool.uv]" in body
    assert "mcp==1.29.0" in body


def test_update_pyproject_overrides_noop_when_unchanged(tmp_path: Path) -> None:
    """Test that an unchanged pin writes nothing at all."""
    path = _write(tmp_path / "pyproject.toml", '[tool.uv]\noverride-dependencies = [\n  "mcp==1.29.0",\n]\n')
    before = path.read_text(encoding="utf-8")
    result = OverrideResult(package="mcp", old_version="1.29.0", new_version="1.29.0")

    assert update_pyproject_overrides(path, [result]) == 0
    assert path.read_text(encoding="utf-8") == before


def test_update_pyproject_overrides_unreadable_file_raises(tmp_path: Path) -> None:
    """Test that an unreadable pyproject surfaces as WriteError."""
    result = OverrideResult(package="mcp", old_version=None, new_version="1.29.0")

    with pytest.raises(WriteError, match="Cannot read"):
        update_pyproject_overrides(tmp_path / "absent.toml", [result])


def test_run_verify_without_command_is_a_noop() -> None:
    """Test that a policy declaring no verify command does nothing."""
    run_verify(_policy(verify=None))


def test_run_verify_passes_on_zero_exit() -> None:
    """Test that a command exiting 0 is accepted."""
    run_verify(_policy(verify=f'"{sys.executable}" -c "import sys"'))


def test_run_verify_raises_on_nonzero_exit() -> None:
    """Test that a failing verify command raises VerifyError with the output attached."""
    command = f'"{sys.executable}" -c "import sys; sys.stderr.write(\'boom\'); sys.exit(1)"'

    with pytest.raises(VerifyError, match="boom"):
        run_verify(_policy(verify=command))


def test_run_verify_raises_when_command_missing() -> None:
    """Test that an unexecutable command raises VerifyError rather than escaping as OSError."""
    with pytest.raises(VerifyError, match="Cannot run verify command"):
        run_verify(_policy(verify="definitely-not-a-real-binary-9f2c"))


def test_run_verify_raises_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a hanging verify command is reported as a timeout, not left to block."""

    def _timeout(*_args: object, **_kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd="x", timeout=1)

    monkeypatch.setattr(subprocess, "run", _timeout)

    with pytest.raises(VerifyError, match="timed out"):
        run_verify(_policy(verify="anything"))


@pytest.mark.parametrize(
    ("unpinned", "expected"),
    [("1.28.1", True), ("1.29.0", True), ("1.28.0", False), ("1.23.3", False)],
)
def test_retirement_boundary(unpinned: str, expected: bool) -> None:
    """Test retirement exactly at, above, and below the declared floor.

    Args:
        unpinned (str): Version the resolution yields without the override.
        expected (bool): Whether that should count as retirable.
    """
    results = converge_overrides([_policy()], {}, {"mcp": "1.29.0"}, {"mcp": unpinned})

    assert results[0].retirable is expected
