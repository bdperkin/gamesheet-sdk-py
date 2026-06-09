#!/usr/bin/env python3
"""Generate API documentation using sphinx-apidoc.

This script discovers all Python modules in src/gamesheet_sdk and generates ReStructuredText files with
automodule directives. It runs automatically during the docs build process.
"""

from __future__ import annotations

import subprocess  # noqa: S404 # nosec B404
import sys
from pathlib import Path

from rich import print as rprint

# Paths relative to this script's location
DOCS_DIR = Path(__file__).parent
PROJECT_ROOT = DOCS_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
PACKAGE_DIR = SRC_DIR / "gamesheet_sdk"
OUTPUT_DIR = DOCS_DIR / "reference" / "_autosummary"


def main() -> int:
    """Run sphinx-apidoc to generate API documentation."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Run sphinx-apidoc
    cmd = [
        "sphinx-apidoc",
        "--force",  # Overwrite existing files
        "--separate",  # Put each module on its own page
        "--module-first",  # Put module docs before submodule docs
        "--no-toc",  # Don't create a table of contents file
        "--implicit-namespaces",  # Support PEP 420 namespace packages
        "--output-dir",
        str(OUTPUT_DIR),
        str(PACKAGE_DIR),
        # Exclude patterns
        str(PACKAGE_DIR / "_version.py"),  # Build-time generated file (gitignored)
        "*/tests/*",  # Test files
        "**/test_*.py",  # Test files
    ]

    rprint(f"[bold]Running:[/bold] [cyan]{' '.join(cmd)}[/cyan]")
    result = subprocess.run(cmd, check=False)  # noqa: S603 # nosec B603

    if result.returncode != 0:
        rprint(
            f"[bold red]sphinx-apidoc failed with exit code {result.returncode}[/bold red]",
            file=sys.stderr,
        )
        return result.returncode

    rprint(f"[bold green]✓[/bold green] API documentation generated in [cyan]{OUTPUT_DIR}[/cyan]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
