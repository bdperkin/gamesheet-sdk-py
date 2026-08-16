# =============================================================================
# Makefile for gamesheet-sdk-py (Powered by uv)
# -----------------------------------------------------------------------------
# Unified developer interface around the Astral uv workflow.
# Run `make help` (or just `make`) for the full target list.
# =============================================================================

SHELL          := /bin/bash
.DEFAULT_GOAL  := help
MAKEFLAGS      += --no-print-directory

# --- Standard paths ----------------------------------------------------------

VENV               := .venv
PKG                := src/gamesheet_sdk
DOCS_BUILD         := docs/_build
DOCS_AUTOSUM       := docs/_autosummary
DOCS_REF_AUTOSUM   := docs/reference/_autosummary

# --- Docker configuration ----------------------------------------------------

DOCKER_REGISTRY    := ghcr.io
DOCKER_OWNER       := bdperkin
DOCKER_IMAGE       := gamesheet-sdk-py
DOCKER_TAG         ?= latest
DOCKER_FULL_IMAGE  := $(DOCKER_REGISTRY)/$(DOCKER_OWNER)/$(DOCKER_IMAGE):$(DOCKER_TAG)

# --- ANSI colors (used by help + status lines) -------------------------------

CYAN   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
RED    := \033[31m
BOLD   := \033[1m
RESET  := \033[0m

# =============================================================================
# Help (default goal)
# =============================================================================

.PHONY: help
help: ## Show this help message
	@printf "$(BOLD)gamesheet-sdk-py$(RESET) — developer Makefile (uv)\n\n"
	@printf "$(BOLD)Usage:$(RESET) make $(CYAN)<target>$(RESET) [VAR=value ...]\n\n"
	@printf "$(BOLD)Variables:$(RESET)\n"
	@printf "  $(CYAN)%-20s$(RESET) %s (current: $(GREEN)%s$(RESET))\n" \
		"VENV"    "Virtualenv directory" "$(VENV)"
	@printf "  $(CYAN)%-20s$(RESET) %s (current: $(GREEN)%s$(RESET))\n" \
		"DOCKER_TAG" "Docker image tag" "$(DOCKER_TAG)"
	@printf "  $(CYAN)%-20s$(RESET) %s (current: $(GREEN)%s$(RESET))\n" \
		"DOCKER_CMD" "Docker run command (e.g., gamesheet-admin --help)" "$(or $(DOCKER_CMD),(default))"
	@printf "\n$(BOLD)Targets:$(RESET)\n"
	@awk 'BEGIN {FS = ":.*?## "} \
			/^[a-zA-Z_-]+:.*?## / { \
			printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 \
			}' $(MAKEFILE_LIST)
	@printf "\n$(BOLD)Pattern rules:$(RESET)\n"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" \
		"venv-<extra>" "Sync venv with a specific extra (e.g., venv-dev, venv-docs)"
	@printf "\n$(BOLD)Examples:$(RESET)\n"
	@printf "  $(YELLOW)make install$(RESET)            $(GREEN)# uv sync --extra dev + Playwright Chromium$(RESET)\n"
	@printf "  $(YELLOW)make install-all$(RESET)        $(GREEN)# uv sync --all-extras + Playwright Chromium$(RESET)\n"
	@printf "  $(YELLOW)make test-fast$(RESET)          $(GREEN)# skip @pytest.mark.browser tests$(RESET)\n"

# =============================================================================
# Installation
# =============================================================================

.PHONY: install
install: ## Editable install with [dev] extra + Playwright Chromium via uv
	uv sync --extra dev
	uv run playwright install chromium

.PHONY: install-all
install-all: ## Editable install with [all] extras + Playwright Chromium via uv
	uv sync --all-extras
	uv run playwright install chromium

# =============================================================================
# Cleaning
# -----------------------------------------------------------------------------

.PHONY: clean
clean: ## Remove caches and build artifacts (preserves Git state)
	@printf "$(CYAN)→$(RESET) clean: __pycache__ .pytest_cache .ty_cache .ruff_cache .coverage dist coverage.xml\n"
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	@rm -rf .pytest_cache .ty_cache .ruff_cache .coverage dist coverage.xml

.PHONY: clean-all
clean-all: clean ## clean + remove .uv, $(VENV), and docs build dirs
	@printf "$(CYAN)→$(RESET) clean-all: .uv $(VENV) $(DOCS_BUILD) $(DOCS_AUTOSUM) $(DOCS_REF_AUTOSUM)\n"
	@rm -rf .uv $(VENV) $(DOCS_BUILD) $(DOCS_AUTOSUM) $(DOCS_REF_AUTOSUM)

# =============================================================================
# Virtual environments
# =============================================================================

.PHONY: venv
venv: ## Create virtual environment using uv
	@printf "$(CYAN)→$(RESET) creating virtualenv with $(GREEN)uv venv$(RESET)\n"
	uv venv $(VENV)
	@printf "$(GREEN)✓$(RESET) $(VENV) ready.\n"

.PHONY: venv-%
venv-%: ## Sync $(VENV) with the named extra using uv (e.g., make venv-dev)
	@printf "$(CYAN)→$(RESET) syncing $(VENV) with extra '$(GREEN)$*$(RESET)' via uv\n"
	uv sync --extra $*
	@printf "$(GREEN)✓$(RESET) $(VENV) synced with [$*].\n"

# =============================================================================
# Testing
# =============================================================================

.PHONY: test
test: ## Run the full pytest suite via uv run
	uv run pytest

.PHONY: test-fast
test-fast: ## Run fast tests (-m "not browser") via uv run
	uv run pytest -m "not browser"

.PHONY: test-cov
test-cov: ## Run pytest with coverage via uv run
	uv run pytest --cov

# =============================================================================
# Linting, formatting, typing
# =============================================================================

.PHONY: dependencies
dependencies: ## Lockfile Synchronization
	uv run --extra dev uv lock

.PHONY: checks
checks: ## Low-level Checks
	uv run --extra editorconfig-checker ec

.PHONY: configuration
configuration: ## Configuration Validation
	uv run --extra format-json format-json --autofix --no-sort-keys
	uv run --extra yamlfix yamlfix $$(git ls-files *.yml *.yaml .yamllint)
	uv run --extra yamllint yamllint --config-file .yamllint $$(git ls-files *.yml *.yaml .yamllint)
	uv run --extra pyproject-fmt pyproject-fmt pyproject.toml
	uv run --extra validate-pyproject validate-pyproject pyproject.toml
	uv run --extra pyroma pyroma --directory --min=10 .

.PHONY: markdown
markdown: ## Markdown Formatting
	uv run --extra mdformat mdformat $$(git ls-files '*.md')
	uv run --extra pymarkdown pymarkdown scan .

.PHONY: security
security: ## Secret and Vulnerability Scans
	uv run --extra semgrep semgrep --disable-version-check --quiet --skip-unknown-extensions

.PHONY: format
format: ## Python Formatting
	uv run --extra unimport unimport docs src tests tools
	uv run --extra absolufy-imports absolufy-imports
	uv run --extra ssort ssort
	uv run --extra add-trailing-comma add-trailing-comma
	uv run --extra blank-line-after-blocks blank-line-after-blocks
	uv run --extra ruff ruff check --force-exclude
	uv run --extra ruff ruff format --force-exclude

.PHONY: quality
quality: ## Code Quality
	uv run --extra vulture vulture
	uv run --extra interrogate interrogate
	uv run --extra codespell codespell $$(git ls-files)
	uv run --extra blocklint blocklint

.PHONY: types
types: ## Static Type Checks
	uv run --extra ty ty check

# =============================================================================
# Complexity / metrics
# =============================================================================

.PHONY: metrics
metrics: ## Radon complexity analysis via uv run
	@printf "$(CYAN)→$(RESET) running radon complexity analysis\n"
	uv run --extra radon radon cc --show-complexity --average .
	@printf "\n$(CYAN)→$(RESET) running radon maintainability index\n"
	uv run --extra radon radon mi --show .

# =============================================================================
# Documentation (Sphinx + Furo theme)
# =============================================================================

.PHONY: docs
docs: ## Build HTML docs via uv run
	uv run --extra docs sphinx-build -b html docs docs/_build/html

.PHONY: docs-serve
docs-serve: ## Live-reload preview of HTML docs via uv run
	uv run --extra docs sphinx-autobuild docs docs/_build/html

.PHONY: docs-pdf
docs-pdf: ## Build PDF docs via LaTeX via uv run
	uv run --extra docs sphinx-build -b latex docs docs/_build/latex
	$(MAKE) -C docs/_build/latex all-pdf

.PHONY: docs-lint
docs-lint: ## sphinx-lint over docs/ + API freshness check via uv run
	uv run --extra docs sphinx-lint -i docs/reference/_autosummary -i docs/_build -i docs/_autosummary docs
	uv run python docs/check_api_freshness.py

.PHONY: docs-api
docs-api: ## Generate API documentation via uv run
	uv run python docs/generate_api_docs.py

.PHONY: docs-check
docs-check: ## Check if API docs are up-to-date with source via uv run
	uv run python docs/check_api_freshness.py

.PHONY: docs-linkcheck
docs-linkcheck: ## Check external links in docs via uv run
	uv run --extra docs sphinx-build -b linkcheck docs docs/_build/linkcheck

.PHONY: docs-epub
docs-epub: ## Build EPUB documentation via uv run
	uv run --extra docs sphinx-build -b epub docs docs/_build/epub

.PHONY: docs-man
docs-man: ## Build man-page documentation via uv run
	uv run --extra docs sphinx-build -b man docs docs/_build/man

.PHONY: docs-doctest
docs-doctest: ## Run doctest examples embedded in documentation via uv run
	uv run --extra docs sphinx-build -b doctest docs docs/_build/doctest

# =============================================================================
# Docker (local container management)
# =============================================================================

.PHONY: docker-build
docker-build: ## Build Docker image locally
	@printf "$(CYAN)→$(RESET) building Docker image: $(GREEN)$(DOCKER_FULL_IMAGE)$(RESET)\n"
	docker build -t $(DOCKER_FULL_IMAGE) .
	@printf "$(GREEN)✓$(RESET) image built successfully\n"
	@printf "  run with: $(YELLOW)make docker-run$(RESET)\n"
	@printf "  push with: $(YELLOW)make docker-push$(RESET) (requires authentication)\n"

DOCKER_CMD         ?=

.PHONY: docker-run
docker-run: ## Run Docker container locally (DOCKER_CMD="gamesheet-admin --help")
	@printf "$(CYAN)→$(RESET) running container: $(GREEN)$(DOCKER_FULL_IMAGE)$(RESET)\n"
	docker run --rm -it $(DOCKER_FULL_IMAGE) $(DOCKER_CMD)

.PHONY: docker-push
docker-push: ## Push Docker image to registry (requires authentication)
	@printf "$(CYAN)→$(RESET) pushing image: $(GREEN)$(DOCKER_FULL_IMAGE)$(RESET)\n"
	@if ! docker info 2>/dev/null | grep -q "Username:"; then \
		printf "$(RED)error:$(RESET) not logged in to Docker registry\n" >&2; \
		printf "  authenticate with: $(CYAN)docker login $(DOCKER_REGISTRY)$(RESET)\n" >&2; \
		exit 1; \
	fi
	docker push $(DOCKER_FULL_IMAGE)
	@printf "$(GREEN)✓$(RESET) image pushed successfully\n"

.PHONY: docker-clean
docker-clean: ## Remove local Docker images
	@printf "$(CYAN)→$(RESET) removing local images: $(DOCKER_REGISTRY)/$(DOCKER_OWNER)/$(DOCKER_IMAGE)\n"
	docker images $(DOCKER_REGISTRY)/$(DOCKER_OWNER)/$(DOCKER_IMAGE) -q | xargs -r docker rmi -f
	@printf "$(GREEN)✓$(RESET) local images removed\n"
