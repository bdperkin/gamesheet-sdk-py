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
- [6. Using Tox](#6-using-tox)
- [7. Makefile Shortcuts](#7-makefile-shortcuts)
- [8. Committing Changes](#8-committing-changes)
- [9. Troubleshooting](#9-troubleshooting)
  - [9.1. Pre-commit hook failures](#91-pre-commit-hook-failures)
  - [9.2. Playwright browser issues](#92-playwright-browser-issues)
  - [9.3. Tox environment issues](#93-tox-environment-issues)
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
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

### 2.2. Install Dependencies

```bash
# Install everything (recommended for full development)
pip install -e ".[all]"

# Or install only what you need:
pip install -e ".[dev,pytest,docs]"  # dev tools + tests + docs
pip install -e ".[dev,pytest]"        # minimal: dev tools + tests only
```

### 2.3. Install Playwright Browsers

```bash
python -m playwright install chromium
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
pytest

# Skip slow browser-based tests
pytest -m "not browser"

# With coverage report
pytest --cov

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
mypy src

# Pyright
pyright

# Both via tox
tox -e mypy
tox -e pyright
```

### 4.3. Linting

```bash
# Run all linters via pre-commit
pre-commit run --all-files

# Individual linters
pylint src/
flake8 src/
bandit -r src/
semgrep scan --config auto --error

# Via tox
tox -e pylint
tox -e flake8
tox -e bandit
tox -e semgrep
```

### 4.4. Formatting

```bash
# Auto-fix with make
make fix

# Or run formatters individually
black src/ tests/
isort src/ tests/
mdformat docs/ *.md

# Via tox
tox -e fix
```

### 4.5. Complexity Gates

```bash
# Check code metrics
make metrics

# Or via tox
tox -e metrics
tox -e xenon
```

## 5. Documentation

### 5.1. Building Docs

```bash
# Build HTML docs
make docs

# Or via tox
tox -e docs

# Build other formats
tox -e docs-epub   # EPUB e-book
tox -e docs-man    # man pages
tox -e docs-pdf    # PDF (requires LaTeX)
```

### 5.2. Live Preview

```bash
# Auto-rebuild on file changes
make docs-serve

# Or via tox
tox -e docs-serve
```

### 5.3. Link Checking

```bash
tox -e docs-linkcheck
```

## 6. Using Tox

Tox provides isolated environments for each tool:

```bash
# List all available environments
tox -l

# Run test matrix
tox -m tests

# Run documentation builds
tox -m docs

# Run pre-commit suite
tox -m pre-commit

# Run single environment
tox -e pytest
tox -e mypy
tox -e docs

# Pass arguments to pytest
tox -e pytest -- -v -k test_name
```

## 7. Makefile Shortcuts

```bash
# Show all available targets
make help

# Common workflows
make install       # pip install + Playwright setup
make test          # pytest
make test-fast     # pytest -m "not browser"
make test-cov      # pytest --cov
make lint          # pre-commit run --all-files
make type          # mypy src
make fix           # auto-format code
make metrics       # radon + xenon
make docs          # build HTML docs
make docs-serve    # live-reload docs
make clean         # remove build artifacts
make clean-all     # aggressive clean (includes .tox, .venv)
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
python -m playwright install --force chromium

# Check installation
python -m playwright install --dry-run
```

### 9.3. Tox environment issues

Clean and rebuild tox environments:

```bash
tox -e pytest --recreate
# or
rm -rf .tox
tox -e pytest
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
