# Documentation

<!--TOC-->

______________________________________________________________________

- [1. Quick start](#1-quick-start)
- [2. Architecture](#2-architecture)
  - [2.1. Automatic API documentation](#21-automatic-api-documentation)
    - [2.1.1. How it works](#211-how-it-works)
    - [2.1.2. When API docs are regenerated](#212-when-api-docs-are-regenerated)
    - [2.1.3. Freshness checking](#213-freshness-checking)
  - [2.2. CLI documentation](#22-cli-documentation)
  - [2.3. Custom templates](#23-custom-templates)
- [3. Directory structure](#3-directory-structure)
- [4. Diataxis framework](#4-diataxis-framework)
- [5. Building documentation](#5-building-documentation)
  - [5.1. Local builds](#51-local-builds)
  - [5.2. Using uv](#52-using-uv)
- [6. CI/CD](#6-cicd)
- [7. Configuration](#7-configuration)
- [8. Troubleshooting](#8-troubleshooting)
  - [8.1. API docs out of date](#81-api-docs-out-of-date)
  - [8.2. Missing modules in API reference](#82-missing-modules-in-api-reference)
  - [8.3. Sphinx warnings](#83-sphinx-warnings)
  - [8.4. Import errors during build](#84-import-errors-during-build)
- [9. References](#9-references)

______________________________________________________________________

<!--TOC-->

This directory contains the Sphinx-based documentation for gamesheet-sdk-py.

## 1. Quick start

```bash
# Generate API documentation
make docs-api

# Build HTML documentation
make docs

# Live-reload preview
make docs-serve

# Check if API docs are up-to-date
make docs-check

# Lint documentation
make docs-lint
```

## 2. Architecture

### 2.1. Automatic API documentation

API documentation is **automatically generated** from Python source code using `sphinx-apidoc`. This ensures the API reference stays in sync with the actual
codebase.

#### 2.1.1. How it works

1. **`docs/generate_api_docs.py`** - Runs `sphinx-apidoc` to recursively discover all Python modules in `src/gamesheet_sdk/` and generates ReStructuredText
   files with `automodule` directives.

2. **`docs/reference/_autosummary/`** - Generated `.rst` files (gitignored) that document each module, package, and subpackage.

3. **`docs/reference/api.md`** - The main API reference page that includes links to all generated documentation.

4. **`docs/conf.py`** - Sphinx configuration with `autosummary_generate = True` to automatically create documentation stubs.

#### 2.1.2. When API docs are regenerated

API documentation is regenerated automatically:

- **During `make docs`** - The two-pass build runs `generate_api_docs.py` before each pass
- **During `make docs-serve`** - The live-reload server watches `src/gamesheet_sdk/` for changes
- **During `make docs-lint`** - Ensures docs are fresh before linting
- **In CI/CD** - `docs.yml` runs `generate_api_docs.py` via `uv run --extra docs` before every build

#### 2.1.3. Freshness checking

**`docs/check_api_freshness.py`** compares modification times of source files vs. generated documentation to detect when regeneration is needed. Run it with:

```bash
make docs-check
```

This is automatically run by `make docs-lint` and in CI.

### 2.2. CLI documentation

CLI documentation uses `sphinx-click` to automatically render the click command trees from `gamesheet_sdk.admin.cli.main:cli` and
`gamesheet_sdk.teams.cli.main:cli`. The rendered documentation always matches the shipped binaries because it's generated live from the actual click groups.

See `docs/reference/cli.md` which uses `eval-rst` directives with the `click` domain to automatically generate CLI documentation for both `gamesheet-admin` and
`gamesheet-teams` from the code.

### 2.3. Custom templates

Sphinx autosummary templates can be customized in `docs/_templates/`:

- `custom-module-template.rst` - Template for module documentation
- `custom-class-template.rst` - Template for class documentation

These templates control how API documentation is structured and formatted.

## 3. Directory structure

```text
docs/
├── README.md                          # This file
├── conf.py                            # Sphinx configuration
├── index.md                           # Documentation home page
├── generate_api_docs.py               # API doc generation script
├── check_api_freshness.py             # Freshness validation script
├── _templates/                        # Custom Sphinx templates
│   ├── custom-module-template.rst
│   └── custom-class-template.rst
├── reference/                         # API & CLI reference
│   ├── api.md                         # Main API reference page
│   ├── cli.md                         # CLI reference (sphinx-click)
│   ├── index.md
│   └── _autosummary/                  # Generated API docs (gitignored)
│       ├── gamesheet_sdk.*.rst
│       └── ...
├── tutorials/                         # Learning-oriented guides
├── how-to/                            # Task-oriented guides
└── explanation/                       # Understanding-oriented guides
```

## 4. Diataxis framework

Documentation is organized using the [Diataxis framework](https://diataxis.fr/):

- **Tutorials** (`tutorials/`) - Learning-oriented, step-by-step lessons
- **How-to guides** (`how-to/`) - Task-oriented, goal-focused recipes
  - [Development Setup](how-to/development-setup.md) - Local development environment setup
  - [Release Process](how-to/release-process.md) - Automated releases with Conventional Commits
- **Reference** (`reference/`) - Information-oriented, technical descriptions
  - [API Reference](reference/api.md) - Auto-generated Python API documentation
  - [CLI Reference](reference/cli.md) - Command-line interface documentation
  - [Configuration](reference/configuration.md) - Environment variables and settings
- **Explanation** (`explanation/`) - Understanding-oriented, background and context

See `docs/explanation/diataxis.md` for more details.

## 5. Building documentation

### 5.1. Local builds

```bash
# Full two-pass build (strict mode on second pass)
make docs

# Live-reload preview at http://127.0.0.1:8000
make docs-serve

# PDF documentation (requires pdflatex + latexmk)
make docs-pdf

# Check external links
make docs-linkcheck
```

### 5.2. Using uv

```bash
# HTML documentation
uv run --extra docs sphinx-build -b html docs docs/_build/html

# Live-reload server
uv run --extra docs sphinx-autobuild docs docs/_build/html

# EPUB format
uv run --extra docs sphinx-build -b epub docs docs/_build/epub

# Man page format
uv run --extra docs sphinx-build -b man docs docs/_build/man

# PDF format
uv run --extra docs sphinx-build -b latex docs docs/_build/latex && make -C docs/_build/latex all-pdf

# Lint documentation
uv run --extra docs sphinx-lint docs

# Check external links
uv run --extra docs sphinx-build -b linkcheck docs docs/_build/linkcheck

# Run doctests
uv run --extra docs sphinx-build -b doctest docs docs/_build/doctest
```

## 6. CI/CD

Documentation builds run in GitHub Actions (`.github/workflows/docs.yml`):

- **HTML, EPUB, man, PDF builds** - Matrix of different output formats
- **Linting** - `sphinx-lint` plus API freshness checks
- **Link checking** - Validation of external links
- **Deployment** - HTML docs deploy to GitHub Pages on push to `main`

## 7. Configuration

Key Sphinx settings in `docs/conf.py`:

```python
# Automatic API documentation
autosummary_generate = True
autosummary_generate_overwrite = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "inherited-members": True,
    "member-order": "bysource",
}

# Extensions
extensions = [
    "sphinx.ext.autodoc",  # API documentation
    "sphinx.ext.autosummary",  # Automatic stub generation
    "sphinx.ext.napoleon",  # Google/NumPy docstring support
    "sphinx.ext.intersphinx",  # Cross-project links
    "sphinx_click",  # CLI documentation
    "myst_parser",  # Markdown support
    # ... and more
]
```

## 8. Troubleshooting

### 8.1. API docs out of date

If source files change but docs don't update:

```bash
# Manually regenerate API docs
make docs-api

# Or rebuild everything
make clean-all
make docs
```

### 8.2. Missing modules in API reference

Check if `sphinx-apidoc` excluded them:

```bash
# See what was generated
ls docs/reference/_autosummary/

# Check exclusion patterns in docs/generate_api_docs.py
```

### 8.3. Sphinx warnings

Run with verbose output:

```bash
sphinx-build -b html -v docs docs/_build/html
```

### 8.4. Import errors during build

Ensure the package is installed in editable mode:

```bash
uv sync --extra docs
```

## 9. References

- [Sphinx documentation](https://www.sphinx-doc.org/)
- [sphinx-apidoc](https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html)
- [sphinx-click](https://sphinx-click.readthedocs.io/)
- [MyST Parser](https://myst-parser.readthedocs.io/)
- [Furo theme](https://pradyunsg.me/furo/)
- [Diataxis framework](https://diataxis.fr/)
