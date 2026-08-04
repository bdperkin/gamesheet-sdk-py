# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project nature

Unofficial Python SDK + CLI for the GameSheet Inc. platform. GameSheet does not publish a public API for the operations this library targets, so functionality
is implemented by **automating the GameSheet WebUI** via a combination of:

- `requests` for plain HTTP
- `playwright` (headless Chromium) for flows that require a real browser

Because behavior depends on a third-party UI, expect breakage on vendor changes. When adding or fixing a workflow, prefer the lightest mechanism that works
(HTTP > HTML parse > headless browser) — headless automation is the slowest and most fragile path.

The package is alpha. It uses a **three-pillar layout** under `src/gamesheet_sdk/`:

- `__init__.py` — public re-exports + `__version__`
- `common/` — shared infrastructure used by both CLIs
  - `auth/` — authentication package
    - `login.py` — `login()` flow (browser-driven or HTTP fallback)
    - `session.py` — `AuthenticatedSession` HTTP layer with auto-refresh on 401
    - `storage.py` — token file I/O and directory management
    - `tokens.py` — token persistence (`load_access_token`, `load_refresh_token`, `save_tokens`, `refresh_access_token`)
    - `constants.py` — auth-related constants (URLs, storage paths)
  - `browser.py` — `BrowserSession` Playwright wrapper
  - `cli/` — shared CLI machinery
    - `core.py` — `ResourceGroup` class, `confirm_destructive` decorator, utility functions
    - `constants.py` — shared CLI constants
  - `config.py` — `pydantic-settings` `Config` (resolves `GAMESHEET_*` env vars; CLI args > env > defaults)
  - `constants.py` — global constants (URLs, base URLs)
  - `errors.py` — error classes
  - `exceptions.py` — `GameSheetError`, `AuthenticationError`
  - `output.py` — `render()` for JSON / YAML / CSV / TSV / 13 tabulate formats + `write_output()`
  - `session.py` — base `requests.Session` subclass
  - `shared/` — shared utilities package
    - `constants.py` — shared constants
    - `gamesheet_http.py` — HTTP helpers for GameSheet API
    - `image_upload.py` — image upload helpers
    - `jsonapi.py` — JSON:API response parsing
- `admin/` — admin dashboard (`gamesheet-admin` CLI)
  - `cli/` — admin CLI package
    - `main.py` — admin CLI entry point (`cli` group and `main()` function)
    - `helpers.py` — admin command helpers
    - `constants.py` — admin CLI constants
    - `commands/` — individual command modules (associations, completion, divisions, games, games_brackets, games_completed, games_scheduled, ipad_keys,
      leagues, locations, login, referees, roster, roster_coaches, roster_players, seasons, teams, teams_roster, teams_roster_coaches, teams_roster_players)
    - `shared/` — admin CLI utilities
      - `datetime_helpers.py` — flexible datetime parsing, timezone detection, and start/end/duration resolution helpers
      - `decorators.py` — CLI decorators for common patterns
      - `rendering.py` — output rendering helpers
  - Domain modules (each provides pydantic models + action functions):
    - `associations.py` — `Association` model + `list_associations()`
    - `divisions.py` — `Division` model + `list_divisions()`, `list_division_teams()`, `create_division()`, `update_division()`, `delete_division()`
    - `games/` — games package (`models.py`, `scheduled.py`, `completed.py`, `brackets.py`, `broadcasters.py`, `locations.py`, `helpers.py`)
    - `ipad_keys.py` — `IPadKey` model + `list_ipad_keys()`
    - `leagues.py` — `League` model + `list_leagues()`
    - `referees.py` — `Referee`, `RefereeReport` models + CRUD + `get_referee_report()`
    - `roster/` — roster management (`models.py`, `players.py`, `coaches.py`, `helpers.py`)
    - `seasons.py` — `Season` and `SeasonDetail` models + `list_seasons()`, `get_season()`
    - `teams.py` — `Team` model + `list_teams()`, `create_team()`, `update_team()`, `delete_team()`
- `teams/` — teams dashboard (`gamesheet-teams` CLI)
  - `cli/` — teams CLI package
    - `main.py` — teams CLI entry point (`cli` group and `main()` function)
    - `commands/` — command modules (completion, login stub)
  - `shared/` — teams-specific utilities (currently empty)

