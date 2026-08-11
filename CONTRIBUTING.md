# Contributing to gamesheet-sdk-py

<!--TOC-->

______________________________________________________________________

- [1. Table of Contents](#1-table-of-contents)
- [2. Code of Conduct](#2-code-of-conduct)
- [3. Getting Started](#3-getting-started)
- [4. Development Setup](#4-development-setup)
  - [4.1. Prerequisites](#41-prerequisites)
  - [4.2. Initial Setup](#42-initial-setup)
  - [4.3. Verifying Your Setup](#43-verifying-your-setup)
- [5. Development Workflow](#5-development-workflow)
  - [5.1. Creating a Feature Branch](#51-creating-a-feature-branch)
  - [5.2. Making Changes](#52-making-changes)
  - [5.3. Project Structure](#53-project-structure)
- [6. Code Style Guidelines](#6-code-style-guidelines)
  - [6.1. Line Length](#61-line-length)
    - [6.1.1. Python Version](#611-python-version)
    - [6.1.2. Formatters (Auto-fix)](#612-formatters-auto-fix)
    - [6.1.3. Linters](#613-linters)
    - [6.1.4. Type Checking](#614-type-checking)
- [7. Testing Requirements](#7-testing-requirements)
  - [7.1. Coverage Requirement](#71-coverage-requirement)
  - [7.2. Test Categories](#72-test-categories)
  - [7.3. Network Isolation](#73-network-isolation)
  - [7.4. Running Tests](#74-running-tests)
  - [7.5. Writing Tests](#75-writing-tests)
- [8. Documentation Requirements](#8-documentation-requirements)
  - [8.1. Docstring Coverage](#81-docstring-coverage)
  - [8.2. Docstring Style](#82-docstring-style)
  - [8.3. Documentation Files](#83-documentation-files)
  - [8.4. API Documentation](#84-api-documentation)
- [9. Commit Message Conventions](#9-commit-message-conventions)
  - [9.1. Format](#91-format)
  - [9.2. Types](#92-types)
  - [9.3. Scopes (Optional but Encouraged)](#93-scopes-optional-but-encouraged)
  - [9.4. Breaking Changes](#94-breaking-changes)
  - [9.5. Examples](#95-examples)
  - [9.6. Commit Message Tips](#96-commit-message-tips)
- [10. Pull Request Process](#10-pull-request-process)
  - [10.1. Before Opening a PR](#101-before-opening-a-pr)
  - [10.2. Opening a PR](#102-opening-a-pr)
  - [10.3. PR Title](#103-pr-title)
  - [10.4. PR Review Process](#104-pr-review-process)
  - [10.5. After Your PR is Merged](#105-after-your-pr-is-merged)
- [11. Complexity Requirements](#11-complexity-requirements)
  - [11.1. Checking Complexity](#111-checking-complexity)
  - [11.2. Reducing Complexity](#112-reducing-complexity)
- [12. Common Tasks](#12-common-tasks)
  - [12.1. Adding a New CLI Command](#121-adding-a-new-cli-command)
  - [12.2. Adding a New Domain Module](#122-adding-a-new-domain-module)
  - [12.3. Adding a New Dependency](#123-adding-a-new-dependency)
  - [12.4. Running Tools via uv](#124-running-tools-via-uv)
- [13. Getting Help](#13-getting-help)
  - [13.1. Project Maintainers](#131-project-maintainers)
- [14. Recognition](#14-recognition)

______________________________________________________________________

<!--TOC-->

Thank you for your interest in contributing to gamesheet-sdk-py! We welcome contributions from the community and are grateful for your time and effort.

This document provides guidelines and information to help you contribute effectively. Whether you are fixing a bug, adding a feature, improving documentation,
or enhancing tests, your contributions help make this project better for everyone.

## 1. Table of Contents

01. [Code of Conduct](#code-of-conduct)
02. [Getting Started](#getting-started)
03. [Development Setup](#development-setup)
04. [Development Workflow](#development-workflow)
05. [Code Style Guidelines](#code-style-guidelines)
06. [Testing Requirements](#testing-requirements)
07. [Documentation Requirements](#documentation-requirements)
08. [Commit Message Conventions](#commit-message-conventions)
09. [Pull Request Process](#pull-request-process)
10. [Complexity Requirements](#complexity-requirements)
11. [Common Tasks](#common-tasks)
12. [Getting Help](#getting-help)

## 2. Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. By participating in this project, you agree to abide by our commitment
to respectful and professional conduct.

## 3. Getting Started

Before you begin:

1. Make sure you have read the [README.md](README.md) to understand the project's purpose and scope
2. Check the [issues](https://github.com/bdperkin/gamesheet-sdk-py/issues) to see if your bug or feature has already been reported or is being worked on
3. For major changes, open an issue first to discuss your proposed approach
4. Review the [documentation](https://bdperkin.github.io/gamesheet-sdk-py/) to understand the project's architecture

## 4. Development Setup

### 4.1. Prerequisites

- **Python 3.11+** (3.11, 3.12, 3.13, or 3.14)
- **Git** for version control
- **make** (optional, but recommended for convenience)

### 4.2. Initial Setup

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR-USERNAME/gamesheet-sdk-py.git
cd gamesheet-sdk-py
```

1. Install the package in editable mode with all development dependencies:

```bash
# Option 1: Install everything (recommended for contributors)
uv sync --all-extras

# Option 2: Leaner install (just tests + docs)
uv sync --extra dev --extra pytest --extra docs

# Option 3: Use the Makefile shortcut
make install
```

1. Install Playwright browser binaries (required for headless-browser code paths):

```bash
python -m playwright install chromium
```

1. Set up pre-commit hooks:

```bash
pre-commit install
```

This will automatically run code quality checks before each commit.

### 4.3. Verifying Your Setup

Run the test suite to ensure everything is working:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Or use the Makefile
make test
```

## 5. Development Workflow

### 5.1. Creating a Feature Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix-name
```

### 5.2. Making Changes

1. Make your changes in the appropriate files under `src/gamesheet_sdk/` or `tests/`
2. Add or update tests to cover your changes
3. Update documentation as needed
4. Run the quality checks:

```bash
# Run pre-commit hooks on all files
pre-commit run --all-files

# Or use the Makefile
make lint
```

1. Run tests to ensure nothing broke:

```bash
pytest --cov
# or
make test-cov
```

### 5.3. Project Structure

The project uses a `src/` layout with the following structure:

- `src/gamesheet_sdk/` - Main package code
  - `auth/` - Authentication package (login, sessions, tokens)
  - `cli/` - Command-line interface package
    - `commands/` - Individual CLI command modules
    - `shared/` - Shared CLI utilities
  - `games/` - Games domain package
  - `roster/` - Roster management package
  - `shared/` - Shared utilities package
  - Domain modules (associations.py, divisions.py, leagues.py, seasons.py, teams.py, etc.)
- `tests/` - Test suite
  - `auth/` - Authentication tests
  - `cli/` - CLI command tests
  - `fixtures/` - Shared test fixtures
  - `helpers/` - Test helper modules
  - `integration/` - Integration tests
  - `unit/` - Unit tests by domain
- `docs/` - Sphinx documentation (follows Diataxis framework)

## 6. Code Style Guidelines

### 6.1. Line Length

- Maximum line length: **110 characters**
- Configured in ruff and other formatters

#### 6.1.1. Python Version

- Use modern Python 3.11+ syntax
- Include `from __future__ import annotations` at the top of files
- Use `X | None` instead of `Optional[X]`
- Use `X | Y` instead of `Union[X, Y]`

#### 6.1.2. Formatters (Auto-fix)

The project uses Ruff for code formatting and linter fixes:

- `ruff format` - fast Python code formatter (line length: 110)
- `ruff check --fix` - automated linter fixes and import sorting

Apply all formatters with:

```bash
make fix
```

#### 6.1.3. Linters

The project uses comprehensive linting:

- **ruff** with ALL rule groups enabled (Google docstring style, PEP 8, complexity, etc.)
- **blocklint** for inclusive language

#### 6.1.4. Type Checking

All code must pass static type checking via Astral `ty`:

```bash
# ty check
uv run --extra ty ty check

# Or use the Makefile
make typecheck
```

**Requirements:**

- All functions, methods, and variables must have type annotations
- No `Any` types without justification
- Pass `ty check` with zero errors
- The project ships with `py.typed` (PEP 561)

## 7. Testing Requirements

### 7.1. Coverage Requirement

**100% test coverage is required** for all code.

- **Local enforcement**: `[tool.coverage.report] fail_under = 100` in pyproject.toml
- **Codecov enforcement**: Project coverage target 100% (0% drop tolerated), patch coverage 100% on newly-introduced lines

### 7.2. Test Categories

Tests use pytest markers (declared in `[tool.pytest.ini_options].markers`):

- `@pytest.mark.vcr` - Replays HTTP from cassettes (sensitive data scrubbed)
- `@pytest.mark.browser` - Requires headless Chromium (slow tests)

### 7.3. Network Isolation

Tests are configured with `--block-network` (via `pytest-recording`):

- Any test that opens a socket without a VCR cassette will fail
- Use `@pytest.mark.vcr` for HTTP-based tests
- Use `@pytest.mark.browser` for Playwright tests

### 7.4. Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run only fast tests (skip browser tests)
pytest -m "not browser"

# Run specific test file
pytest tests/test_init_coverage.py

# Run specific test
pytest tests/test_init_coverage.py::test_version_is_string

# Use Makefile shortcuts
make test        # full suite
make test-fast   # skip browser tests
make test-cov    # with coverage
```

### 7.5. Writing Tests

- Place tests in the appropriate directory under `tests/`
- Follow the existing test structure and naming conventions
- Use fixtures from `tests/fixtures/` and `tests/conftest.py`
- Mock external dependencies
- Use VCR cassettes for HTTP interactions (scrub sensitive data in `tests/conftest.py`)
- Ensure all code paths are covered (branches, exceptions, edge cases)

## 8. Documentation Requirements

### 8.1. Docstring Coverage

**100% docstring coverage is required** for all public APIs.

Enforced via `interrogate` with `fail-under = 100`:

```bash
# Check docstring coverage
uv run --extra interrogate interrogate src
```

### 8.2. Docstring Style

- **Style**: Google (configured in `[tool.ruff.lint.pydocstyle] convention = "google"`)
- **Format**: PEP 257 / Google style, enforced by `ruff`
- **Length**: Wrap at 110 characters

Example:

```python
def example_function(arg1: str, arg2: int) -> bool:
    """
    Short one-line summary of what the function does.

    Longer description if needed, explaining the purpose, behavior, and any important details.

    :param arg1: Description of arg1
    :param arg2: Description of arg2
    :return: Description of return value
    :raises ValueError: When and why this exception is raised
    """
    pass
```

### 8.3. Documentation Files

The project uses [Diataxis](https://diataxis.fr/) for documentation organization under `docs/`:

- **tutorials/** - Learning-oriented guides
- **how-to/** - Task-oriented guides
- **reference/** - Information-oriented reference (API, CLI, configuration)
- **explanation/** - Understanding-oriented explanations

When adding documentation:

1. Choose the appropriate quadrant based on reader's need
2. Follow Sphinx/MyST-Parser syntax
3. Ensure links work (`make docs-linkcheck`)
4. Preview locally (`make docs-serve`)

### 8.4. API Documentation

API docs are auto-generated from docstrings using Sphinx autodoc/autosummary. After adding or modifying public APIs, regenerate docs:

```bash
make docs
```

## 9. Commit Message Conventions

**All commits must follow [Conventional Commits](https://www.conventionalcommits.org/) format.**

This is enforced by the `conventional-pre-commit` hook.

### 9.1. Format

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 9.2. Types

- `feat:` - A new feature (triggers patch bump until 1.0.0, then minor)
- `fix:` - A bug fix (triggers patch bump)
- `docs:` - Documentation-only changes
- `style:` - Code style changes (formatting, missing semicolons, etc.)
- `refactor:` - Code refactoring (neither fixes a bug nor adds a feature)
- `perf:` - Performance improvements (triggers patch bump)
- `test:` - Adding or updating tests
- `build:` - Build system or external dependency changes
- `ci:` - CI configuration changes
- `chore:` - Other changes that don't modify src or test files
- `revert:` - Reverts a previous commit

### 9.3. Scopes (Optional but Encouraged)

Examples: `auth`, `cli`, `api`, `docs`, `tests`, `deps`, `config`

### 9.4. Breaking Changes

For breaking changes (triggers major bump after 1.0.0):

- Add `!` after type/scope: `feat!: breaking change description`
- Or include `BREAKING CHANGE:` in the commit body/footer

### 9.5. Examples

```bash
# Feature commit
feat(cli): add seasons list command with JSON output

# Bug fix commit
fix(auth): handle expired tokens in session refresh flow

# Documentation commit
docs(api): update authentication examples in README

# Breaking change commit (after 1.0.0)
feat(api)!: change list_seasons return type to iterator

BREAKING CHANGE: list_seasons now returns an iterator instead of a list.
Update your code to convert to list if needed: list(list_seasons(...))
```

### 9.6. Commit Message Tips

- Use imperative mood ("add feature" not "added feature")
- Keep the first line under 72 characters
- Provide context in the body for non-trivial changes
- Reference issues: `Closes #123` or `Fixes #456`

## 10. Pull Request Process

### 10.1. Before Opening a PR

1. Ensure all tests pass: `pytest --cov`
2. Ensure 100% test coverage: `pytest --cov` (coverage report will show any gaps)
3. Run quality gates: `pre-commit run --all-files`
4. Check complexity: `make metrics` (all blocks must be grade A)
5. Ensure type checking passes: `make type`
6. Update documentation if needed
7. Ensure all commits follow Conventional Commits format

### 10.2. Opening a PR

1. Push your branch to your fork:

```bash
git push origin feature/your-feature-name
```

1. Open a PR on GitHub from your fork to the main repository
2. Fill out the PR template (if available) with:
   - **Description**: What does this PR do and why?
   - **Testing**: How was this tested?
   - **Related Issues**: Reference any related issues
   - **Breaking Changes**: Note any breaking changes

### 10.3. PR Title

PR titles should also follow Conventional Commits format:

```text
feat(cli): add support for division management commands
fix(auth): prevent token refresh race condition
docs: add CONTRIBUTING.md with comprehensive guidelines
```

### 10.4. PR Review Process

1. Automated CI checks will run:

   - Build and install sanity check
   - Test suite (Python 3.11-3.14 matrix)
   - Pre-commit hooks
   - Type checker (ty)
   - Linters (ruff, blocklint)
   - Security scans (CodeQL, Semgrep, Trivy, OSV-Scanner)
   - Documentation build
   - Codecov upload and coverage enforcement

2. A maintainer will review your code

3. Address any feedback by pushing additional commits to your branch

4. Once approved and CI passes, a maintainer will merge your PR

### 10.5. After Your PR is Merged

1. Delete your feature branch (GitHub offers a button for this)
2. Update your local repository:

```bash
git checkout main
git pull upstream main
```

1. The automated release workflow will handle versioning and changelog generation based on your Conventional Commits

## 11. Complexity Requirements

**All code blocks (functions, methods, classes) must maintain cyclomatic complexity grade A (cc ≤ 5).**

This is enforced by a `xenon` pre-commit hook:

```bash
xenon --max-absolute=A --max-modules=A --max-average=B src/
```

### 11.1. Checking Complexity

```bash
# Check complexity metrics
make metrics

# Or use uv
uv run --extra radon radon cc --show-complexity --average .
```

### 11.2. Reducing Complexity

When adding a fourth `if` / `except` / `for` / `and` / `or` to a block:

1. **Extract a helper function** - Break complex logic into smaller, well-named functions
2. **Use guard clauses** - Return early to reduce nesting
3. **Simplify conditions** - Use boolean algebra to simplify compound conditions
4. **Use dict/mapping** - Replace long if-elif chains with dictionary lookups

Example pattern from `auth/login.py`:

```python
# Instead of one large function with high complexity:
def login(config, email, password):
    # ... many lines of complex logic ...
    pass


# Break into smaller focused functions:
def login(config, email, password):
    email = _resolve_email(config, email)
    password = _resolve_password(config, password)
    _wait_for_login_form(page)
    _attach_response_capture(page)
    _submit_login_form(page, email, password)
    return _await_auth_outcome(page)
```

## 12. Common Tasks

### 12.1. Adding a New CLI Command

1. Create or modify a command module under `src/gamesheet_sdk/cli/commands/`
2. Use `ResourceGroup` for resource-oriented commands (create, get, list, update, delete)
3. Add command to appropriate group or create new group
4. Register in `src/gamesheet_sdk/cli/main.py`
5. Add tests under `tests/cli/`
6. The CLI reference docs will auto-update via `sphinx-click`

### 12.2. Adding a New Domain Module

1. Create pydantic models in a new module under `src/gamesheet_sdk/`
2. Implement action functions (e.g., `list_items()`, `get_item()`, `create_item()`)
3. Create corresponding CLI command module under `src/gamesheet_sdk/cli/commands/`
4. Add comprehensive tests under `tests/unit/` and `tests/cli/`
5. Update documentation

### 12.3. Adding a New Dependency

1. Add to `[project] dependencies` in `pyproject.toml` for runtime dependencies
2. Or add to `optional-dependencies.<group>` for dev/test dependencies
3. Update the `[all]` extra if needed
4. Run `uv sync --all-extras` to install
5. Consider adding type stubs to `optional-dependencies.type-stubs` if available

### 12.4. Running Tools via uv

Run specific tools in isolated environments with `uv run`:

```bash
uv run --extra ty ty check
uv run --extra ruff ruff check .
```

## 13. Getting Help

- **Documentation**: <https://bdperkin.github.io/gamesheet-sdk-py/>
- **Issues**: <https://github.com/bdperkin/gamesheet-sdk-py/issues>
- **Discussions**: Open an issue for questions or feature proposals
- **CLAUDE.md**: See the [CLAUDE.md](CLAUDE.md) file for detailed project architecture and conventions
- **Makefile**: Run `make help` for a list of available make targets

### 13.1. Project Maintainers

The project maintainers are listed in the [CODEOWNERS](https://github.com/bdperkin/gamesheet-sdk-py/blob/main/.github/CODEOWNERS) file (if available) or can be
found in the commit history.

## 14. Recognition

All contributors will be recognized in the project's commit history and on GitHub's contributors page. Significant contributions may be highlighted in release
notes.

Thank you for contributing to gamesheet-sdk-py!
