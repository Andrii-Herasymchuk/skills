"""Forms management tools — faithful port of the verified suppa-forms skill.

The Suppa ``Forms`` entity stores the layout in a JSON ``data`` field with the
keys ``formShema`` (list of field objects), ``formSettings`` (dict) and
``formModul`` (optional JS module string). The original platform spelling of
``formShema`` / ``formModul`` is intentional and must be preserved.
"""

import json
import uuid as _uuid
from typing import Optional

from suppa_mcp.http_client import (
    make_request, search_entity, select_entity, insert_entity,
)
from suppa_mcp.utils import make_filter, json_response


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENTITY_FORMS = "Forms"

FORM_LIST_FIELDS = {
    "id": True,
    "name": True,
    "type": True,
    "alias": True,
    "isPublic": True,
    "entity": {"id": True, "name": True},
    "lockedBy": {"id": True, "firstName": True, "lastName": True},
    "createdAt": True,
    "updatedAt": True,
}

FORM_DETAIL_FIELDS = {**FORM_LIST_FIELDS, "data": True}

DEFAULT_FORM_SETTINGS = {
    "id": 0,
    "size": "md",
    "type": "form",
    "method": "POST",
    "formKey": "",
    "endpoint": "",
    "entityId": "",
    "formType": "elementForm",
    "multilingual": False,
    "useTransaction": True,
    "showSubmitButton": False,
    "validateOnChange": True,
    "validateOnSubmit": True,
}

# Entity backend type -> (form field type, extra props)
ENTITY_TYPE_MAP = {
    "Integer": ("text", {"inputType": "number", "rules": ["numeric"]}),
    "Number": ("text", {"inputType": "number", "rules": ["numeric"]}),
    "Float": ("text", {"inputType": "number", "rules": ["numeric"]}),
    "Decimal": ("text", {"inputType": "number", "rules": ["numeric"]}),
    "String": ("text", {"inputType": "text"}),
    "Text": ("text", {"inputType": "text"}),
    "UUID": ("text", {"inputType": "text"}),
    "Boolean": ("toogle", {}),
    "DateTime": ("date", {"typeDate": "dateTime"}),
    "Timestamp": ("date", {"typeDate": "dateTime"}),
    "Date": ("date", {"typeDate": "date"}),
    "Time": ("date", {"typeDate": "time"}),
    "JSON": ("json", {}),
    "File": ("files", {}),
    "Files": ("files", {}),
    "attachment": ("files", {}),
    "icon": ("icon", {}),
}

# Form field types exposed by the platform.
FORM_FIELD_TYPES = [
    "text", "textarea", "richtext", "date", "checkbox", "radio", "select",
    "userSelect", "toogle", "files", "signature", "static", "button",
    "group", "flexGroup", "tabs", "steps", "widget", "icon", "json",
]


# ---------------------------------------------------------------------------
# Schema field generation
# ---------------------------------------------------------------------------

def _new_id() -> str:
    return str(_uuid.uuid4())


def make_field(field_type, name, label, columns=1, rows=1, **kwargs):
    """Generate a single form field schema object with required properties."""
    pos = kwargs.pop("position", None) or {"x": 1, "y": 1}
    field = {
        "id": _new_id(),
        "fieldId": kwargs.pop("field_id", name),
        "name": name,
        "type": field_type,
        "label": {"en": label} if isinstance(label, str) else label,
        "position": {"lg": pos, "sm": pos, "default": pos},
        "columns": {"lg": {"container": columns}},
        "rows": {"lg": {"container": rows}},
    }
    field.update(kwargs)
    return field


def auto_layout(fields, columns_number=1):
    """Apply grid auto-layout, positioning fields sequentially."""
    current_row = 1
    current_col = 1
    for field in fields:
        field_cols = 1
        if "columns" in field and "lg" in field["columns"]:
            field_cols = field["columns"]["lg"].get("container", 1)
        if current_col + field_cols - 1 > columns_number:
            current_row += 1
            current_col = 1
        pos = {"x": current_col, "y": current_row}
        field["position"] = {"lg": pos, "sm": pos, "default": pos}
        current_col += field_cols
        if current_col > columns_number:
            current_row += 1
            current_col = 1
    return fields


