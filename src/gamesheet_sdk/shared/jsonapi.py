# Copyright (c) 2026 bdperkin
# SPDX-License-Identifier: MIT

"""JSON:API parsing utilities."""

from __future__ import annotations

from typing import Any


def extract_relationship_id(
    item: dict[str, Any],
    relationship_name: str,
    default: str = "",
) -> str:
    """Safely extract ID from JSON:API relationship.

    JSON:API relationships follow the structure:

    .. code-block:: json

        {
            "relationships": {
                "parent": {
                    "data": {"id": "123", "type": "associations"}
                }
            }
        }

    :param item: The JSON:API resource object.
    :type item: dict[str, Any]
    :param relationship_name: Name of the relationship to extract.
    :type relationship_name: str
    :param default: Default value if relationship not found.
    :type default: str
    :returns: The relationship ID or default value.
    :rtype: str
    """
    result: Any = item.get("relationships", {}).get(relationship_name, {}).get("data", {}).get("id", default)
    return str(result) if result else default


def parse_jsonapi_resource(
    item: dict[str, Any],
    relationship_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Parse a JSON:API resource into a flat dictionary.

    Flattens a JSON:API resource object into a simple dict by merging
    the id, attributes, and optionally extracting relationship IDs.

    **JSON:API structure:**

    .. code-block:: json

        {
            "id": "123",
            "type": "leagues",
            "attributes": {"title": "NHL", ...},
            "relationships": {"association": {"data": {"id": "456"}}}
        }

    **Result:**

    .. code-block:: python

        {"id": "123", "title": "NHL", "association_id": "456"}

    :param item: JSON:API resource object.
    :type item: dict[str, Any]
    :param relationship_map: Maps relationship names to attribute keys. Example: ``{"association":
        "association_id"}``.
    :type relationship_map: dict[str, str] | None
    :returns: Flattened dict with id + attributes + relationship IDs.
    :rtype: dict[str, Any]
    """
    result: dict[str, Any] = {"id": item["id"]}
    result.update(item.get("attributes", {}))
    if relationship_map:
        for rel_name, attr_key in relationship_map.items():
            result[attr_key] = extract_relationship_id(item, rel_name)
    return result


def build_invitation_code_lookup(body: dict[str, Any]) -> dict[str, str]:
    """Build invitation code lookup from JSON:API included resources.

    Parses the included section of a JSON:API response to extract invitation codes keyed by invitation ID.

    :param body: The JSON:API response body containing included resources.
    :type body: dict[str, Any]
    :returns: Dictionary mapping invitation IDs to invitation codes.
    :rtype: dict[str, str]
    """
    invitation_codes: dict[str, str] = {}
    for item in body.get("included", []):
        if item.get("type") == "invitations":
            invitation_id = item.get("id")
            code = item.get("attributes", {}).get("code")
            if invitation_id and code:
                invitation_codes[invitation_id] = code
    return invitation_codes


def get_invitation_code_from_relationship(
    item: dict[str, Any],
    invitation_codes: dict[str, str],
) -> str | None:
    """Extract invitation code from team's invitation relationship.

    The invitations relationship can be either a single object or an array of objects.

    :param item: The JSON:API team resource object.
    :type item: dict[str, Any]
    :param invitation_codes: Lookup dictionary from invitation IDs to codes.
    :type invitation_codes: dict[str, str]
    :returns: The invitation code if found, otherwise None.
    :rtype: str | None
    """
    inv_rel = item.get("relationships", {}).get("invitations", {}).get("data")
    if inv_rel:
        # invitations relationship can be single object or array
        inv_id = inv_rel[0]["id"] if isinstance(inv_rel, list) else inv_rel.get("id")
        if inv_id and inv_id in invitation_codes:
            return invitation_codes[inv_id]
    return None
