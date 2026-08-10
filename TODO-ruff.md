# Task: Comprehensive Integration and Standardization on Astral Ruff in Python Project

<!--TOC-->

______________________________________________________________________

- [1. Operational Guardrails & Workflow](#1-operational-guardrails--workflow)
- [2. Scope of Modifications](#2-scope-of-modifications)
  - [2.1. Configuration Centralization (`pyproject.toml`)](#21-configuration-centralization--pyprojecttoml)
  - [2.2. Pre-Commit Integration (`.genprecommitconfig.yaml` & `.pre-commit-config.yaml`)](#22-pre-commit-integration--genprecommitconfigyaml--pre-commit-configyaml)
  - [2.3. CI/CD Workflows (`.github/workflows/`)](#23-cicd-workflows--githubworkflows)
  - [2.4. Task Execution & Automation (`Makefile`, `tox.ini`, `tools/`)](#24-task-execution--automation--makefile--toxini--tools)
  - [2.5. Documentation & Metadata (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/`)](#25-documentation--metadata--readmemd--contributingmd--changelogmd--docs)
  - [2.6. Housekeeping (`.gitignore`)](#26-housekeeping--gitignore)
- [3. Questions / Ambiguity Check](#3-questions--ambiguity-check)

______________________________________________________________________

<!--TOC-->

You are tasked with refactoring and modernizing this Python project to use **Astral Ruff** as the sole, universal linter and code formatter, replacing all
legacy static analysis, formatting, sorting, and upgrade tools. All configurations must be consolidated strictly into `pyproject.toml`, integrated smoothly with
our existing Astral `uv` toolchain, and set to the absolute **strictest possible production-grade standards**.

______________________________________________________________________

## 1. Operational Guardrails & Workflow

1. **Branch Management:** Immediately check out a new, descriptive git branch for this work (e.g., `refactor/migrate-to-ruff`).
2. **No Premature Commits:** Do **not** commit or push any changes until explicitly directed to do so upon review.
3. **Strictness & Quality:** Configure Ruff rules to be comprehensive and strict (e.g., full rule selection across relevant categories like `E`, `W`, `F`, `I`,
   `UP`, `B`, `SIM`, `RUF`, `D`, etc., with appropriate exceptions handled cleanly).
4. **Tool Replacement & Removal:** Completely eradicate all usage, references, configurations, and binary dependencies of the following tools across the entire
   codebase (including pre-commit, workflows, Makefiles, docs, and tox):
   - `Black`, `isort`, `Flake8` (and all Flake8 plugins), `Pyflakes`, `Pycodestyle`, `Pylint`, `pydocstyle`, `pyupgrade`, `autoflake`, and any other redundant
     linters or formatters.
5. **Purge Obsolete Ignore Directives:** Sweep the entire codebase to completely remove any inline ignore comments, suppression flags, or pragmas tied to the
   replaced tools (e.g., `noqa`, `nosec`, `pylint`, `pyupgrade`, `autoflake`, `flake8`, etc.). Clean up any trailing whitespace or residual blank comment lines
   resulting from this removal.

______________________________________________________________________

## 2. Scope of Modifications

Inspect, update, refactor, or purge the following files and directories (at a minimum):

### 2.1. Configuration Centralization (`pyproject.toml`)

- All Ruff configuration **must** reside in `pyproject.toml` under `[tool.ruff]` and `[tool.ruff.lint]` (strictly avoiding any `ruff.toml` or `.ruff.toml`
  files).
- Define comprehensive rule selection (`select`, `ignore`), target Python version matching the project, line length, docstring conventions, and auto-fix
  behaviors.

### 2.2. Pre-Commit Integration (`.genprecommitconfig.yaml` & `.pre-commit-config.yaml`)

- Implement **`ruff-pre-commit`** (`https://github.com/astral-sh/ruff-pre-commit`) providing both the linter (`ruff`) and formatter (`ruff-format`) hooks.
- Modify `.genprecommitconfig.yaml` so that running the custom generator script (`tools/genprecommitconfig`) correctly compiles and updates
  `.pre-commit-config.yaml`.

### 2.3. CI/CD Workflows (`.github/workflows/`)

- Refactor all GitHub Action workflows to execute Ruff using `uv run ruff check` and `uv run ruff format --check` (or official ruff GitHub actions if optimized,
  ensuring seamless integration with `uv` caching).
- Remove all steps invoking legacy linters or formatters.

### 2.4. Task Execution & Automation (`Makefile`, `tox.ini`, `tools/`)

- **`Makefile`**: Update lint and format targets to invoke `uv run ruff check --fix` and `uv run ruff format`. Remove references to black, isort, flake8,
  pylint, etc.
- **`tox.ini`**: Remove environments dedicated to obsolete linters/formatters. If `tox` runs linters, update them to use `uv run ruff`.
- **`tools/`**: Audit any custom scripts referencing old analysis tools and point them to Ruff.

### 2.5. Documentation & Metadata (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/`)

- Update all onboarding guidelines, code style documentation, and developer instructions to reference Ruff and `uv`.
- Document changes in `CHANGELOG.md`.

### 2.6. Housekeeping (`.gitignore`)

- Add standard Ruff cache directories (`.ruff_cache/`) to `.gitignore`.

______________________________________________________________________

## 3. Questions / Ambiguity Check

Before executing the full refactor, please analyze the repository and **prompt the user** if any of the following items require clarification:

1. Are there project-specific legacy rules or code conventions that require specific Ruff rule suppressions (`ignore`) to prevent massive initial diffs on
   legacy modules?
2. Do any existing docstring conventions (e.g., Google, NumPy, Sphinx) dictate specific `pydocstyle` configurations under `[tool.ruff.lint.pydocstyle]`?
3. Are there custom third-party plugins that were previously used in Pylint or Flake8 whose logic needs explicit mapping to native Ruff rules?
