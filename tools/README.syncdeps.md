# syncdeps

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

| Component   | File                          | Purpose                                                     |
| ----------- | ----------------------------- | ----------------------------------------------------------- |
| Entry point | `tools/syncdeps`              | Thin wrapper that imports and runs `depsync.cli.app`        |
| CLI         | `tools/depsync/cli.py`        | Click/rich-click command with options and output formatting |
| Config      | `tools/depsync/config.py`     | Constants, default paths, PyPI↔git repo mapping table       |
| Models      | `tools/depsync/models.py`     | Pydantic v2 models for dependencies, repos, and results     |
| Exceptions  | `tools/depsync/exceptions.py` | Exception hierarchy with exit codes                         |
| Parsers     | `tools/depsync/parsers.py`    | Parse `pyproject.toml` and `.pre-commit-config.yaml`        |
| Fetchers    | `tools/depsync/fetchers.py`   | Query PyPI JSON API and `git ls-remote` for versions        |
| Engine      | `tools/depsync/engine.py`     | Core convergence algorithm                                  |
| Writers     | `tools/depsync/writers.py`    | Style-preserving file updates                               |
| Shared      | `tools/shared/`               | Shared utilities (HTTP, git, logging, TOML, exceptions)     |

### 2.1. Execution Pipeline

| Phase       | Description                                         |
| ----------- | --------------------------------------------------- |
| 1. Parse    | Read `pyproject.toml` and `.pre-commit-config.yaml` |
| 2. Map      | Build bidirectional PyPI↔git repo mappings          |
| 3. Prefetch | Fetch all PyPI versions and git tags in parallel    |
| 4. Converge | Determine updates for each dependency category      |
| 5. Display  | Show results table                                  |
| 6. Write    | Apply updates to all three files directly           |

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

| Option                  | Default                    | Description                                     |
| ----------------------- | -------------------------- | ----------------------------------------------- |
| `--pyproject`           | `pyproject.toml`           | Path to pyproject.toml                          |
| `--precommit-config`    | `.pre-commit-config.yaml`  | Path to .pre-commit-config.yaml                 |
| `--genprecommit-config` | `.genprecommitconfig.yaml` | Path to .genprecommitconfig.yaml                |
| `--log-level`           | `info`                     | Logging verbosity (debug, info, warning, error) |
| `--dry-run`             | off                        | Show changes without modifying files            |
| `--version`             | —                          | Show version and exit                           |
| `--help`                | —                          | Show help and exit                              |

## 5. Convergence Algorithm

Dependencies are categorized and handled differently based on where they appear:

### 5.1. Shared Main Hooks

Packages that exist in both `pyproject.toml` and as a pre-commit repo (mapped via `TOOL_MAPPING`). The tool finds the **highest version common to both** PyPI
releases and git tags, then updates both files to that version.

### 5.2. Shared Additional Dependencies

Packages in both `pyproject.toml` and as `additional_dependencies` in pre-commit hooks. Updated to the latest stable PyPI version in both files.

### 5.3. PyPI-Only Dependencies

Packages only in `pyproject.toml` (not referenced by pre-commit). Updated to the latest stable PyPI version.

### 5.4. Pre-commit-Only Repos

Repos only in `.pre-commit-config.yaml` (no matching pyproject.toml entry). Updated to the latest stable git tag.

### 5.5. Pre-commit-Only Additional Dependencies

`additional_dependencies` not in `pyproject.toml`. Updated to the latest stable PyPI version.

### 5.6. Version Prefix Preservation

The tool preserves `v` prefixes on git tags. If the current rev is `v1.2.3`, the updated rev will also use the `v` prefix (e.g., `v1.3.0`).

### 5.7. Filtered Dependencies

The following are explicitly skipped during parsing:

- Local path references (e.g., `.[all]`, `./gitlint-core[trusted-deps]`)
- URL-based dependencies (containing `@`)
- Inequality constraints (containing `<` or `>`)
- Self-referencing gamesheet-sdk-py extras (e.g., `gamesheet-sdk-py[common]`)

## 6. Exception Hierarchy

```text
SyncDepsError (base)
├── ParseError        — File parsing failures
├── FetchError        — PyPI/git tag fetch failures
├── WriteError        — File write failures
└── LockfileError     — uv.lock generation/validation failures
```

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

| Issue                          | Cause                               | Solution                                |
| ------------------------------ | ----------------------------------- | --------------------------------------- |
| `ParseError` on pyproject.toml | Malformed TOML syntax               | Validate with `tox -e pyprojectfmt`     |
| `FetchError` for PyPI          | Network issue or package not found  | Check network, verify package name      |
| `FetchError` for git tags      | Repository URL unreachable          | Check URL, verify git access            |
| No common version found        | PyPI and git tag sets don't overlap | Check if repo uses different versioning |

## 9. Related Tools

- [`tools/genprecommitconfig`](README.genprecommitconfig.md) — Pre-commit config generation (generates `.pre-commit-config.yaml` from
  `.genprecommitconfig.yaml`)

## 10. Files

| File                          | Purpose                  |
| ----------------------------- | ------------------------ |
| `tools/syncdeps`              | Executable entry point   |
| `tools/depsync/__init__.py`   | Package initialization   |
| `tools/depsync/cli.py`        | CLI interface            |
| `tools/depsync/config.py`     | Constants and mappings   |
| `tools/depsync/models.py`     | Pydantic v2 data models  |
| `tools/depsync/exceptions.py` | Exception hierarchy      |
| `tools/depsync/parsers.py`    | File parsers             |
| `tools/depsync/fetchers.py`   | Version fetchers         |
| `tools/depsync/engine.py`     | Convergence algorithm    |
| `tools/depsync/writers.py`    | Style-preserving writers |
| `tools/README.syncdeps.md`    | This documentation       |