Future domain modules attach the same way: a thin action function in a domain module, a pydantic model, and a corresponding command module in the pillar's
`cli/commands/`.

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
pytest tests/test_init_coverage.py::test_version_is_string

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

Tox now ships ~60 envs — one per linter / formatter / type checker / doc builder — instead of the prior monolithic `lint` / `type` / `security` / `files-check`
aggregates. Use **labels** for grouped runs:

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

Every `pyproject.toml` `optional-dependencies.*` group has a matching tox env that installs only that extra plus the project, so each env runs in an isolated
venv with the minimum surface area.

The package installs two CLIs: `gamesheet-admin` (entry point: `gamesheet_sdk.admin.cli:main`) and `gamesheet-teams` (entry point:
`gamesheet_sdk.teams.cli:main`).

## Architecture notes

- **`src/` layout.** Tests import via the installed package; `pyproject.toml` also sets `pythonpath = ["src"]` so `pytest` works without an install, but
  workflows that need the CLI or Playwright still require `pip install -e ".[all]"` (or at minimum `[dev,pytest]`).

- **Typed package.** `py.typed` is shipped (PEP 561) and `[tool.mypy] strict = true` is enabled — all new code must be fully annotated and pass `mypy --strict`.

- **Automated versioning and changelog.** The project uses `python-semantic-release` (PSR) to fully automate version bumping, CHANGELOG generation, and releases
  based on Conventional Commits. **No manual tagging required** — simply merge to `main` and PSR handles everything:

  1. Analyzes commits since last release
  2. Determines next version (currently patch-only: `feat:`/`fix:`/`perf:` → patch; `major_on_zero = false` prevents breaking changes from bumping to 1.0.0)
  3. Updates `CHANGELOG.md` with new entries
  4. Bumps version in `pyproject.toml` (`[project] version`)
  5. Creates commit: `chore(release): X.Y.Z`
  6. Creates and pushes tag `vX.Y.Z`
  7. Tag push triggers release workflow: Build → TestPyPI → PyPI → GitHub Release

  Version is stored in `pyproject.toml:project.version` (managed by PSR via `version_toml`), accessible at runtime via `importlib.metadata.version()`. **All
  commits must follow Conventional Commits format** — enforced by the `conventional-pre-commit` hook. Common types: `feat:`, `fix:`, `docs:`, `chore:`,
  `refactor:`, `test:`, `ci:`, `build:`. Scopes optional but encouraged (`feat(cli):`, `fix(auth):`). Breaking changes: `feat!:` or `BREAKING CHANGE:` in body.
  See `docs/how-to/release-process.md` for full workflow documentation.

- **Testing patterns.** Pytest is configured with `--block-network` (via `pytest-recording`), so any test that opens a socket without a VCR cassette fails. Two
  markers (declared in `[tool.pytest.ini_options].markers`, enforced by `--strict-markers`): `@pytest.mark.vcr` replays HTTP from `tests/cassettes/` (sensitive
  headers/params scrubbed in `tests/conftest.py`); `@pytest.mark.browser` opts in to a real headless Chromium via `pytest-playwright`. Run only fast tests with
  `pytest -m "not browser"`. Local coverage floor is `[tool.coverage.report] fail_under = 100`; on top of that, `.codecov.yml` declares project coverage target
  100% (0% drop tolerated) and patch coverage 100% on newly-introduced lines, plus test-analytics for flaky-test detection (alert after 2 flaky runs) and a >10%
  slowdown alert. `coverage.xml` and JUnit XML are uploaded to Codecov by `.github/workflows/codecov.yml` (per-PR matrix) and `comprehensive-tests.yml`
  (nightly, multi-OS).

  Test structure under `tests/`:

  - `admin/` — admin CLI entry-point tests
  - `common/` — shared infrastructure tests (auth, cli)
  - `teams/` — teams CLI entry-point tests
  - `cli/` — CLI command tests (associations, divisions, games, ipad_keys, leagues, locations, referees, roster, seasons, teams with their nested subcommands)
  - `fixtures/` — shared test fixtures
  - `helpers/` — test helper modules (cli.py, constants.py, endpoints.py, mocks.py, payloads.py)
  - `integration/` — integration tests (browser, cli_games, cli_roster, config, output, session, smoke)
  - `unit/` — unit tests by domain (associations, divisions, games, ipad_keys, leagues, referees, roster, seasons, teams, gamesheet_http)

