# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""Shared utilities for domain modules."""

from __future__ import annotations

from gamesheet_sdk.common.shared.constants import JSONAPI_CONTENT_TYPE, JSONAPI_HEADERS
from gamesheet_sdk.common.shared.gamesheet_http import (
    check_bff_response_status,
    handle_response,
)
from gamesheet_sdk.common.shared.image_upload import upload_image
from gamesheet_sdk.common.shared.jsonapi import (
    extract_relationship_id,
    parse_jsonapi_resource,
)

__all__ = [
    "JSONAPI_CONTENT_TYPE",
    "JSONAPI_HEADERS",
    "check_bff_response_status",
    "extract_relationship_id",
    "handle_response",
    "parse_jsonapi_resource",
    "upload_image",
]
