# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Per-package relaxation of the ``uv`` publication cutoff.

``[tool.uv] exclude-newer`` is a cooldown: ``uv`` refuses any distribution published after the cutoff, so a
release cannot be installed the hour it lands. For a package ``uv`` is free to float that is exactly the
wanted behavior — the resolver simply picks the newest release the cutoff admits, and nothing fails.

An **exact pin cannot float**. Several convergence targets are chosen outside the resolver: a shared main hook
takes the newest git tag, a ``types-*`` stub takes the newest index release, and ``--no-uv-resolve`` takes the
newest release for everything. Each of those can write a pin the cooldown then refuses, and from that point
every ``uv lock`` in the project fails — including the ``uv-lock`` pre-commit hook, which runs on any change
to ``pyproject.toml``. ``exclude-newer-package`` exists for precisely that case: it relaxes the cutoff for one
package while leaving it in force for the rest of the graph.

This module keeps that table honest in both directions. A pinned release younger than the cutoff gains an
entry; an entry whose release has since aged past the cutoff loses it, because the global rule now admits that
release on its own and a lingering relaxation would silently exempt the package from every future cooldown.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

import tomlkit
from shared.concurrency import PARALLEL_WORKERS
from shared.exceptions import ToolError
from shared.uv_resolve import versions_from_lock
from tomlkit.exceptions import TOMLKitError

from depsync.exceptions import ParseError, WriteError
from depsync.fetchers import fetch_upload_time
from depsync.models import ExcludeNewerPolicy, ExcludeNewerResult
from depsync.overrides import current_overrides
from depsync.parsers import parse_pyproject

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping, Sequence
    from pathlib import Path

    from shared.pip_config import PipConfig
    from tomlkit import TOMLDocument
    from tomlkit.items import Key, Table

logger = logging.getLogger(__name__)

EXCLUDE_NEWER_KEY = "exclude-newer"

EXCLUDE_NEWER_PACKAGE_KEY = "exclude-newer-package"

# Fixed-length units only. Years and months are calendar-dependent, so no timedelta represents them and
# guessing 30 or 365 days would silently move the cutoff; they are rejected instead.
_UNIT_SECONDS: dict[str, float] = {
    "s": 1.0,
    "sec": 1.0,
    "secs": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "m": 60.0,
    "min": 60.0,
    "mins": 60.0,
    "minute": 60.0,
    "minutes": 60.0,
    "h": 3600.0,
    "hr": 3600.0,
    "hrs": 3600.0,
    "hour": 3600.0,
    "hours": 3600.0,
    "d": 86400.0,
    "day": 86400.0,
    "days": 86400.0,
    "w": 604800.0,
    "wk": 604800.0,
    "wks": 604800.0,
    "week": 604800.0,
    "weeks": 604800.0,
}

_SPAN_TOKEN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+)")

_ISO_DURATION = re.compile(
    r"P(?:(?P<weeks>\d+(?:\.\d+)?)W)?(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?",
    re.IGNORECASE,
)


def _normalize_name(name: str) -> str:
    """Normalize a package name to its PEP 503 form.

    Args:
        name (str): Raw package name.

    Returns:
        str: Lower-cased name with runs of separators collapsed to hyphens.

    """
    return re.sub(r"[-_.]+", "-", name).lower()


def _read_pyproject(pyproject_path: Path) -> TOMLDocument:
    """Parse ``pyproject.toml`` for round-trip editing.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.

    Returns:
        TOMLDocument: The parsed document.

    Raises:
        ParseError: If the file cannot be read or is invalid TOML.

    """
    try:
        return tomlkit.parse(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, TOMLKitError) as exc:
        msg = f"Cannot read {pyproject_path}: {exc}"
        raise ParseError(msg) from exc


def _parse_timestamp(value: str) -> datetime | None:
    """Read an absolute cutoff written as a date or RFC 3339 timestamp.

    Args:
        value (str): The value as written.

    Returns:
        datetime | None: Timezone-aware instant, or None if the value is not a date/timestamp. A bare date is
            read in the system's local timezone, matching how uv interprets one.

    """
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    return parsed if parsed.tzinfo else parsed.astimezone()


