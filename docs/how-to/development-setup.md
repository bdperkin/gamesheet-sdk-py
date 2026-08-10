# Development Setup

<!--TOC-->

______________________________________________________________________

- [1. Prerequisites](#1-prerequisites)
- [2. Initial Setup](#2-initial-setup)
  - [2.1. Clone and Create Environment](#21-clone-and-create-environment)
  - [2.2. Install Dependencies](#22-install-dependencies)
  - [2.3. Install Playwright Browsers](#23-install-playwright-browsers)
  - [2.4. Install Pre-commit Hooks](#24-install-pre-commit-hooks)
- [3. Running Tests](#3-running-tests)
- [4. Code Quality](#4-code-quality)
  - [4.1. Pre-commit Hooks](#41-pre-commit-hooks)
  - [4.2. Type Checking](#42-type-checking)
  - [4.3. Linting](#43-linting)
  - [4.4. Formatting](#44-formatting)
  - [4.5. Complexity Gates](#45-complexity-gates)
- [5. Documentation](#5-documentation)
  - [5.1. Building Docs](#51-building-docs)
  - [5.2. Live Preview](#52-live-preview)
  - [5.3. Link Checking](#53-link-checking)
- [6. Using uv](#6-using-uv)
- [7. Makefile Shortcuts](#7-makefile-shortcuts)
- [8. Committing Changes](#8-committing-changes)
- [9. Troubleshooting](#9-troubleshooting)
  - [9.1. Pre-commit hook failures](#91-pre-commit-hook-failures)
  - [9.2. Playwright browser issues](#92-playwright-browser-issues)
  - [9.3. Virtual environment issues](#93-virtual-environment-issues)
  - [9.4. Coverage failures](#94-coverage-failures)
- [10. Next Steps](#10-next-steps)

______________________________________________________________________

<!--TOC-->

This guide covers setting up a local development environment for `gamesheet-sdk-py`.

## 1. Prerequisites

- Python 3.11, 3.12, 3.13, or 3.14
- Git
- Modern Linux, macOS, or Windows system

## 2. Initial Setup

### 2.1. Clone and Create Environment

```bash
git clone https://github.com/bdperkin/gamesheet-sdk-py.git
cd gamesheet-sdk-py

# Create isolated virtual environment
uv venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

### 2.2. Install Dependencies

```bash
# Install everything (recommended for full development)
uv sync --all-extras

# Or install only what you need:
uv sync --extra dev --extra pytest --extra docs  # dev tools + tests + docs
uv sync --extra dev --extra pytest        # minimal: dev tools + tests only
```

### 2.3. Install Playwright Browsers

```bash
uv run playwright install chromium
```

### 2.4. Install Pre-commit Hooks

```bash
# Install commit-msg hook for Conventional Commits enforcement
pre-commit install --hook-type commit-msg

# Install pre-commit hook for code quality checks
pre-commit install
```

## 3. Running Tests

```bash
# Full test suite
uv run pytest

# Skip slow browser-based tests
uv run pytest -m "not browser"

# With coverage report
uv run pytest --cov

# Single test file
pytest tests/test_smoke.py

# Single test function
pytest tests/test_smoke.py::test_version_is_string

# With verbose output
pytest -v

# Stop on first failure
pytest -x
```

## 4. Code Quality

### 4.1. Pre-commit Hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run mypy --all-files
pre-commit run black --all-files

# Update hook versions
pre-commit autoupdate
```

### 4.2. Type Checking

```bash
# MyPy (strict mode)
uv run mypy --strict src

# Pyright
uv run --extra pyright pyright
```

### 4.3. Linting

```bash
# Run all linters via pre-commit
uv run pre-commit run --all-files

# Individual linters
uv run --extra pylint pylint src/
uv run --extra flake8 flake8 src/
uv run --extra bandit bandit -c pyproject.toml -r src/
uv run --extra semgrep semgrep scan --config auto --error
```

### 4.4. Formatting

```bash
# Auto-fix with make
make fix

# Or run formatters individually via uv
uv run --extra black black src/ tests/
uv run --extra isort isort src/ tests/
uv run --extra mdformat mdformat docs/ *.md
```

### 4.5. Complexity Gates

```bash
# Check code metrics
make metrics

# Or via uv
uv run --extra radon radon cc --show-complexity --average .
```

## 5. Documentation

### 5.1. Building Docs

```bash
# Build HTML docs
make docs

# Or via uv
uv run --extra docs sphinx-build -b html docs docs/_build/html

# Build other formats via uv
uv run --extra docs sphinx-build -b epub docs docs/_build/epub
uv run --extra docs sphinx-build -b man docs docs/_build/man
uv run --extra docs sphinx-build -b latex docs docs/_build/latex && make -C docs/_build/latex all-pdf
```

### 5.2. Live Preview

```bash
# Auto-rebuild on file changes
make docs-serve

# Or via uv
uv run --extra docs sphinx-autobuild docs docs/_build/html
```

### 5.3. Link Checking

```bash
uv run --extra docs sphinx-build -b linkcheck docs docs/_build/linkcheck
```

## 6. Using uv

uv provides fast, isolated dependency management and tool execution:

```bash
# Sync all dependencies
uv sync --all-extras

# Run test suite
uv run pytest

# Run type checker
uv run mypy --strict src

# Run docs build
uv run --extra docs sphinx-build -b html docs docs/_build/html
```

## 7. Makefile Shortcuts

```bash
# Show all available targets
make help

# Common workflows
make install       # uv sync --extra dev + Playwright setup
make test          # uv run pytest
make test-fast     # uv run pytest -m "not browser"
make test-cov      # uv run pytest --cov
make lint          # uv run pre-commit run --all-files
make type          # uv run mypy --strict src
make fix           # auto-format code
make metrics       # radon complexity analysis
make docs          # build HTML docs
make docs-serve    # live-reload docs
make clean         # remove build artifacts
make clean-all     # aggressive clean (includes .uv, .venv)
```

## 8. Committing Changes

All commits **must** follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```bash
# Good commits
git commit -m "feat: add new command"
git commit -m "fix(auth): handle expired tokens"
git commit -m "docs: update README"
git commit -m "refactor: simplify login flow"

# Bad commits (will be rejected by pre-commit hook)
git commit -m "added stuff"
git commit -m "bug fix"
git commit -m "WIP"
```

Common types:

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `refactor:` — Code refactoring
- `test:` — Test changes
- `chore:` — Maintenance tasks
- `ci:` — CI/CD changes
- `build:` — Build system changes

## 9. Troubleshooting

### 9.1. Pre-commit hook failures

If a hook modifies files (e.g., black, isort), stage the changes and commit again:

```bash
git add -u
git commit -m "your message"
```

### 9.2. Playwright browser issues

If Playwright fails to launch Chromium:

```bash
# Reinstall browsers
uv run playwright install --force chromium

# Check installation
uv run playwright install --dry-run
```

### 9.3. Virtual environment issues

Clean and rebuild virtual environments:

```bash
uv venv --clear .venv
uv sync --all-extras
```

### 9.4. Coverage failures

If coverage drops below 100%:

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 10. Next Steps

- Read [Release Process](release-process.md) to understand how releases work
- Check [CLAUDE.md](../../CLAUDE.md) for architecture notes and project patterns
- Browse [docs/](../) for tutorials, how-tos, and reference documentation
