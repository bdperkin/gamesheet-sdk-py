# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Authenticated session with automatic token refresh for the teams API gateway."""

from __future__ import annotations

from gamesheet_sdk.common.auth.session import BaseAuthenticatedSession
from gamesheet_sdk.teams.login import refresh_access_token


class TeamsAuthenticatedSession(BaseAuthenticatedSession):
    """Teams-pillar session that refreshes via the teams API gateway.

    Delegates to :func:`~gamesheet_sdk.teams.login.refresh_access_token`, which POSTs to the teams gateway's
    ``/api/auth/refresh`` endpoint.

    Example::

        from gamesheet_sdk.common.auth import (
            load_access_token,
            load_refresh_token,
            save_tokens,
        )
        from gamesheet_sdk.teams.session import TeamsAuthenticatedSession
        from gamesheet_sdk.common.config import Config

        config = Config(base_url="https://teams.gamesheet.app")
        with TeamsAuthenticatedSession(
            config,
            access_token=load_access_token(config),
            refresh_token=load_refresh_token(config),
            on_refresh=lambda tokens: save_tokens(config, **tokens),
        ) as s:
            resp = s.get("/api/seasons/team/123")
            print(resp.json())
    """

    def _do_refresh(self: TeamsAuthenticatedSession) -> dict[str, str]:
        """Refresh via the teams API gateway token endpoint.

        Returns:
            dict[str, str]: Refreshed token dictionary containing new access token.

        """
        return refresh_access_token(
            self._refresh_token,
            timeout=self.config.timeout,
        )
