# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared Firebase Auth helpers.

Provides utilities for interpreting Firebase Authentication REST API responses.  Used by both the admin
browser-based login (:mod:`~gamesheet_sdk.common.auth.login`) and the teams HTTP-only login
(:mod:`~gamesheet_sdk.teams.login`).
"""

from __future__ import annotations

from typing import Any


def extract_firebase_error(body: dict[str, Any], status: int) -> str:
    """Extract a human-readable error string from a Firebase Auth response body.

    Firebase returns ``{"error": {"code": N, "message": "CODE_NAME", ...}}``; the ``message`` is a stable
    identifier like ``EMAIL_NOT_FOUND`` that we surface verbatim so callers can react programmatically.

    Args:
        body (dict[str, Any]): Parsed JSON body from the Firebase
            response.
        status (int): HTTP status code, used as the fallback message.

    Returns:
        str: The Firebase error code string, or ``"HTTP <status>"`` if
        the body does not contain a usable error message.
    """
    err = body.get("error")
    if isinstance(err, dict):
        message = err.get("message")
        if isinstance(message, str):
            return message
    return f"HTTP {status}"
