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

______________________________________________________________________

## ⚠️ Disclaimer

This project is **not affiliated with, endorsed by, or sponsored by GameSheet Inc.** GameSheet Inc. does not publish a public REST/GraphQL API for the
operations this SDK covers. Where a native API is absent, this library **automates the GameSheet WebUI** (using HTTP requests, HTML parsing, and
headless-browser automation).

Because this approach depends on third-party UI structure, **it may break without warning** when GameSheet ships changes. Check the
[GitHub Releases](https://github.com/bdperkin/gamesheet-sdk-py/releases) page before upgrading in production.

Use of this software must comply with the GameSheet Inc. Terms of Service. You are responsible for any automation you perform.

______________________________________________________________________

## Quick Links

- **[Documentation](https://bdperkin.github.io/gamesheet-sdk-py/)** — Full documentation (tutorials, how-tos, API reference)
- **[Installation](#installation)** — Get started quickly
- **[Quick Start](#quick-start)** — First commands to try
- **[CLI Reference](docs/reference/cli.md)** — Command-line usage
- **[Configuration](docs/reference/configuration.md)** — Environment variables and settings
- **[Development Setup](docs/how-to/development-setup.md)** — Contributing guide
- **[Release Process](docs/how-to/release-process.md)** — Automated releases with Conventional Commits
- **[CHANGELOG](CHANGELOG.md)** — Release history

______________________________________________________________________

## Features

- **Authentication** — Browser-driven login flow with persistent session storage
- **Resource-oriented CLI** — `associations`, `leagues`, `seasons`, `ipad-keys` commands with intuitive aliases
- **Python API** — `list_associations()`, `list_leagues()`, `list_seasons()`, `get_season()`, `list_ipad_keys()`
- **Multiple output formats** — JSON, YAML, CSV, TSV, or 13 tabulate table formats
- **Shell completion** — Tab completion for bash, zsh, fish
- **Typed (PEP 561)** — Ships `py.typed` marker, passes `mypy --strict`
- **Automated releases** — [Conventional Commits](https://www.conventionalcommits.org/) +
  [python-semantic-release](https://python-semantic-release.readthedocs.io/)

______________________________________________________________________

## Requirements

- **Python 3.11+** (3.11, 3.12, 3.13, or 3.14)
- **Chromium** (managed by Playwright) — required for login flow

______________________________________________________________________

## Installation

### Via PyPI

```bash
pip install gamesheet-sdk-py

# Install Playwright browser (required for login)
python -m playwright install chromium
```

### Via Docker

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/bdperkin/gamesheet-sdk-py:latest

# Run the CLI
docker run --rm ghcr.io/bdperkin/gamesheet-sdk-py:latest --help

# Run with persistent session storage
docker run --rm -v ~/.gamesheet:/home/gamesheet/.gamesheet ghcr.io/bdperkin/gamesheet-sdk-py:latest associations list
```

Available Docker tags:

- `latest` — most recent release from main branch
- `<version>` — specific version (e.g., `0.1.8`, `0.1`, `0`)
- `<branch>-<sha>` — specific commit for traceability

### From Source

```bash
git clone https://github.com/bdperkin/gamesheet-sdk-py.git
cd gamesheet-sdk-py
pip install -e ".[all]"
python -m playwright install chromium

# Or build the Docker image locally
make docker-build
make docker-run
```

See [Development Setup](docs/how-to/development-setup.md) for detailed instructions.

______________________________________________________________________

## Quick Start

### CLI

```bash
# Authenticate (credentials can also come from env vars)
gamesheet-sdk-py login --email you@example.com

# List associations
gamesheet-sdk-py associations list --format json

# List leagues in an association
gamesheet-sdk-py leagues list 38 --format json

# List seasons in a league
gamesheet-sdk-py seasons list 1148580 --format json

# Get season details
gamesheet-sdk-py season get 15020 --format json

# Get iPad/Scoring keys
gamesheet-sdk-py ipad-keys get 15020 --format json
```

See the [CLI Reference](docs/reference/cli.md) for complete usage.

### Python API

```python
from gamesheet_sdk import (
    AuthenticatedSession,
    Config,
    get_season,
    list_associations,
    list_ipad_keys,
    list_leagues,
    list_seasons,
    load_access_token,
    load_refresh_token,
    save_tokens,
)

config = Config()
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

        # List leagues
        for league in list_leagues(session, assoc.id):
            print(f"  League: {league.title}")

            # List seasons
            for season in list_seasons(session, league.id):
                print(f"    Season: {season.title}")

                # Get detailed info
                detail = get_season(session, season.id)
                print(f"      Sport: {detail.sport}")

                # Get iPad keys
                keys = list_ipad_keys(session, season.id)
                for key in keys:
                    print(f"        Key: {key.value}")
```

______________________________________________________________________

## Configuration

Configuration via environment variables or CLI flags. See [Configuration Reference](docs/reference/configuration.md) for details.

```bash
export GAMESHEET_USERNAME=you@example.com
export GAMESHEET_PASSWORD=secret
export GAMESHEET_TIMEOUT=60

gamesheet-sdk-py login
```

______________________________________________________________________

## Documentation

Full documentation is available at **<https://bdperkin.github.io/gamesheet-sdk-py/>**

The docs follow the [Diátaxis](https://diataxis.fr/) framework:

- **[Tutorials](docs/tutorials/)** — Step-by-step learning guides
- **[How-To Guides](docs/how-to/)** — Task-oriented recipes
- **[Reference](docs/reference/)** — API and CLI documentation
- **[Explanation](docs/explanation/)** — Understanding the architecture

______________________________________________________________________

## Project Status

**Status:** Alpha — Active development, breaking changes possible before 1.0.0

- **Version strategy:** Patch-only bumps until 1.0.0 (see [Release Process](docs/how-to/release-process.md))
- **Test coverage:** 100% (enforced via Codecov)
- **Type checking:** `mypy --strict` passes
- **Complexity:** All blocks at cyclomatic complexity grade A (cc ≤ 5)

______________________________________________________________________

## Contributing

Contributions are welcome! Before opening a PR:

1. Read [Development Setup](docs/how-to/development-setup.md)
2. Follow [Conventional Commits](https://www.conventionalcommits.org/) format
3. Ensure tests pass: `pytest --cov`
4. Run quality gates: `pre-commit run --all-files`
5. Maintain 100% test coverage
6. Keep complexity at grade A (run `make metrics`)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

______________________________________________________________________

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md). Please use the private reporting channel — do not open public issues for security reports.

______________________________________________________________________

## License

Distributed under the [MIT License](LICENSE). © 2026 bdperkin.

______________________________________________________________________

## Links

- **PyPI:** <https://pypi.org/project/gamesheet-sdk-py/>
- **Documentation:** <https://bdperkin.github.io/gamesheet-sdk-py/>
- **Source:** <https://github.com/bdperkin/gamesheet-sdk-py>
- **Issues:** <https://github.com/bdperkin/gamesheet-sdk-py/issues>
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Releases:** <https://github.com/bdperkin/gamesheet-sdk-py/releases>
