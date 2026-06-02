# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project nature

Unofficial Python SDK + CLI for the GameSheet Inc. platform. GameSheet does not publish a public API for the operations this library targets, so
functionality is implemented by **automating the GameSheet WebUI** via a combination of:

- `requests` for plain HTTP
- `playwright` (headless Chromium) for flows that require a real browser

Because behavior depends on a third-party UI, expect breakage on vendor changes. When adding or fixing a workflow, prefer the lightest mechanism that
works (HTTP > HTML parse > headless browser) — headless automation is the slowest and most fragile path.

The package is alpha. Modules under `src/gamesheet_sdk/`:

- `__init__.py` — public re-exports + `__version__`
- `associations.py` — `Association` pydantic model + `list_associations()` action
- `auth.py` — `login()` flow, token persistence (`load_access_token`, `load_refresh_token`, `save_tokens`), `AuthenticatedSession` HTTP layer with
  auto-refresh on 401
- `browser.py` — `BrowserSession` Playwright wrapper
- `cli.py` — click entry point (`gamesheet-sdk-py`), `ResourceGroup` class, `confirm_destructive` decorator, `completion` subcommand emitting
  bash/zsh/fish completion scripts
- `config.py` — `pydantic-settings` `Config` (resolves `GAMESHEET_*` env vars; CLI args > env > defaults)
- `exceptions.py` — `GameSheetError`, `AuthenticationError`
- `output.py` — `render()` for JSON / YAML / CSV / TSV / 13 tabulate formats + `write_output()`
- `session.py` — base `requests.Session` subclass

Future domain modules (teams, games, players, …) attach the same way: a thin action function in a domain module, a corresponding `ResourceGroup` in
`cli.py`.

## Common commands

