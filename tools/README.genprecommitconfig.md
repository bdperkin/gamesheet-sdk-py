# genprecommitconfig

Automated `.pre-commit-config.yaml` generator that fetches hook definitions from upstream repositories, applies declarative configuration overrides, and
validates the result incrementally.

## 1. Overview

`genprecommitconfig` replaces manual maintenance of `.pre-commit-config.yaml` with a reproducible, configuration-driven workflow. Instead of editing the
pre-commit config directly, you declare repositories and hook customizations in `.genprecommitconfig.yaml` and the tool:

1. Resolves the latest version tag for each repository (or uses a pinned/installed version)
2. Fetches the upstream `.pre-commit-hooks.yaml` hook definitions
3. Filters hooks by allowed languages and a blacklist
4. Applies overrides, appends, and prepends from the configuration
5. Validates each repo incrementally by running `pre-commit run --all-files`
6. Writes the final `.pre-commit-config.yaml` with all hook fields statically mapped

This "suck-in" approach means remote hook changes only appear locally when the tool is re-run, giving full control over what lands in the project.

## 2. Architecture

```text
tools/genprecommitconfig        # Thin entry point
tools/precommit/
    __init__.py                 # Package docstring
    cli.py                      # Click CLI with rich-click and RichHandler logging
    config.py                   # Static defaults and constants
    models.py                   # Pydantic v2 models for configuration validation
    exceptions.py               # Exception hierarchy (GenPreCommitConfigError base)
    generator.py                # Main pipeline orchestrator (phases 2-6)
    discovery.py                # Git tag version resolution (Python-native parsing)
    fetcher.py                  # Remote .pre-commit-hooks.yaml fetching via requests
    processor.py                # Hook filtering, blacklisting, overrides, appends
    renderer.py                 # YAML output rendering with ruamel.yaml
    validator.py                # Pre-commit validation runner

Shared utilities: tools/shared/ (HTTP sessions, git subprocess, logging, exceptions)
```

### 2.1. Execution Pipeline

| Phase | Module                                                          | Description                                                      |
| ----- | --------------------------------------------------------------- | ---------------------------------------------------------------- |
| 1     | `cli.py`                                                        | Parse command-line arguments, configure logging                  |
| 2     | `config.py` + `generator.py`                                    | Load static defaults as fallbacks                                |
| 3     | `generator.py`                                                  | Parse and validate `.genprecommitconfig.yaml` with Pydantic      |
| 4     | `generator.py` + `discovery.py` + `fetcher.py` + `processor.py` | Prefetch revs and hooks in parallel, apply filters and overrides |
| 5     | `validator.py`                                                  | Per-repo incremental validation via `pre-commit run`             |
| 6     | `validator.py`                                                  | Final full validation run                                        |

## 3. Prerequisites

- Python 3.11+
- `pre-commit` (installed and available on `PATH`)
- `git` (for `git ls-remote` tag resolution)
- Network access to GitHub/GitLab (for fetching hook definitions)
- Python packages: `click`, `rich`, `rich-click`, `pydantic`, `requests`, `ruamel.yaml`, `packaging`

Install development dependencies:

```bash
make venv  # or: pip install -e ".[dev]"
```

## 4. Usage

### 4.1. Basic Usage

```bash
# Generate .pre-commit-config.yaml from default config
./tools/genprecommitconfig

# Dry-run mode (generate YAML without running validation)
./tools/genprecommitconfig --dry-run

# Skip per-repo incremental validation (still runs final validation)
./tools/genprecommitconfig --no-validate

# Custom config file location
./tools/genprecommitconfig --config-file path/to/config.yaml

# Override output file
./tools/genprecommitconfig --output-file custom-pre-commit.yaml

# Debug logging
./tools/genprecommitconfig --log-level debug
```

### 4.2. Command-Line Options

