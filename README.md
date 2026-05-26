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
**it may break without warning** whenever GameSheet ships UI changes. Always
review the project's CHANGELOG before upgrading in production.

Use of this software must comply with the GameSheet Inc. Terms of Service. You
are responsible for any automation you perform against accounts you control.

## Features

- Pythonic wrappers over common GameSheet WebUI workflows
- A `gamesheet-sdk-py` command-line interface for one-off scripting and shell pipelines
- Typed (PEP 561) — ships a `py.typed` marker for static analysis
- First-class support for headless automation via [Playwright](https://playwright.dev/python/)

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

```python
from gamesheet_sdk import __version__

print(__version__)
```

```bash
gamesheet-sdk-py --help
```

## Project layout

```bash
gamesheet-sdk-py/
├── src/gamesheet_sdk/   # library source
├── tests/                  # pytest suite
├── docs/                   # additional documentation
├── pyproject.toml          # PEP 621 metadata + Hatch build
├── .pre-commit-config.yaml # hooks run locally and on pre-commit.ci
└── LICENSE                 # MIT
```

## Development

```bash
# 1. Create an isolated environment
python -m venv .venv && source .venv/bin/activate

# 2. Install with dev extras
pip install -e ".[dev]"

# 3. Install hook scripts
pre-commit install

# 4. Run the test suite
pytest

# 5. Run all hooks against the repo
pre-commit run --all-files
```

## Contributing

Issues and pull requests are welcome. Please run `pre-commit run --all-files`
and `pytest` before opening a PR.

## License

Distributed under the terms of the [MIT License](LICENSE).
© 2026 bdperkin.
