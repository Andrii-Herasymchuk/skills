#!/usr/bin/env python3
"""
Suppa Forms API Client (new platform: modern.suppa.me)

REST-style API rooted at /api/core/data/{Entity}/{action} using integer IDs and
camelCase field names. Auth: Bearer token via Authorization header (API key OR
JWT extracted from accessToken cookie both work).

No external dependencies — Python stdlib only.

Quick start:
    $env:SUPPA_API_KEY = "<token>"
    python suppa_forms.py get-me
    python suppa_forms.py list-forms --entity Tasks
    python suppa_forms.py create-form --entity Tasks --type elementForm --name "My Form" --fields "title,assignedTo"

Commands:
    get-me            Current authenticated user
    list-forms        List forms (by entity/type)
    get-form          Get a single form by integer id
    create-form       Create a new form
    update-form       Update an existing form
    lock-form         Lock a form for editing
    unlock-form       Unlock a form
    generate-schema   Generate form schema from entity fields (output only)
    add-field         Add a field to an existing form's schema
    list-field-types  Show all available form field types
    list-templates    Show available form templates
    validate-schema   Validate a schema JSON file
"""

import argparse
import json
import os
import sys
import uuid as _uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("SUPPA_BASE_URL", "https://modern.suppa.me")
DEFAULT_LANG = os.environ.get("SUPPA_LANG", "en")
DEFAULT_TZ = os.environ.get("SUPPA_TZ", "Europe/Kyiv")

# Entity names used in URL paths (PascalCase, plural).
ENTITY_FORMS = "Forms"
ENTITY_USERS = "Users"

# Default form configuration
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

# Entity type → form field type mapping
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


# ---------------------------------------------------------------------------
# HTTP transport
# ---------------------------------------------------------------------------

def _get_token():
    tok = os.environ.get("SUPPA_API_KEY") or os.environ.get("SUPPA_TOKEN")
    if not tok:
        sys.stderr.write(
            "ERROR: set SUPPA_API_KEY env var (Bearer token).\n"
            "  PowerShell:  $env:SUPPA_API_KEY = '<token>'\n"
            "  bash:        export SUPPA_API_KEY='<token>'\n"
        )
        sys.exit(2)
    return tok


def make_request(method, path, body=None, token=None):
    """Low-level HTTP. Returns parsed JSON (or raw text if not JSON)."""
    url = path if path.startswith("http") else BASE_URL.rstrip("/") + path
    headers = {
        "Authorization": "Bearer " + (token or _get_token()),
        "Accept": "application/json, text/plain, */*",
        "x-current-language": DEFAULT_LANG,
        "x-timezone": DEFAULT_TZ,
        "x-view-mode": "view",
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json; charset=UTF-8"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = Request(url, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        sys.stderr.write(
            "HTTP {0} {1}\n{2}\nResponse:\n{3}\n".format(
                e.code, e.reason, url, raw[:4000]
            )
        )
        sys.exit(1)
    except URLError as e:
        sys.stderr.write("Network error calling {0}: {1}\n".format(url, e))
        sys.exit(1)

    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return raw


# ---------------------------------------------------------------------------
# Generic data-API helpers
# ---------------------------------------------------------------------------

def _data_url(entity, action):
    return "/api/core/data/{0}/{1}".format(entity, action)


def _filter(field, value, comparator="=", *, disabled=False, filter_id=None):
    return {
        "id": filter_id or str(_uuid.uuid4())[:8],
        "field": field,
        "value": value,
        "disabled": bool(disabled),
        "comparator": comparator,
    }


def _normalize_filters(filters):
    out = []
    for f in filters:
        if isinstance(f, tuple):
            field, value, *rest = f
            comp = rest[0] if rest else "="
            out.append(_filter(field, value, comp))
        elif isinstance(f, dict):
            f = dict(f)
            f.setdefault("id", str(_uuid.uuid4())[:8])
            f.setdefault("disabled", False)
            f.setdefault("comparator", "=")
            out.append(f)
        else:
            raise ValueError("filter must be tuple or dict, got {0!r}".format(f))
    return out