def _iso_duration(value: str) -> timedelta | None:
    """Read a span written as an ISO 8601 duration, the form ``uv.lock`` records.

    Args:
        value (str): The value as written, such as ``P7D``.

    Returns:
        timedelta | None: The span, or None if the value is not an ISO 8601 duration.

    """
    match = _ISO_DURATION.fullmatch(value.strip())
    if match is None:
        return None

    parts = {unit: float(raw) for unit, raw in match.groupdict().items() if raw is not None}

    return timedelta(**parts) if parts else None


def _span_seconds(unit: str, raw: str, value: str) -> float | None:
    """Convert one ``<number> <unit>`` token to seconds.

    Args:
        unit (str): The unit as written.
        raw (str): The numeric part as written.
        value (str): The whole value, for the warning message.

    Returns:
        float | None: Seconds, or None if the unit is not one of fixed length.

    """
    per_unit = _UNIT_SECONDS.get(unit.lower())
    if per_unit is None:
        logger.warning("Cannot interpret %r in exclude-newer value %r as a fixed-length span", unit, value)
        return None

    return float(raw) * per_unit


def _friendly_span(value: str) -> timedelta | None:
    """Read a span written the way uv accepts it in configuration, such as ``7 days``.

    Args:
        value (str): The value as written.

    Returns:
        timedelta | None: The span, or None if the value is not a duration or names a calendar unit.

    """
    tokens = list(_SPAN_TOKEN.finditer(value))
    if not tokens or _SPAN_TOKEN.sub("", value).strip():
        return None

    total = 0.0
    for token in tokens:
        seconds = _span_seconds(token.group("unit"), token.group("value"), value)
        if seconds is None:
            return None

        total += seconds

    return timedelta(seconds=total)


def _parse_span(value: str) -> timedelta | None:
    """Read a span in either notation uv accepts.

    The two are checked separately rather than short-circuited with ``or``, because a zero span is a perfectly
    valid answer and a falsy one.

    Args:
        value (str): The value as written.

    Returns:
        timedelta | None: The span, or None if the value is not a fixed-length duration.

    """
    span = _iso_duration(value)

    return _friendly_span(value) if span is None else span


def parse_cutoff(value: str) -> ExcludeNewerPolicy | None:
    """Interpret an ``exclude-newer``-style value in either of the forms uv accepts.

    Args:
        value (str): The value as written, absolute or relative.

    Returns:
        ExcludeNewerPolicy | None: The parsed policy, or None if the value is neither a timestamp nor a
            fixed-length span.

    """
    timestamp = _parse_timestamp(value)
    if timestamp is not None:
        return ExcludeNewerPolicy(raw=value, timestamp=timestamp)

    span = _parse_span(value)
    if span is None:
        return None

    return ExcludeNewerPolicy(raw=value, span=span)


def _uv_table(doc: TOMLDocument) -> Mapping[str, object] | None:
    """Return the ``[tool.uv]`` table if the document declares one.

    Args:
        doc (TOMLDocument): Parsed pyproject document.

    Returns:
        Mapping[str, object] | None: The table, or None if absent.

    """
    tbl = (doc.get("tool") or {}).get("uv")
    return cast("Mapping[str, object]", tbl) if isinstance(tbl, Mapping) else None


def parse_policy(pyproject_path: Path) -> ExcludeNewerPolicy | None:
    """Read the project-wide cutoff from ``[tool.uv] exclude-newer``.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.

    Returns:
        ExcludeNewerPolicy | None: The declared policy, or None when no cutoff is declared or its value cannot
            be interpreted. Both cases mean there is nothing to manage, so neither is an error.

    Raises:
        ParseError: If ``pyproject.toml`` cannot be read.

    """
    uv_table = _uv_table(_read_pyproject(pyproject_path))
    raw = (uv_table or {}).get(EXCLUDE_NEWER_KEY)
    if raw is None:
        logger.debug("%s declares no [tool.uv] exclude-newer", pyproject_path)
        return None

    policy = parse_cutoff(str(raw))
    if policy is None:
        logger.warning("Cannot interpret exclude-newer value %r; leaving per-package entries alone", str(raw))

    return policy


def current_entries(pyproject_path: Path) -> dict[str, str]:
    """Read the ``exclude-newer-package`` entries currently written to ``pyproject.toml``.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.

    Returns:
        dict[str, str]: Mapping of normalized package name to the value as written.

    Raises:
        ParseError: If ``pyproject.toml`` cannot be read.

    """
    uv_table = _uv_table(_read_pyproject(pyproject_path))
    declared = (uv_table or {}).get(EXCLUDE_NEWER_PACKAGE_KEY) or {}

    declared_map = cast("Mapping[Any, Any]", declared) if isinstance(declared, Mapping) else {}
    return {_normalize_name(str(name)): str(value) for name, value in declared_map.items()}


