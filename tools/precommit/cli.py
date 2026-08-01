# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""CLI interface for pre-commit configuration generation."""

from __future__ import annotations

from pathlib import Path

from precommit.config import DEFAULT_CONFIG_FILE, INIT_TEMPLATE
from precommit.exceptions import GenPreCommitConfigError
from precommit.generator import PreCommitGenerator
from precommit.models import RunConfig
from rich.console import Console
import rich_click as click
from shared import PROJECT_NAME
from shared.log_config import configure_logging

console = Console()


def _write_init_template(config_file: Path) -> None:
    """Write a minimal template configuration file.

    :param config_file: Path to write the template to.
    :raises SystemExit: If the file already exists.
    """
    if config_file.exists():
        console.print(f"[bold red]Error:[/] {config_file} already exists")
        raise SystemExit(1)

    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(INIT_TEMPLATE, encoding="utf-8")
    except OSError as exc:
        console.print(f"[bold red]Error:[/] Failed to write {config_file}: {exc}")
        raise SystemExit(1) from exc

    console.print(f"Wrote {config_file}")


@click.command("genprecommitconfig")
@click.option(
    "--config-file",
    type=click.Path(exists=False),
    default=DEFAULT_CONFIG_FILE,
    show_default=True,
    help="Path to the YAML configuration file.",
)
@click.option(
    "--output-file",
    type=click.Path(),
    default=None,
    help="Override output file path from configuration.",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    show_default=True,
    help="Logging verbosity level.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Generate YAML only, do not run pre-commit validation.",
)
@click.option(
    "--no-validate",
    is_flag=True,
    default=False,
    help="Skip per-repo incremental validation (final validation still runs).",
)
@click.option(
    "--max-downgrade-attempts",
    type=int,
    default=None,
    help="Max older revisions to try on validation failure (0=none, -1=all).",
)
@click.option(
    "--init",
    is_flag=True,
    default=False,
    help="Write a minimal template config file and exit.",
)
@click.version_option(package_name=PROJECT_NAME)
def app(
    config_file: str,
    output_file: str | None,
    log_level: str,
    max_downgrade_attempts: int | None,
    *,
    dry_run: bool,
    no_validate: bool,
    init: bool,
) -> None:
    """Generate .pre-commit-config.yaml from a declarative configuration file.

    Fetches hook definitions from upstream repositories, applies overrides and filters from the configuration,
    and validates each repo incrementally with pre-commit.

    :param config_file: Path to the YAML configuration file.
    :type config_file: str
    :param output_file: Override output file path from configuration.
    :type output_file: str | None
    :param log_level: Logging verbosity level.
    :type log_level: str
    :param max_downgrade_attempts: Max older revisions to try on validation failure.
    :type max_downgrade_attempts: int | None
    :param dry_run: Generate YAML only, do not run pre-commit validation.
    :type dry_run: bool
    :param no_validate: Skip per-repo incremental validation.
    :type no_validate: bool
    :param init: Write a minimal template config file and exit.
    :type init: bool
    :raises SystemExit: If generation fails.
    """
    configure_logging(log_level, console)

    config_path = Path(config_file)
    output_path = Path(output_file) if output_file is not None else None

    if init:
        _write_init_template(config_path)
        return

    run_config = RunConfig(
        config_file=config_path,
        output_file=output_path,
        log_level=log_level,
        dry_run=dry_run,
        validate_incremental=not no_validate,
        max_downgrade_attempts=max_downgrade_attempts,
    )

    try:
        generator = PreCommitGenerator(run_config=run_config)
        generator.generate()
    except GenPreCommitConfigError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise SystemExit(exc.exit_code) from exc
