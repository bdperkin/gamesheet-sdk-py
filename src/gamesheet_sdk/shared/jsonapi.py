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
    {
        "relationships": {
            "parent": {
                "data": {"id": "123", "type": "associations"}
            }
        }
    }

    Args:
        item: The JSON:API resource object
        relationship_name: Name of the relationship to extract
        default: Default value if relationship not found

    Returns:
        The relationship ID or default value
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

    JSON:API structure:
    {
        "id": "123",
        "type": "leagues",
        "attributes": {"title": "NHL", ...},
        "relationships": {"association": {"data": {"id": "456"}}}
    }

    Result:
    {"id": "123", "title": "NHL", "association_id": "456", ...}

    Args:
        item: JSON:API resource object
        relationship_map: Maps relationship names to attribute keys.
            Example: {"association": "association_id"}

    Returns:
        Flattened dict with id + attributes + relationship IDs
    """
    result: dict[str, Any] = {"id": item["id"]}
    result.update(item.get("attributes", {}))

    if relationship_map:
        for rel_name, attr_key in relationship_map.items():
            result[attr_key] = extract_relationship_id(item, rel_name)

    return result
