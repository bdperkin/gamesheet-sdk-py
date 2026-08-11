# syncdeps

<!--TOC-->

______________________________________________________________________

- [1. Overview](#1-overview)
- [2. Architecture](#2-architecture)
  - [2.1. Execution Pipeline](#21-execution-pipeline)
- [3. Prerequisites](#3-prerequisites)
  - [3.1. Python Version](#31-python-version)
  - [3.2. Python Packages](#32-python-packages)
  - [3.3. External Tools](#33-external-tools)
- [4. Usage](#4-usage)
  - [4.1. Basic Usage](#41-basic-usage)
  - [4.2. Dry Run (Preview Only)](#42-dry-run-preview-only)
  - [4.3. Debug Logging](#43-debug-logging)
  - [4.4. CLI Options](#44-cli-options)
- [5. Convergence Algorithm](#5-convergence-algorithm)
  - [5.1. Version targets](#51-version-targets)
  - [5.2. Shared Main Hooks](#52-shared-main-hooks)
  - [5.3. Shared Additional Dependencies](#53-shared-additional-dependencies)
  - [5.4. PyPI-Only Dependencies](#54-pypi-only-dependencies)
  - [5.5. Pre-commit-Only Repos](#55-pre-commit-only-repos)
  - [5.6. Pre-commit-Only Additional Dependencies](#56-pre-commit-only-additional-dependencies)
  - [5.7. Version Prefix Preservation](#57-version-prefix-preservation)
  - [5.8. Filtered Dependencies](#58-filtered-dependencies)
  - [5.9. Transitive-Dependency Overrides](#59-transitive-dependency-overrides)
  - [5.10. Capped Pins and the Dependabot Ignore List](#510-capped-pins-and-the-dependabot-ignore-list)
- [6. Exception Hierarchy](#6-exception-hierarchy)
- [7. Dependencies](#7-dependencies)
- [8. Troubleshooting](#8-troubleshooting)
- [9. Related Tools](#9-related-tools)
- [10. Files](#10-files)

______________________________________________________________________

<!--TOC-->

## 1. Overview

`syncdeps` performs **bidirectional dependency convergence** between `pyproject.toml` and `.pre-commit-config.yaml`. It ensures that pinned versions in both
files stay synchronized by querying PyPI and git tags for the latest stable releases, then applying the appropriate updates while preserving file formatting and
comments.

Unlike the legacy `cideps` script, `syncdeps` is a modular package that:

- Handles **all** dependency categories in a single pass (no exit-on-first-mismatch)
- Supports `--dry-run` to preview changes without modifying files
- Directly updates all three files: `pyproject.toml`, `.pre-commit-config.yaml`, and `.genprecommitconfig.yaml` (additional_dependencies only)
- Uses `rich` for structured output tables and progress reporting
- Preserves file formatting via `tomlkit` (TOML) and `ruamel.yaml` (YAML)

## 2. Architecture

The tool follows the same modular package pattern as `tools/precommit/`.

| Component   | File                          | Purpose                                                             |
| ----------- | ----------------------------- | ------------------------------------------------------------------- |
| Entry point | `tools/syncdeps`              | Thin wrapper that imports and runs `depsync.cli.app`                |
| CLI         | `tools/depsync/cli.py`        | Click/rich-click command with options and output formatting         |
| Config      | `tools/depsync/config.py`     | Constants, default paths, PyPI↔git repo mapping table               |
| Models      | `tools/depsync/models.py`     | Pydantic v2 models for dependencies, repos, and results             |
| Exceptions  | `tools/depsync/exceptions.py` | Exception hierarchy with exit codes                                 |
| Parsers     | `tools/depsync/parsers.py`    | Parse `pyproject.toml` and `.pre-commit-config.yaml`                |
| Fetchers    | `tools/depsync/fetchers.py`   | Query PyPI JSON API and `git ls-remote` for versions                |
| Engine      | `tools/depsync/engine.py`     | Core convergence algorithm                                          |
| Type stubs  | `tools/depsync/typestubs.py`  | `types-*` stub discovery and synchronization                        |
| Writers     | `tools/depsync/writers.py`    | Style-preserving file updates                                       |
| Resolver    | `tools/shared/uv_resolve.py`  | Delegates resolution to `uv lock`; shared with `genprecommitconfig` |
| Shared      | `tools/shared/`               | Shared utilities (HTTP, git, logging, TOML, exceptions)             |

### 2.1. Execution Pipeline

| Phase       | Description                                                                            |
| ----------- | -------------------------------------------------------------------------------------- |
| 1. Parse    | Read `pyproject.toml` and `.pre-commit-config.yaml`                                    |
| 2. Resolve  | Ask `uv lock` which versions can co-exist (see [Version targets](#51-version-targets)) |
| 3. Map      | Build bidirectional PyPI↔git repo mappings                                             |
| 4. Prefetch | Fetch all PyPI versions and git tags in parallel                                       |
| 5. Converge | Determine updates for each dependency category                                         |
| 6. Display  | Show results table                                                                     |
| 7. Write    | Apply updates to all three files directly                                              |

## 3. Prerequisites

### 3.1. Python Version

- Python 3.11 or later

### 3.2. Python Packages

Installed via the `syncdeps` optional-dependency group in `pyproject.toml`:

- `packaging` — Semantic version parsing and comparison
- `requests` — PyPI JSON API queries
- `rich-click` — CLI framework with rich formatting
- `ruamel.yaml` — Round-trip YAML reading/writing
- `tomlkit` — Round-trip TOML reading/writing

Core dependencies (already installed):

- `rich` — Terminal UI (tables, logging)

### 3.3. External Tools

- `uv` — performs dependency resolution (see [Version targets](#51-version-targets)). Required unless `--no-uv-resolve` is passed.
- `git` — tag discovery via `git ls-remote`.

## 4. Usage

### 4.1. Basic Usage

```console
./tools/syncdeps
```

### 4.2. Dry Run (Preview Only)

```console
./tools/syncdeps --dry-run
```

### 4.3. Debug Logging

```console
./tools/syncdeps --log-level=debug
```

### 4.4. CLI Options

| Option                  | Default                    | Description                                                   |
| ----------------------- | -------------------------- | ------------------------------------------------------------- |
| `--pyproject`           | `pyproject.toml`           | Path to pyproject.toml                                        |
| `--precommit-config`    | `.pre-commit-config.yaml`  | Path to .pre-commit-config.yaml                               |
| `--genprecommit-config` | `.genprecommitconfig.yaml` | Path to .genprecommitconfig.yaml                              |
| `--dependabot`          | `.github/dependabot.yml`   | Path to dependabot.yml (ignores synced with pins + overrides) |
| `--overrides`           | `.syncdepsoverrides.yaml`  | Path to the transitive-dependency override policy file        |
| `--uv-lock`             | `uv.lock`                  | Path to uv.lock (used with `--sync-types`)                    |
| `--log-level`           | `info`                     | Logging verbosity (debug, info, warning, error)               |
| `--dry-run`             | off                        | Show changes without modifying files                          |
| `--sync-types`          | off                        | Sync `types-*` stub packages in the `type-stubs` group        |
| `--no-uv-resolve`       | off                        | Skip uv resolution; pin each package to its latest release    |
| `--backup`              | off                        | Write `.bak` copies before modifying any file                 |
| `--check`               | off                        | Exit 1 if any file would be modified (writes nothing)         |
| `--diff`                | off                        | Show a unified diff of the changes                            |
| `--version`             | —                          | Show version and exit                                         |
| `--help`                | —                          | Show help and exit                                            |

`--dry-run`, `--check`, and `--diff` never leave changes behind. Producing a diff requires really writing the files, so the rollback runs in a `finally` block —
an exception, a `SIGPIPE` from a truncated pager, or a `Ctrl-C` mid-render cannot turn a preview into a commit.

## 5. Convergence Algorithm

### 5.1. Version targets

**Resolution is delegated to `uv`.** Choosing the newest release of each package independently produces pins that cannot co-exist — one package's own
requirements may cap a sibling below its latest release. For example, `python-semantic-release==10.6.1` requires `rich~=14.0` and `tomlkit>=0.13,<0.14`, so
pinning `rich` and `tomlkit` to their newest releases yields a `pyproject.toml` that `uv lock` rejects as unsatisfiable.

Rather than reimplement a resolver, the tool asks `uv` for the answer:

1. Copy `pyproject.toml` to a scratch directory, rewriting each managed `==` pin to a bare requirement. No lockfile is copied in, so the resolution is unbiased
   by previous choices. The real project directory is never touched.
2. Revs pinned in `.genprecommitconfig.yaml` are **kept as exact pins** instead of relaxed, so the resolution bends around them rather than proposing versions
   that contradict the pre-commit config.
3. Run `uv lock` there and harvest the chosen versions.

Whatever `uv` resolved is authoritative for every package it covers, which makes the pins written back **lockable by construction**. Packages outside the
project graph — chiefly pre-commit-only `additional_dependencies`, which install into their own isolated hook environments — fall back to the latest index
release compatible with `requires-python`.

If `uv lock` finds no solution even with the pins relaxed, that is a genuine pre-existing conflict and the tool surfaces uv's own error rather than writing
something broken. Pass `--no-uv-resolve` to fall back to the legacy latest-release-per-package behavior (which may produce a `pyproject.toml` that will not
lock).

**Yanked releases** are excluded from candidates everywhere, since PEP 592 makes them reachable only through an exact pin — a pin the tool could never later
relax to discover an upgrade. If an existing pin turns out to be the *only* non-yanked option for a package, relaxing it would make the resolution
unsatisfiable, so the tool restores that pin verbatim and retries.

Dependencies are then categorized and handled differently based on where they appear:

### 5.2. Shared Main Hooks

Packages that exist in both `pyproject.toml` and as a pre-commit repo (mapped via `TOOL_MAPPING`). The target is the uv-resolved version, and the rev becomes
the git tag carrying it. If the repo ships no tag for that version, the tool falls back to the **highest version common to both** PyPI releases and git tags.

### 5.3. Shared Additional Dependencies

Packages in both `pyproject.toml` and as `additional_dependencies` in pre-commit hooks. Updated to the uv-resolved version in both files.

### 5.4. PyPI-Only Dependencies

Packages only in `pyproject.toml` (not referenced by pre-commit). Updated to the uv-resolved version.

### 5.5. Pre-commit-Only Repos

Repos only in `.pre-commit-config.yaml` (no matching pyproject.toml entry). Updated to the latest stable git tag.

### 5.6. Pre-commit-Only Additional Dependencies

`additional_dependencies` not in `pyproject.toml`. Updated to the latest stable PyPI version — these are outside the project's resolution.

### 5.7. Version Prefix Preservation

The tool preserves `v` prefixes on git tags. If the current rev is `v1.2.3`, the updated rev will also use the `v` prefix (e.g., `v1.3.0`).

### 5.8. Filtered Dependencies

The following are explicitly skipped during parsing, in both `pyproject.toml` dependencies and pre-commit `additional_dependencies`:

- Local path references (e.g., `.[all]`, `./gitlint-core[trusted-deps]`)
- URL-based dependencies (containing `@`)
- Inequality constraints (containing `<` or `>`)
- Self-referencing gamesheet-sdk-py extras (e.g., `gamesheet-sdk-py[common]`) — these carry no version to converge, and treating one as a package produces a
  phantom "update" that never lands and a permanent `--check` exit 1

### 5.9. Transitive-Dependency Overrides

Everything above converges **declared** dependencies. A transitive package whose version is dictated by an upstream requirement is declared nowhere, so there is
no pin to converge and bumping the parent cannot move it. The motivating case: `semgrep` hard-pins `mcp==1.23.3` — every release to date does — and that version
carries three HIGH advisories, so no reachable `semgrep` version yields a patched `mcp`.

Such packages are declared in **`.syncdepsoverrides.yaml`**, which holds the *policy* (why the override exists, and which versions are acceptable) while
`pyproject.toml` holds the *result* (the resolved exact pin):

```yaml
overrides:
  - package: mcp
    pinned_by: semgrep
    floor: ">=1.28.1" # the reason the override exists
    ceiling: "<2" # compatibility bound
    reason: >-
      semgrep hard-pins mcp==1.23.3, which carries three HIGH advisories.
    verify: uv run --extra semgrep --no-dev python -c "import semgrep.cli"
    review: 2026-11-09
```

Per run, for each policy:

| Step       | Behavior                                                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1. Resolve | `uv` resolves the project with `override-dependencies` set to the declared **bounds**, so it picks the newest release in range |
| 2. Probe   | `uv` resolves again with overrides **stripped**, to learn what upstream would give on its own                                  |
| 3. Write   | The bounded result is written to `pyproject.toml` as an **exact** `==` pin, appending the entry if absent                      |
| 4. Lock    | `uv.lock` is regenerated                                                                                                       |
| 5. Verify  | The policy's `verify` command must exit 0; on failure the pin **and** the lockfile are rolled back and the run exits non-zero  |
| 6. Retire  | If the stripped resolution already satisfies `floor`, the override is reported as retirable                                    |
| 7. Guard   | The package joins the `ignore` list in `.github/dependabot.yml`, alongside rev-pinned packages                                 |

The dependabot guard matters as much as the pin. Without it Dependabot is free to propose a version update past the declared ceiling, which for a security
override is precisely the breakage the ceiling exists to prevent — arriving as an innocuous-looking dependency PR. An override takes precedence over a rev pin
for the same package, since the override is what actually governs what gets installed, and the entry uses the **target** version so `--check` reports the end
state rather than whatever happens to be on disk.

### 5.10. Capped Pins and the Dependabot Ignore List

A pin can be held below the newest release by a sibling requirement. `python-semantic-release==10.6.1` requires `rich~=14.0` and `tomlkit~=0.13.0`, so
`rich==15.0.0` or `tomlkit==0.15.1` makes the project unsatisfiable — `uv lock` refuses it outright.

syncdeps never proposes such a pin, because it writes whatever `uv` resolved. Dependabot has no such protection: it compares each pin against the index in
isolation and opens a PR for the newest release. That PR can never merge, and it is worse than merely useless — a Dependabot PR touching only `pyproject.toml`
matches every workflow's `paths-ignore`, so almost no checks run and it **looks green while being unmergeable**.

After convergence, syncdeps therefore compares each managed pin's resolved version against the newest release the index offers. Anything resolved *below* the
newest release is capped by something in the graph, and joins the `ignore` list in `.github/dependabot.yml` alongside rev-pinned and overridden packages.

The suppression is deliberately narrow, because **a Dependabot `ignore` rule also applies to security updates**. Suppressing a package that is not genuinely
capped would hide a future security bump for no benefit, so a pin is reported only when the index actually offers something newer — precisely the case where a
Dependabot proposal could not be installed anyway. A fetch failure omits the package rather than guessing, and an unparseable version never manufactures a
suppression.

Because the entry is keyed on the resolved version (`> 14.3.4`), it maintains itself: once the cap lifts and `uv` resolves higher the entry follows, and it
disappears once the pin reaches the newest release.

Notes on the design, each of which is load-bearing:

- **Resolution is delegated to `uv`,** as everywhere else in the tool — "newest release within bounds" is just what `uv` picks when handed those bounds, so the
  pin is lockable by construction.
- **`constraint-dependencies` cannot substitute for `override-dependencies`.** Constraints only *narrow* existing requirements, so a floor above an upstream
  exact pin is unsatisfiable rather than winning.
- **The pin is exact, and a ceiling matters.** Left as a bare floor, `mcp>=1.28.1` resolves to `2.0.0`, which removes `mcp.server.fastmcp`; since
  `semgrep/cli.py` imports `semgrep.commands.mcp` unconditionally, the `semgrep` binary then fails to start at all. That is exactly the class of breakage
  `verify` exists to catch.
- **Nothing is retired automatically.** Silently dropping an override would reintroduce whatever it was added to fix, so retirement is reported and left to a
  human.
- **`verify` does not run under `--check` / `--dry-run`,** because those modes never leave changes behind and the command needs the new pin actually on disk to
  mean anything. Both modes say so rather than implying the override was validated.
- **A project with no policy file pays nothing** — the stage is skipped before any resolution work. `--no-uv-resolve` also skips it, since the whole mechanism
  depends on uv.

## 6. Exception Hierarchy

```text
SyncDepsError (base)
├── ParseError        — File parsing failures
├── FetchError        — PyPI/git tag fetch failures
├── WriteError        — File write failures
├── LockfileError     — uv.lock generation/validation failures
├── ResolveError      — uv-delegated version resolution failures
└── VerifyError       — an override's verify command failed with the new pin applied
```

`ResolveError` wraps `shared.uv_resolve.UvResolveError` so the CLI keeps a single exit-code contract.

## 7. Dependencies

The `syncdeps` optional-dependency group in `pyproject.toml`:

```toml
syncdeps = [
    "packaging==26.2",
    "requests==2.34.2",
    "rich-click==1.9.8",
    "ruamel.yaml==0.19.1",
    "tomlkit==0.15.0",
]
```

## 8. Troubleshooting

| Issue                                     | Cause                                    | Solution                                                              |
| ----------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------- |
| `ParseError` on pyproject.toml            | Malformed TOML syntax                    | `uv run --extra validate-pyproject validate-pyproject pyproject.toml` |
| `FetchError` for PyPI                     | Network issue or package not found       | Check network, verify package name                                    |
| `FetchError` for git tags                 | Repository URL unreachable               | Check URL, verify git access                                          |
| No common version found                   | PyPI and git tag sets don't overlap      | Check if repo uses different versioning                               |
| `ResolveError: 'uv' is not on PATH`       | uv missing                               | Install uv, or use `--no-uv-resolve`                                  |
| `ResolveError: found no valid resolution` | Real conflict that survives pin relaxing | Read uv's message; loosen the requirement                             |
| `uv lock` fails after a successful sync   | A pin was written without uv resolution  | Re-run without `--no-uv-resolve`                                      |

## 9. Related Tools

- [`tools/genprecommitconfig`](README.genprecommitconfig.md) — Pre-commit config generation (generates `.pre-commit-config.yaml` from
  `.genprecommitconfig.yaml`)

## 10. Files

| File                          | Purpose                                     |
| ----------------------------- | ------------------------------------------- |
| `tools/syncdeps`              | Executable entry point                      |
| `tools/depsync/__init__.py`   | Package initialization                      |
| `tools/depsync/cli.py`        | CLI interface                               |
| `tools/depsync/config.py`     | Constants and mappings                      |
| `tools/depsync/models.py`     | Pydantic v2 data models                     |
| `tools/depsync/exceptions.py` | Exception hierarchy                         |
| `tools/depsync/parsers.py`    | File parsers                                |
| `tools/depsync/fetchers.py`   | Version fetchers                            |
| `tools/depsync/engine.py`     | Convergence algorithm                       |
| `tools/depsync/caps.py`       | Capped-pin detection for Dependabot ignores |
| `tools/depsync/overrides.py`  | Transitive-dependency override subsystem    |
| `tools/depsync/typestubs.py`  | `types-*` stub sync                         |
| `tools/depsync/writers.py`    | Style-preserving writers                    |
| `tools/shared/uv_resolve.py`  | uv-delegated resolution                     |
| `.syncdepsoverrides.yaml`     | Transitive-dependency override policy       |
| `tools/README.syncdeps.md`    | This documentation                          |
