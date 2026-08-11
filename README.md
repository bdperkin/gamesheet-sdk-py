# gamesheet-sdk-py

<!--TOC-->

______________________________________________________________________

- [1. ⚠️ Disclaimer](#1--disclaimer)
- [2. Quick Links](#2-quick-links)
- [3. Features](#3-features)
- [4. Requirements](#4-requirements)
- [5. Installation](#5-installation)
  - [5.1. Via PyPI / uv](#51-via-pypi--uv)
  - [5.2. Via Docker](#52-via-docker)
  - [5.3. From Source](#53-from-source)
- [6. Available Resources](#6-available-resources)
- [7. Quick Start](#7-quick-start)
  - [7.1. CLI](#71-cli)
  - [7.2. Python API](#72-python-api)
- [8. Configuration](#8-configuration)
- [9. Documentation](#9-documentation)
- [10. Project Status](#10-project-status)
- [11. Contributing](#11-contributing)
- [12. Security](#12-security)
- [13. License](#13-license)
- [14. Support](#14-support)
- [15. Links](#15-links)

______________________________________________________________________

<!--TOC-->

> **Unofficial** Python SDK and command-line interface for the [GameSheet Inc.](https://gamesheetinc.com) platform.

<!-- Build & Quality -->

[![CI](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/ci.yml)
[![Tests](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/tests.yml)
[![CodeQL](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/codeql.yml)
[![Docs](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/docs.yml)
[![Dependency Review](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/dependency-review.yml/badge.svg?event=pull_request)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/dependency-review.yml)
[![pre-commit](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/pre-commit.yml/badge.svg?branch=main)](https://github.com/bdperkin/gamesheet-sdk-py/actions/workflows/pre-commit.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bdperkin/gamesheet-sdk-py/main.svg)](https://results.pre-commit.ci/latest/github/bdperkin/gamesheet-sdk-py/main)
[![codecov](https://codecov.io/gh/bdperkin/gamesheet-sdk-py/graph/badge.svg?token=8608BKui41)](https://codecov.io/gh/bdperkin/gamesheet-sdk-py)

<!-- Code Quality -->

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with ty](https://img.shields.io/badge/types-ty-blue.svg)](https://github.com/astral-sh/ty)
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

## 1. ⚠️ Disclaimer

This project is **not affiliated with, endorsed by, or sponsored by GameSheet Inc.** GameSheet Inc. does not publish a public REST/GraphQL API for the
operations this SDK covers. Where a native API is absent, this library **automates the GameSheet WebUI** (using HTTP requests, HTML parsing, and
headless-browser automation).

Because this approach depends on third-party UI structure, **it may break without warning** when GameSheet ships changes. Check the
[GitHub Releases](https://github.com/bdperkin/gamesheet-sdk-py/releases) page before upgrading in production.

Use of this software must comply with the GameSheet Inc. Terms of Service. You are responsible for any automation you perform.

______________________________________________________________________

## 2. Quick Links

- **[Documentation](https://bdperkin.github.io/gamesheet-sdk-py/)** — Full documentation (tutorials, how-tos, API reference)
- **[Installation](#installation)** — Get started quickly
- **[Quick Start](#quick-start)** — First commands to try
- **[CLI Reference](docs/reference/cli.md)** — Command-line usage
- **[Configuration](docs/reference/configuration.md)** — Environment variables and settings
- **[Development Setup](docs/how-to/development-setup.md)** — Contributing guide
- **[Release Process](docs/how-to/release-process.md)** — Automated releases with Conventional Commits
- **[CHANGELOG](CHANGELOG.md)** — Release history

______________________________________________________________________

## 3. Features

- **Authentication** — Browser-driven login flow with persistent session storage
- **Resource-oriented CLI** — Intuitive verb-noun command structure with aliases (`ls`, `rm`, `get`, etc.)
- **Comprehensive resource coverage** — Manage associations, leagues, seasons, divisions, teams, games, referees, rosters (players & coaches), locations, and
  broadcasters
- **Python API** — Fully typed Python SDK with pydantic models for all resources
- **Multiple output formats** — JSON, YAML, CSV, TSV, or 13 tabulate table formats
- **Shell completion** — Tab completion for bash, zsh, fish
- **Typed (PEP 561)** — Ships `py.typed` marker, passes `ty check`
- **100% test coverage** — Comprehensive test suite with VCR cassettes and browser automation tests
- **Automated releases** — [Conventional Commits](https://www.conventionalcommits.org/) +
  [python-semantic-release](https://python-semantic-release.readthedocs.io/)
- **Docker support** — Pre-built container images with Playwright bundled

______________________________________________________________________

## 4. Requirements

- **Python 3.11+** (3.11, 3.12, 3.13, or 3.14)
- **Chromium** (managed by Playwright) — required for login flow

______________________________________________________________________

## 5. Installation

### 5.1. Via PyPI / uv

```bash
uv add gamesheet-sdk-py

# Install Playwright browser (required for login)
uv run playwright install chromium
```

### 5.2. Via Docker

Pre-built images include Playwright (Chromium) for seamless browser automation.

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/bdperkin/gamesheet-sdk-py:latest

# Show available CLIs
docker run --rm ghcr.io/bdperkin/gamesheet-sdk-py:latest

# Run the admin CLI
docker run --rm ghcr.io/bdperkin/gamesheet-sdk-py:latest gamesheet-admin --help

# Run with persistent session storage (recommended for multi-command workflows)
docker run --rm -v ~/.gamesheet:/home/gamesheet/.gamesheet \
  ghcr.io/bdperkin/gamesheet-sdk-py:latest gamesheet-admin associations list

# Example: login and list associations
docker run -it --rm -v ~/.gamesheet:/home/gamesheet/.gamesheet \
  -e GAMESHEET_USERNAME=you@example.com \
  -e GAMESHEET_PASSWORD=secret \
  ghcr.io/bdperkin/gamesheet-sdk-py:latest gamesheet-admin login

docker run --rm -v ~/.gamesheet:/home/gamesheet/.gamesheet \
  ghcr.io/bdperkin/gamesheet-sdk-py:latest gamesheet-admin associations list --format json
```

**Available Docker tags:**

- `latest` — most recent release from main branch
- `<version>` — specific version (e.g., `0.2.2`, `0.2`, `0`)
- `<branch>-<sha>` — specific commit for traceability

### 5.3. From Source

```bash
git clone https://github.com/bdperkin/gamesheet-sdk-py.git
cd gamesheet-sdk-py
uv sync --all-extras
uv run playwright install chromium

# Or build the Docker image locally
make docker-build
make docker-run
```

See [Development Setup](docs/how-to/development-setup.md) for detailed instructions.

______________________________________________________________________

## 6. Available Resources

The CLI and Python API provide comprehensive coverage of GameSheet resources:

| Resource         | CLI Command                                            | Description                             |
| ---------------- | ------------------------------------------------------ | --------------------------------------- |
| **Associations** | `associations`                                         | Top-level organizational units          |
| **Leagues**      | `leagues`                                              | Leagues within associations             |
| **Seasons**      | `seasons`                                              | Seasons within leagues                  |
| **Divisions**    | `divisions`                                            | Divisions within seasons                |
| **Teams**        | `teams`                                                | Teams within divisions                  |
| **Games**        | `games scheduled`, `games completed`, `games brackets` | Scheduled, completed, and bracket games |
| **Referees**     | `referees`                                             | Referee management and reports          |
| **Roster**       | `roster players`, `roster coaches`                     | Season-level roster management          |
| **Team Roster**  | `teams roster players`, `teams roster coaches`         | Team-level roster management            |
| **Locations**    | `locations`                                            | Game locations and venues               |
| **iPad Keys**    | `ipad-keys`                                            | iPad scoring access keys                |

Each resource supports intuitive verbs: `list` (or `ls`), `get` (or `show`/`view`), `create` (or `add`/`new`), `update` (or `set`/`edit`), `delete` (or
`rm`/`remove`) where applicable. Most resources default to `list` when invoked without a verb (e.g., `gamesheet-admin associations` runs `list`).

______________________________________________________________________

## 7. Quick Start

### 7.1. CLI

```bash
# Authenticate (credentials can also come from env vars)
gamesheet-admin login --email you@example.com

# List associations
gamesheet-admin associations list --format json
# Shorthand: gamesheet-admin associations (default=list)

# List leagues in an association
gamesheet-admin leagues list 38 --format json

# List seasons in a league
gamesheet-admin seasons list 1148580 --format json

# Get season details
gamesheet-admin seasons get --season-id 15020 --format json

# Get iPad/Scoring keys
gamesheet-admin ipad-keys get 15020 --format json

# Manage divisions
gamesheet-admin divisions list --season-id 15020 --format json
gamesheet-admin divisions create --season-id 15020 --name "Bantam A" --format json

# Manage teams
gamesheet-admin teams list --division-id 123 --format json
gamesheet-admin teams create --division-id 123 --name "Hawks" --format json

# List games (scheduled, completed, brackets)
gamesheet-admin games scheduled --season-id 15020 --format json
gamesheet-admin games completed --season-id 15020 --format json
gamesheet-admin games brackets --season-id 15020 --format json

# Manage referees
gamesheet-admin referees list --season-id 15020 --format json
gamesheet-admin referees get --referee-id 456 --format json

# Manage roster (players and coaches)
gamesheet-admin roster players list --season-id 15020 --format json
gamesheet-admin roster coaches list --season-id 15020 --format json

# Tab completion setup
gamesheet-admin completion bash > ~/.gamesheet-admin-completion.bash
source ~/.gamesheet-admin-completion.bash
```

See the [CLI Reference](docs/reference/cli.md) for complete usage.

### 7.2. Python API

```python
from gamesheet_sdk import (
    AuthenticatedSession,
    Config,
    get_season,
    list_associations,
    list_divisions,
    list_ipad_keys,
    list_leagues,
    list_seasons,
    list_teams,
    load_access_token,
    load_refresh_token,
    save_tokens,
)

# Configure and authenticate
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

                # Get detailed season info
                detail = get_season(session, season.id)
                print(f"      Sport: {detail.sport}")

                # Get iPad keys
                keys = list_ipad_keys(session, season.id)
                for key in keys:
                    print(f"        Key: {key.value}")

                # List divisions
                divisions = list_divisions(session, season.id)
                for division in divisions:
                    print(f"      Division: {division.name}")

                    # List teams in division
                    teams = list_teams(session, division.id)
                    for team in teams:
                        print(f"        Team: {team.name}")
```

All functions return fully typed pydantic models with comprehensive field validation.

______________________________________________________________________

## 8. Configuration

Configuration via environment variables or CLI flags. See [Configuration Reference](docs/reference/configuration.md) for details.

```bash
export GAMESHEET_USERNAME=you@example.com
export GAMESHEET_PASSWORD=secret
export GAMESHEET_TIMEOUT=60

gamesheet-admin login
```

______________________________________________________________________

## 9. Documentation

Full documentation is available at **<https://bdperkin.github.io/gamesheet-sdk-py/>**

The docs follow the [Diataxis](https://diataxis.fr/) framework:

- **[Tutorials](docs/tutorials/)** — Step-by-step learning guides
- **[How-To Guides](docs/how-to/)** — Task-oriented recipes
- **[Reference](docs/reference/)** — API and CLI documentation
- **[Explanation](docs/explanation/)** — Understanding the architecture

______________________________________________________________________

## 10. Project Status

**Status:** Alpha — Active development, breaking changes possible before 1.0.0

- **Current version:** 0.2.2
- **Python support:** 3.11, 3.12, 3.13, 3.14
- **Version strategy:** Patch-only bumps until 1.0.0 (see [Release Process](docs/how-to/release-process.md))
- **Test coverage:** 100% (enforced locally and via Codecov)
- **Type checking:** `ty check` passes on all source code
- **Code quality:** All blocks maintain cyclomatic complexity grade A (cc ≤ 5)
- **CI/CD:** Comprehensive test matrix across Python versions, multi-OS testing (nightly), security scanning (Bandit, Semgrep, Trivy, GitGuardian, OSV-Scanner,
  CodeQL), and automated PyPI releases

______________________________________________________________________

## 11. Contributing

Contributions are welcome! Before opening a PR:

1. Read [Development Setup](docs/how-to/development-setup.md)
2. Follow [Conventional Commits](https://www.conventionalcommits.org/) format
3. Ensure tests pass: `pytest --cov`
4. Run quality gates: `pre-commit run --all-files`
5. Maintain 100% test coverage
6. Keep complexity at grade A (run `make metrics`)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines. We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

______________________________________________________________________

## 12. Security

Security is a top priority. This project employs multiple layers of automated security scanning:

- **Static analysis:** Bandit (Python), Semgrep (SAST), CodeQL (semantic analysis)
- **Dependency scanning:** OSV-Scanner, pip-audit
- **Container scanning:** Trivy (with CVE suppression documented in `.trivyignore.yaml`, each entry carrying a rationale and an expiry date)
- **Secret detection:** GitGuardian
- **Code quality:** Pre-commit hooks enforce security best practices

**Reporting vulnerabilities:** See [SECURITY.md](SECURITY.md). Please use the private reporting channel — do not open public issues for security reports.

______________________________________________________________________

## 13. License

Distributed under the [MIT License](LICENSE). © 2026 bdperkin.

______________________________________________________________________

## 14. Support

Need help? See [SUPPORT.md](SUPPORT.md) for:

- Common issues and solutions
- How to ask questions (GitHub Discussions)
- How to report bugs (GitHub Issues)
- Response time expectations

______________________________________________________________________

## 15. Links

- **PyPI:** <https://pypi.org/project/gamesheet-sdk-py/>
- **Documentation:** <https://bdperkin.github.io/gamesheet-sdk-py/>
- **Source:** <https://github.com/bdperkin/gamesheet-sdk-py>
- **Issues:** <https://github.com/bdperkin/gamesheet-sdk-py/issues>
- **Discussions:** <https://github.com/bdperkin/gamesheet-sdk-py/discussions>
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Releases:** <https://github.com/bdperkin/gamesheet-sdk-py/releases>
