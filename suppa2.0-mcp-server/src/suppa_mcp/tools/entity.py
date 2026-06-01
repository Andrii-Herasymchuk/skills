"""Entity, Schema, Fields, and Enums tools."""

import json
from typing import Optional

from suppa_mcp.http_client import (
    make_request, data_url, search_entity, insert_entity,
)
from suppa_mcp.utils import make_filter, json_response


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def list_entities(search: str = "") -> str:
    """List all entities (tables) available on the platform."""
    result = make_request("GET", "/api/core/schema")
    if isinstance(result, list) and search:
        search_lower = search.lower()
        result = [e for e in result if isinstance(e, dict) and (
            search_lower in str(e.get("name", "")).lower()
            or search_lower in str(e.get("title", "")).lower()
        )]
    return json_response(result)


def describe_entity(entity_name: str) -> str:
    """Get full schema of an entity including all fields, relations, and their types."""
    result = make_request("GET", f"/api/core/schema/{entity_name}")
    return json_response(result)


def search_records(
    entity_name: str,
    filters_json: str = "[]",
    fields_json: str = '{"id": true}',
    limit: int = 20,
    offset: int = 0,
    search: str = "",
    order_by: str = "createdAt:desc",
) -> str:
    """Search records of any entity with filters.
    filters_json: JSON array of filter objects [{field, value, comparator}].
    fields_json: JSON object specifying which fields to return.
    order_by: 'field:direction' (e.g. 'createdAt:desc').
    """
    filters = json.loads(filters_json)
    fields = json.loads(fields_json)

    order_parts = order_by.split(":")
    order = [{"field": order_parts[0], "order": order_parts[1] if len(order_parts) > 1 else "desc"}]

    results = search_entity(entity_name, filters, fields, limit, offset, order, search)
    return json_response(results)


def create_entity(
    name: str,
    title: str,
    title_field_name: str = "title",
) -> str:
    """Create a new entity (database table) on the platform."""
    body = {
        "name": name,
        "title": title,
        "titleFieldName": title_field_name,
    }
    result = make_request("POST", "/api/core/builder/create-entity", body)
    return json_response(result)


def add_field(
    entity_name: str,
    field_name: str,
    field_type: str,
    title: Optional[str] = None,
    required: bool = False,
    unique: bool = False,
    relation_entity: Optional[str] = None,
    enum_name: Optional[str] = None,
) -> str:
    """Add a field to an existing entity.
    field_type: text, integer, numeric, boolean, date, datetime, enum, relation, file, json, richtext, email, url, phone.
    For relation fields, provide relation_entity. For enum fields, provide enum_name.
    """
    field_def: dict = {
        "name": field_name,
        "type": field_type,
        "title": title or field_name,
        "required": required,
        "unique": unique,
    }
    if relation_entity:
        field_def["relationEntity"] = relation_entity
    if enum_name:
        field_def["enumName"] = enum_name

    body = {
        "entityName": entity_name,
        "fields": [field_def],
    }
    result = make_request("POST", "/api/core/builder/add-fields", body)
    return json_response(result)


def add_enum_values(
    enum_name: str,
    values: str,
) -> str:
    """Add values to an enum (lookup table). values: comma-separated list of values to add."""
    value_list = [v.strip() for v in values.split(",") if v.strip()]
    fields_list = [{"name": enum_name, "value": v} for v in value_list]

    body = {"fields": fields_list}
    result = make_request("POST", "/api/core/data-bulk/Enums", body)
    return json_response(result)


def list_field_types() -> str:
    """List all available field types for entity creation."""
    types = [
        {"type": "text", "description": "Single-line text string"},
        {"type": "integer", "description": "Whole number"},
        {"type": "numeric", "description": "Decimal number"},
        {"type": "boolean", "description": "True/false"},
        {"type": "date", "description": "Date only (no time)"},
        {"type": "datetime", "description": "Date and time"},
        {"type": "enum", "description": "Lookup value from Enums table (requires enum_name)"},
        {"type": "relation", "description": "Foreign key to another entity (requires relation_entity)"},
        {"type": "file", "description": "File attachment"},
        {"type": "json", "description": "JSON object/array"},
        {"type": "richtext", "description": "HTML rich text"},
        {"type": "email", "description": "Email address"},
        {"type": "url", "description": "URL"},
        {"type": "phone", "description": "Phone number"},
    ]
    return json_response(types)


def create_record(entity_name: str, fields_json: str) -> str:
    """Create a new record in any entity. fields_json: JSON object of field values."""
    fields = json.loads(fields_json)
    result = insert_entity(entity_name, [fields])
    return json_response(result[0] if result else None)


def update_record(entity_name: str, record_id: int, fields_json: str) -> str:
    """Update a record in any entity. fields_json: JSON object of field values to update."""
    from suppa_mcp.http_client import update_entity
    fields = json.loads(fields_json)
    result = update_entity(entity_name, record_id, fields)
    return json_response(result)


def delete_record(entity_name: str, record_id: int) -> str:
    """Delete a record from any entity."""
    from suppa_mcp.http_client import remove_entity
    result = remove_entity(entity_name, [make_filter("id", record_id)])
    return json_response(result)