- **Dependency updates.** `pre-commit.ci` configuration lives inline in `.pre-commit-config.yaml` under the top-level `ci:` key (the only path that service
  reads). It pins `python_version: "3.11"`, runs `autoupdate_schedule: weekly`, and auto-fixes formatting on PRs (`autofix_prs: true`). Eleven hooks are listed
  in `ci.skip` — they still run in GitHub Actions where there is no 250 MiB tier limit and `python -m venv` works. The three main reasons a hook lands in the
  skip list:

  - **Deps exceed the 250 MiB tier** — `pyright`, `flake8` (`[flake8-plugins]` pulls fastapi, flake8-django, etc.), `deptry`, `yesqa`, `refurb`.
  - **Requires runtime deps via `additional_dependencies`** — `mypy`, `pylint`, `pyrefly-check`, `semgrep`.
  - **Needs `python -m venv`** — `pyroma` (introspects via `python -m build`; pre-commit.ci's bundled Python lacks `ensurepip`).

  Also skipped: `editorconfig-checker`, `mdformat`.

  Autoupdates land as PRs (empty `autoupdate_branch`), not auto-merges. `.github/dependabot.yml` opens grouped weekly PRs for Python runtime deps, Python dev
  deps, and GitHub Actions versions — three PRs/week max.

- **CI workflow layout.** GitHub Actions is fanned out into per-category workflow files under `.github/workflows/`: a small `ci.yml` build/install sanity check,
  `tests.yml` (pytest matrix py3.11–3.14), `docs.yml` (HTML/EPUB/man/PDF/lint/linkcheck/doctest as parallel jobs + a Pages deploy gated on `push` to main),
  `pre-commit.yml`, `codecov.yml` (per-PR pytest matrix with coverage + JUnit uploads to Codecov), plus one workflow per tool category: `type_checkers.yml`,
  `code_quality_linters_-_static_analysis.yml`, `code_style_-_formatting_-automated_fixers-.yml`, `code_cleaners_-_dead_code_detectors.yml`,
  `configuration_file_linters_-_formatters.yml`, `documentation_-_docstring_tools.yml`, `documentation_-_markdown_tools.yml`,
  `security-_metrics_-_complexity.yml`, and `comprehensive-tests.yml` (nightly, multi-OS; also uploads to Codecov). Plus the GitHub-supplied `codeql.yml`,
  `dependency-review.yml`, security scanning workflows (`gitguardian.yml`, `semgrep.yml`, `security-trivy.yml`, `security-trivy-image.yml`, `osv-scanner.yml`,
  `workflow-linter.yml`), and `release.yml`. Each tool runs as its own matrixed job (py3.11–3.14) installing the `tox-workdir` plugin and invoking the matching
  tox env. Job display names are the bare tool name (e.g. `mypy (py3.11)`, `pytest (py3.12)`) so the Checks UI stays scannable.

  **Trigger layout (uniform across most workflows):** `push:` is scoped to `branches: [main]` — CI runs on main branch pushes and when PRs are opened/updated
  against main. `pull_request:` uses either `types: [opened, reopened, synchronize]` (default behavior, runs on every PR push) or `branches: [main]` depending
  on the workflow. Both `push` and `pull_request` include `paths-ignore: ["CHANGELOG.md", "pyproject.toml"]` to skip workflows when only version/changelog files
  change (those are updated by automated release commits). All workflows use
  `concurrency.group: ${{ github.workflow }}-${{ github.head_ref || github.ref_name }}` with `cancel-in-progress: true` to collapse overlapping runs — only the
  latest run continues. The exceptions are `codeql.yml`/`dependency-review.yml` (kept on their original GitHub-supplied triggers), `release.yml` (only
  `push: branches: [main]`), and `comprehensive-tests.yml` (nightly `schedule` trigger plus manual `workflow_dispatch`).

- **Python 3.11–3.14.** Use modern syntax (`from __future__ import annotations`, `X | None`, etc.) as the `cli` and `auth` packages already do.

- **Formatting/lint pipeline.** The suite is broken out tool-per-hook in `.pre-commit-config.yaml`, tool-per-env in `tox.ini`, and tool-per-job in the
  per-category GitHub Actions workflows. Categories:

  - **Code style / formatters (auto-fix):** black (88), black-jupyter, isort (`profile = "black"`), pyupgrade (`--py311-plus`), autopep8, ssort,
    add-trailing-comma, absolufy-imports.
  - **Code cleaners / dead-code:** autoflake, unimport, vulture, deptry.
  - **Code-quality linters / static analysis:** flake8 (via `flake8-pyproject` + ~50 plugins in `[flake8-plugins]`), pylint, refurb, pyrefly, blocklint.
  - **Type checkers:** mypy (`--strict`), pyright.
  - **Security / metrics / complexity:** bandit (`[tool.bandit]`), semgrep (`--config auto --error`), xenon (complexity gate — see below), radon (cc / raw / mi
    / hal as separate envs).
  - **Docstring / doc tools:** codespell, blacken-docs, docformatter, interrogate, pydocstyle, mdformat (+ mdformat-gfm), pymarkdown. Note: `docconvert` is
    available via tox and CI workflows but not in pre-commit hooks.
  - **Configuration-file linters / formatters:** yamllint (`-d relaxed`), tox-ini-fmt, pyproject-fmt, validate-pyproject, editorconfig-checker (+ -system
    variant), pyroma.
  - **Meta:** sync-pre-commit-deps.

  Several hooks need the project's runtime deps or tool-specific plugins to resolve imports inside the isolated hook venv. Every such hook's
  `additional_dependencies` is consolidated to a single `gamesheet-sdk-py[<extras>]` self-reference (e.g. `gamesheet-sdk-py[mypy,tools]`,
  `gamesheet-sdk-py[pylint,tools]`, `gamesheet-sdk-py[pyright,tools]`, `gamesheet-sdk-py[pyrefly]`, `gamesheet-sdk-py[deptry]`, `gamesheet-sdk-py[flake8]`,
  `gamesheet-sdk-py[refurb]`, `gamesheet-sdk-py[mdformat]`) so `pyproject.toml`'s `optional-dependencies.*` groups are the single source of truth for what each
  tool needs. Pyroma is skipped on pre-commit.ci (see above) and runs locally / in GitHub Actions where the project's build backend (`hatchling`) is already
  present.

- **Complexity gate.** A `xenon` pre-commit hook enforces `--max-absolute=A --max-modules=A --max-average=B` against `src/` on every commit
  (`pass_filenames: false`, runs the whole package as one analysis). Translation: **every block (function / method / class) must stay at cyclomatic-complexity
  grade A (cc \<= 5)**; every module must average grade A; the project as a whole must average grade B or better. As of the gate landing the project average is
  2.43 with zero blocks above A. `tox -e radon-cc` (or `make metrics`) runs `radon cc -s -a` + `radon mi -s` to report the actual numbers — useful before
  pushing a function that's growing conditionals. When you find yourself adding a fourth `if` / `except` / `for` / `and` / `or` to a block, extract a helper
  instead — see how `auth/login.py:login` is decomposed into `_resolve_email` + `_resolve_password` + `_wait_for_login_form` + `_attach_response_capture` +
  `_submit_login_form` + `_await_auth_outcome` for the pattern. **CodeQL data-flow gotcha worth preserving:** don't return a sensitive value (password, token,
  secret) bundled in the same tuple / list / dict as a non-sensitive sibling that downstream code logs. CodeQL's taint analyzer treats both elements as tainted,
  which fires `py/clear-text-logging-sensitive-data` on perfectly innocent `email` log calls. Keep credential resolvers split (one helper per secret).

