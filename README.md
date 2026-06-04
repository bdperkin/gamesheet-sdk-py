# gamesheet-sdk-py

> **Unofficial** Python SDK and command-line interface for the [GameSheet Inc.](https://gamesheetinc.com) platform.

<!-- Build & Quality -->

[![CI](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/ci.yml)
[![Tests](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/tests.yml)
[![CodeQL](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/codeql.yml)
[![Docs](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/docs.yml)
[![Dependency review](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/dependency-review.yml)
[![pre-commit](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/pre-commit.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/pre-commit.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bdperkin/gamesheet-sdk-py/main.svg)](https://results.pre-commit.ci/latest/github/bdperkin/gamesheet-sdk-py/main)
[![codecov](https://codecov.io/gh/bdperkin/gamesheet-sdk-py/graph/badge.svg?token=8608BKui41)](https://codecov.io/gh/bdperkin/gamesheet-sdk-py)

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

This project is **not affiliated with, endorsed by, or sponsored by GameSheet Inc.** GameSheet Inc. does not publish a public REST/GraphQL API for the
operations this SDK covers. Where a native API is absent, this library **automates the GameSheet WebUI** (using a combination of HTTP requests, HTML
parsing, and headless-browser automation) in order to perform routine tasks programmatically.

Because this approach depends on the structure of a third-party web interface, **it may break without warning** whenever GameSheet ships UI changes.
Check the [GitHub Releases](https://github.com/bdperkin/gamesheet-sdk-py/releases) page for release notes before upgrading in production.

Use of this software must comply with the GameSheet Inc. Terms of Service. You are responsible for any automation you perform against accounts you
control.

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

- **`login` flow** — authenticates against the GameSheet dashboard with [Playwright](https://playwright.dev/python/), persists the auth cookie and
  Playwright storage state so subsequent commands run without a browser.
- **`AuthenticatedSession`** — a `requests`-backed HTTP layer that attaches the saved bearer token, transparently refreshes it on 401, and re-persists
  rotated tokens via a user-supplied callback.
- **`BrowserSession`** — a Playwright wrapper that opens Chromium with the saved storage state for any flow that genuinely needs a real browser
  (headed mode available via `--no-headless` for debugging).
- **`associations list`** — read-only command to list associations (resource-oriented CLI; `ls` alias and a bare `gamesheet-sdk-py associations`
  shortcut both run the same action).
- **`leagues list`** — read-only command to list leagues within a specified association (resource-oriented CLI; `ls` alias works the same as
  associations).
- **`seasons list`** — read-only command to list seasons within a specified league (resource-oriented CLI; `ls` alias works the same as
  associations/leagues).
- **`season get`** — read-only command to get detailed information about a specific season, including settings, penalty codes, flagging criteria, and
  more (resource-oriented CLI; `show` and `view` aliases available, with `get` as the default).
- **Pluggable output** — `render()` produces JSON, YAML, CSV, TSV, or any of 13 human-readable tabulate formats (`simple`, `grid`, `fancy_grid`,
  `rst`, `html`, `latex`, …).
- **Shell completion** — `gamesheet-sdk-py completion {bash,zsh,fish}` prints a sourceable script that tab-completes sub-commands (including aliases),
  option names, and `--format` choices.
- **Typed (PEP 561)** — ships a `py.typed` marker and passes `mypy --strict`.
- **Config from env or kwargs** — `pydantic-settings` resolves `GAMESHEET_*` environment variables with CLI overrides taking precedence.

## Requirements

- **Python 3.11, 3.12, 3.13, or 3.14** (declared in `pyproject.toml`)
- **Chromium binary** managed by Playwright — required for the `login` flow and any other browser-driven workflow. Install once per machine with
  `python -m playwright install chromium`.
- Any modern Linux, macOS, or Windows host on which Python and Playwright Chromium run.

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
pip install -e ".[all]"   # everything: pytest, mypy, lint suite, docs, pre-commit
python -m playwright install chromium
```

The `[all]` extra pulls every per-tool dependency declared in `pyproject.toml`. For a leaner setup pick the extras you need explicitly — e.g.
`pip install -e ".[dev,pytest,docs]"` for tests + docs without the full lint matrix.

## Quick start

Authenticate once, then list the associations on your account:

```bash
# Credentials can also be supplied via GAMESHEET_USERNAME / GAMESHEET_PASSWORD;
# omit the flags to be prompted interactively.
gamesheet-sdk-py login --email you@example.com

# Subsequent commands reuse the saved session — no browser, no re-prompt.
gamesheet-sdk-py associations list --format json   # also: `associations ls`, or bare `associations`

# List leagues within a specific association (replace 38 with your association ID)
gamesheet-sdk-py leagues list 38 --format json     # also: `leagues ls 38`

# List seasons within a specific league (replace 1148580 with your league ID)
gamesheet-sdk-py seasons list 1148580 --format json     # also: `seasons ls 1148580`

# Get detailed information about a specific season (replace 15020 with your season ID)
gamesheet-sdk-py season get 15020 --format json          # also: `season show 15020` or `season view 15020`
gamesheet-sdk-py season get 15020 --fields id,title,sport,start_date,end_date  # Filter to specific fields
```

Or from Python:

```python
from gamesheet_sdk import (
    AuthenticatedSession,
    Config,
    get_season,
    list_associations,
    list_leagues,
    list_seasons,
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
    # List all associations
    for assoc in list_associations(session):
        print(f"Association: {assoc.title}")

        # List leagues for each association
        for league in list_leagues(session, assoc.id):
            print(f"  League: {league.title}")

            # List seasons for each league
            for season in list_seasons(session, league.id):
                print(f"    Season: {season.title}")

                # Get detailed information about a specific season
                season_detail = get_season(session, season.id)
                print(
                    f"      Sport: {season_detail.sport}, Dates: {season_detail.start_date} to {season_detail.end_date}"
                )
```

## Configuration

`Config` is a `pydantic-settings` model. Values resolve in this order:

1. Keyword arguments passed to `Config(...)` (or CLI flags like `--base-url`).
2. `GAMESHEET_`-prefixed environment variables.
3. Built-in defaults.

| Environment variable           | Purpose                                              | Default                                               |
| ------------------------------ | ---------------------------------------------------- | ----------------------------------------------------- |
| `GAMESHEET_BASE_URL`           | Root URL of the GameSheet WebUI                      | `https://gamesheet.app`                               |
| `GAMESHEET_USERNAME`           | Account email (CLI `--email` overrides)              | _unset_                                               |
| `GAMESHEET_PASSWORD`           | Account password (CLI `--password` overrides)        | _unset_                                               |
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
  associations  Manage GameSheet associations.
  completion    Print a SHELL completion script to stdout.
  login         Authenticate and persist a GameSheet session.
```

The CLI is **resource-oriented (noun-first)**: each resource gets a nested group whose canonical verbs are `create / get / list / update / delete`,
with the aliases `add|new / show|view / ls / set|edit / rm|remove`. A bare `gamesheet-sdk-py <resource>` implicitly runs `list`.

```console
$ gamesheet-sdk-py associations --help
Commands:
  list (ls)  List the associations the signed-in user can see.
```

Render formats accepted by `associations list --format`:

- **Data:** `json`, `yaml`, `csv`, `tsv`
- **Tables (via [tabulate](https://github.com/astanin/python-tabulate)):** `plain`, `simple` (default), `grid`, `fancy_grid`, `pipe`, `orgtbl`, `rst`,
  `mediawiki`, `html`, `latex`, `latex_raw`, `latex_booktabs`, `latex_longtable`

### Tab completion

```bash
# Bash, current shell:
eval "$(gamesheet-sdk-py completion bash)"

# Bash, persistent:
gamesheet-sdk-py completion bash >> ~/.bashrc

# Zsh, persistent:
gamesheet-sdk-py completion zsh >> ~/.zshrc

# Fish, persistent (fish auto-loads ~/.config/fish/completions/):
gamesheet-sdk-py completion fish > ~/.config/fish/completions/gamesheet-sdk-py.fish
```

## Documentation

Full documentation is published on GitHub Pages: **<https://bdperkin.github.io/gamesheet-sdk-py/>**

The docs are organized following the [Diátaxis](https://diataxis.fr/) framework into tutorials, how-to guides, reference, and explanation. The
reference section (API + CLI) is generated from source, so it cannot drift from the shipped package.

## Project layout

```text
gamesheet-sdk-py/
├── src/gamesheet_sdk/
│   ├── __init__.py            # public re-exports + __version__
│   ├── associations.py        # list_associations action + Association model
│   ├── auth.py                # login, token persistence, AuthenticatedSession
│   ├── browser.py             # Playwright BrowserSession wrapper
│   ├── cli.py                 # click entry point — `gamesheet-sdk-py` (resource groups)
│   ├── config.py              # pydantic-settings Config (GAMESHEET_*)
│   ├── exceptions.py          # GameSheetError, AuthenticationError
│   ├── output.py              # render() — json/yaml/csv/tsv + tabulate
│   ├── session.py             # base requests.Session subclass
│   └── py.typed               # PEP 561 marker
├── tests/                     # pytest suite (VCR cassettes + Playwright)
├── docs/                      # Sphinx (Diátaxis) — published to GH Pages
├── .github/workflows/         # per-category fan-out: ci, tests, codeql, docs,
│                              #   pre-commit, dependency-review, release, plus
│                              #   one file per tool category (type checkers,
│                              #   formatters, linters, doc tools, …)
├── Makefile                   # unified dev shortcuts (`make help`)
├── pyproject.toml             # PEP 621 metadata + Hatch + tool config + extras
├── tox.ini                    # ~45 per-tool envs + labels (tests / docs / pre-commit)
├── .pre-commit-config.yaml    # local hooks + pre-commit.ci settings (inline `ci:` block)
├── .codecov.yml               # Codecov targets (project 100% / patch 100%) + analytics
├── SECURITY.md                # vulnerability reporting policy
└── LICENSE                    # MIT
```

## Development

```bash
# 1. Create an isolated environment and install everything
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"            # all per-tool extras: pytest, mypy, lint suite, docs, …
python -m playwright install chromium

# 2. Install pre-commit hooks (runs on every `git commit`)
pre-commit install

# 3. Run the test suite (network is blocked unless replayed via VCR)
pytest                              # everything
pytest -m "not browser"             # skip slow real-Chromium tests
pytest --cov                        # with coverage (local floor: fail_under = 100)

# 4. Run quality gates
pre-commit run --all-files          # every hook (mypy, pylint, pyright, bandit, xenon, …)
mypy src                            # strict mode only
```

### Makefile shortcuts

The `Makefile` wraps the most common workflows so you don't have to memorize tox env names. Run `make help` for the full list.

```bash
make install       # editable install with [dev] extras + Playwright Chromium
make test          # full pytest suite
make test-fast     # pytest -m "not browser"
make test-cov      # pytest --cov
make lint          # pre-commit across the whole repo
make type          # mypy --strict against src/
make fix           # apply formatters in place (isort, black, mdformat)
make metrics       # radon + xenon complexity gates
make docs          # Sphinx HTML build
make docs-serve    # live-reload preview
make clean         # caches + build artifacts
```

### Coverage

Local pytest runs enforce `fail_under = 100` (see `[tool.coverage.report]`). On every push, the `codecov.yml` workflow uploads `coverage.xml` and
JUnit XML to [Codecov](https://codecov.io/gh/bdperkin/gamesheet-sdk-py), which gates PRs against `.codecov.yml` targets — **project coverage = 100%**
(0% drop tolerated) and **patch coverage = 100%** on newly-introduced lines. Codecov test-analytics tracks flaky tests and a >10% performance
regression alert.

### Tox

Tox orchestrates ~45 per-tool envs (one per linter / formatter / type checker / doc builder), a single `pytest` env, and a fix-everything `fix` env.
Selected envs and label groups:

```bash
tox -l                # list every available env
tox -m tests          # all test envs (sanity build/install + pytest)
tox -m docs           # docs, docs-lint, docs-linkcheck, docs-doctest, docs-epub, docs-man, docs-pdf, docs-serve
tox -m pre-commit     # run pre-commit hooks
tox -e pytest         # the runtime pytest env (Python matrix lives in tests.yml on CI)
tox -e mypy           # mypy --strict
tox -e pylint         # pylint
tox -e bandit         # bandit security scan
tox -e metrics        # radon cc + radon mi (complexity)
tox -e fix            # apply isort, black, mdformat in place
tox -e pytest -- -k test_name  # pass args to pytest after `--`
```

Every `pyproject.toml` `optional-dependencies.*` group has a matching tox env that pulls only that extra — so `tox -e mypy` runs in an isolated venv
with just `mypy` + project imports, `tox -e pyright` with just `pyright`, etc.

### Releases

The package version is **derived from `git describe`** via `hatch-vcs` — never edit a version literal. To cut a release, tag the commit
(`git tag -a vX.Y.Z` then `git push origin vX.Y.Z`); the `release.yml` workflow builds, publishes to PyPI via Trusted Publishing (OIDC), and creates a
GitHub Release.

## Contributing

Issues and pull requests are welcome.

Before opening a PR:

- Run `make lint` (or `pre-commit run --all-files`) and `make test` (or `pytest`). To cover the full lint/type/security/docs matrix in isolated envs,
  run `tox` — or scope it with the labels `tox -m tests`, `tox -m docs`, `tox -m pre-commit`.
- New code must be fully annotated and pass `mypy --strict`. Every block must stay at cyclomatic-complexity grade A (cc ≤ 5) — the `xenon` pre-commit
  hook enforces this on every commit. Run `make metrics` to see the numbers before you push.
- New documentation pages belong in one of the four Diátaxis quadrants under `docs/` — see
  [`docs/explanation/diataxis.md`](docs/explanation/diataxis.md) for guidance.

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md). Please do not open public issues for security reports — use the private reporting channel
documented there.

## License

Distributed under the terms of the [MIT License](LICENSE). © 2026 bdperkin.
