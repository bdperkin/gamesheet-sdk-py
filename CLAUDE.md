# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project nature

Unofficial Python SDK + CLI for the GameSheet Inc. platform. GameSheet does not publish a public API for the operations this library targets, so functionality is implemented by **automating the GameSheet WebUI** via a combination of:

- `requests` for plain HTTP
- `beautifulsoup4` + `lxml` for HTML parsing
- `playwright` (headless Chromium) for flows that require a real browser

Because behavior depends on a third-party UI, expect breakage on vendor changes. When adding or fixing a workflow, prefer the lightest mechanism that works (HTTP > HTML parse > headless browser) — headless automation is the slowest and most fragile path.

The package is alpha (`0.0.1`) and currently a skeleton: only `__init__.py` and `cli.py` exist under `src/gamesheet_sdk/`. Most domain modules are yet to be written.

## Common commands

```bash
# Editable install with dev extras (run once after clone / when deps change)
pip install -e ".[dev]"

# Playwright browser binaries — required for any headless-browser code path
python -m playwright install chromium

# Hook setup (run once)
pre-commit install

# Full test suite
pytest

# Single test
pytest tests/test_smoke.py::test_version_is_string

# With coverage (config in pyproject under [tool.coverage])
pytest --cov

# Lint / format / hooks across the whole repo
pre-commit run --all-files

# Type check (strict mode is on)
mypy src
```

The CLI installed by the package is `gamesheet-sdk-py` (entry point: `gamesheet_sdk.cli:main`).

## Architecture notes

- **`src/` layout.** Tests import via the installed package; `pyproject.toml` also sets `pythonpath = ["src"]` so `pytest` works without an install, but workflows that need the CLI or Playwright still require `pip install -e ".[dev]"`.
- **Typed package.** `py.typed` is shipped (PEP 561) and `[tool.mypy] strict = true` is enabled — all new code must be fully annotated and pass `mypy --strict`.
- **Python 3.11–3.14.** Use modern syntax (`from __future__ import annotations`, `X | None`, etc.) as `cli.py` already does.
- **Formatting/lint.** Black (line length 88) + flake8 with `extend-select = B950` and `E203, E501, W503` ignored. Pre-commit also runs trailing-whitespace, EOF, YAML/TOML, merge-conflict, and large-file (>512 KB) checks. `pre-commit.ci` auto-fixes PRs and runs weekly autoupdates.
- **Dependency note.** `click>=8.1` is declared in `pyproject.toml` but `cli.py` currently uses `argparse`. If extending the CLI, pick one and standardize — don't mix.
