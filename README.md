# gamesheet-sdk-py

> **Unofficial** Python SDK and command-line interface for the
> [GameSheet Inc.](https://gamesheetinc.com) platform.

<!-- Build & Quality -->

[![CI](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/ci.yml)
[![CodeQL](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/codeql.yml)
[![Pylint](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/pylint.yml)
[![Docs](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/docs.yml)
[![Dependency review](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/dependency-review.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bdperkin/gamesheet-sdk-py/main.svg)](https://results.pre-commit.ci/latest/github/bdperkin/gamesheet-sdk-py/main)

<!-- Code Quality -->

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/imports-isort-1674b1.svg?labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Linting: flake8](https://img.shields.io/badge/linting-flake8-yellow.svg)](https://flake8.pycqa.org/)
[![Linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen.svg)](https://pylint.readthedocs.io/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- Package Info -->

[![PyPI version](https://img.shields.io/pypi/v/gamesheet-sdk-py.svg)](https://pypi.org/project/gamesheet-sdk-py/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gamesheet-sdk-py.svg)](https://pypi.org/project/gamesheet-sdk-py/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/gamesheet-sdk-py.svg)](https://pypi.org/project/gamesheet-sdk-py/)
[![PyPI - Status](https://img.shields.io/pypi/status/gamesheet-sdk-py.svg)](https://pypi.org/project/gamesheet-sdk-py/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gamesheet-sdk-py.svg)](https://pypi.org/project/gamesheet-sdk-py/)
[![License: MIT](https://img.shields.io/github/license/bdperkin/gamesheet-sdk-py.svg)](LICENSE)
[![Typed](https://img.shields.io/pypi/types/gamesheet-sdk-py.svg)](https://peps.python.org/pep-0561/)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

<!-- Community & Activity -->

[![GitHub release](https://img.shields.io/github/v/release/bdperkin/gamesheet-sdk-py?include_prereleases&sort=semver)](https://github.com/bdperkin/gamesheet-sdk-py/releases)
[![GitHub stars](https://img.shields.io/github/stars/bdperkin/gamesheet-sdk-py.svg?style=social)](https://github.com/bdperkin/gamesheet-sdk-py/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/bdperkin/gamesheet-sdk-py.svg?style=social)](https://github.com/bdperkin/gamesheet-sdk-py/network/members)
[![GitHub issues](https://img.shields.io/github/issues/bdperkin/gamesheet-sdk-py.svg)](https://github.com/bdperkin/gamesheet-sdk-py/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/bdperkin/gamesheet-sdk-py.svg)](https://github.com/bdperkin/gamesheet-sdk-py/pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/bdperkin/gamesheet-sdk-py.svg)](https://github.com/bdperkin/gamesheet-sdk-py/graphs/contributors)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/bdperkin/gamesheet-sdk-py.svg)](https://github.com/bdperkin/gamesheet-sdk-py/commits/main)

<!-- Maintenance -->

[![GitHub last commit](https://img.shields.io/github/last-commit/bdperkin/gamesheet-sdk-py.svg)](https://github.com/bdperkin/gamesheet-sdk-py/commits/main)
[![Maintenance](https://img.shields.io/maintenance/yes/2026.svg)](https://github.com/bdperkin/gamesheet-sdk-py/graphs/commit-activity)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-025E8C?logo=dependabot)](https://github.com/bdperkin/gamesheet-sdk-py/network/updates)
[![GitHub repo size](https://img.shields.io/github/repo-size/bdperkin/gamesheet-sdk-py.svg)](https://github.com/bdperkin/gamesheet-sdk-py)
[![GitHub code size](https://img.shields.io/github/languages/code-size/bdperkin/gamesheet-sdk-py.svg)](https://github.com/bdperkin/gamesheet-sdk-py)

## ⚠️ Disclaimer

This project is **not affiliated with, endorsed by, or sponsored by GameSheet Inc.**
GameSheet Inc. does not publish a public REST/GraphQL API for the operations this
SDK covers. Where a native API is absent, this library **automates the GameSheet
WebUI** (using a combination of HTTP requests, HTML parsing, and headless-browser
automation) in order to perform routine tasks programmatically.

Because this approach depends on the structure of a third-party web interface,
**it may break without warning** whenever GameSheet ships UI changes. Check the
[GitHub Releases](https://github.com/bdperkin/gamesheet-sdk-py/releases) page for
release notes before upgrading in production.

Use of this software must comply with the GameSheet Inc. Terms of Service. You
are responsible for any automation you perform against accounts you control.

## Table of contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [CLI usage](#cli-usage)
- [Documentation](#documentation)
- [Project layout](#project-layout)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Features

- **`login` flow** — authenticates against the GameSheet dashboard with
  [Playwright](https://playwright.dev/python/), persists the auth cookie and
  Playwright storage state so subsequent commands run without a browser.
- **`AuthenticatedSession`** — a `requests`-backed HTTP layer that attaches the
  saved bearer token, transparently refreshes it on 401, and re-persists rotated
  tokens via a user-supplied callback.
- **`BrowserSession`** — a Playwright wrapper that opens Chromium with the
  saved storage state for any flow that genuinely needs a real browser (headed
  mode available via `--no-headless` for debugging).
- **`list-associations`** — first concrete read-only command; lists the
  associations the signed-in user can see.
- **Pluggable output** — `render()` produces JSON, YAML, CSV, TSV, or any of 13
  human-readable tabulate formats (`simple`, `grid`, `fancy_grid`, `rst`,
  `html`, `latex`, …).
- **Typed (PEP 561)** — ships a `py.typed` marker and passes `mypy --strict`.
- **Config from env or kwargs** — `pydantic-settings` resolves `GAMESHEET_*`
  environment variables with CLI overrides taking precedence.

## Requirements

- **Python 3.11, 3.12, 3.13, or 3.14** (declared in `pyproject.toml`)
- **Chromium binary** managed by Playwright — required for the `login` flow
  and any other browser-driven workflow. Install once per machine with
  `python -m playwright install chromium`.
- Any modern Linux, macOS, or Windows host on which Python and Playwright
  Chromium run.

## Installation

```bash
pip install gamesheet-sdk-py

# Playwright browser binaries are required for headless WebUI flows:
python -m playwright install chromium
```

### From source

```bash
git clone https://github.com/bdperkin/gamesheet-sdk-py.git
cd gamesheet-sdk-py
pip install -e ".[dev]"
python -m playwright install chromium
```

## Quick start

Authenticate once, then list the associations on your account:

```bash
# Credentials can also be supplied via GAMESHEET_USERNAME / GAMESHEET_PASSWORD;
# omit the flags to be prompted interactively.
gamesheet-sdk-py login --email you@example.com

# Subsequent commands reuse the saved session — no browser, no re-prompt.
gamesheet-sdk-py list-associations --format json
```

Or from Python:

```python
from gamesheet_sdk import (
    AuthenticatedSession,
    Config,
    list_associations,
    load_access_token,
    load_refresh_token,
    save_tokens,
)

config = Config()  # reads GAMESHEET_* env vars; CLI args > env > defaults
access = load_access_token(config)
refresh = load_refresh_token(config)

with AuthenticatedSession(
    config,
    access_token=access or "",
    refresh_token=refresh or "",
    on_refresh=lambda tokens: save_tokens(config, **tokens),
) as session:
    for assoc in list_associations(session):
        print(assoc.name)
```

## Configuration

`Config` is a `pydantic-settings` model. Values resolve in this order:

1. Keyword arguments passed to `Config(...)` (or CLI flags like `--base-url`).
1. `GAMESHEET_`-prefixed environment variables.
1. Built-in defaults.

| Environment variable           | Purpose                                              | Default                                               |
| ------------------------------ | ---------------------------------------------------- | ----------------------------------------------------- |
| `GAMESHEET_BASE_URL`           | Root URL of the GameSheet WebUI                      | `https://gamesheet.app`                               |
| `GAMESHEET_USERNAME`           | Account email (CLI `--email` overrides)              | *unset*                                               |
| `GAMESHEET_PASSWORD`           | Account password (CLI `--password` overrides)        | *unset*                                               |
| `GAMESHEET_TIMEOUT`            | Default per-request HTTP timeout in seconds          | `30`                                                  |
| `GAMESHEET_REQUEST_RETRIES`    | Auto-retries on 5xx and connection errors            | `3`                                                   |
| `GAMESHEET_USER_AGENT`         | Override the HTTP `User-Agent` header                | requests default                                      |
| `GAMESHEET_VERIFY_SSL`         | TLS certificate verification                         | `true`                                                |
| `GAMESHEET_SESSION_PATH`       | Where to persist cookie state                        | `$XDG_CACHE_HOME/gamesheet-sdk-py/session.json`       |
| `GAMESHEET_BROWSER_STATE_PATH` | Where to persist Playwright storage state            | `$XDG_CACHE_HOME/gamesheet-sdk-py/browser-state.json` |
| `GAMESHEET_BROWSER_HEADLESS`   | Launch Playwright in headless mode (`--no-headless`) | `true`                                                |

## CLI usage

```console
$ gamesheet-sdk-py --help
Usage: gamesheet-sdk-py [OPTIONS] COMMAND [ARGS]...

  Unofficial CLI for the GameSheet Inc. platform.

Options:
  --version       Show the version and exit.
  -v, --verbose   Increase logging verbosity. -v sets INFO; -vv sets DEBUG.
  --base-url URL  Override Config.base_url for this invocation.
  --no-headless   Run browser-driven flows with a visible window (for
                  debugging).
  -h, --help      Show this message and exit.

Commands:
  list-associations  List the associations the signed-in user can see.
  login              Authenticate and persist a GameSheet session.
```

Render formats accepted by `list-associations --format`:

- **Data:** `json`, `yaml`, `csv`, `tsv`
- **Tables (via [tabulate](https://github.com/astanin/python-tabulate)):**
  `plain`, `simple` (default), `grid`, `fancy_grid`, `pipe`, `orgtbl`, `rst`,
  `mediawiki`, `html`, `latex`, `latex_raw`, `latex_booktabs`, `latex_longtable`

## Documentation

Full documentation is published on GitHub Pages:
**<https://bdperkin.github.io/gamesheet-sdk-py/>**

The docs are organized following the [Diátaxis](https://diataxis.fr/)
framework into tutorials, how-to guides, reference, and explanation. The
reference section (API + CLI) is generated from source, so it cannot drift
from the shipped package.

## Project layout

```text
gamesheet-sdk-py/
├── src/gamesheet_sdk/
│   ├── __init__.py            # public re-exports + __version__
│   ├── associations.py        # list-associations action + model
│   ├── auth.py                # login, token persistence, AuthenticatedSession
│   ├── browser.py             # Playwright BrowserSession wrapper
│   ├── cli.py                 # click entry point — `gamesheet-sdk-py`
│   ├── config.py              # pydantic-settings Config (GAMESHEET_*)
│   ├── exceptions.py          # GameSheetError, AuthenticationError
│   ├── output.py              # render() — json/yaml/csv/tsv + tabulate
│   ├── session.py             # base requests.Session subclass
│   └── py.typed               # PEP 561 marker
├── tests/                     # pytest suite (VCR cassettes + Playwright)
├── docs/                      # Sphinx (Diátaxis) — published to GH Pages
├── .github/workflows/         # ci, codeql, docs, pylint, release, deps
├── pyproject.toml             # PEP 621 metadata + Hatch + tool config
├── tox.ini                    # tox envs: lint, type, security, files-check, …
├── .pre-commit-config.yaml    # runs locally and on pre-commit.ci
├── SECURITY.md                # vulnerability reporting policy
└── LICENSE                    # MIT
```

## Development

```bash
# 1. Create an isolated environment and install dev + docs extras
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,docs]"
python -m playwright install chromium

# 2. Install pre-commit hooks
pre-commit install

# 3. Run the test suite (network is blocked unless replayed via VCR)
pytest                       # everything
pytest -m "not browser"      # skip slow real-Chromium tests
pytest --cov                 # with coverage (fail_under = 80)

# 4. Run individual quality gates
pre-commit run --all-files   # every hook
mypy src                     # strict mode
```

`tox` orchestrates everything in isolated venvs:

```bash
tox                  # py311..py314 + lint + type + pylint + security + files-check
tox -e lint          # black --check, isort --check, flake8
tox -e type          # mypy --strict
tox -e security      # bandit
tox -e files-check   # codespell, yamllint, validate-pyproject, …
tox -e fix           # auto-apply isort, black, mdformat
tox -e docs          # build the Sphinx HTML docs
tox -e docs-serve    # live-reload preview
```

The package version is **derived from `git describe`** via `hatch-vcs` — never
edit a version literal. To cut a release, tag the commit (`git tag -a vX.Y.Z`
then `git push origin vX.Y.Z`); the `release.yml` workflow builds, publishes
to PyPI via Trusted Publishing (OIDC), and creates a GitHub Release.

## Contributing

Issues and pull requests are welcome.

Before opening a PR:

- Run `pre-commit run --all-files` and `pytest` (or `tox` to cover both plus lint/type/security in isolated envs).
- New code must be fully annotated and pass `mypy --strict`.
- New documentation pages belong in one of the four Diátaxis quadrants under `docs/` — see [`docs/explanation/diataxis.md`](docs/explanation/diataxis.md) for guidance.

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md). Please do not
open public issues for security reports — use the private reporting channel
documented there.

## License

Distributed under the terms of the [MIT License](LICENSE).
© 2026 bdperkin.