- **Documentation.** Sphinx (Furo theme, MyST-Parser for markdown sources) lives under `docs/`. `conf.py` enables autodoc + autosummary (API), `sphinx-click`
  (CLI rendered live from both `gamesheet_sdk.admin.cli.main:cli` and `gamesheet_sdk.teams.cli.main:cli` — so it always tracks the shipped click trees,
  including nested resource groups), intersphinx (cross-refs to stdlib/requests/pydantic/click), autosectionlabel, napoleon, todo, copybutton, sphinx-design.
  Output formats: HTML, EPUB, man, LaTeX/PDF. Strict-mode build (`-n -W`) runs two-pass to satisfy autosummary's stub-then-toctree ordering. Built,
  link-checked, and deployed to GitHub Pages by `.github/workflows/docs.yml`; `_build/` and `_autosummary/` are gitignored.

  Documentation structure under `docs/`:

  - `conf.py` — Sphinx configuration
  - `index.md` — documentation homepage
  - `tutorials/` — learning-oriented guides (Diátaxis)
  - `how-to/` — task-oriented guides (development-setup, release-process)
  - `reference/` — information-oriented reference (API, CLI, configuration)
  - `explanation/` — understanding-oriented explanations (architecture, design decisions, Diátaxis primer)
  - `security/` — security policies and guidelines
  - `_static/` — static assets (CSS, images)
  - `_templates/` — custom Sphinx templates
  - `generate_api_docs.py` — script to generate API documentation
  - `check_api_freshness.py` — script to check if API docs are up-to-date