| Option          | Default                             | Description                                 |
| --------------- | ----------------------------------- | ------------------------------------------- |
| `--config-file` | `.genprecommitconfig.yaml`          | Path to configuration file                  |
| `--output-file` | From config (`globals.output_file`) | Override output file path                   |
| `--log-level`   | `info`                              | Logging level: debug, info, warning, error  |
| `--dry-run`     | `false`                             | Generate YAML only, skip all validation     |
| `--no-validate` | `false`                             | Skip per-repo validation (final still runs) |
| `--version`     | —                                   | Show version and exit                       |
| `--help`        | —                                   | Show help and exit                          |

### 4.3. Expected Runtime

- **Dry-run**: 10-30 seconds (network I/O for version discovery and hook fetching)
- **Full run**: 1-5 minutes (includes pre-commit validation after each repo)

## 5. Configuration File

The tool reads `.genprecommitconfig.yaml` from the project root. An example template is provided at `tools/genprecommitconfig.example.yaml`.

### 5.1. Structure

```yaml
globals:
  default_language_version:    # Language version mapping for pre-commit
    python: python3.11
  default_stages:              # Default stages for all hooks
    - pre-commit
    - pre-push
  fail_fast: true              # Stop on first hook failure
  output_file: .pre-commit-config.yaml  # Output file path
  allowed_languages:           # Only include hooks using these languages
    - fail
    - pygrep
    - python
    - script
    - system
  blacklisted_hooks:           # Hook IDs to exclude globally
    - check-byte-order-marker
    - uv-export

categories:                    # Repos grouped by function
  meta:                        # Category key (organizational grouping)
    description: Meta Hooks (pre-commit validation)  # Rendered as sub-section comment
    repos:                     # List of repository configurations
      - name: meta
        repo: meta
        hooks:
          - id: check-hooks-apply
          - id: identity
            overrides:
              stages: [manual]

  check:
    description: Global File Sanity Checks
    repos:
      - name: uv
        repo: https://github.com/astral-sh/uv-pre-commit
        rev: installed         # Match installed uv version

      - name: pre-commit-hooks
        repo: https://github.com/pre-commit/pre-commit-hooks
        hooks:
          - id: end-of-file-fixer
            appends:           # Add to existing list fields
              exclude_types: [jinja, markdown]
          - id: detect-private-key
            overrides:         # Replace fields entirely
              exclude: "^path/to/allowed/key$"

  lint:
    description: Code Quality Linters
    repos:
      - name: mypy
        repo: https://github.com/pre-commit/mirrors-mypy
        rev: v2.1.0           # Pinned version
        hooks:
          - id: mypy
            comment: "Type checking with extra deps"
            appends:
              args: [--install-types, --non-interactive]
              additional_dependencies: [pydantic]
            overrides:
              exclude: "^(bin|docs)/.*$"
```

### 5.2. Category Configuration

Each category entry supports:

| Field         | Type   | Description                                                            |
| ------------- | ------ | ---------------------------------------------------------------------- |
| `description` | string | **Required.** Human-readable label rendered as a sub-section comment   |
| `repos`       | list   | **Required.** List of repository configurations (see Repository below) |

### 5.3. Repository Configuration

Each repository entry (within `repos`) supports:

| Field   | Type        | Description                                                                                    |
| ------- | ----------- | ---------------------------------------------------------------------------------------------- |
| `name`  | string      | **Required.** Friendly name (e.g., "ruff" for ruff-pre-commit)                                 |
| `repo`  | string      | **Required.** Repository URL or `"meta"`                                                       |
| `rev`   | string/null | Version: `null` = auto-detect latest, `"installed"` = match installed package, or exact string |
| `hooks` | list        | Per-hook overrides (see below)                                                                 |

### 5.4. Hook Configuration

Each hook entry (within `hooks`) supports:

| Field       | Type    | Description                                          |
| ----------- | ------- | ---------------------------------------------------- |
| `id`        | string  | **Required.** Hook identifier to match               |
| `comment`   | string  | Rendered as a YAML comment above the hook in output  |
| `overrides` | mapping | Fields that replace fetched values entirely          |
| `appends`   | mapping | List fields to extend (added after existing values)  |
| `prepends`  | mapping | List fields to extend (added before existing values) |

