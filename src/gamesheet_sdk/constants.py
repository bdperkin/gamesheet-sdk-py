"""SDK-wide constants and configuration values.

This module defines all URL constants and endpoints used throughout the GameSheet SDK.

Constants
---------
DEFAULT_BASE_URL : str
    Default GameSheet web application base URL.
APP_GAMESHEET_COM : str
    Legacy GameSheet domain (used for browser storage).
BFF_API_BASE_URL : str
    Backend-for-Frontend API base URL.
CLOUDFLARE_IMAGE_DELIVERY_BASE : str
    Cloudflare image delivery CDN base URL with account hash.

Examples
--------
Using base URLs in session configuration:

.. code-block:: python

    from gamesheet_sdk.constants import DEFAULT_BASE_URL
    from gamesheet_sdk import Session

    session = Session(base_url=DEFAULT_BASE_URL)

Using BFF API endpoints:

.. code-block:: python

    from gamesheet_sdk.constants import BFF_API_BASE_URL

    games_url = f"{BFF_API_BASE_URL}/games-list/v1"

Using image delivery:

.. code-block:: python

    from gamesheet_sdk.constants import CLOUDFLARE_IMAGE_DELIVERY_BASE

    logo_url = f"{CLOUDFLARE_IMAGE_DELIVERY_BASE}/{image_id}"
"""

from __future__ import annotations

from typing import Final

# Default base URL for the GameSheet web application
DEFAULT_BASE_URL: Final[str] = "https://gamesheet.app"

# Legacy domain used for browser storage state
APP_GAMESHEET_COM: Final[str] = "https://app.gamesheet.com"

# Backend-for-Frontend (BFF) API base URL
BFF_API_BASE_URL: Final[str] = "https://bff-dashboard-api-awy26srzoa-nn.a.run.app"

# Cloudflare image delivery CDN base URL
CLOUDFLARE_IMAGE_DELIVERY_BASE: Final[str] = "https://imagedelivery.net/ErrQpIaCOWR-Tz51PhN1zA"
