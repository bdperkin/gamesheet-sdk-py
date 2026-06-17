"""Response payload builders for tests."""

from __future__ import annotations

from typing import Any


def jsonapi_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a JSON:API response with data array.

    Args:
        rows: List of JSON:API resource objects

    Returns:
        JSON:API response dict with {"data": [...]}

    Example:
        >>> jsonapi_payload([{"type": "associations", "id": "1", "attributes": {...}}])
        {'data': [{'type': 'associations', 'id': '1', 'attributes': {...}}]}
    """
    return {"data": rows}


def jsonapi_detail_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON:API response with single data object.

    Args:
        data: Single JSON:API resource object

    Returns:
        JSON:API response dict with {"data": {...}}

    Example:
        >>> jsonapi_detail_payload({"type": "associations", "id": "1", "attributes": {...}})
        {'data': {'type': 'associations', 'id': '1', 'attributes': {...}}}
    """
    return {"data": data}


def bff_payload(items: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    """Build a BFF API successful response.

    Args:
        items: List of items or single item for the response

    Returns:
        BFF response dict with {"status": "success", "data": ...}

    Example:
        >>> bff_payload([{"id": 1, "name": "Test"}])
        {'status': 'success', 'data': [{'id': 1, 'name': 'Test'}]}
    """
    return {"status": "success", "data": items}