### 5.5. Version Resolution

The `rev` field controls how the tool resolves the repository version:

- **`null` or omitted**: Queries `git ls-remote --tags` and selects the latest release tag using PEP 440 version sorting. Pre-release tags (containing `a` or
  `b` between digits) are excluded.
- **`"installed"`**: Uses `importlib.metadata.version()` to match the locally installed package version. The package name is derived from the repository URL
  (e.g., `uv-pre-commit` → `uv`).
- **Exact string** (e.g., `"v1.7.7"`): Used as-is without any resolution.

### 5.6. Hook Filtering

Hooks from remote repositories are filtered through three gates:

1. **Language filter**: Only hooks using languages in `globals.allowed_languages` are included
2. **Blacklist filter**: Hooks with IDs in `globals.blacklisted_hooks` are excluded
3. **Targeting filter**: Only hooks with explicit file targeting metadata (`always_run`, `files`, `stages`, `types`, or `types_or`) are included

### 5.7. Override vs. Append vs. Prepend

- **`overrides`**: Replaces the fetched field value entirely. Use for scalar fields (`exclude`, `entry`, `always_run`) or when you want to replace the entire
  list.
- **`appends`**: Extends existing list fields by adding values at the end. Use for `args`, `additional_dependencies`, `exclude_types`.
- **`prepends`**: Extends existing list fields by inserting values at the beginning. Use when argument order matters (e.g., `--add-plugin` must come before
  other args).

## 6. Exception Hierarchy

```text
GenPreCommitConfigError         # Base (has exit_code attribute)
├── ConfigError                 # Config file loading/validation
├── DiscoveryError              # Git tag resolution failure
├── FetchError                  # Remote hook fetch failure
├── ProcessingError             # Hook filtering/override failure
├── RenderError                 # YAML output generation failure
├── ValidationError             # pre-commit run failure
└── SubprocessError             # Subprocess command failure
```

## 7. Dependencies

The tool requires the `pre-commit-config` optional dependency group:

```toml
pre-commit-config = [
    "packaging==26.2",
    "pydantic==2.13.4",
    "requests==2.34.2",
    "rich-click==1.9.8",
    "ruamel.yaml==0.19.1",
]
```

These are included transitively via `gamesheet-sdk-py[dev]`.

## 8. Troubleshooting

### 8.1. Common Issues

| Problem                                         | Solution                                                                   |
| ----------------------------------------------- | -------------------------------------------------------------------------- |
| `ConfigError: Configuration file not found`     | Create `.genprecommitconfig.yaml` or use `--config-file`                   |
| `DiscoveryError: git ls-remote failed`          | Check network access to repository URL                                     |
| `DiscoveryError: Package 'X' is not installed`  | Install the package or change `rev` from `"installed"` to a version string |
| `FetchError: Unsupported repository host`       | Only GitHub and GitLab URLs are supported                                  |
| `ValidationError: pre-commit validation failed` | Check pre-commit output for hook failures; fix and re-run                  |
| `pre-commit executable not found`               | Install pre-commit: `pip install pre-commit`                               |

### 8.2. Debug Mode

```bash
# Enable debug logging to see all operations
./tools/genprecommitconfig --log-level debug

# Generate without validation to inspect the output
./tools/genprecommitconfig --dry-run
```

## 9. Related Tools

- [`tools/syncdeps`](README.syncdeps.md) — Bidirectional dependency convergence

## 10. Files

| File                                    | Purpose                              |
| --------------------------------------- | ------------------------------------ |
| `.genprecommitconfig.yaml`              | Project configuration (input)        |
| `.pre-commit-config.yaml`               | Generated pre-commit config (output) |
| `tools/genprecommitconfig`              | Entry point script                   |
| `tools/precommit/`                      | Implementation package (11 modules)  |
| `tools/genprecommitconfig.example.yaml` | Example/template configuration       |