- **Documentation organization — Diátaxis.** Every doc page belongs to exactly one of four quadrants under `docs/`: `tutorials/` (learning-oriented), `how-to/`
  (task-oriented), `reference/` (information-oriented), or `explanation/` (understanding-oriented). When adding a page, pick the quadrant by asking _what is the
  reader's need?_, not _what is the topic?_ — a topic may have a page in more than one quadrant (e.g. an "auth" how-to _and_ an "auth" reference page). The
  `docs/explanation/diataxis.md` page is the in-tree primer; the canonical source is [diataxis.fr](https://diataxis.fr/).

- **CLI framework.** The package ships two CLIs, each with its own `cli/main.py` defining a root click group (`cli`) with a thin `main(argv) -> int` wrapper.
  `gamesheet-admin` (entry point: `gamesheet_sdk.admin.cli:main`) handles admin dashboard operations; `gamesheet-teams` (entry point:
  `gamesheet_sdk.teams.cli:main`) handles teams dashboard operations (currently stub). Each root group's callback builds a `Config` (with `--base-url` /
  `--no-headless` / `-v` overrides applied) and stows it in `ctx.obj`, so any subcommand pulls it via `@click.pass_context`. Shared CLI machinery lives in
  `common/cli/core.py` (`ResourceGroup` class and decorators). Individual command modules live under each pillar's `cli/commands/`. The admin CLI uses a
  **resource-oriented (noun-first) layout**: each resource (e.g. `associations`) gets a nested `ResourceGroup` whose canonical verbs are `create`, `get`,
  `list`, `update`, `delete` with the aliases `add/new`, `show/view`, `ls`, `set/edit`, `rm/remove`. `login` stays at the root as a global operation. New CLI
  surface attaches like:

  - **New verb on an existing resource** — add a `@<resource>_group.command("verb")` in the appropriate `cli/commands/<resource>.py` module; aliases come from
    the group's `aliases=` table so no extra wiring.
  - **New resource** — create `cli/commands/<resource>.py` with `@cli.group("resource", cls=ResourceGroup, default="list", aliases={...})` for the group, then
    attach verbs to it. Import and register the group in the pillar's `cli/main.py`. `default="list"` makes a bare `gamesheet-admin <resource>` implicitly run
    `list`.
  - **Destructive verbs** (`delete`/`rm`/`remove`) — wrap with `@confirm_destructive("<target>")` (from `common/cli/core.py`) so the command gains `--force/-f`
    and a `[y/N]` prompt.

  **CLI shared utilities** in `admin/cli/shared/`:

  - `datetime_helpers.py` — flexible datetime parsing (via `python-dateutil`), timezone detection (`get_local_timezone_name`, `get_local_timezone_offset`), and
    start/end/duration resolution (`resolve_create_times`, `resolve_update_times`). Used by `games scheduled create` and `games scheduled update` to accept
    flexible date/time input and auto-calculate the missing value from any two of start, end, and duration.
  - `decorators.py` — common decorators for CLI commands
  - `rendering.py` — output rendering and formatting helpers

  **Flexible date/time input.** The `games scheduled create` and `games scheduled update` commands accept flexible date/time input via `--start-datetime`,
  `--end-datetime`, split `--start-date`/`--start-time`, split `--end-date`/`--end-time`, and `--duration` (minutes). Any non-ambiguous date/time string
  accepted by `dateutil.parser.parse` works (ISO 8601, natural language like `"July 4 2026 7pm"`, etc.). If no timezone is specified, the system's local
  timezone is assumed. Any timezone info is stripped and the face-value time is sent to the API in ISO 8601 format with a trailing `Z` (e.g.
  `2026-07-04T12:00:00Z`) — GameSheet displays times as-is without timezone conversion. For `create`, exactly 2 of 3 (start, end, duration) are required and the
  missing value is calculated; if all 3 are given they must be consistent. For `update`, partial inputs are allowed — a single new value updates that field
  while preserving the other; two or more trigger recalculation. Mixing `--start-datetime` with `--start-date`/`--start-time` (or the end equivalents) raises a
  validation error.

  **Tab-completion.** `gamesheet-admin completion {bash,zsh,fish}` (and `gamesheet-teams completion {bash,zsh,fish}`) prints a sourceable script (uses click's
  built-in `shell_completion` via the `_GAMESHEET_ADMIN_COMPLETE` / `_GAMESHEET_TEAMS_COMPLETE` env var; no third-party dep). `ResourceGroup.shell_complete` (in
  `common/cli/core.py`) overrides click's default to also enumerate aliases (`ls`, `rm`, …) so tab-completion stays in sync with the verb table. **Gotcha worth
  preserving:** `ResourceGroup.parse_args` gates its default-subcommand injection on `not ctx.resilient_parsing` — without that guard, click's completion walker
  descends silently into the leaf command and `gamesheet-admin associations <TAB>` returns nothing. A regression test
  (`test_completion_does_not_descend_into_default_subcommand`) pins this.

  The Sphinx CLI reference is regenerated from the click tree by `sphinx-click` on every docs build, so it always tracks shipping behavior.

