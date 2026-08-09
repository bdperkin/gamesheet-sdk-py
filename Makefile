# =============================================================================
# Makefile for gamesheet-sdk-py
# -----------------------------------------------------------------------------
# Unified developer interface around the tooling described in CLAUDE.md.
# Run `make help` (or just `make`) for the full target list.
# =============================================================================

SHELL          := /bin/bash
.DEFAULT_GOAL  := help
MAKEFLAGS      += --no-print-directory

# --- Python interpreter detection --------------------------------------------
# Probe /usr/bin for python3.11-3.14 binaries and pick the highest version.
# Override on the command line: `make PYTHON=python3.12 install`
# Only searches for Python 3.11-3.14 (project's supported versions).

DETECTED_PYTHON := $(shell basename -a /usr/bin/python3.1[1-4] 2>/dev/null \
					| grep -E '^python3\.1[1-4]$$' \
					| sort -V \
					| tail -n1)
PYTHON         ?= $(or $(DETECTED_PYTHON),python3)

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
	@printf "$(BOLD)gamesheet-sdk-py$(RESET) — developer Makefile\n\n"
	@printf "$(BOLD)Usage:$(RESET) make $(CYAN)<target>$(RESET) [VAR=value ...]\n\n"
	@printf "$(BOLD)Variables:$(RESET)\n"
	@printf "  $(CYAN)%-20s$(RESET) %s (current: $(GREEN)%s$(RESET))\n" \
		"PYTHON"  "Python interpreter (auto-detected 3.11-3.14; override to pick version)" "$(PYTHON)"
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
		"venv-<extra>" "Create venv + install a single extra (e.g., venv-dev, venv-docs)"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" \
		"tox-<env>"    "Run any tox env (e.g., tox-py312, tox-mypy, tox-radon-cc)"
	@printf "\n$(BOLD)Examples:$(RESET)\n"
	@printf "  $(YELLOW)make install$(RESET)            $(GREEN)# editable + dev extras + Playwright Chromium$(RESET)\n"
	@printf "  $(YELLOW)make venv-dev$(RESET)           $(GREEN)# fresh $(VENV) with [dev]$(RESET)\n"
	@printf "  $(YELLOW)make test-fast$(RESET)          $(GREEN)# skip @pytest.mark.browser tests$(RESET)\n"
	@printf "  $(YELLOW)make tox-py313$(RESET)          $(GREEN)# pytest under Python 3.13 only$(RESET)\n"
	@printf "  $(YELLOW)make PYTHON=python3.12 venv$(RESET)  $(GREEN)# pin venv interpreter$(RESET)\n"

# =============================================================================
# Installation
# =============================================================================

.PHONY: install
install: ## Editable install with [dev] extras + Playwright Chromium
	pip install -e ".[dev]"
	python -m playwright install chromium

.PHONY: install-all
install-all: ## Editable install with [all] extras + Playwright Chromium
	pip install -e ".[all]"
	python -m playwright install chromium

# =============================================================================
# Cleaning
# -----------------------------------------------------------------------------

.PHONY: clean
clean: ## Remove caches and build artifacts (preserves Git state)
	@printf "$(CYAN)→$(RESET) clean: __pycache__ .pytest_cache .mypy_cache .ruff_cache .coverage dist coverage.xml\n"
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .pyright .coverage dist coverage.xml

.PHONY: clean-all
clean-all: clean ## clean + remove .tox, $(VENV), and docs build dirs
	@printf "$(CYAN)→$(RESET) clean-all: .tox $(VENV) $(DOCS_BUILD) $(DOCS_AUTOSUM) $(DOCS_REF_AUTOSUM)\n"
	@rm -rf .tox $(VENV) $(DOCS_BUILD) $(DOCS_AUTOSUM) $(DOCS_REF_AUTOSUM)

# =============================================================================
# Virtual environments
# -----------------------------------------------------------------------------
# Both `venv` and `venv-<extra>` start from a clean slate — they wipe any
# existing $(VENV) first, then build with the detected (or overridden) PYTHON.
# =============================================================================

.PHONY: venv
venv: ## Create a fresh $(VENV) using $(PYTHON) (no project install)
	@printf "$(CYAN)→$(RESET) creating $(VENV) with $(GREEN)$(PYTHON)$(RESET)\n"
	@rm -rf $(VENV)
	$(PYTHON) -m venv $(VENV)
	@$(VENV)/bin/pip install --quiet --upgrade pip
	@printf "$(GREEN)✓$(RESET) $(VENV) ready. Activate with: $(YELLOW)source $(VENV)/bin/activate$(RESET)\n"

.PHONY: venv-%
venv-%: ## Create $(VENV) and install the named extra (e.g., make venv-dev)
	@printf "$(CYAN)→$(RESET) creating $(VENV) with $(GREEN)$(PYTHON)$(RESET) + extra '$(GREEN)$*$(RESET)'\n"
	@rm -rf $(VENV)
	$(PYTHON) -m venv $(VENV)
	@$(VENV)/bin/pip install --quiet --upgrade pip
	$(VENV)/bin/pip install -e ".[$*]"
	@printf "$(GREEN)✓$(RESET) $(VENV) ready with [$*]. Activate with: $(YELLOW)source $(VENV)/bin/activate$(RESET)\n"

