# ==============================================================================
# Multi-stage Dockerfile for gamesheet-sdk-py
# ==============================================================================
# Production-optimized container with security best practices:
# - Multi-stage build to minimize final image size
# - Non-root user for runtime security
# - Health check using CLI --version command
# - Slim Python base for reduced attack surface
# - Latest pip/setuptools/wheel to address CVE-2026-24049 and CVE-2026-23949
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Upgrade pip, setuptools, and wheel to latest versions (security fix)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Build wheel distribution
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# ------------------------------------------------------------------------------
# Stage 2: Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim

# Metadata labels
LABEL org.opencontainers.image.title="gamesheet-sdk-py"
LABEL org.opencontainers.image.description="Unofficial Python SDK and CLI for the GameSheet Inc. platform"
LABEL org.opencontainers.image.url="https://github.com/bdperkin/gamesheet-sdk-py"
LABEL org.opencontainers.image.source="https://github.com/bdperkin/gamesheet-sdk-py"
LABEL org.opencontainers.image.vendor="bdperkin"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime dependencies for Playwright (Chromium)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # Chromium dependencies
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
        # Additional utilities
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 gamesheet

# Set working directory
WORKDIR /app

# Copy wheel from builder stage
COPY --from=builder /build/dist/*.whl /tmp/

# Upgrade pip, setuptools, and wheel in runtime stage (security fix)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install the package and Playwright browsers as root (required for system-wide install)
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -f /tmp/*.whl && \
    python -m playwright install chromium && \
    python -m playwright install-deps chromium

# Switch to non-root user
USER gamesheet

# Health check using CLI --version command
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD gamesheet-sdk-py --version || exit 1

# Set entry point to the CLI
ENTRYPOINT ["gamesheet-sdk-py"]

# Default command shows help
CMD ["--help"]
