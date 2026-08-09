# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Security and file permission utilities."""

from __future__ import annotations

import contextlib
import os
from pathlib import Path


def write_secure_text(path: Path, content: str) -> None:
    """Write text content to path with restricted POSIX file permissions (0600).

    Creates parent directories if necessary. On POSIX systems, sets directory permissions to 0700 and file
    permissions to 0600 so that sensitive credentials and session state are protected from other users.

    Args:
        path (Path): Target file path.
        content (str): Text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        with contextlib.suppress(OSError):
            path.parent.chmod(0o700)

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