def convert_entity_prop(prop, entity_name):
    """Convert a backend entity property to a form schema field."""
    prop_type = prop.get("type", "text")
    prop_name = prop.get("name", "field")
    prop_title = prop.get("title", {})
    sub_type = prop.get("subType") or prop.get("sub_type") or ""
    relation_target = prop.get("relationTarget", "")
    representative = prop.get("representativeField", {})
    rep_field_name = (representative.get("name", "title")
                      if isinstance(representative, dict)
                      else str(representative or "title"))

    is_relation = prop_type in ("many-to-one", "one-to-many", "many-to-many", "relation")
    is_many = prop_type in ("many-to-many", "one-to-many")

    if is_relation:
        form_type = "userSelect" if relation_target == "Users" else "select"
    elif prop_type in ("enum", "custom_enum", "Enum"):
        form_type = "select"
    elif prop_type == "text":
        if sub_type == "html_text" or "html" in prop_name.lower():
            form_type = "richtext"
        elif sub_type == "icon":
            form_type = "icon"
        elif sub_type == "ucid_prefix":
            form_type = "ucidPrefix"
        else:
            form_type = "text"
    elif prop_type in ("timestamp", "Timestamp", "DateTime", "date", "Date", "time", "Time"):
        form_type = "date"
    elif prop_type in ENTITY_TYPE_MAP:
        form_type = ENTITY_TYPE_MAP[prop_type][0]
    elif prop_type.lower() in ("integer", "number", "float", "decimal"):
        form_type = "text"
    elif prop_type.lower() == "boolean":
        form_type = "toogle"
    elif prop_type.lower() in ("json",):
        form_type = "json"
    elif prop_type.lower() in ("file", "files", "attachment"):
        form_type = "files"
    else:
        form_type = "text"

    if isinstance(prop_title, dict) and prop_title:
        label = prop_title
    elif isinstance(prop_title, str) and prop_title:
        label = {"en": prop_title}
    else:
        label = {"en": prop_name}

    field = make_field(form_type, prop_name, label, field_id=prop_name)

    if form_type == "text" and prop_type in ENTITY_TYPE_MAP:
        field.update(ENTITY_TYPE_MAP[prop_type][1])
    elif form_type == "text" and prop_type.lower() in ("integer", "number", "float", "decimal"):
        field["inputType"] = "number"
        field["rules"] = field.get("rules", []) + ["numeric"]
    elif form_type == "date":
        if prop_type in ("timestamp", "Timestamp", "DateTime") or sub_type in ("timestamp", "DateTime"):
            field["typeDate"] = "dateTime"
        elif prop_type in ("time", "Time") or sub_type in ("time", "Time"):
            field["typeDate"] = "time"
        else:
            field["typeDate"] = "date"
    elif form_type == "userSelect":
        field["items"] = {
            "targetEntityName": relation_target or "Users",
            "targetValueField": "id",
            "targetLabelField": rep_field_name or "fullName",
        }
        field["options"] = {"multiple": is_many}
        field["additionalRequestFields"] = ["firstName", "lastName", "fullName", "avatar", "position"]
    elif form_type == "select" and is_relation:
        field["items"] = {
            "targetEntityName": relation_target,
            "targetValueField": "id",
            "targetLabelField": rep_field_name or "title",
        }
        field["options"] = {"valueIsObject": True, "usePreLoadItemsFunction": True, "multiple": is_many}
    elif form_type == "select" and prop_type in ("enum", "custom_enum", "Enum"):
        custom_enum = prop.get("custom_enum", {})
        field["items"] = {
            "enum_id": custom_enum.get("enum_id", f"{entity_name}.{prop_name}"),
            "targetType": "internal",
            "targetEntityName": "Enums",
            "targetValueField": "id",
            "targetLabelField": "title",
        }
        field["options"] = {"valueIsObject": True, "multiple": prop.get("isArray", False)}
    elif form_type == "files":
        field["options"] = {"multiple": prop.get("isArray", True)}

    rules = field.get("rules", [])
    if prop.get("required") == "always" or prop.get("notNull"):
        if "required" not in rules:
            rules.append("required")
    if sub_type == "email":
        rules.append("email")
    max_length = prop.get("maxLength") or prop.get("max_length")
    if max_length:
        rules.append(f"maxLength:{max_length}")
    precision = prop.get("decimalPlaces") or prop.get("precision")
    if precision:
        rules.append(f"decimalPlaces:{precision}")
    if prop.get("isOnlyPositive") or prop.get("only_positive"):
        rules.append("isOnlyPositive")
    if rules:
        field["rules"] = rules

    return field


