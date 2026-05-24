# gamesheet-sdk-py

> **Unofficial** Python SDK and command-line interface for the
> [GameSheet Inc.](https://gamesheet.com) platform.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/downloads/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bdperkin/gamesheet-sdk-py/main.svg)](https://results.pre-commit.ci/latest/github/bdperkin/gamesheet-sdk-py/main)

---

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

```
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
