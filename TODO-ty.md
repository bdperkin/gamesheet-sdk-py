# Task: Comprehensive Integration and Standardization on Astral `ty` in Python Project

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

You are tasked with refactoring and modernizing this Python project to use **Astral `ty`** as the universal, high-performance static type checker and language
server, completely replacing legacy type checking tools like `mypy`, `pyright`, and `pyrefly`. All configurations must be consolidated strictly into
`pyproject.toml`, optimized for seamless integration alongside Astral `uv` and `ruff`, and configured to the absolute **strictest possible production-grade
standards**.

______________________________________________________________________

## 1. Operational Guardrails & Workflow

1. **Branch Management:** Immediately check out a new, descriptive git branch for this work (e.g., `refactor/migrate-to-ty`).
2. **No Premature Commits:** Do **not** commit or push any changes until explicitly directed to do so upon review.
3. **Strictness & Quality:** Configure `ty` rule levels, strict checking modes, and diagnostic options under `[tool.ty]` to be maximally strict.
4. **Tool Replacement & Removal:** Completely eradicate all usage, references, configurations, and binary dependencies of the following tools across the entire
   codebase (including pre-commit hooks, workflows, Makefiles, docs, and tox):
   - `mypy`, `pyright`, `pyrefly`, and any associated type-stub packages or runner extensions (e.g., `types-` packages if handled natively or restructured by
     `ty`, and legacy `mypy`/`pyright` config files like `mypy.ini` or `pyrightconfig.json`).
5. **Purge Obsolete Ignore Directives:** Sweep the entire codebase to completely remove all inline ignore comments, suppression flags, or pragmas tied to the
   replaced type checkers (e.g., `# type: ignore[...]`, `# pyright: ignore[...]`, `# pyrefly: ignore[...]`, etc.). Clean up any trailing whitespace or residual
   blank comment lines resulting from this removal.

______________________________________________________________________

## 2. Scope of Modifications

Inspect, update, refactor, or purge the following files and directories (at a minimum):

### 2.1. Configuration Centralization (`pyproject.toml`)

- All `ty` configuration **must** reside in `pyproject.toml` under `[tool.ty]` (and associated sub-tables like `[tool.ty.rules]`). Absolutely avoid any
  standalone `ty.toml` files.
- Define strict diagnostics, target Python versions matching project constraints, and source paths.

### 2.2. Pre-Commit Integration (`.genprecommitconfig.yaml` & `.pre-commit-config.yaml`)

- Implement **`ty-pre-commit`** (`https://github.com/astral-sh/ty-pre-commit`).
- Modify `.genprecommitconfig.yaml` so that running the custom generator script (`tools/genprecommitconfig`) correctly compiles and updates
  `.pre-commit-config.yaml` to include the `ty` hook via its official repo.

### 2.3. CI/CD Workflows (`.github/workflows/`)

- Refactor all GitHub Action workflows to execute type checking using `uv run ty check` (leveraging `uv`'s environment management and optimized caching).
- Remove all workflow steps invoking `mypy`, `pyright`, or `pyrefly`.

### 2.4. Task Execution & Automation (`Makefile`, `tox.ini`, `tools/`)

- **`Makefile`**: Update typecheck targets to invoke `uv run ty check`. Remove all legacy typing commands.
- **`tox.ini`**: Remove type checking environments dedicated to obsolete checkers. If `tox` is maintained, ensure any type checking uses `uv run ty check`.
- **`tools/`**: Audit custom scripts referencing old typing tools and update them to target `ty`.

### 2.5. Documentation & Metadata (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/`)

- Update onboarding guides, developer instructions, and architecture documents to reference `ty` instead of `mypy`/`pyright`.
- Document changes in `CHANGELOG.md`.

### 2.6. Housekeeping (`.gitignore`)

- Add any `ty` caching or local diagnostic metadata paths if applicable to `.gitignore`.

______________________________________________________________________

## 3. Questions / Ambiguity Check

Before executing the full refactor, please analyze the repository and **prompt the user** if any of the following items require clarification:

1. Because `ty` evaluates all code (including unannotated function bodies that `mypy` might bypass), do you want specific rules/modules downgraded to `warn` or
   `ignore` initially to prevent an overwhelming volume of typing errors on legacy modules during this first integration?
2. Are there specific path exclusions (`src.exclude`) or workspace layouts that need custom mapping inside `[tool.ty]` to accommodate generated code or tests?