# =============================================================================
# Testing
# -----------------------------------------------------------------------------
# pytest is configured with --block-network (pytest-recording). Any test that
# opens a socket without a VCR cassette fails. test-fast skips the browser
# marker so you don't spin up real Chromium for the inner dev loop.
# =============================================================================

.PHONY: test
test: ## Run the full pytest suite (network-blocked; VCR + playwright)
	pytest

.PHONY: test-fast
test-fast: ## Run only fast tests (-m "not browser")
	pytest -m "not browser"

.PHONY: test-cov
test-cov: ## Run pytest with coverage (fail_under threshold lives in pyproject)
	pytest --cov

# =============================================================================
# Linting, formatting, typing
# -----------------------------------------------------------------------------
# `lint` runs the whole pre-commit suite. `type` runs mypy directly in --strict
# mode (the project is a PEP 561 typed package; new code must pass strict).
# =============================================================================

.PHONY: lint
lint: ## Run pre-commit across the whole repo (includes mypy --strict, xenon)
	pre-commit run --all-files

.PHONY: type
type: ## Run mypy --strict against src/ (PEP 561 typed package — strict required)
	mypy --strict $(PKG)

.PHONY: fix
fix: _check-tox ## Apply formatters in place (isort, black, mdformat)
	@printf "$(CYAN)→$(RESET) applying formatters (isort, black, mdformat)\n"
	tox -e isort -- .
	tox -e black -- .
	tox -e mdformat -- .
	@printf "$(GREEN)✓$(RESET) formatting complete\n"

# =============================================================================
# Complexity / metrics
# -----------------------------------------------------------------------------
# Xenon enforces the project-wide cyclomatic-complexity ceiling via pre-commit
# (--max-absolute=A --max-modules=A --max-average=B). `make metrics` reports
# the actual radon numbers — useful before pushing a function that's growing
# conditionals.
# =============================================================================

.PHONY: metrics
metrics: _check-tox ## Radon + Xenon complexity gates (radon cc + mi)
	@printf "$(CYAN)→$(RESET) running radon complexity analysis\n"
	tox -e radon-cc -- --show-complexity --average .
	@printf "\n$(CYAN)→$(RESET) running radon maintainability index\n"
	tox -e radon-mi -- --show .

# =============================================================================
# Documentation (Sphinx + Furo theme)
# -----------------------------------------------------------------------------
# `docs` builds HTML two-pass (warm-up + strict -n -W). `docs-serve` runs
# sphinx-autobuild for live reload. `docs-pdf` requires LaTeX + latexmk on
# PATH; install texlive-latex-extra (or your distro's equivalent) first.
# =============================================================================

.PHONY: docs
docs: _check-tox ## Build HTML docs (Sphinx + Furo, two-pass strict)
	tox -e docs

.PHONY: docs-serve
docs-serve: _check-tox ## Live-reload preview of HTML docs (sphinx-autobuild)
	tox -e docs-serve

.PHONY: docs-pdf
docs-pdf: _check-tox ## Build PDF docs via LaTeX (needs pdflatex + latexmk on PATH)
	tox -e docs-pdf

.PHONY: docs-lint
docs-lint: _check-tox ## sphinx-lint over docs/ + API freshness check
	tox -e docs-lint

.PHONY: docs-api
docs-api: ## Generate API documentation using sphinx-apidoc
	python docs/generate_api_docs.py

.PHONY: docs-check
docs-check: ## Check if API docs are up-to-date with source
	python docs/check_api_freshness.py

.PHONY: docs-linkcheck
docs-linkcheck: _check-tox ## Check external links in docs
	tox -e docs-linkcheck

.PHONY: docs-epub
docs-epub: _check-tox ## Build EPUB documentation
	tox -e docs-epub

.PHONY: docs-man
docs-man: _check-tox ## Build man-page documentation
	tox -e docs-man

.PHONY: docs-doctest
docs-doctest: _check-tox ## Run doctest examples embedded in documentation
	tox -e docs-doctest

# =============================================================================
# Docker (local container management)
# -----------------------------------------------------------------------------
# Build, run, and push Docker containers locally. The container is published
# to GitHub Container Registry (GHCR) during the release workflow.
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

# =============================================================================
# Tox pattern rule
# -----------------------------------------------------------------------------
# Escape hatch for any tox env not given a dedicated target above:
#   make tox-py312        →  tox -e py312
#   make tox-mypy         →  tox -e mypy
#   make tox-radon-cc     →  tox -e radon-cc
# =============================================================================

.PHONY: tox-%
tox-%: _check-tox ## Run any tox env (e.g., tox-py312, tox-mypy, tox-radon-cc)
	tox -e $*

.PHONY: _check-tox
_check-tox:
	@command -v tox >/dev/null 2>&1 || { \
		printf "$(RED)error:$(RESET) $(BOLD)tox$(RESET) is not on PATH.\n" >&2; \
		printf "  install it with: $(CYAN)make install$(RESET)  (or: $(CYAN)pip install tox$(RESET))\n" >&2; \
		exit 1; \
	}