```bash
# Editable install with everything (run once after clone / when deps change).
# `[dev]` is now minimal (pre-commit + tox-workdir only). `[all]` pulls every
# per-tool extra declared in pyproject.toml — pytest, mypy, lint suite, docs, …
pip install -e ".[all]"

# Or a leaner combo for just tests + docs:
pip install -e ".[dev,pytest,docs]"

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

### Makefile shortcuts

A `Makefile` wraps the most common workflows. `make help` lists every target. Highlights:

```bash
make install       # editable install ([dev] extras) + Playwright Chromium
make test          # full pytest suite
make test-fast     # pytest -m "not browser"
make test-cov      # pytest --cov
make lint          # pre-commit run --all-files
make type          # mypy --strict src
make fix           # apply formatters in place (isort, black, mdformat)
make metrics       # radon + xenon complexity gates
make docs          # Sphinx HTML build (two-pass strict)
make docs-serve    # live-reload preview
make docs-pdf      # PDF docs (needs LaTeX on PATH)
make docs-linkcheck
make clean         # caches + build artifacts (.tox, .venv, _build untouched)
make clean-all     # + .tox, $(VENV), docs build dirs
```

### Tox

Tox now ships ~45 envs — one per linter / formatter / type checker / doc builder — instead of the prior monolithic `lint` / `type` / `security` /
`files-check` aggregates. Use **labels** for grouped runs:

```bash
tox -l                # list every env
tox -m tests          # sanity (build/install) + pytest-py3{11..14}
tox -m docs           # docs, docs-lint, docs-linkcheck, docs-doctest, docs-epub, docs-man, docs-pdf, docs-serve
tox -m pre-commit     # pre-commit run --all-files inside a venv
tox -e pytest         # single-version pytest run (no Python matrix)
tox -e mypy           # mypy --strict
tox -e pyright        # pyright
tox -e pylint         # pylint
tox -e pyrefly        # pyrefly (architectural-health linter)
tox -e bandit         # bandit security scan
tox -e xenon          # complexity gate
tox -e metrics        # radon cc + radon mi
tox -e fix            # apply isort, black, mdformat in place
tox -e py314 -- -k test_name   # pass args to pytest after --
```

Every `pyproject.toml` `optional-dependencies.*` group has a matching tox env that installs only that extra plus the project, so each env runs in an
isolated venv with the minimum surface area.

The CLI installed by the package is `gamesheet-sdk-py` (entry point: `gamesheet_sdk.cli:main`).

## Architecture notes

- **`src/` layout.** Tests import via the installed package; `pyproject.toml` also sets `pythonpath = ["src"]` so `pytest` works without an install,
  but workflows that need the CLI or Playwright still require `pip install -e ".[all]"` (or at minimum `[dev,pytest]`).

- **Typed package.** `py.typed` is shipped (PEP 561) and `[tool.mypy] strict = true` is enabled — all new code must be fully annotated and pass
  `mypy --strict`.

- **Dynamic versioning.** The package version is _not_ in `pyproject.toml`. `[tool.hatch.version]` uses `source = "vcs"` (hatch-vcs) to derive it from
  `git describe`. A `_version.py` is written into `src/gamesheet_sdk/` at build time and is gitignored; `__init__.py` imports `__version__` from it,
  falling back to `importlib.metadata` when running uninstalled. To cut a release, tag the commit (`git tag -a vX.Y.Z -m '...'` then
  `git push origin vX.Y.Z`) — never edit a version literal. Untagged commits get setuptools-scm's `guess-next-dev` form like `0.0.2.dev1+gHASH`. Tag
  pushes trigger `.github/workflows/release.yml` which builds, verifies tag-vs-version, publishes to PyPI via Trusted Publishing (OIDC, no tokens),
  and creates a GitHub Release; see `docs/how-to/cut-a-release.md`.

- **Testing patterns.** Pytest is configured with `--block-network` (via `pytest-recording`), so any test that opens a socket without a VCR cassette
  fails. Two markers (declared in `[tool.pytest.ini_options].markers`, enforced by `--strict-markers`): `@pytest.mark.vcr` replays HTTP from
  `tests/cassettes/` (sensitive headers/params scrubbed in `tests/conftest.py`); `@pytest.mark.browser` opts in to a real headless Chromium via
  `pytest-playwright`. Run only fast tests with `pytest -m "not browser"`. Coverage floor is `[tool.coverage.report] fail_under = 80`.

- **Dependency updates.** `pre-commit.ci` configuration lives inline in `.pre-commit-config.yaml` under the top-level `ci:` key (the only path that
  service reads). It pins `python_version: "3.11"`, runs `autoupdate_schedule: weekly`, auto-fixes formatting on PRs (`autofix_prs: true`), and skips
  `pyright` on the hosted runner (heavier deps than pre-commit.ci can practically install). Autoupdates land as PRs (empty `autoupdate_branch`), not
  auto-merges. `.github/dependabot.yml` opens grouped weekly PRs for Python runtime deps, Python dev deps, and GitHub Actions versions — three
  PRs/week max.

- **CI workflow layout.** GitHub Actions is fanned out into per-category workflow files under `.github/workflows/`: a small `ci.yml` build/install
  sanity check, `tests.yml` (pytest matrix py3.11–3.14), `docs.yml` (HTML/EPUB/man/PDF/lint/linkcheck/doctest as parallel jobs + a Pages deploy gated
  on `push` to main), `pre-commit.yml`, plus one workflow per tool category: `type_checkers.yml`, `code_quality_linters_-_static_analysis.yml`,
  `code_style_-_formatting_-automated_fixers-.yml`, `code_cleaners_-_dead_code_detectors.yml`, `configuration_file_linters_-_formatters.yml`,
  `documentation_-_docstring_tools.yml`, `documentation_-_markdown_tools.yml`, `security-_metrics_-_complexity.yml`, and `comprehensive-tests.yml`.
  Plus the GitHub-supplied `codeql.yml`, `dependency-review.yml`, and `release.yml`. Each tool runs as its own matrixed job (py3.11–3.14) installing
  the `tox-workdir` plugin and invoking the matching tox env. Job display names are the bare tool name (e.g. `mypy (py3.11)`, `pytest (py3.12)`) so
  the Checks UI stays scannable.

- **Python 3.11–3.14.** Use modern syntax (`from __future__ import annotations`, `X | None`, etc.) as `cli.py` already does.

- **Formatting/lint pipeline.** The suite is broken out tool-per-hook in `.pre-commit-config.yaml`, tool-per-env in `tox.ini`, and tool-per-job in the
  per-category GitHub Actions workflows. Categories:

  - **Code style / formatters (auto-fix):** black (88), black-jupyter, isort (`profile = "black"`), pyupgrade (`--py311-plus`), autopep8, ssort,
    add-trailing-comma, absolufy-imports.
  - **Code cleaners / dead-code:** autoflake, unimport, vulture, deptry.
  - **Code-quality linters / static analysis:** flake8 (via `flake8-pyproject` + ~50 plugins in `[flake8-plugins]`), pylint, refurb, pyrefly,
    blocklint.
  - **Type checkers:** mypy (`--strict`), pyright.
  - **Security / metrics / complexity:** bandit (`[tool.bandit]`), xenon (complexity gate — see below), radon (cc / raw / mi / hal as separate envs).
  - **Docstring / doc tools:** codespell, blacken-docs, docformatter, interrogate, pydocstyle, sphinx-lint, mdformat (+ mdformat-gfm), pymarkdown.
  - **Configuration-file linters / formatters:** yamllint (`-d relaxed`), tox-ini-fmt, pyproject-fmt, validate-pyproject, editorconfig-checker (+
    -system variant), pyroma.
  - **Meta:** sync-pre-commit-deps.

  mypy + pylint in pre-commit use `local` hooks because (a) pre-commit/mirrors-mypy tags currently drift ahead of upstream mypy on PyPI, and (b)
  pylint needs the project's runtime deps duplicated in `additional_dependencies` to resolve imports inside the isolated hook venv. The same
  `gamesheet-sdk-py[<extra>]` self-reference is used to inject project deps into other hooks that need to import the package (deptry, pyrefly, pyroma,
  etc.). pyroma additionally needs `hatchling` + `hatch-vcs` as deps because it imports the build backend during introspection.

- **Complexity gate.** A `xenon` pre-commit hook enforces `--max-absolute=A --max-modules=A --max-average=B` against `src/` on every commit
  (`pass_filenames: false`, runs the whole package as one analysis). Translation: **every block (function / method / class) must stay at
  cyclomatic-complexity grade A (cc \<= 5)**; every module must average grade A; the project as a whole must average grade B or better. As of the gate
  landing the project average is 2.43 with zero blocks above A. `tox -e metrics` runs `radon cc -s -a` + `radon mi -s` to report the actual numbers —
  useful before pushing a function that's growing conditionals. When you find yourself adding a fourth `if` / `except` / `for` / `and` / `or` to a
  block, extract a helper instead — see how `auth.py:login` is decomposed into `_resolve_email` + `_resolve_password` + `_wait_for_login_form` +
  `_attach_response_capture` + `_submit_login_form` + `_await_auth_outcome` for the pattern. **CodeQL data-flow gotcha worth preserving:** don't
  return a sensitive value (password, token, secret) bundled in the same tuple / list / dict as a non-sensitive sibling that downstream code logs.
  CodeQL's taint analyzer treats both elements as tainted, which fires `py/clear-text-logging-sensitive-data` on perfectly innocent `email` log calls.
  Keep credential resolvers split (one helper per secret).

- **Documentation.** Sphinx (Furo theme, MyST-Parser for markdown sources) lives under `docs/`. `conf.py` enables autodoc + autosummary (API),
  `sphinx-click` (CLI rendered live from the `gamesheet_sdk.cli:cli` group — so it always tracks the shipped click tree, including nested resource
  groups), intersphinx (cross-refs to stdlib/requests/pydantic/click), autosectionlabel, napoleon, todo, copybutton, sphinx-design. Output formats:
  HTML, EPUB, man, LaTeX/PDF. Strict-mode build (`-n -W`) runs two-pass to satisfy autosummary's stub-then-toctree ordering. Built, link-checked, and
  deployed to GitHub Pages by `.github/workflows/docs.yml`; `_build/` and `_autosummary/` are gitignored.

- **Documentation organization — Diátaxis.** Every doc page belongs to exactly one of four quadrants under `docs/`: `tutorials/` (learning-oriented),
  `how-to/` (task-oriented), `reference/` (information-oriented), or `explanation/` (understanding-oriented). When adding a page, pick the quadrant by
  asking _what is the reader's need?_, not _what is the topic?_ — a topic may have a page in more than one quadrant (e.g. an "auth" how-to _and_ an
  "auth" reference page). The `docs/explanation/diataxis.md` page is the in-tree primer; the canonical source is [diataxis.fr](https://diataxis.fr/).

- **CLI framework.** `src/gamesheet_sdk/cli.py` is a click group (`cli`) with a thin `main(argv) -> int` wrapper for the `gamesheet-sdk-py` entry
  point. The root group's callback builds a `Config` (with `--base-url` / `--no-headless` / `-v` overrides applied) and stows it in `ctx.obj`, so any
  subcommand pulls it via `@click.pass_context`. The CLI uses a **resource-oriented (noun-first) layout**: each resource (e.g. `associations`) gets a
  nested `ResourceGroup` whose canonical verbs are `create`, `get`, `list`, `update`, `delete` with the aliases `add/new`, `show/view`, `ls`,
  `set/edit`, `rm/remove`. `login` stays at the root as a global operation. New CLI surface attaches like:

  - **New verb on an existing resource** — `@<resource>_group.command("verb")`; aliases come from the group's `aliases=` table so no extra wiring.
  - **New resource** — `@cli.group("resource", cls=ResourceGroup, default="list", aliases={...})` for the group, then attach verbs to it.
    `default="list"` makes a bare `gamesheet-sdk-py <resource>` implicitly run `list`.
  - **Destructive verbs** (`delete`/`rm`/`remove`) — wrap with `@confirm_destructive("<target>")` so the command gains `--force/-f` and a `[y/N]`
    prompt.

  **Tab-completion.** `gamesheet-sdk-py completion {bash,zsh,fish}` prints a sourceable script (uses click's built-in `shell_completion` via the
  `_GAMESHEET_SDK_PY_COMPLETE` env var; no third-party dep). `ResourceGroup.shell_complete` overrides click's default to also enumerate aliases (`ls`,
  `rm`, …) so tab-completion stays in sync with the verb table. **Gotcha worth preserving:** `ResourceGroup.parse_args` gates its default-subcommand
  injection on `not ctx.resilient_parsing` — without that guard, click's completion walker descends silently into the leaf command and
  `gamesheet-sdk-py associations <TAB>` returns nothing. A regression test (`test_completion_does_not_descend_into_default_subcommand`) pins this.

  The Sphinx CLI reference is regenerated from the click tree by `sphinx-click` on every docs build, so it always tracks shipping behavior.