def _get_entity_schema(entity_name: str):
    return make_request("GET", f"/api/core/schema/{entity_name}")


def _generate_schema_from_entity(entity_name, field_names=None, columns_number=1):
    """Fetch an entity schema and build (schema_list, settings_dict)."""
    schema_data = _get_entity_schema(entity_name)
    if not schema_data:
        return None, None

    props = []
    if isinstance(schema_data, dict):
        props = schema_data.get("properties", schema_data.get("fields", []))
    elif isinstance(schema_data, list):
        props = schema_data
    if isinstance(props, dict):
        props = [{**v, "name": v.get("name", k)} for k, v in props.items()]

    if field_names:
        prop_map = {p.get("name"): p for p in props}
        props = [prop_map[n] for n in field_names if n in prop_map]
    else:
        props = [p for p in props
                 if not p.get("system", False) and p.get("initiator") == "client"]

    fields = []
    for prop in props:
        field = convert_entity_prop(prop, entity_name)
        ftype = field.get("type", "")
        if columns_number > 1 and ftype in (
            "richtext", "textarea", "group", "flexGroup", "tabs", "steps", "table", "files"):
            field["columns"] = {"lg": {"container": columns_number}}
        else:
            field["columns"] = {"lg": {"container": 1}}
        fields.append(field)

    fields = auto_layout(fields, columns_number)
    settings = dict(DEFAULT_FORM_SETTINGS, columnsNumber=columns_number)
    return fields, settings


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def list_forms(
    entity_name: Optional[str] = None,
    form_type: Optional[str] = None,
    limit: int = 50,
) -> str:
    """List forms. Optionally filter by entity name or form type (e.g. 'elementForm')."""
    filters = []
    if entity_name:
        filters.append(make_filter("entity.name", entity_name))
    if form_type:
        filters.append(make_filter("type", form_type))
    results = search_entity(ENTITY_FORMS, filters, FORM_LIST_FIELDS, limit)
    return json_response(results)


def get_form(form_id: int) -> str:
    """Get a form by ID including its full schema (data.formShema) and settings."""
    result = select_entity(ENTITY_FORMS, [make_filter("id", form_id)], FORM_DETAIL_FIELDS)
    return json_response(result)


def create_form(
    name: str,
    form_type: str = "elementForm",
    entity_name: Optional[str] = None,
    alias: Optional[str] = None,
    is_public: bool = False,
    schema_json: Optional[str] = None,
    settings_json: Optional[str] = None,
    generate_from_entity: bool = False,
    fields: Optional[str] = None,
    columns: int = 1,
    module_code: Optional[str] = None,
) -> str:
    """Create a new form.

    Provide a layout in one of three ways:
      - schema_json: a JSON array of field objects (or an object with 'formShema').
      - generate_from_entity=True with entity_name: auto-build fields from the
        entity schema (optionally limit to comma-separated 'fields').
      - neither: an empty form.
    settings_json overrides default form settings. module_code is optional JS.
    """
    schema: list = []
    settings = dict(DEFAULT_FORM_SETTINGS)

    if schema_json:
        parsed = json.loads(schema_json)
        if isinstance(parsed, dict):
            schema = parsed.get("formShema", parsed.get("schema", []))
            if "formSettings" in parsed:
                settings.update(parsed["formSettings"])
        elif isinstance(parsed, list):
            schema = parsed
    elif generate_from_entity and entity_name:
        field_names = [f.strip() for f in fields.split(",")] if fields else None
        gen_schema, gen_settings = _generate_schema_from_entity(entity_name, field_names, columns)
        if gen_schema is None:
            return json_response({"error": f"Entity '{entity_name}' not found"})
        schema = gen_schema
        settings.update(gen_settings)

    if settings_json:
        settings.update(json.loads(settings_json))
    settings["columnsNumber"] = columns
    settings["formType"] = form_type
    if entity_name:
        settings["entityId"] = entity_name

    form_view: dict = {
        "name": name,
        "type": form_type,
        "isPublic": is_public,
        "data": {
            "formShema": schema,
            "formSettings": settings,
            "formModul": module_code,
        },
    }
    if alias:
        form_view["alias"] = alias
    if entity_name:
        ent_schema = _get_entity_schema(entity_name)
        if isinstance(ent_schema, dict) and ent_schema.get("id"):
            form_view["entity"] = {"id": int(ent_schema["id"])}

    result = insert_entity(ENTITY_FORMS, [form_view],
                          returning={"id": True, "name": True, "type": True})
    return json_response(result[0] if result else None)


