# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared HTTP session with retry-on-transient-error for CLI tools."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from shared.pip_config import PipConfig
from urllib3.util.retry import Retry

HTTP_RETRY_TOTAL = 3

HTTP_RETRY_BACKOFF_FACTOR = 1

HTTP_RETRY_STATUS_FORCELIST = (429, 500, 502, 503, 504)

_state: dict[str, requests.Session] = {}


def get_session(pip_config: PipConfig | None = None) -> requests.Session:
    """Return a shared requests Session with retry-on-transient-error.

    Args:
        pip_config (PipConfig | None): Optional pip configuration for
            SSL settings.

    Returns:
        requests.Session: A shared requests Session with retry-on-
        transient-error.
    """
    if "session" not in _state:
        retry = Retry(
            total=HTTP_RETRY_TOTAL,
            backoff_factor=HTTP_RETRY_BACKOFF_FACTOR,
            status_forcelist=HTTP_RETRY_STATUS_FORCELIST,
            allowed_methods={"GET", "HEAD"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        if pip_config and pip_config.cert:
            session.verify = pip_config.cert
        if pip_config and pip_config.client_cert:
            session.cert = pip_config.client_cert
        _state["session"] = session
    return _state["session"]
