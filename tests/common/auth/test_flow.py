# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Tests for the LoginFlow protocol."""

from __future__ import annotations

from gamesheet_sdk.common.auth import LoginFlow
from gamesheet_sdk.common.auth.flow import LoginFlow as DirectLoginFlow


# pylint: disable-next=too-few-public-methods
class _ConformingFlow:
    """Minimal class that satisfies the LoginFlow protocol."""

    def authenticate(
        self: _ConformingFlow,
        # pylint: disable-next=unused-argument
        email: str | None = None,  # noqa: U100
        # pylint: disable-next=unused-argument
        password: str | None = None,  # noqa: U100
        *,
        # pylint: disable-next=unused-argument
        timeout: float | None = None,  # noqa: U100
    ) -> dict[str, str]:
        """Return stub tokens."""
        return {"access": "a", "refresh": "r"}


# pylint: disable-next=too-few-public-methods
class _NonConformingFlow:
    """Class that does NOT satisfy the LoginFlow protocol."""

    def login(self: _NonConformingFlow) -> None:
        """Do nothing."""


# pylint: disable-next=too-few-public-methods
class _BareFlow(LoginFlow):
    """Concrete subclass that inherits the Protocol's default body."""


def test_login_flow_is_importable_from_package() -> None:
    """LoginFlow is re-exported from the auth package."""
    assert LoginFlow is DirectLoginFlow


def test_conforming_class_is_instance() -> None:
    """A class with a matching authenticate() signature satisfies the protocol."""
    flow = _ConformingFlow()
    assert isinstance(flow, LoginFlow)


def test_non_conforming_class_is_not_instance() -> None:
    """A class without authenticate() does not satisfy the protocol."""
    obj = _NonConformingFlow()
    assert not isinstance(obj, LoginFlow)


def test_conforming_flow_returns_tokens() -> None:
    """Authenticate() returns a dict with 'access' and 'refresh' keys."""
    tokens = _ConformingFlow().authenticate(email="a@b.c", password="pw")
    assert "access" in tokens
    assert "refresh" in tokens


def test_protocol_default_body_returns_empty_dict() -> None:
    """The Protocol's default authenticate() body returns an empty dict."""
    result = _BareFlow().authenticate(email="a@b.c", password="pw")
    assert not result
