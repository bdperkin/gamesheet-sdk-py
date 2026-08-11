# Supported configurations

<!--TOC-->

______________________________________________________________________

- [1. Python versions](#1-python-versions)
- [2. Operating systems](#2-operating-systems)
- [3. Bundled browser](#3-bundled-browser)
- [4. Runtime dependencies](#4-runtime-dependencies)
- [5. Optional dependency groups](#5-optional-dependency-groups)
  - [5.1. Core extras](#51-core-extras)
  - [5.2. Individual tool extras](#52-individual-tool-extras)
  - [5.3. Install combinations](#53-install-combinations)
- [6. Distribution](#6-distribution)
- [7. How the package version is managed](#7-how-the-package-version-is-managed)

______________________________________________________________________

<!--TOC-->

This page enumerates the Python versions, operating systems, browsers, and dependencies that `gamesheet-sdk-py` officially supports. The authoritative source
for everything below is `pyproject.toml`; this page mirrors it for lookup convenience.

## 1. Python versions

| Version  | Status        |
| -------- | ------------- |
| 3.11     | Supported     |
| 3.12     | Supported     |
| 3.13     | Supported     |
| 3.14     | Supported     |
| \<= 3.10 | Not supported |

The constraint is enforced in `pyproject.toml` as `requires-python = ">=3.11"`. Installing on an unsupported interpreter will be rejected by pip.

## 2. Operating systems

The SDK runs anywhere CPython 3.11–3.14 runs _and_ Playwright can install Chromium. In practice that means:

- Linux: `x86_64`, `aarch64`
- macOS: `x86_64`, `arm64` (Apple Silicon)
- Windows: `x86_64`

Other targets (Linux 32-bit, BSD, etc.) are not tested. They may work for SDK operations that do not require Playwright; they will fail at
`python -m playwright install chromium`.

## 3. Bundled browser

Workflows that need a real browser drive headless Chromium via Playwright.

| Attribute        | Value                                                             |
| ---------------- | ----------------------------------------------------------------- |
| Engine           | Chromium                                                          |
| Version          | Whatever Playwright's current release fetches (not pinned by us). |
| Install command  | `python -m playwright install chromium`                           |
| Cache location   | `~/.cache/ms-playwright/` (analogous user-cache path on Windows)  |
| Approximate size | 150 MB on disk                                                    |

For caching the install across CI runs, see {doc}`../how-to/install-in-github-actions`.

## 4. Runtime dependencies

These are required and installed automatically by `pip install gamesheet-sdk-py`:

| Package             | Purpose                                                                    |
| ------------------- | -------------------------------------------------------------------------- |
| `click`             | Subcommand framework for the `gamesheet-admin` and `gamesheet-teams` CLIs. |
| `colorlog`          | ANSI-coloured log levels in the CLI (TTY-only).                            |
| `playwright`        | Headless-browser automation for the heavy code path.                       |
| `pydantic`          | Data validation for SDK models.                                            |
| `pydantic-settings` | Env-driven resolution of `Config`.                                         |
| `pyyaml`            | YAML output for CLI workflows.                                             |
| `requests`          | HTTP client for the lightweight code path.                                 |
| `rich`              | Syntax-highlighted JSON / YAML output to a TTY.                            |
| `tabulate`          | Human-readable table formats for CLI output.                               |
| `urllib3`           | HTTP connection pooling and request retries.                               |

If you change `[project.dependencies]` in `pyproject.toml`, update this table in the same commit.

## 5. Optional dependency groups

The package declares many extras via `[project.optional-dependencies]`. The two most important are:

- **`dev`** — minimal development setup: `pre-commit`, `pre-commit-uv`, `uv`.
- **`docs`** — Sphinx and its plugins: `sphinx`, `furo`, `myst-parser[linkify]`, `sphinx-copybutton`, `sphinx-design`, `sphinx-click`, `sphinx-lint`,
  `sphinx-autobuild`.
- **`all`** — includes every tool extra declared in the project (pytest, ty, bandit, formatters, linters, type checkers, etc.). This is the one-line install for
  full local development capability.

### 5.1. Core extras

| Extra    | Contents                                                                                                       |
| -------- | -------------------------------------------------------------------------------------------------------------- |
| `dev`    | `pre-commit`, `pre-commit-uv`, `uv`                                                                            |
| `docs`   | `sphinx`, `furo`, `myst-parser[linkify]`, `sphinx-copybutton`, `sphinx-design`, `sphinx-click`, `sphinx-lint`, |
|          | `sphinx-autobuild`                                                                                             |
| `pytest` | `pytest`, `pytest-cov`, `pytest-playwright`, `pytest-recording`, `responses`                                   |
| `ty`     | `ty`, `gamesheet-sdk-py[pytest]`                                                                               |
| `all`    | Includes every extra listed in this table plus all individual tool extras                                      |

### 5.2. Individual tool extras

Each linter, formatter, type checker, and quality tool is isolated to its own extra. Examples include:

- **Formatters**: `ruff`
- **Linters**: `bandit`, `blocklint`, `vulture`, `deptry`, `semgrep`
- **Doc tools**: `codespell`, `interrogate`, `pymarkdown`, `mdformat`
- **Config file tools**: `yamllint`, `yamlfix`, `pyproject-fmt`, `validate-pyproject`, `editorconfig-checker`, `pyroma`
- **Metrics**: `radon`

See `[project.optional-dependencies]` in `pyproject.toml` for the complete list.

### 5.3. Install combinations

| Command                            | What it gets you                                   |
| ---------------------------------- | -------------------------------------------------- |
| `pip install gamesheet-sdk-py`     | Runtime deps only.                                 |
| `pip install -e ".[dev]"`          | Runtime + pre-commit hooks + uv.                   |
| `pip install -e ".[docs]"`         | Runtime + Sphinx toolchain.                        |
| `pip install -e ".[dev,pytest]"`   | Runtime + dev tools + testing suite.               |
| `pip install -e ".[all]"`          | Everything (all tools, all extras).                |
| `pip install -e ".[dev,docs,all]"` | Equivalent to `[all]` (all is already exhaustive). |

## 6. Distribution

| Channel | Identifier                                                                |
| ------- | ------------------------------------------------------------------------- |
| PyPI    | [`gamesheet-sdk-py`](https://pypi.org/project/gamesheet-sdk-py/)          |
| Source  | <https://github.com/bdperkin/gamesheet-sdk-py>                            |
| Type    | Pure-Python wheel; ships `py.typed` (PEP 561) so type checkers see hints. |

## 7. How the package version is managed

The version **is** written in `pyproject.toml` in the `[project] version` field. It is managed by
[python-semantic-release](https://python-semantic-release.readthedocs.io/) (PSR), which automates version bumping and changelog generation based on Conventional
Commits.

- PSR analyzes commits since the last release to determine the next version (following semver).
- It updates `pyproject.toml`, `CHANGELOG.md`, creates a release commit, and pushes a git tag.
- The automated release workflow is triggered by the tag push and handles building and publishing to PyPI.

The version is accessible at runtime via `importlib.metadata.version("gamesheet-sdk-py")` or through `gamesheet_sdk.__version__`.

A `src/gamesheet_sdk/_version.py` file is generated during the build process (by the build backend) to carry version metadata into the installed package. This
file is gitignored and should never be manually edited.
