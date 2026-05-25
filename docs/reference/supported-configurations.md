# Supported configurations

This page enumerates the Python versions, operating systems, browsers, and
dependencies that `gamesheet-sdk-py` officially supports. The authoritative
source for everything below is `pyproject.toml`; this page mirrors it for
lookup convenience.

## Python versions

| Version | Status        |
| ------- | ------------- |
| 3.11    | Supported     |
| 3.12    | Supported     |
| 3.13    | Supported     |
| 3.14    | Supported     |
| ≤ 3.10  | Not supported |
| ≥ 3.15  | Not supported |

The constraint is enforced in `pyproject.toml` as
`requires-python = ">=3.11,<3.15"`. Installing on an unsupported interpreter
will be rejected by pip.

## Operating systems

The SDK runs anywhere CPython 3.11–3.14 runs *and* Playwright can install
Chromium. In practice that means:

- Linux: `x86_64`, `aarch64`
- macOS: `x86_64`, `arm64` (Apple Silicon)
- Windows: `x86_64`

Other targets (Linux 32-bit, BSD, etc.) are not tested. They may work for
SDK operations that do not require Playwright; they will fail at
`python -m playwright install chromium`.

## Bundled browser

Workflows that need a real browser drive headless Chromium via Playwright.

| Attribute        | Value                                                             |
| ---------------- | ----------------------------------------------------------------- |
| Engine           | Chromium                                                          |
| Version          | Whatever Playwright's current release fetches (not pinned by us). |
| Install command  | `python -m playwright install chromium`                           |
| Cache location   | `~/.cache/ms-playwright/` (analogous user-cache path on Windows)  |
| Approximate size | 150 MB on disk                                                    |

For caching the install across CI runs, see
{doc}`../how-to/install-in-github-actions`.

## Runtime dependencies

These are required and installed automatically by `pip install gamesheet-sdk-py`:

| Package          | Floor    | Purpose                                              |
| ---------------- | -------- | ---------------------------------------------------- |
| `requests`       | `>=2.32` | HTTP client for the lightweight code path.           |
| `beautifulsoup4` | `>=4.12` | HTML parsing.                                        |
| `lxml`           | `>=5.2`  | Parser backend used by beautifulsoup4.               |
| `playwright`     | `>=1.45` | Headless-browser automation for the heavy code path. |
| `pydantic`       | `>=2.7`  | Data validation for SDK models.                      |
| `click`          | `>=8.1`  | Declared; the CLI currently uses argparse.           |

If you change `[project.dependencies]` in `pyproject.toml`, update this
table in the same commit.

## Optional dependency groups

The package declares two extras via `[project.optional-dependencies]`:

- **`dev`** — everything used to develop, test, lint, and release the
  package: `pytest`, `pytest-cov`, `black`, `isort`, `flake8`,
  `Flake8-pyproject`, `pre-commit`, `mypy`, `types-requests`, `pyupgrade`,
  `bandit[toml]`, `codespell`, `mdformat`, `mdformat-gfm`, `yamllint`,
  `validate-pyproject`, `editorconfig-checker`, `tox`, `build`.
- **`docs`** — Sphinx and its plugins: `sphinx`, `furo`,
  `myst-parser[linkify]`, `sphinx-copybutton`, `sphinx-design`,
  `sphinx-argparse`, `sphinx-lint`, `sphinx-autobuild`.

Install combinations:

| Command                        | What it gets you             |
| ------------------------------ | ---------------------------- |
| `pip install gamesheet-sdk-py` | Runtime deps only.           |
| `pip install -e ".[dev]"`      | Runtime + development tools. |
| `pip install -e ".[docs]"`     | Runtime + Sphinx toolchain.  |
| `pip install -e ".[dev,docs]"` | Everything.                  |

## Distribution

| Channel | Identifier                                                                |
| ------- | ------------------------------------------------------------------------- |
| PyPI    | [`gamesheet-sdk-py`](https://pypi.org/project/gamesheet-sdk-py/)          |
| Source  | <https://github.com/bdperkin/gamesheet-sdk-py>                            |
| Type    | Pure-Python wheel; ships `py.typed` (PEP 561) so type checkers see hints. |
