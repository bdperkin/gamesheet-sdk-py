"""Shared utilities for domain modules."""

from __future__ import annotations

from gamesheet_sdk.shared.constants import JSONAPI_CONTENT_TYPE, JSONAPI_HEADERS
from gamesheet_sdk.shared.http import check_bff_response_status, handle_response
from gamesheet_sdk.shared.jsonapi import extract_relationship_id, parse_jsonapi_resource

__all__ = [
    "JSONAPI_CONTENT_TYPE",
    "JSONAPI_HEADERS",
    "check_bff_response_status",
    "extract_relationship_id",
    "handle_response",
    "parse_jsonapi_resource",
]