def search_entity(entity, *, filters=None, fields=None, limit=100, offset=0,
                  order_by=None, search_value="", token=None):
    """POST /api/core/data/{entity}/search"""
    body = {
        "conditions": {
            "operator": "and",
            "filters": _normalize_filters(filters or []),
        },
        "fields": fields or {"id": True},
        "limit": limit,
        "offset": offset,
        "orderBy": (order_by if order_by is not None
                    else [{"field": "id", "order": "desc"}]),
        "searchValue": search_value,
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    return make_request("POST", _data_url(entity, "search"), body, token=token)


def select_entity(entity, *, filters, fields=None, token=None):
    """POST /api/core/data/{entity}/select — single-record fetch."""
    body = {
        "conditions": {
            "operator": "and",
            "filters": _normalize_filters(filters),
        },
        "fields": fields or {"id": True},
        "limit": 1,
        "offset": 0,
        "orderBy": [{"field": "id", "order": "asc"}],
        "searchValue": "",
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    res = make_request("POST", _data_url(entity, "select"), body, token=token)
    if isinstance(res, list):
        return res[0] if res else None
    if isinstance(res, dict):
        for key in ("data", "rows", "items", "result"):
            arr = res.get(key)
            if isinstance(arr, list):
                return arr[0] if arr else None
    return res


def insert_entity(entity, fields_list, *, returning=None, token=None):
    """POST /api/core/data/{entity}/insert"""
    body = {
        "fields": fields_list if isinstance(fields_list, list) else [fields_list],
    }
    if returning is not None:
        body["returning"] = returning
    return make_request("POST", _data_url(entity, "insert"), body, token=token)


def update_entity(entity, *, filters, fields, token=None):
    """POST /api/core/data/{entity}/update (with conditions)."""
    body = {
        "fields": fields if isinstance(fields, dict) else fields[0],
        "conditions": {
            "operator": "and",
            "filters": _normalize_filters(filters),
        },
    }
    return make_request("POST", _data_url(entity, "update"), body, token=token)


# ---------------------------------------------------------------------------
# Forms domain — CRUD
# ---------------------------------------------------------------------------

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

FORM_DETAIL_FIELDS = dict(FORM_LIST_FIELDS, **{
    "data": True,
})


def list_forms(entity_name=None, form_type=None, limit=50):
    """List forms, optionally filtered."""
    filters = []
    if entity_name:
        filters.append(("entity.name", entity_name, "="))
    if form_type:
        filters.append(("type", form_type, "="))
    return search_entity(ENTITY_FORMS, filters=filters, fields=FORM_LIST_FIELDS, limit=limit)


def get_form(form_id):
    """Get a single form by ID with full data."""
    return select_entity(ENTITY_FORMS, filters=[("id", int(form_id), "=")], fields=FORM_DETAIL_FIELDS)


def create_form(form_view):
    """Insert a new form. Returns result from API."""
    res = insert_entity(ENTITY_FORMS, form_view, returning={"id": True, "name": True, "type": True})
    if isinstance(res, list) and res:
        return res[0]
    return res


def update_form_by_id(form_id, update_data):
    """Update a form by ID using /api/core/data/Forms/update/{id}."""
    body = {"fields": update_data}
    return make_request("POST", "/api/core/data/{0}/update/{1}".format(ENTITY_FORMS, int(form_id)), body)


def get_entity_schema(entity_name):
    """GET /api/core/schema/{EntityName} — returns entity field definitions."""
    return make_request("GET", "/api/core/schema/{0}".format(entity_name))


# ---------------------------------------------------------------------------
# Field generation helpers
# ---------------------------------------------------------------------------

def _new_id():
    return str(_uuid.uuid4())


def make_field(field_type, name, label, position=None, columns=1, rows=1, **kwargs):
    """Generate a single TField schema object with all required properties.

    Position uses 3 breakpoints: lg (desktop), sm (mobile), default (fallback).
    Columns/rows use lg breakpoint with container key for grid span.
    Labels use ISO 639-1 codes: en, uk, pl.
    """
    pos = position or {"x": 1, "y": 1}
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


def make_text_field(name, label, input_type="text", rules=None, **kwargs):
    return make_field("text", name, label, inputType=input_type, rules=rules or [], **kwargs)


def make_number_field(name, label, **kwargs):
    kwargs.setdefault("rules", ["numeric"])
    return make_field("text", name, label, inputType="number", **kwargs)


def make_email_field(name, label, **kwargs):
    kwargs.setdefault("rules", ["email"])
    return make_field("text", name, label, inputType="email", **kwargs)


def make_phone_field(name, label, **kwargs):
    kwargs.setdefault("rules", ["phone"])
    return make_field("text", name, label, inputType="phone", **kwargs)


def make_password_field(name, label, **kwargs):
    return make_field("text", name, label, inputType="password", **kwargs)


def make_date_field(name, label, date_type="date", **kwargs):
    return make_field("date", name, label, typeDate=date_type, **kwargs)


def make_textarea_field(name, label, **kwargs):
    return make_field("textarea", name, label, **kwargs)


def make_richtext_field(name, label, **kwargs):
    return make_field("richtext", name, label, **kwargs)


def make_checkbox_field(name, label, mode="checkbox", **kwargs):
    return make_field("checkbox", name, label, mode=mode, **kwargs)


def make_radio_field(name, label, **kwargs):
    return make_field("radio", name, label, mode="radio", **kwargs)


def make_select_field(name, label, items=None, options=None, **kwargs):
    return make_field("select", name, label, items=items or {}, options=options or {}, **kwargs)


def make_user_select_field(name, label, multiple=False, **kwargs):
    return make_field(
        "userSelect", name, label,
        items={"targetEntityName": "Users", "targetValueField": "id", "targetLabelField": "fullName"},
        options={"multiple": multiple},
        additionalRequestFields=["firstName", "lastName", "fullName", "avatar", "position"],
        **kwargs,
    )


def make_toggle_field(name, label, **kwargs):
    return make_field("toogle", name, label, **kwargs)


def make_files_field(name, label, multiple=True, **kwargs):
    return make_field("files", name, label, options={"multiple": multiple}, **kwargs)


def make_signature_field(name, label, **kwargs):
    return make_field("signature", name, label, **kwargs)


def make_static_field(name, tag="text", content="", **kwargs):
    return make_field("static", name, content, tag=tag, content=content, submit=False, **kwargs)


def make_button_field(name, label, color="primary", variant="elevated", icon=None, **kwargs):
    extra = {"color": color, "variant": variant, "submit": False, "rounded": "md", "size": "default", "fontWeight": "500"}
    if icon:
        extra["icon"] = icon
    return make_field("button", name, label, buttonLabel={"en": label} if isinstance(label, str) else label, **extra, **kwargs)


def make_group_field(name, schema=None, columns_number=1, **kwargs):
    return make_field("group", name, "", schema=schema or [], columnsNumber=columns_number, **kwargs)


def make_flex_group_field(name, schema=None, justify="start", align="center", **kwargs):
    return make_field("flexGroup", name, "", schema=schema or [], justifyContent=justify, alignItems=align, **kwargs)


def make_tabs_field(name, schema=None, **kwargs):
    return make_field("tabs", name, "", schema=schema or [], **kwargs)


def make_steps_field(name, schema=None, **kwargs):
    return make_field("steps", name, "", schema=schema or [], **kwargs)


def make_chart_field(name, chart_type, label="", **kwargs):
    return make_field("widget", name, label, widgetName="BaseChart", props={"config": {"type": chart_type}}, **kwargs)


# ---------------------------------------------------------------------------
# Auto-layout algorithm
# ---------------------------------------------------------------------------

def auto_layout(fields, columns_number=1):
    """Apply grid auto-layout: position fields sequentially in the grid.

    Uses CSS Grid positioning: x = column start (1-indexed), container = colspan.
    For columnsNumber=N: x ranges from 1..N, container ranges from 1..N.
    """
    current_row = 1
    current_col = 1

    for field in fields:
        field_cols = 1
        if "columns" in field and "lg" in field["columns"]:
            field_cols = field["columns"]["lg"].get("container", 1)

        # Wrap to next row if field won't fit
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


# ---------------------------------------------------------------------------
# Entity field → form field conversion
# ---------------------------------------------------------------------------

def convert_entity_prop(prop, entity_name):
    """Convert a backend entity property object to a form schema field.

    Real schema API format:
      - type: "many-to-one"|"one-to-many"|"many-to-many"|"text"|"timestamp"|"enum"|...
      - relationTarget: "Users" (string, at root level)
      - representativeField: {id, name, type} (object)
      - subType: "timestamp"|"html_text"|"icon"|"ucid_prefix"|null
      - title: {en: "...", id: N, key: "...", name: "..."}
    """
    prop_type = prop.get("type", "text")
    prop_name = prop.get("name", "field")
    prop_title = prop.get("title", {})
    sub_type = prop.get("subType") or prop.get("sub_type") or ""
    relation_target = prop.get("relationTarget", "")
    representative = prop.get("representativeField", {})
    rep_field_name = representative.get("name", "title") if isinstance(representative, dict) else str(representative or "title")

    # Determine if relation type
    is_relation = prop_type in ("many-to-one", "one-to-many", "many-to-many", "relation")
    is_many = prop_type in ("many-to-many", "one-to-many")

    # Determine form field type
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
    elif prop_type in ("timestamp", "Timestamp", "DateTime"):
        form_type = "date"
    elif prop_type in ("date", "Date"):
        form_type = "date"
    elif prop_type in ("time", "Time"):
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

    # Build label
    if isinstance(prop_title, dict) and prop_title:
        label = prop_title
    elif isinstance(prop_title, str) and prop_title:
        label = {"en": prop_title}
    else:
        label = {"en": prop_name}

    # Base field
    field = make_field(form_type, prop_name, label, field_id=prop_name)

    # Type-specific config
    if form_type == "text" and prop_type in ENTITY_TYPE_MAP:
        extra = ENTITY_TYPE_MAP[prop_type][1]
        field.update(extra)
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
        field["options"] = {
            "valueIsObject": True,
            "usePreLoadItemsFunction": True,
            "multiple": is_many,
        }
    elif form_type == "select" and prop_type in ("enum", "custom_enum", "Enum"):
        custom_enum = prop.get("custom_enum", {})
        field["items"] = {
            "enum_id": custom_enum.get("enum_id", "{0}.{1}".format(entity_name, prop_name)),
            "targetType": "internal",
            "targetEntityName": "Enums",
            "targetValueField": "id",
            "targetLabelField": "title",
        }
        field["options"] = {"valueIsObject": True, "multiple": prop.get("isArray", False)}
    elif form_type == "files":
        field["options"] = {"multiple": prop.get("isArray", True)}

    # Validation rules
    rules = field.get("rules", [])
    if prop.get("required") == "always" or prop.get("notNull"):
        if "required" not in rules:
            rules.append("required")
    if sub_type == "email":
        rules.append("email")
    max_length = prop.get("maxLength") or prop.get("max_length")
    if max_length:
        rules.append("maxLength:{0}".format(max_length))
    precision = prop.get("decimalPlaces") or prop.get("precision")
    if precision:
        rules.append("decimalPlaces:{0}".format(precision))
    if prop.get("isOnlyPositive") or prop.get("only_positive"):
        rules.append("isOnlyPositive")
    if rules:
        field["rules"] = rules

    return field


# ---------------------------------------------------------------------------
# Schema generation from entity
# ---------------------------------------------------------------------------

def generate_schema_from_entity(entity_name, field_names=None, columns_number=1):
    """Fetch entity schema and generate form fields.

    Returns: (schema: list, settings: dict)
    """
    schema_data = get_entity_schema(entity_name)
    if not schema_data:
        sys.stderr.write("ERROR: Entity '{0}' not found or empty schema.\n".format(entity_name))
        sys.exit(1)

    # Extract properties
    props = []
    if isinstance(schema_data, dict):
        props = schema_data.get("properties", schema_data.get("fields", []))
    elif isinstance(schema_data, list):
        props = schema_data

    # Filter and preserve requested order
    if field_names:
        # Build a lookup dict for quick access
        prop_map = {p.get("name"): p for p in props}
        props = [prop_map[n] for n in field_names if n in prop_map]
    else:
        # Exclude system/internal fields
        props = [p for p in props if not p.get("system", False) and p.get("initiator") == "client"]

    # Convert
    fields = []
    for prop in props:
        field = convert_entity_prop(prop, entity_name)
        # Default column span based on field type
        if columns_number > 1:
            ftype = field.get("type", "")
            if ftype in ("richtext", "textarea", "group", "flexGroup", "tabs", "steps", "table", "files"):
                field["columns"] = {"lg": {"container": columns_number}}
            else:
                field["columns"] = {"lg": {"container": 1}}
        else:
            field["columns"] = {"lg": {"container": 1}}
        fields.append(field)

    fields = auto_layout(fields, columns_number)
    settings = dict(DEFAULT_FORM_SETTINGS, columnsNumber=columns_number)
    return fields, settings


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def validate_schema(schema):
    """Validate a form schema. Returns list of error strings."""
    errors = []
    if not isinstance(schema, list):
        return ["Schema must be a JSON array of fields."]

    names = set()
    ids = set()

    def check_fields(fields, path=""):
        for i, field in enumerate(fields):
            fpath = "{0}[{1}]".format(path, i)
            if not isinstance(field, dict):
                errors.append("{0}: field must be an object".format(fpath))
                continue
            if "id" not in field:
                errors.append("{0}: missing 'id'".format(fpath))
            elif field["id"] in ids:
                errors.append("{0}: duplicate id '{1}'".format(fpath, field["id"]))
            else:
                ids.add(field["id"])
            if "name" not in field:
                errors.append("{0}: missing 'name'".format(fpath))
            elif field["name"] in names:
                errors.append("{0}: duplicate name '{1}'".format(fpath, field["name"]))
            else:
                names.add(field["name"])
            if "type" not in field:
                errors.append("{0}: missing 'type'".format(fpath))
            if "schema" in field and isinstance(field["schema"], list):
                check_fields(field["schema"], "{0}.schema".format(fpath))

    check_fields(schema)
    return errors


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    "entity-basic": {
        "description": "Basic entity form: title + description + submit button",
        "columns": 1,
        "generate": lambda: [
            make_text_field("title", "Title", rules=["required"]),
            make_richtext_field("description", "Description"),
            make_button_field("submitBtn", "Save", color="primary"),
        ],
    },
    "contact-form": {
        "description": "Public contact form: name, email, phone, message",
        "columns": 2,
        "generate": lambda: [
            make_text_field("firstName", "First Name", rules=["required"], columns=1),
            make_text_field("lastName", "Last Name", rules=["required"], columns=1),
            make_email_field("email", "Email", rules=["required", "email"], columns=1),
            make_phone_field("phone", "Phone", columns=1),
            make_textarea_field("message", "Message", rules=["required"], columns=2),
            make_button_field("submitBtn", "Send Message", color="primary", columns=2),
        ],
    },
    "task-form": {
        "description": "Task creation: title, description, assignee, due date, priority",
        "columns": 2,
        "generate": lambda: [
            make_text_field("title", "Task Title", rules=["required"], columns=2),
            make_richtext_field("description", "Description", columns=2),
            make_user_select_field("assignedTo", "Assignee", columns=1),
            make_date_field("dueDate", "Due Date", date_type="dateTime", columns=1),
            make_select_field(
                "priority", "Priority",
                items={"enum_id": "Tasks.priority", "targetType": "internal",
                       "targetEntityName": "Enums", "targetValueField": "id", "targetLabelField": "title"},
                options={"valueIsObject": True},
                columns=1,
            ),
            make_select_field(
                "status", "Status",
                items={"enum_id": "Tasks.status", "targetType": "internal",
                       "targetEntityName": "Enums", "targetValueField": "id", "targetLabelField": "title"},
                options={"valueIsObject": True},
                columns=1,
            ),
        ],
    },
    "feedback": {
        "description": "Feedback/survey: rating, comment, submit",
        "columns": 1,
        "generate": lambda: [
            make_radio_field("rating", "How would you rate your experience?"),
            make_textarea_field("comment", "Additional Comments"),
            make_button_field("submitBtn", "Submit Feedback", color="primary"),
        ],
    },
    "wizard": {
        "description": "Multi-step wizard form with 3 steps",
        "columns": 1,
        "generate": lambda: [
            make_steps_field("steps", schema=[
                make_group_field("step1", schema=[make_text_field("name", "Full Name", rules=["required"])]),
                make_group_field("step2", schema=[make_email_field("email", "Email", rules=["required", "email"])]),
                make_group_field("step3", schema=[make_textarea_field("notes", "Any Notes")]),
            ]),
        ],
    },
    "dashboard-basic": {
        "description": "Basic dashboard with bar chart and donut chart",
        "columns": 2,
        "generate": lambda: [
            make_chart_field("barChart", "groupedBarChartCategories", "Revenue by Category", columns=1),
            make_chart_field("donutChart", "donutChart", "Status Distribution", columns=1),
        ],
    },
}


def get_template(name):
    """Get template schema + settings. Returns (fields, settings) or (None, None)."""
    tmpl = TEMPLATES.get(name)
    if not tmpl:
        return None, None
    fields = tmpl["generate"]()
    cols = tmpl["columns"]
    fields = auto_layout(fields, cols)
    settings = dict(DEFAULT_FORM_SETTINGS, columnsNumber=cols)
    return fields, settings


# ---------------------------------------------------------------------------
# CLI command implementations
# ---------------------------------------------------------------------------

USER_FIELDS = {
    "id": True, "firstName": True, "lastName": True, "fullName": True,
    "position": True, "avatar": {"id": True, "fileName": True},
    "roles": {"id": True, "name": True},
}


def cmd_get_me(args):
    body = {
        "fields": USER_FIELDS,
        "conditions": {"operator": "and", "filters": [_filter("id", "$current-user", "=")]},
        "limit": 1,
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    res = make_request("POST", _data_url(ENTITY_USERS, "select") + "?markAsView=false", body)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_list_forms(args):
    result = list_forms(entity_name=args.entity, form_type=args.type, limit=args.limit)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if not result:
        print("No forms found.")
        return
    print("{0:<8} {1:<14} {2:<30} {3:<20}".format("ID", "Type", "Name", "Entity"))
    print("-" * 74)
    for f in result:
        ename = f.get("entity", {}).get("name", "-") if f.get("entity") else "-"
        print("{0:<8} {1:<14} {2:<30} {3:<20}".format(
            f.get("id", "?"), f.get("type", "?"),
            (f.get("name") or "?")[:28], ename[:18]
        ))


def cmd_get_form(args):
    result = get_form(args.id)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if not result:
        print("Form not found.")
        return
    print("ID:       {0}".format(result.get("id")))
    print("Name:     {0}".format(result.get("name")))
    print("Type:     {0}".format(result.get("type")))
    print("Alias:    {0}".format(result.get("alias") or "-"))
    print("Public:   {0}".format(result.get("isPublic", False)))
    entity = result.get("entity")
    print("Entity:   {0}".format(entity.get("name") if entity else "-"))
    locked = result.get("lockedBy")
    if locked and locked.get("id"):
        print("Locked:   {0} {1}".format(locked.get("firstName", ""), locked.get("lastName", "")))
    else:
        print("Locked:   No")
    data = result.get("data") or {}
    schema = data.get("formShema") or []
    settings = data.get("formSettings") or {}
    has_module = bool(data.get("formModul"))
    print("Fields:   {0}".format(len(schema)))
    print("Columns:  {0}".format(settings.get("columnsNumber", 1)))
    print("Module:   {0}".format("Yes" if has_module else "No"))
    if schema:
        print("\nSchema fields:")
        for f in schema:
            rules_str = " rules={0}".format(f["rules"]) if f.get("rules") else ""
            print("  - {0} ({1}){2}".format(f.get("name", "?"), f.get("type", "?"), rules_str))


def cmd_create_form(args):
    schema = []
    settings = dict(DEFAULT_FORM_SETTINGS)

    # Source: schema file
    if args.schema_file:
        with open(args.schema_file, "r", encoding="utf-8") as fp:
            schema_data = json.load(fp)
        if isinstance(schema_data, dict):
            schema = schema_data.get("formShema", schema_data.get("schema", []))
            if "formSettings" in schema_data:
                settings.update(schema_data["formSettings"])
        elif isinstance(schema_data, list):
            schema = schema_data

    # Source: template
    elif args.template:
        schema, tmpl_settings = get_template(args.template)
        if schema is None:
            sys.stderr.write("ERROR: Unknown template '{0}'\n".format(args.template))
            sys.stderr.write("Available: {0}\n".format(", ".join(TEMPLATES.keys())))
            sys.exit(1)
        settings.update(tmpl_settings)

    # Source: entity fields (specific)
    elif args.entity and args.fields:
        field_names = [f.strip() for f in args.fields.split(",")]
        schema, gen_settings = generate_schema_from_entity(args.entity, field_names, args.columns or 1)
        settings.update(gen_settings)

    # Source: entity fields (all custom)
    elif args.entity and args.generate_all:
        schema, gen_settings = generate_schema_from_entity(args.entity, None, args.columns or 1)
        settings.update(gen_settings)

    # Override settings
    # Override settings
    if args.columns:
        settings["columnsNumber"] = args.columns
    if args.submit_button:
        settings["showSubmitButton"] = True
    if args.entity:
        settings["entityId"] = args.entity
    settings["formType"] = args.type or "elementForm"

    # Module code
    module_code = None
    if args.module_file:
        with open(args.module_file, "r", encoding="utf-8") as fp:
            module_code = fp.read()

    # Resolve entity
    entity_ref = None
    if args.entity:
        ent_schema = get_entity_schema(args.entity)
        if isinstance(ent_schema, dict):
            entity_id = ent_schema.get("id")
            if entity_id:
                entity_ref = {"id": int(entity_id)}

    # Build IFormView
    form_view = {
        "name": args.name or "Untitled Form",
        "type": args.type or "elementForm",
        "isPublic": args.public or False,
        "data": {
            "formShema": schema,
            "formSettings": settings,
            "formModul": module_code,
        },
    }
    if entity_ref:
        form_view["entity"] = entity_ref
    if args.alias:
        form_view["alias"] = args.alias

    result = create_form(form_view)

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        form_id = result.get("id") if isinstance(result, dict) else "?"
        print("Form created. ID: {0}".format(form_id))
        print("  Name:   {0}".format(args.name or "Untitled Form"))
        print("  Type:   {0}".format(args.type or "elementForm"))
        print("  Fields: {0}".format(len(schema)))


def cmd_update_form(args):
    update_data = {}

    if args.schema_file:
        with open(args.schema_file, "r", encoding="utf-8") as fp:
            schema_data = json.load(fp)
        if isinstance(schema_data, dict):
            form_data = {}
            if "formShema" in schema_data or "schema" in schema_data:
                form_data["formShema"] = schema_data.get("formShema", schema_data.get("schema", []))
            if "formSettings" in schema_data:
                form_data["formSettings"] = schema_data["formSettings"]
            if "formModul" in schema_data:
                form_data["formModul"] = schema_data["formModul"]
            update_data["data"] = form_data
        elif isinstance(schema_data, list):
            existing = get_form(args.id)
            existing_data = (existing.get("data") or {}) if existing else {}
            existing_data["formShema"] = schema_data
            update_data["data"] = existing_data

    if args.settings_json:
        new_settings = json.loads(args.settings_json)
        if "data" not in update_data:
            existing = get_form(args.id)
            update_data["data"] = (existing.get("data") or {}) if existing else {}
        current_settings = update_data["data"].get("formSettings") or {}
        current_settings.update(new_settings)
        update_data["data"]["formSettings"] = current_settings

    if args.module_file:
        with open(args.module_file, "r", encoding="utf-8") as fp:
            module_code = fp.read()
        if "data" not in update_data:
            existing = get_form(args.id)
            update_data["data"] = (existing.get("data") or {}) if existing else {}
        update_data["data"]["formModul"] = module_code

    if args.name:
        update_data["name"] = args.name

    if not update_data:
        sys.stderr.write("ERROR: Nothing to update. Provide --schema-file, --settings-json, --module-file, or --name.\n")
        sys.exit(1)

    result = update_form_by_id(args.id, update_data)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Form {0} updated.".format(args.id))


def cmd_lock_form(args):
    # Get current user ID
    body = {
        "fields": {"id": True},
        "conditions": {"operator": "and", "filters": [_filter("id", "$current-user", "=")]},
        "limit": 1, "getAccessByFields": True, "includeDeletedRelations": False,
    }
    res = make_request("POST", _data_url(ENTITY_USERS, "select") + "?markAsView=false", body)
    user_id = None
    if isinstance(res, list) and res:
        user_id = res[0].get("id")
    elif isinstance(res, dict):
        user_id = res.get("id")
    if not user_id:
        sys.stderr.write("ERROR: Could not resolve current user.\n")
        sys.exit(1)
    update_form_by_id(args.id, {"lockedBy": {"id": user_id}})
    print("Form {0} locked by user {1}.".format(args.id, user_id))


def cmd_unlock_form(args):
    update_form_by_id(args.id, {"lockedBy": None})
    print("Form {0} unlocked.".format(args.id))


def cmd_generate_schema(args):
    field_names = [f.strip() for f in args.fields.split(",")] if args.fields else None
    columns = args.columns or 1
    schema, settings = generate_schema_from_entity(args.entity, field_names, columns)

    output = {"formShema": schema, "formSettings": settings}
    if args.module_file:
        with open(args.module_file, "r", encoding="utf-8") as fp:
            output["formModul"] = fp.read()

    result_json = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(result_json)
        print("Schema written to {0} ({1} fields)".format(args.output, len(schema)))
    else:
        print(result_json)


def cmd_add_field(args):
    existing = get_form(args.id)
    if not existing:
        sys.stderr.write("ERROR: Form {0} not found.\n".format(args.id))
        sys.exit(1)

    data = existing.get("data") or {}
    schema = data.get("formShema") or []
    settings = data.get("formSettings") or {}

    # Build new field
    label = args.label or args.name
    new_field = make_field(args.type or "text", args.name, label)
    if args.rules:
        new_field["rules"] = [r.strip() for r in args.rules.split(",")]
    if args.input_type:
        new_field["inputType"] = args.input_type
    if args.field_columns:
        new_field["columns"] = {"lg": {"container": args.field_columns}}

    # Position at end
    max_y = 0
    for f in schema:
        pos = f.get("position", {}).get("lg", f.get("position", {}))
        rows_val = f.get("rows", {}).get("lg", {}).get("container", 1)
        max_y = max(max_y, pos.get("y", 0) + rows_val - 1)
    new_pos = {"x": 1, "y": max_y + 1}
    new_field["position"] = {"lg": new_pos, "sm": new_pos, "default": new_pos}

    schema.append(new_field)
    data["formShema"] = schema
    update_form_by_id(args.id, {"data": data})

    if args.format == "json":
        print(json.dumps(new_field, indent=2, ensure_ascii=False))
    else:
        print("Field '{0}' ({1}) added to form {2} at row {3}.".format(
            args.name, args.type or "text", args.id, max_y + 1))


def cmd_list_field_types(args):
    types = {
        "INPUT FIELDS (category: fields)": [
            ("text", "Single line text (inputType: text/number/email/password/phone)"),
            ("date", "Date/time picker (typeDate: date/dateTime/time)"),
            ("textarea", "Multi-line text"),
            ("richtext", "CKEditor rich text"),
            ("checkbox", "Checkbox (mode: checkbox/checkboxgroup)"),
            ("radio", "Radio group"),
            ("select", "Dropdown select (relations, enums, static options)"),
            ("toogle", "Boolean toggle switch"),
            ("files", "File upload"),
            ("avatar", "Avatar image upload"),
            ("signature", "Digital signature pad"),
            ("listItems", "Dynamic list"),
            ("ucidPrefix", "Entity ID prefix"),
            ("html", "HTML renderer"),
            ("icon", "Icon picker"),
        ],
        "STRUCTURE (category: structure)": [
            ("group", "Container with nested grid (columnsNumber)"),
            ("flexGroup", "Flex container (justifyContent, alignItems)"),
            ("tabs", "Tabbed sections"),
            ("steps", "Step-by-step wizard"),
            ("accordion", "Collapsible sections"),
            ("resizeWindow", "Resizable panels"),
            ("list", "Repeatable list"),
            ("menuPanel", "Sidebar menu"),
            ("buttonList", "Button group container"),
        ],
        "STATIC (category: static)": [
            ("button", "Button (buttonLabel, color, icon)"),
            ("static", "Static content (tag: h1/h2/h3/h4/hr/text, content)"),
            ("image", "Static image (src, alt)"),
            ("dynamic", "Custom Vue component (template, script)"),
        ],
        "WIDGETS (category: widgets)": [
            ("table", "Data table"),
            ("cards", "Card list"),
            ("userSelect", "User picker (items.targetEntityName: Users)"),
            ("widget", "Generic widget (widgetName, props)"),
            ("commentEditorWidget", "Comment input"),
            ("commentRendererWidget", "Comment display"),
            ("filesWidget", "Files management"),
            ("periodWidget", "Date period selector"),
            ("checkListsWidget", "Checklists"),
            ("approvalsWidget", "Approval workflows"),
            ("links", "Entity links"),
            ("progressBar", "Progress bar"),
            ("activities", "Activity feed"),
            ("timeTracking", "Time tracker"),
            ("tags", "Tag management"),
            ("calendar", "Full calendar"),
            ("iFrameWidget", "Embedded iframe (src)"),
            ("customForm", "Embedded sub-form"),
        ],
        "CHARTS (type: 'widget', widgetName: 'BaseChart', props.config.type:)": [
            ("groupedBarChartCategories", "Grouped bar chart"),
            ("columnBarChart", "Column bar chart"),
            ("comboChart", "Combo chart"),
            ("lineChart", "Line chart"),
            ("areaChart", "Area chart"),
            ("funnelChart", "Funnel chart"),
            ("stackedBarChart", "Stacked bar chart"),
            ("treemapChart", "Treemap chart"),
            ("donutChart", "Donut chart"),
            ("radialBar", "Radial bar chart"),
            ("radarChart", "Radar chart"),
            ("tileChart", "Tile chart"),
        ],
    }
    for category, items in types.items():
        print("\n{0}".format(category))
        print("-" * len(category))
        for t, desc in items:
            print("  {0:<28} {1}".format(t, desc))


def cmd_list_templates(args):
    print("{0:<18} {1:<6} {2}".format("Template", "Cols", "Description"))
    print("-" * 70)
    for name, tmpl in TEMPLATES.items():
        print("{0:<18} {1:<6} {2}".format(name, tmpl["columns"], tmpl["description"]))


def cmd_validate_schema(args):
    with open(args.file, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    if isinstance(data, dict):
        schema = data.get("formShema", data.get("schema", []))
    elif isinstance(data, list):
        schema = data
    else:
        sys.stderr.write("ERROR: File must contain a JSON array or object with 'formShema' key.\n")
        sys.exit(1)

    errors = validate_schema(schema)
    if errors:
        print("INVALID — {0} error(s):".format(len(errors)))
        for err in errors:
            print("  x {0}".format(err))
        sys.exit(1)
    else:
        print("VALID — {0} field(s), no issues found.".format(len(schema)))


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="suppa_forms",
        description="Suppa Dynamic Forms CLI — manage forms via HTTP API",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # get-me
    sub.add_parser("get-me", help="Smoke test — show current user")

    # list-forms
    p = sub.add_parser("list-forms", help="List forms (by entity/type)")
    p.add_argument("--entity", help="Filter by entity name")
    p.add_argument("--type", help="Filter by form type")
    p.add_argument("--limit", type=int, default=50, help="Max results")

    # get-form
    p = sub.add_parser("get-form", help="Get a form by ID")
    p.add_argument("id", help="Form ID (integer)")

    # create-form
    p = sub.add_parser("create-form", help="Create a new form")
    p.add_argument("--name", help="Form name")
    p.add_argument("--type", default="elementForm",
                   help="Form type: elementForm, customForm, dashboard, webform, listForm")
    p.add_argument("--entity", help="Entity name (for entity forms)")
    p.add_argument("--alias", help="URL-friendly alias")
    p.add_argument("--public", action="store_true", help="Make form public")
    p.add_argument("--columns", type=int, help="Grid columns (1-12)")
    p.add_argument("--submit-button", action="store_true", help="Show submit button")
    p.add_argument("--schema-file", help="JSON file with schema")
    p.add_argument("--module-file", help="JS file with module code")
    p.add_argument("--template",
                   help="Use a template: {0}".format(", ".join(TEMPLATES.keys())))
    p.add_argument("--fields", help="Comma-separated entity field names")
    p.add_argument("--generate-all", action="store_true",
                   help="Generate from all custom entity fields")

    # update-form
    p = sub.add_parser("update-form", help="Update an existing form")
    p.add_argument("id", help="Form ID (integer)")
    p.add_argument("--name", help="New form name")
    p.add_argument("--schema-file", help="JSON file with new schema")
    p.add_argument("--settings-json", help="JSON string with settings to merge")
    p.add_argument("--module-file", help="JS file with module code")

    # lock-form / unlock-form
    p = sub.add_parser("lock-form", help="Lock a form for editing")
    p.add_argument("id", help="Form ID")

    p = sub.add_parser("unlock-form", help="Unlock a form")
    p.add_argument("id", help="Form ID")

    # generate-schema
    p = sub.add_parser("generate-schema", help="Generate schema from entity fields")
    p.add_argument("--entity", required=True, help="Entity name")
    p.add_argument("--fields", help="Comma-separated field names (omit for all custom)")
    p.add_argument("--columns", type=int, default=1, help="Grid columns")
    p.add_argument("--module-file", help="JS file to include as formModul")
    p.add_argument("--output", "-o", help="Output file path (default: stdout)")

    # add-field
    p = sub.add_parser("add-field", help="Add a field to an existing form")
    p.add_argument("id", help="Form ID")
    p.add_argument("--name", required=True, help="Field name (unique key)")
    p.add_argument("--type", default="text", help="Field type")
    p.add_argument("--label", help="Field label (default: same as name)")
    p.add_argument("--rules", help="Comma-separated validation rules")
    p.add_argument("--input-type", help="Input type (text, number, email, phone, password)")
    p.add_argument("--field-columns", type=int, default=1, help="Column span")

    # list-field-types / list-templates / validate-schema
    sub.add_parser("list-field-types", help="Show all available field types")
    sub.add_parser("list-templates", help="Show available form templates")

    p = sub.add_parser("validate-schema", help="Validate a schema JSON file")
    p.add_argument("file", help="Path to JSON file")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMAND_MAP = {
    "get-me": cmd_get_me,
    "list-forms": cmd_list_forms,
    "get-form": cmd_get_form,
    "create-form": cmd_create_form,
    "update-form": cmd_update_form,
    "lock-form": cmd_lock_form,
    "unlock-form": cmd_unlock_form,
    "generate-schema": cmd_generate_schema,
    "add-field": cmd_add_field,
    "list-field-types": cmd_list_field_types,
    "list-templates": cmd_list_templates,
    "validate-schema": cmd_validate_schema,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    handler = COMMAND_MAP.get(args.command)
    if handler:
        handler(args)
    else:
        sys.stderr.write("Unknown command: {0}\n".format(args.command))
        sys.exit(1)


if __name__ == "__main__":
    main()