def update_form(
    form_id: int,
    name: Optional[str] = None,
    schema_json: Optional[str] = None,
    settings_json: Optional[str] = None,
    module_code: Optional[str] = None,
) -> str:
    """Update a form's name, schema (data.formShema), settings, or module code."""
    existing = select_entity(ENTITY_FORMS, [make_filter("id", form_id)], FORM_DETAIL_FIELDS)
    if not existing:
        return json_response({"error": f"Form {form_id} not found"})

    data = dict(existing.get("data") or {})
    changed = False
    update_fields: dict = {}

    if name is not None:
        update_fields["name"] = name

    if schema_json is not None:
        parsed = json.loads(schema_json)
        if isinstance(parsed, dict):
            data["formShema"] = parsed.get("formShema", parsed.get("schema", []))
            if "formSettings" in parsed:
                data["formSettings"] = parsed["formSettings"]
        elif isinstance(parsed, list):
            data["formShema"] = parsed
        changed = True

    if settings_json is not None:
        current = dict(data.get("formSettings") or {})
        current.update(json.loads(settings_json))
        data["formSettings"] = current
        changed = True

    if module_code is not None:
        data["formModul"] = module_code
        changed = True

    if changed:
        update_fields["data"] = data

    if not update_fields:
        return json_response({"error": "No fields to update"})

    result = make_request("POST", f"/api/core/data/{ENTITY_FORMS}/update/{form_id}",
                         {"fields": update_fields})
    return json_response(result)


def generate_form_schema(
    entity_name: str,
    columns: int = 1,
    fields: Optional[str] = None,
) -> str:
    """Generate a form schema (formShema + formSettings) from an entity's fields.

    'fields': optional comma-separated list to limit/order the included fields.
    Returns a JSON object you can pass to create_form via schema_json.
    """
    field_names = [f.strip() for f in fields.split(",")] if fields else None
    schema, settings = _generate_schema_from_entity(entity_name, field_names, columns)
    if schema is None:
        return json_response({"error": f"Entity '{entity_name}' not found"})
    return json_response({"formShema": schema, "formSettings": settings})


def add_field_to_form(
    form_id: int,
    field_name: str,
    field_type: str = "text",
    label: Optional[str] = None,
    required: bool = False,
    extra_json: Optional[str] = None,
) -> str:
    """Append a single field to an existing form's schema (data.formShema)."""
    existing = select_entity(ENTITY_FORMS, [make_filter("id", form_id)], FORM_DETAIL_FIELDS)
    if not existing:
        return json_response({"error": f"Form {form_id} not found"})

    data = dict(existing.get("data") or {})
    schema = list(data.get("formShema") or [])
    settings = data.get("formSettings") or {}
    columns_number = settings.get("columnsNumber", 1)

    extra = json.loads(extra_json) if extra_json else {}
    rules = extra.pop("rules", [])
    if required and "required" not in rules:
        rules.append("required")
    if rules:
        extra["rules"] = rules

    new_field = make_field(field_type, field_name, label or field_name,
                          field_id=field_name, **extra)
    schema.append(new_field)
    data["formShema"] = auto_layout(schema, columns_number)

    result = make_request("POST", f"/api/core/data/{ENTITY_FORMS}/update/{form_id}",
                         {"fields": {"data": data}})
    return json_response(result)


def list_form_field_types() -> str:
    """List the available form field types."""
    return json_response(FORM_FIELD_TYPES)
