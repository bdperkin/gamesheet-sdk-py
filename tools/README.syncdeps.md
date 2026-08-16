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
  - [5.11. Publication Cutoff Relaxations](#511-publication-cutoff-relaxations)
  - [5.12. Type Stub Gates](#512-type-stub-gates)
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

| Component   | File                            | Purpose                                                             |
| ----------- | ------------------------------- | ------------------------------------------------------------------- |
| Entry point | `tools/syncdeps`                | Thin wrapper that imports and runs `depsync.cli.app`                |
| CLI         | `tools/depsync/cli.py`          | Click/rich-click command with options and output formatting         |
| Config      | `tools/depsync/config.py`       | Constants, default paths, PyPI↔git repo mapping table               |
| Models      | `tools/depsync/models.py`       | Pydantic v2 models for dependencies, repos, and results             |
| Exceptions  | `tools/depsync/exceptions.py`   | Exception hierarchy with exit codes                                 |
| Parsers     | `tools/depsync/parsers.py`      | Parse `pyproject.toml` and `.pre-commit-config.yaml`                |
| Fetchers    | `tools/depsync/fetchers.py`     | Query PyPI JSON API and `git ls-remote` for versions                |
| Engine      | `tools/depsync/engine.py`       | Core convergence algorithm                                          |
| Type stubs  | `tools/depsync/typestubs.py`    | `types-*` stub discovery and synchronization                        |
| Stub gates  | `tools/depsync/typedness.py`    | Import scan and `py.typed` detection gating stub additions          |
| Cutoff      | `tools/depsync/excludenewer.py` | Per-package relaxation of the `uv` publication cutoff               |
| Writers     | `tools/depsync/writers.py`      | Style-preserving file updates                                       |
| Resolver    | `tools/shared/uv_resolve.py`    | Delegates resolution to `uv lock`; shared with `genprecommitconfig` |
| Shared      | `tools/shared/`                 | Shared utilities (HTTP, git, logging, TOML, exceptions)             |

### 2.1. Execution Pipeline

| Phase       | Description                                                                                               |
| ----------- | --------------------------------------------------------------------------------------------------------- |
| 1. Parse    | Read `pyproject.toml` and `.pre-commit-config.yaml`                                                       |
| 2. Resolve  | Ask `uv lock` which versions can co-exist (see [Version targets](#51-version-targets))                    |
| 3. Map      | Build bidirectional PyPI↔git repo mappings                                                                |
| 4. Prefetch | Fetch all PyPI versions and git tags in parallel                                                          |
| 5. Converge | Determine updates for each dependency category                                                            |
| 6. Display  | Show results table                                                                                        |
| 7. Write    | Apply updates to all three files directly                                                                 |
| 8. Relax    | Reconcile `exclude-newer-package` with the pins written (see [5.11](#511-publication-cutoff-relaxations)) |

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

| Option                    | Default                    | Description                                                   |
| ------------------------- | -------------------------- | ------------------------------------------------------------- |
| `--pyproject`             | `pyproject.toml`           | Path to pyproject.toml                                        |
| `--precommit-config`      | `.pre-commit-config.yaml`  | Path to .pre-commit-config.yaml                               |
| `--genprecommit-config`   | `.genprecommitconfig.yaml` | Path to .genprecommitconfig.yaml                              |
| `--dependabot`            | `.github/dependabot.yml`   | Path to dependabot.yml (ignores synced with pins + overrides) |
| `--overrides`             | `.syncdepsoverrides.yaml`  | Path to the transitive-dependency override policy file        |
| `--uv-lock`               | `uv.lock`                  | Path to uv.lock (used with `--sync-types`)                    |
| `--log-level`             | `info`                     | Logging verbosity (debug, info, warning, error)               |
| `--dry-run`               | off                        | Show changes without modifying files                          |
| `--sync-types`            | off                        | Sync `types-*` stub packages in the `type-stubs` group        |
| `--no-sync-exclude-newer` | on                         | Suppress the `exclude-newer-package` reconciliation           |
| `--no-uv-resolve`         | off                        | Skip uv resolution; pin each package to its latest release    |
| `--backup`                | off                        | Write `.bak` copies before modifying any file                 |
| `--check`                 | off                        | Exit 1 if any file would be modified (writes nothing)         |
| `--diff`                  | off                        | Show a unified diff of the changes                            |
| `--version`               | —                          | Show version and exit                                         |
| `--help`                  | —                          | Show help and exit                                            |

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
isolation and opens a PR for the newest release, and that PR can never merge — `uv lock` refuses the combination. It used to be worse still: while every
workflow's `pull_request` trigger carried `paths-ignore: [CHANGELOG.md, pyproject.toml]`, a Dependabot PR touching only `pyproject.toml` ran almost no checks
and **looked green while being unmergeable**. That filter now applies to `push` only, so such a PR is at least checked honestly; suppressing the pin remains the
point, since a checked PR that cannot lock is still noise.

After convergence, syncdeps therefore compares each managed pin's resolved version against the newest release the index offers. Anything resolved *below* the
newest release is capped by something in the graph, and joins the `ignore` list in `.github/dependabot.yml` alongside rev-pinned and overridden packages.

The suppression is deliberately narrow, because **a Dependabot `ignore` rule also applies to security updates** — GitHub's documentation is explicit that you
can "configure Dependabot to ignore those dependencies when it opens pull requests for version updates *and security updates*". Suppressing a package that is
not genuinely capped would hide a future security bump for no benefit, so a pin is reported only when the index actually offers something newer — precisely the
case where a Dependabot proposal could not be installed anyway. A fetch failure omits the package rather than guessing, and an unparsable version never
manufactures a suppression.

Because the entry is keyed on the resolved version (`> 14.3.4`), it maintains itself: once the cap lifts and `uv` resolves higher the entry follows, and it
disappears once the pin reaches the newest release.

**Caveat — the rule is slightly broader than "versions that cannot be installed".** It ignores everything *above* the resolved version, which includes releases
that sit **inside** the cap and therefore would install fine. Today that distinction is empty: the only release above `rich==14.3.4` is `15.0.0`, and the only
ones above `tomlkit==0.13.3` are `0.14.0`/`0.15.x` — every one of them outside its cap, so the rules currently suppress exactly the unmergeable versions and
nothing else. The gap is prospective: if `rich 14.3.5` shipped a security fix, `rich~=14.0` would permit it, yet `> 14.3.4` would suppress Dependabot's security
PR for it until the next syncdeps run advanced the entry.

That window is bounded by the syncdeps cadence rather than open-ended, and it is not the only net — `pip-audit` and OSV-Scanner both scan dependencies
independently of Dependabot and would still report the vulnerability. The precise alternative is to ignore from the **cap boundary** up (`>= 15` for `rich`)
instead of from the resolved version up, which would let in-cap security releases through. That needs the boundary discovered, either by probing candidates with
`uv lock` or by parsing the capping requirement out of the resolver's error, and was judged not worth the cost given the bounded exposure. Revisit it if a
capped package ever starts shipping security fixes within its cap.

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

### 5.11. Publication Cutoff Relaxations

`[tool.uv] exclude-newer` is a cooldown: `uv` refuses any distribution published after the cutoff, so a release cannot be installed the hour it lands. For a
package `uv` is free to float that is exactly the wanted behavior — the resolver picks the newest release the cutoff admits and nothing fails.

**An exact pin cannot float.** Several convergence targets above are chosen outside the resolver:

- a shared main hook takes the newest **git tag** ([5.2](#52-shared-main-hooks)),
- a `types-*` stub takes the newest **index release**,
- `--no-uv-resolve` takes the newest release for everything.

Each of those can write a pin the cooldown then refuses, and from that moment every `uv lock` in the project fails — including the `uv-lock` pre-commit hook,
which runs on any change to `pyproject.toml`. `semgrep` is the standing example: it ships several releases a week, so its tag is usually newer than a seven-day
window, and a run that bumps it without relaxing the cutoff leaves the repo unable to lock.

`exclude-newer-package` is uv's answer — it relaxes the cutoff for one package while leaving it in force for the rest of the graph. syncdeps keeps that table in
step, in both directions:

| Situation                                                       | Action                                                      |
| --------------------------------------------------------------- | ----------------------------------------------------------- |
| Pinned release is **newer** than the cutoff, no entry yet       | Add `exclude-newer-package.<pkg>`, narrowed to that release |
| Pinned release is newer, existing entry **already admits** it   | Leave the entry exactly as written                          |
| Pinned release is newer, existing entry **no longer admits** it | Rewrite it (the pin moved to a newer release)               |
| Pinned release has **aged past** the cutoff                     | Remove the entry — the global rule now admits it unaided    |
| Entry's package is **absent from `uv.lock`**                    | Remove the entry — it governs nothing                       |
| Release date could not be determined                            | Leave the entry alone; a failed lookup is not evidence      |

Written values follow whichever notation `exclude-newer` itself uses. A relative cutoff (`"7 days"`) yields whole-day spans; an absolute one (`"2026-08-05"`)
yields RFC 3339 timestamps:

```toml
[tool.uv]
exclude-newer = "7 days"
exclude-newer-package.pre-commit = "1 days"     # released 1.8 days ago
exclude-newer-package.semgrep = "0 days"        # released this morning
```

The scope is every exact pin the project declares — `pyproject.toml` dependencies, `override-dependencies` ([5.9](#59-transitive-dependency-overrides)), and the
targets the current run is about to write — plus every package already named in the table. Publication times come from the per-release PyPI JSON endpoint, or
from a configured index's PEP 700 `upload-time` field, fetched in parallel.

Notes on the design, each of which is load-bearing:

- **The value is the narrowest relaxation that works,** floored to whole days rather than set to `0 days`. It is the smallest exemption that admits the pin.
- **A sufficient entry is never recomputed.** A value derived from the release's age would grow by a day every day, so every run would rewrite the table and
  `--check` would fail daily on a project nobody had touched. Stability comes from keeping any value that still admits the pin.
- **A rendered timestamp rounds *up* to the whole second.** PyPI reports microseconds; truncating would place the cutoff *before* the upload it exists to admit,
  excluding the very file the entry was written for.
- **The stage runs twice** — after convergence and again after the `types-*` sync — because both write pins and the stages between them run `uv lock`.
  Publication lookups are cached across the two passes, so the second costs only what the first did not already answer.
- **Retirement is automatic here, unlike an override.** An override encodes a human judgment that dropping it would undo; a relaxation encodes only "this
  release is younger than the cutoff", which stops being true on its own. Leaving a spent entry behind would exempt that package from every future cooldown
  without saying so.
- **A calendar-unit cutoff (`"3 months"`) disables the stage** rather than being approximated. No `timedelta` represents a month, and guessing 30 days would
  move the cutoff silently.
- **An unreadable `uv.lock` suppresses retirement, not addition.** Without the lockfile the graph is invisible, and an entry cannot be declared dead on the
  strength of something we could not see.

### 5.12. Type Stub Gates

`--sync-types` used to add `types-<pkg>` for every resolved dependency whose stub merely **existed** on PyPI. That is how `optional-dependencies.type-stubs`
reached 34 entries, of which 30 stubbed modules no file in the repo imports (`types-pywin32` alone contributed ~60 Windows-only module stubs), and one —
`types-click==7.1.8` — described click 7 while the project ran click 8, shadowing click's own inline types so `click.shell_completion` read as unresolved.

**An unused stub is not inert.** It is a second, staler definition of a package, and PEP 561 puts it *ahead* of the runtime's inline annotations. Availability
on the index is therefore necessary but not sufficient; two gates in `tools/depsync/typedness.py` run before the index is even queried:

| Rule               | Rejected when                                                     | Rationale                                            |
| ------------------ | ----------------------------------------------------------------- | ---------------------------------------------------- |
| 1. Imported        | No file under the source roots imports a module the dist provides | An unimported stub can only shadow, never help       |
| 2. No inline types | The runtime distribution ships `py.typed`                         | Inline types need no stub, and a stub displaces them |

The source roots are `src/`, `tests/`, `tools/` and `docs/`.

Module names come from installed metadata (`top_level.txt`, else the recorded file list), never from the distribution name — `pyyaml` provides `yaml`,
`python-dateutil` provides `dateutil`. Imports are collected with `ast`, so a function-level import counts (`tools/precommit/processor.py` imports `pre_commit`
inside a function body) and a relative import does not (it can never name a distribution).

The gates are deliberately asymmetric between adding and removing:

- **An undeterminable answer rejects an addition.** Not adding costs nothing: `ty` reports the unresolved import and the stub is then added deliberately, which
  is the documented workflow.
- **An undeterminable answer keeps an existing stub.** A distribution absent from the environment `syncdeps` runs in has no authoritative module list, and
  deleting a load-bearing stub on a guessed name would break `ty` in CI.
- **Only rule 1 drives removals.** Rule 2 is add-time only, because a stub that shadows `py.typed` is sometimes the one that is right: `types-requests` is kept
  on purpose, since typeshed types `Session.headers` as `CaseInsensitiveDict[str | bytes]` where requests itself says `CaseInsensitiveDict[str]`, and the wider
  view is the accurate one. "Stub shadows `py.typed`" is a prompt to verify, not an automatic removal — so it may block an unreviewed addition but never undo a
  reviewed keep.
- **Nothing is narrowed silently.** Every rejection is reported — a per-reason count on stdout, and one line per candidate at `--log-level debug`.

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
| `uv lock` rejects a pin as too new        | Cutoff relaxation missing or suppressed  | Re-run without `--no-sync-exclude-newer`                              |

## 9. Related Tools

- [`tools/genprecommitconfig`](README.genprecommitconfig.md) — Pre-commit config generation (generates `.pre-commit-config.yaml` from
  `.genprecommitconfig.yaml`)

## 10. Files

| File                            | Purpose                                     |
| ------------------------------- | ------------------------------------------- |
| `tools/syncdeps`                | Executable entry point                      |
| `tools/depsync/__init__.py`     | Package initialization                      |
| `tools/depsync/cli.py`          | CLI interface                               |
| `tools/depsync/config.py`       | Constants and mappings                      |
| `tools/depsync/models.py`       | Pydantic v2 data models                     |
| `tools/depsync/exceptions.py`   | Exception hierarchy                         |
| `tools/depsync/parsers.py`      | File parsers                                |
| `tools/depsync/fetchers.py`     | Version fetchers                            |
| `tools/depsync/engine.py`       | Convergence algorithm                       |
| `tools/depsync/caps.py`         | Capped-pin detection for Dependabot ignores |
| `tools/depsync/overrides.py`    | Transitive-dependency override subsystem    |
| `tools/depsync/excludenewer.py` | Publication-cutoff relaxation subsystem     |
| `tools/depsync/typestubs.py`    | `types-*` stub sync                         |
| `tools/depsync/typedness.py`    | Stub gates (imported? inline types?)        |
| `tools/depsync/writers.py`      | Style-preserving writers                    |
| `tools/shared/uv_resolve.py`    | uv-delegated resolution                     |
| `.syncdepsoverrides.yaml`       | Transitive-dependency override policy       |
| `tools/README.syncdeps.md`      | This documentation                          |