def _pyproject_pins(pyproject_path: Path) -> dict[str, str]:
    """Collect every exact pin the project declares.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.

    Returns:
        dict[str, str]: Mapping of package name to pinned version, for dependencies written as ``name==ver``.

    Raises:
        ParseError: If ``pyproject.toml`` cannot be read.

    """
    return {
        name: entries[0].version
        for name, entries in parse_pyproject(pyproject_path).items()
        if entries[0].version
    }


def _normalized(pins: Mapping[str, str]) -> dict[str, str]:
    """Re-key a pin mapping by normalized package name.

    Override pins and convergence targets arrive keyed however the source wrote them; the table is keyed the
    way uv matches, so the two have to be brought onto the same footing before they can be compared.

    Args:
        pins (Mapping[str, str]): Package name to version.

    Returns:
        dict[str, str]: The same pins, keyed by PEP 503 name.

    """
    return {_normalize_name(name): version for name, version in pins.items()}


def _locked_versions(uv_lock_path: Path) -> dict[str, str] | None:
    """Read the resolved version of every package in the lockfile.

    Args:
        uv_lock_path (Path): Path to ``uv.lock``.

    Returns:
        dict[str, str] | None: Locked versions, or None when the lockfile is missing or unreadable. None means
            "the graph is not visible", which is what stops an unmanaged entry from being retired on a guess.

    """
    if not uv_lock_path.exists():
        logger.debug("%s not found; unmanaged entries will be left alone", uv_lock_path)
        return None

    try:
        return versions_from_lock(uv_lock_path)
    except ToolError as exc:
        logger.warning("Cannot read %s (%s); unmanaged entries will be left alone", uv_lock_path, exc)
        return None


def collect_versions(
    pyproject_path: Path,
    uv_lock_path: Path,
    entries: Mapping[str, str],
    targets: Mapping[str, str],
) -> dict[str, str | None]:
    """Decide which version each package should be judged against.

    Managed pins — the project's own ``==`` requirements, its ``override-dependencies``, and the targets this
    run is about to write — are judged against that pin, because it is the version ``uv`` will be forced to
    install. A package that only appears in the table is judged against the lockfile instead, which is the
    only evidence available that it is still in the graph at all.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.
        uv_lock_path (Path): Path to ``uv.lock``.
        entries (Mapping[str, str]): Entries currently written to the table.
        targets (Mapping[str, str]): Package name to the version this run is about to pin.

    Returns:
        dict[str, str | None]: Package name to the version to judge it against. A None value marks an entry
            whose package has left the dependency graph entirely. Packages omitted from the mapping are left
            untouched.

    Raises:
        ParseError: If ``pyproject.toml`` cannot be read.

    """
    versions: dict[str, str | None] = {}
    versions.update(_pyproject_pins(pyproject_path))
    versions.update(_normalized(current_overrides(pyproject_path)))
    versions.update(_normalized(targets))

    locked = _locked_versions(uv_lock_path)
    if locked is None:
        return versions

    for package in entries:
        versions.setdefault(package, locked.get(package))

    return versions


def _pinned(versions: Mapping[str, str | None]) -> dict[str, str]:
    """Drop packages with no version to look up.

    Args:
        versions (Mapping[str, str | None]): Package name to version, possibly None.

    Returns:
        dict[str, str]: Only the entries carrying a version.

    """
    return {name: version for name, version in versions.items() if version}


def _uncached(
    versions: Mapping[str, str],
    cache: Mapping[tuple[str, str], datetime | None],
) -> dict[str, str]:
    """Select the releases whose publication time is not already known.

    Args:
        versions (Mapping[str, str]): Package name to version.
        cache (Mapping[tuple[str, str], datetime | None]): Lookups already performed this run.

    Returns:
        dict[str, str]: The subset still needing a lookup.

    """
    return {name: version for name, version in versions.items() if (name, version) not in cache}


