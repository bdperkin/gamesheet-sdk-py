"""Shared constants used across domain modules."""

from __future__ import annotations

#: JSON:API content type for request/response headers
JSONAPI_CONTENT_TYPE = "application/vnd.api+json"

#: Standard headers for JSON:API requests
JSONAPI_HEADERS = {
    "Accept": JSONAPI_CONTENT_TYPE,
    "Content-Type": JSONAPI_CONTENT_TYPE,
}
