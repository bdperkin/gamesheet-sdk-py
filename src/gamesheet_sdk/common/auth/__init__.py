# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Authentication flows and token management for GameSheet."""

from gamesheet_sdk.common.auth.credentials import resolve_email, resolve_password
from gamesheet_sdk.common.auth.firebase import extract_firebase_error
from gamesheet_sdk.common.auth.flow import LoginFlow
from gamesheet_sdk.common.auth.login import AdminLoginFlow, login
from gamesheet_sdk.common.auth.session import (
    AuthenticatedSession,
    BaseAuthenticatedSession,
    OnRefreshCallback,
)
from gamesheet_sdk.common.auth.tokens import (
    load_access_token,
    load_refresh_token,
    refresh_access_token,
    save_tokens,
)

__all__ = [
    "AdminLoginFlow",
    "AuthenticatedSession",
    "BaseAuthenticatedSession",
    "LoginFlow",
    "OnRefreshCallback",
    "extract_firebase_error",
    "load_access_token",
    "load_refresh_token",
    "login",
    "refresh_access_token",
    "resolve_email",
    "resolve_password",
    "save_tokens",
]
