# CLAUDE.md

<!--TOC-->

______________________________________________________________________

- [1. Project nature](#1-project-nature)
- [2. Common commands](#2-common-commands)
  - [2.1. Makefile shortcuts](#21-makefile-shortcuts)
  - [2.2. Running a single tool with uv](#22-running-a-single-tool-with-uv)
- [3. Architecture notes](#3-architecture-notes)

______________________________________________________________________

<!--TOC-->

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1. Project nature

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

## 2. Common commands

```bash
# Editable install with everything (run once after clone / when deps change).
# `[dev]` is minimal (pre-commit, pre-commit-uv, uv). `[all]` pulls every
# per-tool extra declared in pyproject.toml — pytest, lint suite, docs, …
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

# Type check (Astral ty)
ty check
```

### 2.1. Makefile shortcuts

A `Makefile` wraps the most common workflows. `make help` lists every target. Highlights:

```bash
make install       # editable install ([dev] extras) + Playwright Chromium
make install-all   # editable install ([all] extras) + Playwright Chromium
make test          # full pytest suite
make test-fast     # pytest -m "not browser"
make test-cov      # pytest --cov
make metrics       # radon complexity + maintainability report
make docs          # Sphinx HTML build (two-pass strict)
make docs-serve    # live-reload preview
make docs-pdf      # PDF docs (needs LaTeX on PATH)
make docs-linkcheck
make clean         # caches + build artifacts (.uv, $(VENV), _build untouched)
make clean-all     # + .uv, $(VENV), docs build dirs
```

**Tool targets are named after hook categories, not after tools** — there is one target per category in `.genprecommitconfig.yaml`, running that category's
tools in hook order:

```bash
make dependencies    # uv lock
make checks          # editorconfig-checker
make configuration   # format-json, yamlfix, yamllint, pyproject-fmt, validate-pyproject, pyroma
make markdown        # mdformat, pymarkdown
make security        # semgrep
make format          # ruff check, ruff format
make quality         # vulture, interrogate, codespell, blocklint
make types           # ty check
```

**These are not byte-identical to the CI jobs, and deliberately so:** where a tool can fix, the `make` target lets it (`mdformat`, `ruff format`,
`pyproject-fmt`, `yamlfix`, `format-json` all write in place), whereas the workflow job passes `--check`. The category also spans more tools than the matching
workflow in two places — `format-json` and `yamlfix` are pre-commit-only, with no CI job — and `make security` runs
`semgrep --disable-version-check --quiet --skip-unknown-extensions` where the workflow job runs `semgrep --config auto .`. For a faithful reproduction of a CI
job, copy the `run:` line out of the workflow (see [§2.2](#22-running-a-single-tool-with-uv)).

There is no aggregate target; use `pre-commit run --all-files`. Two categories have no target either: `commits` is inherently per-commit
(`conventional-pre-commit`), and `architecture` is split between `make metrics` (radon) and `pre-commit run xenon --all-files` (the complexity gate).

### 2.2. Running a single tool with uv

There is no separate task runner. Every tool is invoked directly through `uv run --extra <extra> <tool>`, which resolves an ephemeral environment holding the
project plus only that extra. Each `pyproject.toml` `optional-dependencies.*` group is therefore the single source of truth for what one tool needs, and
`.github/workflows/` invokes exactly these commands:

```bash
uv run --extra pytest pytest --cov            # tests + coverage gate
uv run --extra ty ty check
uv run --extra radon radon cc --show-complexity --average .
uv run --extra docs sphinx-build -b html docs docs/_build/html
uv run --extra dev pre-commit run --all-files
uv run --extra pytest pytest -k test_name     # pass pytest args directly
```

`xenon` now has its own extra like every other tool (pulled in by `architecture` alongside `radon`), but no workflow job invokes it: the complexity gate runs
solely as the `rubik/xenon` pre-commit hook, which supplies its own environment. Run it with `pre-commit run xenon --all-files`.

Prefer the `make` targets in [§2.1](#21-makefile-shortcuts) for everyday work — they wrap these same commands. Reach for the raw `uv run` form when you need a
flag the Makefile does not expose, or when reproducing a specific CI job.

The package installs two CLIs: `gamesheet-admin` (entry point: `gamesheet_sdk.admin.cli:main`) and `gamesheet-teams` (entry point:
`gamesheet_sdk.teams.cli:main`).

## 3. Architecture notes

- **`src/` layout.** Tests import via the installed package — there is no `pythonpath` setting, so `pytest` needs the project installed
  (`uv run --extra pytest pytest`, or `pip install -e ".[all]"` / at minimum `[dev,pytest]` for anything touching the CLI or Playwright).

- **Typed package.** `py.typed` is shipped (PEP 561) and `[tool.ty]` is configured — all new code must be fully annotated and pass `ty check`. `rules.all` is
  `error`, and `missing-override-decorator` is the only rule ignored.

  **Keep `unresolved-import` an error.** It is the only thing that reports a missing dependency or type stub, and downgrading it to `ignore` does not merely
  hide import noise — every symbol from the unresolved module silently degrades to `Unknown` or to a wrong inferred type, and `ty --fix` then acts on that.
  While it was globally ignored, `import totally_nonexistent_module_xyz` type checked clean, `types-requests` went missing from the ty extra unnoticed, and
  `ty --fix` deleted a load-bearing `cast()` in `common/session.py` as "redundant". Fix the cause — add the stub to `optional-dependencies.type-stubs`, or
  remove a stale one — rather than widening the rule.

  **Do not add stubs for a dependency that ships `py.typed`.** An obsolete stub package *shadows* the real inline types, so every symbol is checked against the
  version the stub describes. `types-click==7.1.8` did exactly that: it describes click 7, the project runs click 8.4.2, and `click.shell_completion` (added in
  click 8) therefore read as unresolved — which is what the old `analysis.allowed-unresolved-imports` allowlist existed to paper over. Dropping the stub made
  the import resolve and the allowlist unnecessary.

  **`optional-dependencies.type-stubs` is deliberately tiny — four entries.** It was 34 before the audit on 2026-08-15; 30 of those stubbed modules that no file
  under `src/`, `tests/`, `tools/` or `docs/` imports (`types-pywin32` alone contributed ~60 Windows-only module stubs), and dropping them left `ty check`
  green. Add a stub only when ty actually reports something unresolved, and delete one the moment its module stops being imported — an unused stub is not inert,
  it is a second, staler definition of a package waiting to shadow the real one.

  **`syncdeps --sync-types` enforces those two rules itself (since 2026-08-16).** It used to add `types-<pkg>` for every resolved dependency whose stub merely
  *existed on PyPI*, with no check for `py.typed` or for whether anything imports the module — which is how the group reached 34. Two gates in
  `tools/depsync/typedness.py` now run *before* the index is queried: a candidate must have one of its top-level modules imported under `src/`, `tests/`,
  `tools/` or `docs/` (collected with `ast`, so a function-level import counts and a relative import does not), and its runtime distribution must not ship
  `py.typed`. Module names come from installed metadata (`top_level.txt`, else the recorded file list), never from the distribution name — `pyyaml` provides
  `yaml`. Against the current tree that gates out 197 of 203 candidates and proposes zero additions.

  The gates are **asymmetric on purpose, and the asymmetry is the load-bearing part:** an undeterminable answer rejects an *addition* (not adding is cheap — ty
  reports the unresolved import and you add it deliberately) but keeps an existing stub (a distribution absent from the env `syncdeps` runs in has no
  authoritative module list, and deleting a load-bearing stub on a guessed name breaks ty in CI). And only the imports rule drives removals: `py.typed` is
  add-time only, so `types-requests` — deliberately kept, see below — survives a sync. Rejections are never silent: a per-reason count prints on stdout and
  `--log-level debug` lists every one. Still review what a run proposes; the gates narrow the input, they do not replace the judgment.

  **When a stub and an inline `py.typed` disagree, check which matches runtime — the stub is sometimes right.** `types-requests` shadows requests' own
  annotations and is kept on purpose: requests declares `Session.headers` as `CaseInsensitiveDict[str]` and typeshed as `CaseInsensitiveDict[str | bytes]`, and
  the wider typeshed view is the accurate one. Remove that stub and `common/session.py:211` plus the `json.loads(request.body)` call sites in `tests/unit/` fail
  immediately — which is exactly the breakage #215 hit from the other direction. So "stub shadows `py.typed`" is a prompt to verify, not an automatic removal.

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
  reads) — but edit it in `.genprecommitconfig.yaml`, since the generator owns the output file. It runs `autoupdate_schedule: weekly` and auto-fixes formatting
  on PRs (`autofix_prs: true`). The interpreter comes from the top-level `default_language_version.python: python3.11`, not from a `ci.python_version` key.

  **`ci.skip` is deliberately minimal — four hooks.** Everything skipped still runs in GitHub Actions, which has no tier limit, real network access during hook
  execution, and a working `python -m venv`:

  - `identity` — a meta hook that only echoes filenames; no value in CI.
  - `pyroma` — introspects via `python -m build`, and pre-commit.ci's bundled Python lacks `ensurepip`, so the build venv cannot be created.
  - `semgrep-ci` — the semgrep repo env is 332 MiB against a 250 MiB tier limit. This is the only enabled id from that repo (the plain `semgrep` id is in
    `globals.blacklisted_hooks`), so skipping it keeps the env from being built at all. **Both conditions matter:** leaving any id from an oversized repo
    enabled fails the whole run at *build* time with `exceeds tier max size`, before a single hook executes.
  - `ty` — its entry is `uv check`, which syncs the project environment when it runs, and pre-commit.ci has no network during hook execution.
  - `unimport` — 0.11.1 calls `ast.Str`, removed in Python 3.12. pre-commit.ci runs it on a newer interpreter than the `python3.11` this config asks for, so it
    dies with `AttributeError`; the GitHub Actions `pre-commit` job honors `python3.11` and runs it fine.

  **Add to this list only in response to a specific failed run, never preemptively.** The list was 9 entries before it was rebuilt from evidence on 2026-08-14;
  `deptry`, `editorconfig-checker`, `mdformat` and `uv-lock` had all been skipped for conditions that no longer applied, and a run with them enabled proved they
  work on the free tier. Each entry above is reproduced by a real pre-commit.ci failure, and the rationale is kept as comments beside the list in
  `.genprecommitconfig.yaml`.

  Autoupdates land as PRs (empty `autoupdate_branch`), not auto-merges. `.github/dependabot.yml` opens grouped weekly PRs for Python runtime deps, Python dev
  deps, and GitHub Actions versions — three PRs/week max.

- **CI workflow layout.** GitHub Actions is fanned out into per-category workflow files under `.github/workflows/`: a small `ci.yml` build/install sanity check,
  `tests.yml` (pytest matrix py3.11–3.14), `docs.yml` (HTML/EPUB/man/PDF/lint/linkcheck/doctest as parallel jobs + a Pages deploy gated on `push` to main),
  `pre-commit.yml`, `codecov.yml` (per-PR pytest matrix with coverage + JUnit uploads to Codecov), plus one workflow per tool category: `types.yml`,
  `format.yml`, `quality.yml`, `architecture.yml`, `configuration.yml`, `markdown.yml`, `security.yml`, and `comprehensive-tests.yml` (nightly, multi-OS; also
  uploads to Codecov). Plus the GitHub-supplied `codeql.yml`, `dependency-review.yml`, security scanning workflows (`gitguardian.yml`, `semgrep.yml`,
  `security-trivy.yml`, `security-trivy-image.yml`, `osv-scanner.yml`, `workflow-linter.yml`), and `release.yml`. Each tool runs as its own matrixed job
  (py3.11–3.14) invoking `uv run --extra <extra> <tool>` directly, so the extra is the only dependency declaration involved. Job display names are the bare tool
  name (e.g. `pytest (py3.12)`) so the Checks UI stays scannable.

  **Trigger layout (uniform across most workflows):** `push:` is scoped to `branches: [main]` — CI runs on main branch pushes and when PRs are opened/updated
  against main. `pull_request:` uses either `types: [opened, reopened, synchronize]` (default behavior, runs on every PR push) or `branches: [main]` depending
  on the workflow. **`paths-ignore: ["CHANGELOG.md", "pyproject.toml"]` appears under `push:` only** — it exists to skip CI for the automated release commit,
  which PSR pushes straight to `main` and never opens a PR for, so under `pull_request:` it filtered nothing useful and made config-only PRs unmergeable (see
  below). All workflows use `concurrency.group: ${{ github.workflow }}-${{ github.head_ref || github.ref_name }}` with `cancel-in-progress: true` to collapse
  overlapping runs — only the latest run continues. The exceptions are `codeql.yml`/`dependency-review.yml` (kept on their original GitHub-supplied triggers),
  `release.yml` (only `push: branches: [main]`), and `comprehensive-tests.yml` (nightly `schedule` trigger plus manual `workflow_dispatch`).

  **Never add `paths-ignore` to a `pull_request:` trigger (gotcha worth preserving):** a path filter that excludes a workflow does not *fail* its jobs, it never
  reports them — and a required status check that is never reported leaves the PR at `mergeStateStatus: BLOCKED` with a green check list and no explanation.
  While every gating workflow ignored `pyproject.toml`, a PR touching *only* that file ran none of the nine required contexts and could never merge: it bit
  hand-made config-only changes (restoring a `[tool.pytest]` block) and every Dependabot version bump, which is what `tools/depsync/caps.py` documents from the
  Dependabot side. Fixed on 2026-08-16 by dropping `paths-ignore` from all 18 `pull_request:` triggers that carried it; the `push:` filters stay, since that is
  the only place the release commit lands. The rule generalizes past this repo: **a filter on `pull_request` can only ever silence a check that something is
  waiting on.**

  **Keep required status checks in sync with job names (gotcha worth preserving):** `main`'s branch protection pins a list of required status-check contexts by
  *exact job name* (`pytest (py3.11)`, `pre-commit (py)`, …). That list lives in **repo settings, not in the tree**, so nothing in a PR diff reveals it and no
  hook validates it. Renaming, removing, or re-matrixing a job therefore desynchronizes it silently, and it fails in both directions:

  - **Required but never reported** — the context can never turn green, so *every* PR sits at `mergeStateStatus: BLOCKED` with all its checks passing and no
    hint as to why.
  - **Reported but no longer required** — the gate quietly stops enforcing, and a red job no longer blocks a merge.

  This bit us once: #200 (`refactor(tools): migrate code style, formatting, and linting to ruff`) deleted the pylint jobs, but `pylint (py3.11)` … `(py3.14)`
  stayed in the required contexts. Every subsequent PR was unmergeable-by-default until those four were dropped on 2026-08-11 (17 contexts → 13). **After any
  change to a workflow's job names or matrix, diff the two lists:**

  ```bash
  gh api repos/bdperkin/gamesheet-sdk-py/branches/main/protection --jq '.required_status_checks.contexts[]' | sort > /tmp/required
  gh pr checks <pr> --json name --jq '.[].name' | sort > /tmp/actual
  comm -23 /tmp/required /tmp/actual   # required but never reported → blocks every PR
  comm -13 /tmp/required /tmp/actual   # reported but unguarded → candidates to add
  ```

- **Python 3.11–3.14.** Use modern syntax (`from __future__ import annotations`, `X | None`, etc.) as the `cli` and `auth` packages already do.

- **Formatting/lint pipeline.** `.genprecommitconfig.yaml` is the source of truth. It declares tools grouped into **categories**, and one category name is
  reused across every surface: it generates `.pre-commit-config.yaml` (tool-per-hook), matches an extra in `pyproject.toml` (tool-per-extra, each category extra
  fanning out to the per-tool extras it contains), a `make` target ([§2.1](#21-makefile-shortcuts)), and a per-category workflow file (tool-per-job). Add a tool
  in one place and regenerate; **never hand-edit `.pre-commit-config.yaml`.** The workflow surface is the one that can lag: the five import/layout fixers below
  have no dedicated jobs yet, so in CI they are covered only by the `pre-commit` job. Categories, in hook order:

  - **meta** (Hook Management): pre-commit's own `check-hooks-apply` / `check-useless-excludes` / `identity`, sync-pre-commit-deps.
  - **dependencies** (Lockfile Synchronization): uv — `uv-lock` on every run; `uv-export` and `uv-audit` are `manual`-stage, `uv-sync` is
    post-checkout/merge/rewrite.
  - **checks** (Low-level Checks): pre-commit-hooks, pygrep-hooks, editorconfig-checker.
  - **configuration** (Configuration Validation): format-json, yamlfix, yamllint, pyproject-fmt, validate-pyproject, pyroma.
  - **markdown** (Markdown Formatting): mdformat (+ mdformat-gfm), markdown-heading-numbering, markdown-toc-creator, pymarkdown.
  - **security** (Secret and Vulnerability Scans): detect-secrets, semgrep (`semgrep ci --dry-run --baseline-commit HEAD`; the plain `semgrep` id is
    blacklisted, and the full `--config auto .` scan runs as a workflow job).
  - **format** (Python Formatting): unimport (`--remove`), absolufy-imports, ssort, add-trailing-comma, blank-line-after-blocks, ruff (`ruff-check --fix` +
    `ruff-format`, line length 110).
  - **quality** (Code Quality): vulture, interrogate, codespell, blocklint.
  - **architecture** (Dependencies and Complexity Metrics): deptry, xenon (complexity gate — see below). radon is *not* a hook; it runs as workflow jobs (cc /
    raw / mi / hal) and via `make metrics`.
  - **types** (Static Type Checks): ty (`[tool.ty]`, `--fix --extra ty`).
  - **commits** (Commit Standards): conventional-pre-commit, pre-commit-ci-config.

  Hooks needing the project's runtime deps or tool plugins inside their isolated venv use a single `gamesheet-sdk-py[<extras>]` self-reference, so
  `pyproject.toml`'s `optional-dependencies.*` groups stay the single source of truth. Three hooks currently do: `gamesheet-sdk-py[mdformat]`,
  `gamesheet-sdk-py[unimport]`, `gamesheet-sdk-py[deptry]`. Pyroma is skipped on pre-commit.ci (see above) and runs locally / in GitHub Actions where the
  project's build backend (`hatchling`) is already present.

  **ty environment gotcha worth preserving:** ty reports against whatever is installed, so an incomplete extra does not fail loudly — it silently infers
  `Unknown` or the wrong type, and `--fix` then acts on that. `optional-dependencies.ty` must keep fanning out to `[pytest,type-stubs]` (and `pytest` to
  `[tools]`), which is why every invocation is a bare `--extra ty`. This has bitten twice: without `[tools]` everything in `tools/` inferred as `Unknown` and
  tripped `unsound-return-statement`; without `[type-stubs]`, `requests.Session.headers` typed as `CaseInsensitiveDict[str]` instead of
  `CaseInsensitiveDict[str | bytes]`, so `ty --fix` deleted a **load-bearing** `cast()` in `common/session.py` as redundant and the CI job — which had no stubs
  either — then failed on the very line the fix produced. **Never add an extra to one ty invocation only**; a passing local `ty check` against a fat, long-lived
  `.venv` proves nothing about CI, so reproduce with `uv run --isolated --extra ty ty check`.

  **Convergence gotcha worth preserving:** the auto-fixers are ordered `format` (unimport, ruff, …) *before* `types` (ty), so a fix that ty makes cannot be
  cleaned up by an earlier category until the next run. Concretely, `ty --fix` deletes a redundant `cast(...)` call but leaves `from typing import cast`
  orphaned; `unimport` / `ruff --fix` only remove that import on the following pass. **A single `pre-commit run --all-files` can therefore exit dirty on a tree
  that is one more run away from clean** — re-run before concluding a hook is broken, and expect the two-stage churn in the diff when new fixers land.

- **Complexity gate.** A `xenon` pre-commit hook enforces `--max-absolute=A --max-modules=A --max-average=B` against `src/` on every commit
  (`pass_filenames: false`, runs the whole package as one analysis). Translation: **every block (function / method / class) must stay at cyclomatic-complexity
  grade A (cc \<= 5)**; every module must average grade A; the project as a whole must average grade B or better. As of the gate landing the project average is
  2.43 with zero blocks above A. `make metrics` runs `radon cc --show-complexity --average .` + `radon mi --show .` to report the actual numbers — useful before
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
  - `tutorials/` — learning-oriented guides (Diataxis)
  - `how-to/` — task-oriented guides (development-setup, release-process)
  - `reference/` — information-oriented reference (API, CLI, configuration)
  - `explanation/` — understanding-oriented explanations (architecture, design decisions, Diataxis primer)
  - `security/` — security policies and guidelines
  - `_static/` — static assets (CSS, images)
  - `_templates/` — custom Sphinx templates
  - `generate_api_docs.py` — script to generate API documentation
  - `check_api_freshness.py` — script to check if API docs are up-to-date

- **Documentation organization — Diataxis.** Every doc page belongs to exactly one of four quadrants under `docs/`: `tutorials/` (learning-oriented), `how-to/`
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

  **Unified game option set.** `gamesheet-admin games <verb>` and `gamesheet-teams schedule games <verb>` do the same job against different backends — a
  season-schedule JSON:API for admin, the teams gateway's `/api/schedule-game` for teams — and expose **one option vocabulary**, so a command line written for
  either runs unchanged on the other. All five verbs (`create`, `update`, `get`, `list`, `delete`) expose byte-identical option names and short flags; a test
  (`tests/cli/games/test_unified_options.py`) and its teams counterpart pin the pieces. The set is declared once in `common/cli/`:

  - `game_options.py` — the option decorators (`game_time_options`, `game_side_options`, `game_detail_options`, `season_id_option`, `game_id_option`), the
    `GameArgs`/`GameSides` typed view over a command's `**params`, and `resolve_game_sides`.
  - `game_times.py` — start/end/duration resolution (`resolve_game_window`, `resolve_game_window_update`), `parse_duration_minutes`, `resolve_time_zone`.
  - `teams_lookup_options.py` — the read-side options that originate with the teams gateway (`--team-id`, `--month`, `--event-data`, `--availability`).
  - `game_constants.py` — help strings. Duplicated from `admin/cli/constants.py` on purpose so `common` takes no dependency on `admin`.

  Execution stays per-pillar in `admin/cli/shared/game_runner.py` and `teams/cli/commands/schedule/game_runner.py`; the command modules are thin, take
  `**params`, and delegate. Design decisions worth knowing:

  - **Two team-naming spellings, both accepted everywhere.** admin names the sides absolutely (`--home-team-id`/`--visitor-team-id`); teams names them relative
    to "my" team (`--team-id`/`--opposing-team-id` plus `--home`/`--visitor`, spelled `--away` on `update`). `resolve_game_sides` translates whichever was given
    into `GameSides`, which holds the absolute pair plus `home_flag` and derives the relative view. Naming the same slot twice with different values is a usage
    error. On teams `update` the default side comes from the game's *current* `home_flag`, not a blanket "home" — otherwise `--home-team-id` would silently mean
    the wrong team on an away game.
  - **`--association-id`/`--league-id` were removed, not aliased.** They are wholly determined by `--season-id`, so the teams runner derives them via
    `teams.seasons.get_season_ownership` (one extra `GET /api/seasons` per create). This costs a round trip but removes two options admin has no equivalent for.
  - **Options only one backend can send are warned about, not rejected.** `--home-label`/`--visitor-label` are admin-only; `--team-id`/`--month`/`--event-data`/
    `--availability` on `list`/`get` are teams-only. The receiving CLI prints a `Warning: … is not supported by …` line on stderr and continues with exit 0
    (`warn_unsupported_options`). This keeps command lines portable; silently dropping them would hide real data loss.
  - **`--start`/`--end` accept a bare time of day.** They alias `--start-datetime`/`--end-datetime`, but `--date 2026-08-20 --start 12:00 --end 13:15` is
    long-standing teams idiom, so `is_bare_time` reclassifies a time-only value into the split time slot instead of colliding with `--date`. Two *times* for the
    same end of the window (`--start 12:00 --start-time 13:00`) is still a usage error.
  - **`--season-id` is accepted in two positions on admin.** The `games` group option is now optional and `resolve_season_id` falls back to it, so both
    `games --season-id 1 create` and `games create --season-id 1` work. The `scheduled` verbs are also promoted onto the group, so
    `gamesheet-admin games create` lines up with `gamesheet-teams schedule games create`.
  - The two remaining asymmetries are genuine backend requirements, and both are "teams needs more": teams `create` requires `--season-id` (admin can inherit it
    from the group) and teams `list` requires `--team-id` (admin lists a whole season). A command line that satisfies teams therefore satisfies admin.

  **click gotcha worth preserving:** in click 8.4.2, passing `default=None` explicitly *cancels* `required=True` — the option arrives as `None` and the command
  body runs, with no error and no warning. Passing no `default` at all is not the same as passing `default=None`, even though click's implicit default *is*
  `None`. This silently disabled `--game-type`, `--number`, `--season-id` and `--team-id` when they were first made required. Build the keyword pair with
  `game_options.requiredness(required=...)` rather than writing `required=..., default=None` by hand.

  **Layering note:** the real datetime helpers live in `common/cli/datetime_helpers.py` and `admin/cli/shared/datetime_helpers.py` re-exports them. It used to
  be the other way round; that inversion meant importing anything under `common.cli` from the teams CLI blew up with a circular import as soon as a second
  `common.cli` module depended on the helpers. Keep the implementation in `common`.

  **One name per concept, one meaning per short flag.** Output subsetting is spelled `--columns` / `-c` on *every* command in both CLIs, whether the output is a
  table (`list`) or a single object (`get`, `create`, `update`, `delete -F json`) — they are all "show me only these keys", and `common/cli/decorators.py` has a
  single `columns_option` for it. There used to be a second spelling, `--fields` / `-f`, applied to the single-object commands; it did exactly the same thing
  (both route through `parse_columns_spec`) and it took `-f`, so `-f` meant `--fields` on 37 commands and `--force` on 12. `--fields` is gone with no
  deprecation alias.

  Two more second-spellings were removed with it: `--output-path` on `gamesheet-admin games completed download` (the same `output_path` dest as `--output`
  everywhere else) and `-c` on `gamesheet-teams lookups get` / `lookups list`, where it meant `--category`. `--category` now has no short flag, because `-c`
  belongs to `--columns`.

  `-t` was likewise taken off `--timeout` on the two `login` commands, where it was the odd one out against `--team-id` on 28.

  `RESERVED_SHORT_FLAGS` in `tests/common/cli/test_option_conventions.py` pins the invariants by walking both shipped click trees: `-c` is always `--columns`,
  `-f` always `--force`, `-t` always `--team-id`, `-F` always `--format`, `-o` always `--output`, `--force` and `--columns` always offer their short flag, and
  neither `--fields` nor `--output-path` comes back. Add to that table when you reserve a flag or retire a spelling.

  **Two known exceptions, both confined to the two `login` commands:** `-e` is `--email` there but `--event-id` on six `schedule` commands, and `-p` is
  `--password` there but `--practice-id` on three. Nothing is ambiguous *within* a command — `login` has no event or practice options — so these are
  muscle-memory conflicts rather than parsing ones, and `-e`/`-p` for email/password at a login prompt are strong conventions in their own right. Left as-is
  deliberately; if they ever go, `--email` and `--password` should give the flags up rather than be reassigned, as `--category` and `--timeout` did.

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

  - `if TYPE_CHECKING: from pydantic import SecretStr` alongside `cast("SecretStr", ...)` in tests reads as `py/unused-import`.
  - `FIREBASE_AUTH_URL` and `TOKEN_EXCHANGE_URL` in `common/auth/constants.py` read as `py/unused-global-variable` because nothing in their defining module
    consumes them — they are imported by `teams/login.py` and `tests/common/auth/conftest.py`.

  Both were dismissed as false positives in the Security UI. Note the contrast with Trivy: CVE suppression belongs in `.trivyignore.yaml` because Trivy supports
  a versioned ignore file with expiry, whereas CodeQL offers no equivalent per-alert repo-side mechanism short of `query-filters`, which would suppress a whole
  rule across the codebase rather than six specific sites.
