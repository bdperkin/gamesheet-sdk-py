# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project nature

Unofficial Python SDK + CLI for the GameSheet Inc. platform. GameSheet does not publish a public API for the operations this library targets, so functionality is implemented by **automating the GameSheet WebUI** via a combination of:

- `requests` for plain HTTP
- `beautifulsoup4` + `lxml` for HTML parsing
- `playwright` (headless Chromium) for flows that require a real browser

Because behavior depends on a third-party UI, expect breakage on vendor changes. When adding or fixing a workflow, prefer the lightest mechanism that works (HTTP > HTML parse > headless browser) — headless automation is the slowest and most fragile path.

The package is alpha and currently a skeleton: only `__init__.py` and `cli.py` exist under `src/gamesheet_sdk/`. Most domain modules are yet to be written.

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

# Tox: orchestrates all of the above in isolated venvs (config in [tool.tox])
tox                          # py311..py314 + lint + type + pylint + security + files-check
tox -e lint                  # black --check, isort --check, flake8
tox -e type                  # mypy --strict
tox -e pylint                # pylint
tox -e security              # bandit -r src (config in [tool.bandit])
tox -e files-check           # codespell, yamllint, validate-pyproject, editorconfig-checker, mdformat --check
tox -e fix                   # apply formatters in place: isort, black, mdformat
tox -e py314 -- -k test_name # pass args to pytest after --

# Sphinx documentation (extras: pip install -e ".[docs]")
tox -e docs                  # HTML (two-pass: warm-up + strict -n -W)
tox -e docs-lint             # sphinx-lint over docs/
tox -e docs-doctest          # run doctest examples
tox -e docs-linkcheck        # check external links
tox -e docs-epub             # EPUB
tox -e docs-man              # man pages
tox -e docs-pdf              # PDF (needs LaTeX/pdflatex/latexmk on PATH)
tox -e docs-serve            # sphinx-autobuild live-reload preview
```

The CLI installed by the package is `gamesheet-sdk-py` (entry point: `gamesheet_sdk.cli:main`).

## Architecture notes

- **`src/` layout.** Tests import via the installed package; `pyproject.toml` also sets `pythonpath = ["src"]` so `pytest` works without an install, but workflows that need the CLI or Playwright still require `pip install -e ".[dev]"`.
- **Typed package.** `py.typed` is shipped (PEP 561) and `[tool.mypy] strict = true` is enabled — all new code must be fully annotated and pass `mypy --strict`.
- **Dynamic versioning.** The package version is *not* in `pyproject.toml`. `[tool.hatch.version]` uses `source = "vcs"` (hatch-vcs) to derive it from `git describe`. A `_version.py` is written into `src/gamesheet_sdk/` at build time and is gitignored; `__init__.py` imports `__version__` from it, falling back to `importlib.metadata` when running uninstalled. To cut a release, tag the commit (`git tag -a vX.Y.Z -m '...'` then `git push --tags`) — never edit a version literal. Untagged commits get setuptools-scm's `guess-next-dev` form like `0.0.2.dev1+gHASH`.
- **Python 3.11–3.14.** Use modern syntax (`from __future__ import annotations`, `X | None`, etc.) as `cli.py` already does.
- **Formatting/lint pipeline.** Python: black (88), isort (`profile = "black"`), flake8 (via `Flake8-pyproject` reading `[tool.flake8]`), pyupgrade (`--py311-plus`), mypy (`--strict`), pylint, bandit (`[tool.bandit]`). Non-Python: codespell (`[tool.codespell]`), yamllint (`-d relaxed`), validate-pyproject, editorconfig-checker, mdformat (+ mdformat-gfm), sphinx-lint. All wired into pre-commit, tox (envs: `lint`, `type`, `pylint`, `security`, `files-check`, plus `fix` for auto-apply), and GitHub Actions (CI calls tox). mypy + pylint in pre-commit use `local` hooks because (a) pre-commit/mirrors-mypy tags currently drift ahead of upstream mypy on PyPI, and (b) pylint needs the project's runtime deps duplicated in `additional_dependencies` to resolve imports inside the isolated hook venv. `pre-commit.ci` auto-fixes PRs and runs weekly autoupdates.
- **Documentation.** Sphinx (Furo theme, MyST-Parser for markdown sources) lives under `docs/`. `conf.py` enables autodoc + autosummary (API), `sphinx-argparse` (CLI from the live `build_parser`), intersphinx (cross-refs to stdlib/requests/pydantic/click), autosectionlabel, napoleon, todo, copybutton, sphinx-design. Output formats: HTML, EPUB, man, LaTeX/PDF. Strict-mode build (`-n -W`) runs two-pass to satisfy autosummary's stub-then-toctree ordering. Built, link-checked, and deployed to GitHub Pages by `.github/workflows/docs.yml`; `_build/` and `_autosummary/` are gitignored.
- **Documentation organization — Diátaxis.** Every doc page belongs to exactly one of four quadrants under `docs/`: `tutorials/` (learning-oriented), `how-to/` (task-oriented), `reference/` (information-oriented), or `explanation/` (understanding-oriented). When adding a page, pick the quadrant by asking *what is the reader's need?*, not *what is the topic?* — a topic may have a page in more than one quadrant (e.g. an "auth" how-to *and* an "auth" reference page). The `docs/explanation/diataxis.md` page is the in-tree primer; the canonical source is [diataxis.fr](https://diataxis.fr/).
- **Dependency note.** `click>=8.1` is declared in `pyproject.toml` but `cli.py` currently uses `argparse`. If extending the CLI, pick one and standardize — don't mix.
