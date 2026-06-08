# Development Setup

This guide covers setting up a local development environment for `gamesheet-sdk-py`.

## Prerequisites

- Python 3.11, 3.12, 3.13, or 3.14
- Git
- Modern Linux, macOS, or Windows system

## Initial Setup

### 1. Clone and Create Environment

```bash
git clone https://github.com/bdperkin/gamesheet-sdk-py.git
cd gamesheet-sdk-py

# Create isolated virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
# Install everything (recommended for full development)
pip install -e ".[all]"

# Or install only what you need:
pip install -e ".[dev,pytest,docs]"  # dev tools + tests + docs
pip install -e ".[dev,pytest]"        # minimal: dev tools + tests only
```

### 3. Install Playwright Browsers

```bash
python -m playwright install chromium
```

### 4. Install Pre-commit Hooks

```bash
# Install commit-msg hook for Conventional Commits enforcement
pre-commit install --hook-type commit-msg

# Install pre-commit hook for code quality checks
pre-commit install
```

## Running Tests

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

## Code Quality

### Pre-commit Hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run mypy --all-files
pre-commit run black --all-files

# Update hook versions
pre-commit autoupdate
```

### Type Checking

```bash
# MyPy (strict mode)
mypy src

# Pyright
pyright

# Both via tox
tox -e mypy
tox -e pyright
```

### Linting

```bash
# Run all linters via pre-commit
pre-commit run --all-files

# Individual linters
pylint src/
flake8 src/
bandit -r src/

# Via tox
tox -e pylint
tox -e flake8
tox -e bandit
```

### Formatting

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

### Complexity Gates

```bash
# Check code metrics
make metrics

# Or via tox
tox -e metrics
tox -e xenon
```

## Documentation

### Building Docs

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

### Live Preview

```bash
# Auto-rebuild on file changes
make docs-serve

# Or via tox
tox -e docs-serve
```

### Link Checking

```bash
tox -e docs-linkcheck
```

## Using Tox

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

## Makefile Shortcuts

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

## Committing Changes

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

## Troubleshooting

### Pre-commit hook failures

If a hook modifies files (e.g., black, isort), stage the changes and commit again:

```bash
git add -u
git commit -m "your message"
```

### Playwright browser issues

If Playwright fails to launch Chromium:

```bash
# Reinstall browsers
python -m playwright install --force chromium

# Check installation
python -m playwright install --dry-run
```

### Tox environment issues

Clean and rebuild tox environments:

```bash
tox -e pytest --recreate
# or
rm -rf .tox
tox -e pytest
```

### Coverage failures

If coverage drops below 100%:

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Next Steps

- Read [Release Process](release-process.md) to understand how releases work
- Check [CLAUDE.md](../../CLAUDE.md) for architecture notes and project patterns
- Browse [docs/](../) for tutorials, how-tos, and reference documentation
