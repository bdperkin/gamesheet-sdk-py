# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared base exceptions for CLI tools."""

from __future__ import annotations


class ToolError(Exception):
    """Base error for all CLI tools.

    Carries an ``exit_code`` so CLI entry points can translate caught exceptions into process exit codes.
    """

    exit_code: int = 1

    def __init__(self: ToolError, *args: object) -> None:
        """Initialize with exception arguments.

        Args:
            *args (object): Exception arguments passed to the base
                class.
        """
        super().__init__(*args)


class SubprocessError(ToolError):
    """A subprocess command failed."""

    def __init__(
        self: SubprocessError,
        command: str,
        exit_code: int,
        stderr: str,
    ) -> None:
        """Initialize with command details.

        Args:
            command (str): The command string that failed.
            exit_code (int): Process exit code from the failed command.
            stderr (str): Captured standard error output.
        """
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(command, exit_code, stderr)