- **Build system.** Uses `hatchling` as the build backend (PEP 517/518/621 compliant). Package metadata lives in `pyproject.toml` under `[project]`. Build
  configuration under `[tool.hatch]` controls wheel/sdist targets. The package ships with `src/gamesheet_sdk/py.typed` for PEP 561 type hint distribution.

- **Docker support.** A `Dockerfile` is provided for containerized deployments. The image ships both `gamesheet-admin` and `gamesheet-teams` CLIs; there is no
  fixed `ENTRYPOINT`, so users specify which CLI to run: `docker run <image> gamesheet-admin --help`. The image is published to GitHub Container Registry
  (ghcr.io) during the release workflow. Local Docker commands are available via Makefile: `make docker-build`, `make docker-run`, `make docker-push`,
  `make docker-clean`.

- **Security scanning.** The project uses multiple security tools in CI:

  - **bandit** — Python code security scanner (via pre-commit and dedicated workflow)
  - **GitGuardian** — secret scanning in commits
  - **Semgrep** — SAST (static application security testing)
  - **Trivy** — container vulnerability scanning with `.trivyignore.yaml` for suppressed CVEs
  - **OSV-Scanner** — dependency vulnerability scanning
  - **CodeQL** — semantic code analysis, running the `security-extended` + `security-and-quality` suites (see `codeql.yml`), so alerts include quality and
    maintainability findings, not just vulnerabilities
  - **pip-audit** — Python dependency vulnerability scanning

  The `.trivyignore.yaml` file contains suppressed container base image CVEs that cannot be fixed. It uses Trivy's YAML ignore format so each entry carries a
  `statement` (why it is not exploitable here, plus Debian tracker status) and an `expired_at` date, after which Trivy reports the CVE again. Expiries are
  staggered by severity — CRITICAL/HIGH at 3 months, MEDIUM at 6, LOW at 12 — so the file cannot silently accumulate stale suppressions.

  **This file is the single source of truth for CVE suppression.** Base-image noise used to be split between it and 337 "won't fix" dismissals in the GitHub
  Security UI, which were invisible to anyone reading the repo and never expired. Those were folded in on 2026-07-27 and the dismissals then reopened, so **no
  Trivy alert is dismissed in the UI any more** and the file's 164 rules account for every CVE in the published image exactly (164 rules, 164 image CVEs, zero
  unsuppressed, zero rules matching nothing). **Suppress new base-image CVEs by adding an entry here, not by dismissing the alert in the UI** — a UI dismissal
  reintroduces the split and is silently exempt from the expiry mechanism. Conversely, a rule that stops matching anything should be deleted rather than left in
  place, since a dead rule hides the fact that it is obsolete. This arrangement is also what `docs/security/vulnerability-acceptance-criteria.md`
  ("Documentation Requirements") actually asks for: CVE ID, package, severity, justification, review date and expiration date per accepted vulnerability — none
  of which a UI dismissal recorded.

  **Gotcha worth preserving:** Trivy auto-loads a plain `.trivyignore` from the working directory but does **not** auto-load `.trivyignore.yaml` (verified
  against trivy 0.69.3). Every Trivy invocation must therefore pass the file explicitly (`trivyignores: .trivyignore.yaml` for `aquasecurity/trivy-action`,
  `--ignorefile` on the CLI). Omitting it silently disables all suppressions rather than erroring, which floods the Security tab with base-image noise.

  Container images are scanned in two places. `security-trivy-image.yml` builds and scans the image as a pass/fail gate on PRs that touch the `Dockerfile`, plus
  a weekly run and a `workflow_dispatch` for base-image drift. `release.yml` scans the published image during a release. Both upload SARIF under the **explicit
  shared category `trivy-image`**, so they write to one analysis stream and refresh each other's findings instead of creating two parallel alert sets for the
  same image; PR runs skip the upload entirely, because a PR should gate rather than mutate the repository's alert state.

  **Gotcha worth preserving:** an *omitted* `category:` is not a shared category. GitHub derives one per workflow as `.github/workflows/<file>:<job>`, and
  replacement of previous findings happens per category — same category replaces, different categories accumulate in parallel. Uploading the same tool's results
  from two workflows without an explicit shared category therefore produces two independent alert sets that never close each other out. This bit us once: the
  `trivy-image` category was introduced precisely because a category-less upload from `security-trivy-image.yml` created a third stream instead of refreshing
  `release.yml`'s.

  **Second gotcha, for hand-uploaded SARIF:** when POSTing to `/code-scanning/sarifs` directly, the category comes from `runs[].automationDetails.id`, and that
  field is parsed as `<category>/<run-specific-id>` — GitHub splits at the **final `/`** and keeps only the part before it as the category. So an id of
  `.github/workflows/release.yml:build-container` files the analysis under category `.github/workflows`, silently landing in the wrong stream. **Append a
  trailing slash** to have the whole string treated as the category:

  ```text
  automationDetails.id = ".github/workflows/release.yml:build-container/"   → category ".github/workflows/release.yml:build-container"
  automationDetails.id = ".github/workflows/release.yml:build-container"    → category ".github/workflows"          ← wrong stream
  ```

  This is only a concern for manual uploads; `github/codeql-action/upload-sarif` handles the suffix itself when given `category:`. It matters because the
  failure is silent — the upload returns `202`, processing completes, and the analysis appears under a plausible-looking category while the alerts you meant to
  close stay open. Verify after any manual upload with
  `gh api "repos/<owner>/<repo>/code-scanning/analyses?per_page=5" --jq '.[]|"\(.created_at) results=\(.results_count) cat=\(.category)"'`.

  A zero-result SARIF posted to an existing category is the non-destructive way to close a stale alert set — it marks those alerts fixed while leaving the
  category's analysis history intact, unlike deleting analyses (which, done one at a time, promotes the previous analysis and resurrects its alerts).

  **Why `security-trivy-image.yml` uploads SARIF at all:** `release.yml`'s `build-container` job is gated on `needs.version.outputs.released == 'true'`, and PSR
  only releases on `feat:`/`fix:`/`perf:`. A run of `ci:`- or `chore:`-only commits therefore produces no container scan and no SARIF, which would leave image
  findings stale — and any alert that has been reopened stuck open — indefinitely. The weekly run bounds that staleness to seven days;
  `gh workflow run "Security - Trivy Container Image Scan"` clears it on demand.

- **CodeQL quality findings that are false positives.** Two code shapes in this repo are reported by the `security-and-quality` suite but must not be "fixed",
  and both carry inline comments saying so:

  - `if TYPE_CHECKING: from pydantic import SecretStr` alongside `cast("SecretStr", ...)` in tests reads as `py/unused-import`. It isn't: flake8-type-checking's
    **TC006** requires `cast()` annotations to be string literals, and a string annotation means the import can only live in a `TYPE_CHECKING` block. Unquoting
    the cast or moving the import to runtime trades a CodeQL note for a flake8 failure, and flake8 gates merges while the note does not.
  - `FIREBASE_AUTH_URL` and `TOKEN_EXCHANGE_URL` in `common/auth/constants.py` read as `py/unused-global-variable` because nothing in their defining module
    consumes them — they are imported by `teams/login.py` and `tests/common/auth/conftest.py`.

  Both were dismissed as false positives in the Security UI. Note the contrast with Trivy: CVE suppression belongs in `.trivyignore.yaml` because Trivy supports
  a versioned ignore file with expiry, whereas CodeQL offers no equivalent per-alert repo-side mechanism short of `query-filters`, which would suppress a whole
  rule across the codebase rather than six specific sites.
