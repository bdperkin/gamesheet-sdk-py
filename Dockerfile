# ==============================================================================
# Multi-stage Dockerfile for gamesheet-sdk-py
# ==============================================================================
# Production-optimized container with security best practices:
# - Multi-stage build to minimize final image size
# - Non-root user for runtime security
# - Health check using both CLI --version commands
# - Slim Python base for reduced attack surface
# - Playwright Chromium for headless browser automation
# - Latest pip/setuptools/wheel to address known CVEs
# - Ships both CLIs: gamesheet-admin and gamesheet-teams
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder
# ------------------------------------------------------------------------------
# Purpose: Build the wheel distribution in an isolated environment
# This stage includes build tools that aren't needed at runtime
FROM python:3.11-slim AS builder

# Set working directory for build
WORKDIR /build

# Install build dependencies (git needed for setuptools-scm if used)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files needed for build
# Note: .dockerignore controls what gets excluded
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Upgrade pip, setuptools, and wheel to latest versions (security fix)
# setuptools>=83.0.0 addresses CVE-2025-47273 and CVE-2026-59890
RUN pip install --no-cache-dir --upgrade pip "setuptools>=83.0.0" wheel

# Build wheel distribution (no editable installs in containers)
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# ------------------------------------------------------------------------------
# Stage 2: Runtime
# ------------------------------------------------------------------------------
# Purpose: Minimal runtime environment with only what's needed to run the CLI
# Size-optimized by excluding build tools and dev dependencies
FROM python:3.11-slim

# ------------------------------------------------------------------------------
# Metadata (OCI image spec labels)
# ------------------------------------------------------------------------------
LABEL org.opencontainers.image.title="gamesheet-sdk-py"
LABEL org.opencontainers.image.description="Unofficial Python SDK and CLI for the GameSheet Inc. platform"
LABEL org.opencontainers.image.url="https://github.com/bdperkin/gamesheet-sdk-py"
LABEL org.opencontainers.image.source="https://github.com/bdperkin/gamesheet-sdk-py"
LABEL org.opencontainers.image.documentation="https://bdperkin.github.io/gamesheet-sdk-py/"
LABEL org.opencontainers.image.vendor="bdperkin"
LABEL org.opencontainers.image.licenses="MIT"

# ------------------------------------------------------------------------------
# Environment configuration
# ------------------------------------------------------------------------------
# PYTHONUNBUFFERED: Force stdout/stderr to be unbuffered (better for logs)
# PYTHONDONTWRITEBYTECODE: Don't create .pyc files (not needed in container)
# PIP_NO_CACHE_DIR: Don't cache pip downloads (saves space)
# PIP_DISABLE_PIP_VERSION_CHECK: Skip pip version check (offline-friendly)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ------------------------------------------------------------------------------
# Runtime dependencies installation
# ------------------------------------------------------------------------------
# Install system libraries required for Playwright Chromium to run headless
# This list is based on Playwright's official Chromium dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # Core Chromium dependencies
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        # Certificate trust store for HTTPS
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------------------
# Non-root user setup (security hardening)
# ------------------------------------------------------------------------------
# Run the application as a non-root user to limit potential attack surface
# UID 1000 is a common convention for the first non-system user
RUN useradd --create-home --shell /bin/bash --uid 1000 gamesheet

# Set working directory (owned by root, but readable by all)
WORKDIR /app

# ------------------------------------------------------------------------------
# Package installation
# ------------------------------------------------------------------------------
# Copy the wheel built in the builder stage
COPY --from=builder /build/dist/*.whl /tmp/

# Upgrade pip/setuptools/wheel in runtime stage (security fix)
# setuptools>=83.0.0 addresses CVE-2025-47273 and CVE-2026-59890
# Must run as root for system-wide Playwright installation
RUN pip install --no-cache-dir --upgrade pip "setuptools>=83.0.0" wheel && \
    rm -rf /usr/local/lib/python3.11/ensurepip/_bundled/ && \
    pip install --no-cache-dir /tmp/*.whl && \
    rm -f /tmp/*.whl && \
    # Install Chromium browser binary (headless mode)
    python -m playwright install chromium && \
    # Install Chromium system dependencies
    python -m playwright install-deps chromium

# ------------------------------------------------------------------------------
# Switch to non-root user for runtime
# ------------------------------------------------------------------------------
# From this point on, all operations run as the 'gamesheet' user
USER gamesheet

# ------------------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------------------
# Verify both CLIs are functional by running --version
# Interval: check every 30 seconds
# Timeout: allow 3 seconds for command to complete
# Start-period: wait 5 seconds before first check
# Retries: mark unhealthy after 3 consecutive failures
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD gamesheet-admin --version && gamesheet-teams --version || exit 1

# ------------------------------------------------------------------------------
# Default command
# ------------------------------------------------------------------------------
# No ENTRYPOINT — users choose which CLI to run:
#   docker run <image> gamesheet-admin --help
#   docker run <image> gamesheet-teams --help
CMD ["sh", "-c", "echo 'Usage: docker run <image> <command> [args]' && echo '' && echo 'Available commands:' && echo '  gamesheet-admin   Admin dashboard CLI' && echo '  gamesheet-teams   Teams dashboard CLI' && echo '' && echo 'Example: docker run <image> gamesheet-admin --help'"]