def _lookup_upload_times(
    wanted: Mapping[str, str],
    cache: MutableMapping[tuple[str, str], datetime | None],
    *,
    index_url: str | None,
    extra_index_urls: Sequence[str],
    pip_config: PipConfig | None,
) -> None:
    """Fill *cache* with the publication time of each wanted release, in parallel.

    Args:
        wanted (Mapping[str, str]): Package name to version to look up.
        cache (MutableMapping[tuple[str, str], datetime | None]): Cache to populate, including misses so a
            second pass does not re-ask.
        index_url (str | None): Optional PEP 503 index URL.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs.
        pip_config (PipConfig | None): Pip configuration for SSL settings.

    """
    logger.debug("Looking up publication time for %d release(s)", len(wanted))

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futures = {
            pool.submit(
                fetch_upload_time,
                name,
                version,
                index_url=index_url,
                extra_index_urls=extra_index_urls,
                pip_config=pip_config,
            ): (name, version)
            for name, version in wanted.items()
        }
        for future in as_completed(futures):
            cache[futures[future]] = future.result()


def prefetch_upload_times(
    versions: Mapping[str, str | None],
    *,
    index_url: str | None = None,
    extra_index_urls: Sequence[str] = (),
    pip_config: PipConfig | None = None,
    cache: MutableMapping[tuple[str, str], datetime | None] | None = None,
) -> dict[str, datetime]:
    """Look up when each package's chosen release was published.

    Args:
        versions (Mapping[str, str | None]): Package name to the version to look up.
        index_url (str | None): Optional PEP 503 index URL.
        extra_index_urls (Sequence[str]): Additional PEP 503 index URLs.
        pip_config (PipConfig | None): Pip configuration for SSL settings.
        cache (MutableMapping[tuple[str, str], datetime | None] | None): Cache shared across the passes a run
            makes, so the second pass only pays for what the first did not already resolve.

    Returns:
        dict[str, datetime]: Package name to publication time, omitting anything that could not be determined.
            An omission is deliberate: it leaves that package's entry exactly as it is rather than acting on a
            failed lookup.

    """
    store: MutableMapping[tuple[str, str], datetime | None] = {} if cache is None else cache
    pinned = _pinned(versions)

    _lookup_upload_times(
        _uncached(pinned, store),
        store,
        index_url=index_url,
        extra_index_urls=extra_index_urls,
        pip_config=pip_config,
    )

    found = ((name, store.get((name, version))) for name, version in pinned.items())

    return {name: stamp for name, stamp in found if stamp is not None}


def _still_admits(existing: str | None, upload: datetime, now: datetime) -> bool:
    """Check whether the value already written is enough to let *upload* through.

    Keeping a sufficient value rather than recomputing it is what makes the table stable: a value derived from
    a release's age would grow by a day every day, so every run would rewrite it and ``--check`` would fail
    daily on a project nobody had touched.

    Args:
        existing (str | None): Value currently written, if any.
        upload (datetime): When the pinned release was published.
        now (datetime): Current time.

    Returns:
        bool: True if the existing value admits the release.

    """
    if existing is None:
        return False

    parsed = parse_cutoff(existing)

    return parsed is not None and parsed.admits(upload, now)


def _desired_value(
    policy: ExcludeNewerPolicy,
    existing: str | None,
    upload: datetime | None,
    now: datetime,
) -> str | None:
    """Decide what one package's entry should be.

    Args:
        policy (ExcludeNewerPolicy): The project-wide cutoff.
        existing (str | None): Value currently written, if any.
        upload (datetime | None): When the pinned release was published, or None if unknown.
        now (datetime): Current time.

    Returns:
        str | None: The value to write, or None for no entry at all.

    """
    if upload is None:
        return existing

    if policy.admits(upload, now):
        return None

    if _still_admits(existing, upload, now):
        return existing

    return policy.render(upload, now)


def _result_for(
    policy: ExcludeNewerPolicy,
    package: str,
    version: str | None,
    entries: Mapping[str, str],
    uploads: Mapping[str, datetime],
    now: datetime,
) -> ExcludeNewerResult | None:
    """Determine the change one package needs, if any.

    Args:
        policy (ExcludeNewerPolicy): The project-wide cutoff.
        package (str): Package name.
        version (str | None): Version to judge against, or None if the package left the graph.
        entries (Mapping[str, str]): Entries currently written.
        uploads (Mapping[str, datetime]): Package name to publication time.
        now (datetime): Current time.

    Returns:
        ExcludeNewerResult | None: The change, or None if the entry is already what it should be.

    """
    old_value = entries.get(package)
    new_value = None if version is None else _desired_value(policy, old_value, uploads.get(package), now)
    if new_value == old_value:
        return None

    return ExcludeNewerResult(
        package=package,
        version=version,
        old_value=old_value,
        new_value=new_value,
    )


def converge_exclude_newer(
    policy: ExcludeNewerPolicy,
    entries: Mapping[str, str],
    versions: Mapping[str, str | None],
    uploads: Mapping[str, datetime],
    now: datetime,
) -> list[ExcludeNewerResult]:
    """Work out every change the ``exclude-newer-package`` table needs.

    Args:
        policy (ExcludeNewerPolicy): The project-wide cutoff.
        entries (Mapping[str, str]): Entries currently written.
        versions (Mapping[str, str | None]): Package name to the version to judge it against.
        uploads (Mapping[str, datetime]): Package name to publication time.
        now (datetime): Current time, supplied by the caller so a run is reproducible.

    Returns:
        list[ExcludeNewerResult]: One result per package whose entry should change, package-name ordered.

    """
    results: list[ExcludeNewerResult] = []
    for package in sorted(versions):
        result = _result_for(policy, package, versions[package], entries, uploads, now)
        if result is not None:
            results.append(result)

    return results


def apply_results(
    entries: Mapping[str, str],
    results: Iterable[ExcludeNewerResult],
) -> dict[str, str]:
    """Fold converged changes into the table that should end up on disk.

    Entries no result mentions are carried through untouched — those are the packages this run could not see,
    and dropping them would retire a relaxation on the strength of a failed lookup.

    Args:
        entries (Mapping[str, str]): Entries currently written.
        results (Iterable[ExcludeNewerResult]): Converged changes.

    Returns:
        dict[str, str]: The complete table to write.

    """
    desired = dict(entries)
    for result in results:
        if result.new_value is None:
            desired.pop(result.package, None)
        else:
            desired[result.package] = result.new_value

    return desired


def _rewrite_entries(uv_table: Table, desired: Mapping[str, str]) -> None:
    """Replace the managed dotted keys in ``[tool.uv]``, sorted, in one block.

    The whole block is rebuilt rather than patched key by key, because tomlkit's out-of-order table proxy does
    not survive an interleaved delete and insert, and because rebuilding is the only way to keep the block
    sorted as packages come and go.

    Args:
        uv_table (Table): The ``[tool.uv]`` table, mutated in place.
        desired (Mapping[str, str]): The complete table to write.

    """
    if EXCLUDE_NEWER_PACKAGE_KEY in uv_table:
        del uv_table[EXCLUDE_NEWER_PACKAGE_KEY]

    # tomlkit exposes no public positional insert. Appending instead would drop the block at the end of
    # [tool.uv], detaching it from the `exclude-newer` line it qualifies; anchoring each key to its
    # predecessor keeps the two together and the diff limited to the entries that actually changed.
    anchor: Key = tomlkit.key(EXCLUDE_NEWER_KEY)
    for name, value in sorted(desired.items()):
        entry = tomlkit.key([EXCLUDE_NEWER_PACKAGE_KEY, name])
        uv_table.value._insert_after(anchor, entry, tomlkit.item(value))  # noqa: SLF001
        anchor = entry


def update_pyproject_exclude_newer(pyproject_path: Path, desired: Mapping[str, str]) -> int:
    """Write the ``exclude-newer-package`` table into ``pyproject.toml``.

    Args:
        pyproject_path (Path): Path to ``pyproject.toml``.
        desired (Mapping[str, str]): The complete table to write.

    Returns:
        int: Number of entries written.

    Raises:
        WriteError: If ``pyproject.toml`` has no ``[tool.uv]`` table, or cannot be read or written.

    """
    try:
        doc = _read_pyproject(pyproject_path)
    except ParseError as exc:
        raise WriteError(str(exc)) from exc

    uv_table = _uv_table(doc)
    if uv_table is None:
        msg = f"{pyproject_path} has no [tool.uv] table"
        raise WriteError(msg)

    _rewrite_entries(cast("Table", uv_table), desired)

    try:
        pyproject_path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    except OSError as exc:
        msg = f"Cannot write {pyproject_path}: {exc}"
        raise WriteError(msg) from exc

    logger.info("Wrote %d exclude-newer-package entries in %s", len(desired), pyproject_path)

    return len(desired)
