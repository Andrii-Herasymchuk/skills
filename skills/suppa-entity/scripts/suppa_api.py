#!/usr/bin/env python3
"""
Suppa Entity Builder & Schema API Client (new platform: modern.suppa.me)

REST-style API rooted at /api/core/data/{Entity}/{action} and
/api/core/builder/... using integer IDs and camelCase field names.

No external dependencies — Python stdlib only.

Quick start:
    $env:SUPPA_API_KEY = "<token>"
    python suppa_api.py list-entities
    python suppa_api.py describe-entity Tasks
    python suppa_api.py search Users --field id --field fullName --limit 10

Commands:
    get-me            Current authenticated user (smoke test)
    list-entities     List ALL entities on the tenant (GET /api/core/schema)
    describe-entity   Show one entity's fields/options (GET /api/core/schema/{name})
    search            Generic instance search for any entity with simple --filter syntax
    create-entity     Create a new entity via the builder API
    add-field         Add one or more fields to an existing entity
    list-field-types  Show all supported field types with example shapes
    add-enum-values   Insert allowed values for an enum field (POST /api/core/data-bulk/Enums)
    raw               Power-user: POST arbitrary body to any /api/core/data/{Entity}/{action}
"""

import argparse
import json
import os
import sys
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("SUPPA_BASE_URL", "https://modern.suppa.me")
DEFAULT_LANG = os.environ.get("SUPPA_LANG", "en")
DEFAULT_TZ = os.environ.get("SUPPA_TZ", "Europe/Kyiv")

ENTITY_USERS = "Users"


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


def make_request(method, path, body=None, token=None, extra_headers=None):
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
    if extra_headers:
        headers.update(extra_headers)

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


def search_entity(entity, *, filters=None, fields=None, limit=100, offset=0,
                  order_by=None, search_value="", group_by=None,
                  include_deleted=False, token=None):
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
                    else [{"field": "createdAt", "order": "desc"}]),
        "searchValue": search_value,
        "getAccessByFields": True,
        "includeDeletedRelations": include_deleted,
    }
    if group_by:
        body["groupBy"] = group_by
    return make_request("POST", _data_url(entity, "search"), body, token=token)


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def _filter(field, value, comparator="=", *, disabled=False, filter_id=None):
    if comparator == "like" and isinstance(value, str) and "%" not in value:
        value = "%" + value + "%"
    return {
        "id": filter_id or str(uuid.uuid4())[:8],
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
            f.setdefault("id", str(uuid.uuid4())[:8])
            f.setdefault("disabled", False)
            f.setdefault("comparator", "=")
            out.append(f)
        else:
            raise ValueError("filter must be tuple or dict, got {0!r}".format(f))
    return out


# ---------------------------------------------------------------------------
# Builder API — field types & helpers
# ---------------------------------------------------------------------------

FIELD_TYPES = {
    "text":           {"type": "text"},
    "integer":        {"type": "integer"},
    "numeric":        {"type": "numeric"},
    "boolean":        {"type": "boolean"},
    "date":           {"type": "timestamp", "subType": "date"},
    "datetime":       {"type": "timestamp", "subType": "timestamp"},
    "timestamp":      {"type": "timestamp", "subType": "timestamp"},
    "json":           {"type": "json"},
    "enum":           {"type": "enum"},
    "icon":           {"type": "icon"},
    "uuid":           {"type": "uuid"},
    "relation":       {"type": "many-to-one"},
    "many-to-one":    {"type": "many-to-one"},
    "many-to-many":   {"type": "many-to-many"},
    "file":           {"type": "file",       "relationTarget": "Files"},
    "multi-file":     {"type": "multi-file", "relationTarget": "Files"},
    "multi-language": {"type": "multi-language"},
}

DEFAULT_FIELD_OPTIONS = {
    "canGroup":      True,
    "canSort":       True,
    "canFilter":     True,
    "showInTable":   True,
    "editFromTable": True,
}

DEFAULT_ENTITY_OPTIONS = {
    "comments":           False,
    "favorites":          False,
    "approvals":          False,
    "timeTracking":       False,
    "browsingHistory":    False,
    "trackChangeHistory": False,
    "globalSearch":       False,
    "notificationMutes":  False,
    "reminders":          False,
    "reactions":          False,
}


def create_entity(name, *, title=None, options=None, fields=None, token=None):
    """POST /api/core/builder/create-entity"""
    body = {
        "options": dict(DEFAULT_ENTITY_OPTIONS, **(options or {})),
        "title": title or {},
        "name": name,
        "fields": fields or [],
    }
    return make_request("POST", "/api/core/builder/create-entity", body, token=token)


def add_fields(entity_name, fields, *, token=None):
    """POST /api/core/builder/{entity}/add-fields  (body is the bare array)."""
    return make_request(
        "POST",
        "/api/core/builder/{0}/add-fields".format(entity_name),
        fields if isinstance(fields, list) else [fields],
        token=token,
    )


def get_entity_id(entity_name, *, token=None):
    """Return numeric entity id by name via GET /api/core/schema/{name}."""
    res = make_request("GET", "/api/core/schema/{0}".format(entity_name), token=token)
    return res.get("id")


def add_enum_values(enum_name, values, entity_id, *, icons=None, titles=None, token=None):
    """Bulk-insert enum values for a qualified enum field.

    POST /api/core/data-bulk/Enums  body: {insert:[...], update:[], remove:[]}
    """
    inserts = []
    for i, v in enumerate(values):
        icon = (icons[i] if icons and i < len(icons) else "") or ""
        title = titles[i] if titles and i < len(titles) else None
        inserts.append({
            "name": enum_name,
            "value": str(v),
            "icon": icon,
            "entity": {"id": int(entity_id)},
            "title": title,
        })
    body = {"insert": inserts, "update": [], "remove": []}
    return make_request("POST", "/api/core/data-bulk/Enums", body, token=token)


def build_field(name, kind, *, title=None, default_value=None, default_is_null=False,
                required=False, unique=False, relation_target=None, sub_type=None,
                decimal_places=None, max_length=None, min_length=None,
                max_value=None, min_value=None, is_only_positive=False,
                is_array=False, options=None):
    """Build a single field spec for create-entity / add-fields."""
    if kind not in FIELD_TYPES:
        raise ValueError(
            "Unknown field kind {0!r}. Valid: {1}".format(kind, sorted(FIELD_TYPES))
        )
    base = dict(FIELD_TYPES[kind])
    spec = {
        "name": name,
        "type": base["type"],
        "options": dict(DEFAULT_FIELD_OPTIONS, **(options or {})),
    }
    if sub_type is not None:
        spec["subType"] = sub_type
    elif "subType" in base:
        spec["subType"] = base["subType"]

    rt = relation_target if relation_target is not None else base.get("relationTarget")
    if rt is not None:
        spec["relationTarget"] = rt
        if spec["type"] == "enum" and "subType" not in spec:
            spec["subType"] = rt

    if title is not None:
        spec["title"] = title
    if default_value is not None:
        spec["defaultValue"] = default_value
    if default_is_null:
        spec["defaultValueIsNull"] = True
    if required:
        spec["notNull"] = True
    if unique:
        spec["unique"] = True
    if is_array:
        spec["isArray"] = True
    if decimal_places is not None:
        spec["decimalPlaces"] = int(decimal_places)
    if max_length is not None:
        spec["maxLength"] = int(max_length)
    if min_length is not None:
        spec["minLength"] = int(min_length)
    if max_value is not None:
        spec["maxValue"] = max_value
    if min_value is not None:
        spec["minValue"] = min_value
    if is_only_positive:
        spec["isOnlyPositive"] = True
    return spec


# ---------------------------------------------------------------------------
# Schema discovery
# ---------------------------------------------------------------------------

def list_all_entities(token=None):
    """GET /api/core/schema — returns full list of every entity on the tenant."""
    return make_request("GET", "/api/core/schema", body=None, token=token)


def describe_entity_schema(name, token=None):
    """GET /api/core/schema/{name} — full schema for one entity."""
    return make_request("GET", "/api/core/schema/" + name, body=None, token=token)


# ---------------------------------------------------------------------------
# Filter expression parser
# ---------------------------------------------------------------------------

def _parse_filter_expr(expr):
    """Parse a simple CLI filter string into a {field,value,comparator} dict."""
    ops = ["!=", ">=", "<=", "~", "=", ">", "<"]
    found_op = None
    found_idx = -1
    for op in ops:
        i = expr.find(op)
        if i > 0 and (found_idx == -1 or i < found_idx):
            found_op = op
            found_idx = i
    if found_op is None:
        raise ValueError("filter must contain an operator (=, !=, ~, >, <, >=, <=): " + expr)
    field = expr[:found_idx].strip()
    raw = expr[found_idx + len(found_op):].strip()
    comp_map = {"=": "=", "!=": "!=", "~": "like", ">": ">", "<": "<", ">=": ">=", "<=": "<="}
    comparator = comp_map[found_op]

    if comparator == "=" and raw.lower() == "null":
        return {"field": field, "value": None, "comparator": "is null"}
    if comparator == "=" and raw == "*":
        return {"field": field, "value": None, "comparator": "is not null"}
    if comparator == "!=" and raw.lower() == "null":
        return {"field": field, "value": None, "comparator": "is not null"}

    if comparator == "=" and "," in raw and not raw.startswith(("[", "{", '"')):
        parts = [_decode_value(p.strip()) for p in raw.split(",") if p.strip()]
        return {"field": field, "value": parts, "comparator": "in"}

    return {"field": field, "value": _decode_value(raw), "comparator": comparator}


def _decode_value(raw):
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw


def _parse_fields_arg(field_args):
    """Convert CLI --field args into the nested-boolean fields dict."""
    out = {}
    for spec in field_args:
        cur = out
        parts = spec.split(".")
        for i, p in enumerate(parts):
            if i == len(parts) - 1:
                cur[p] = True
            else:
                if not isinstance(cur.get(p), dict):
                    cur[p] = {}
                cur = cur[p]
    return out


# ---------------------------------------------------------------------------
# CLI command implementations
# ---------------------------------------------------------------------------

def cmd_get_me(args):
    body = {
        "fields": {"id": True, "firstName": True, "lastName": True, "fullName": True,
                   "position": True, "createdAt": True,
                   "roles": {"id": True, "name": True}},
        "conditions": {
            "operator": "and",
            "filters": [_filter("id", "$current-user", "=")],
        },
        "limit": 1,
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    res = make_request(
        "POST",
        _data_url(ENTITY_USERS, "select") + "?markAsView=false",
        body,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_list_entities(args):
    rows = list_all_entities()
    if not isinstance(rows, list):
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if args.initiator:
        rows = [r for r in rows if r.get("initiator") == args.initiator]
    if args.type:
        rows = [r for r in rows if r.get("type") == args.type]
    if args.application:
        rows = [r for r in rows if (r.get("application") or {}).get("name") == args.application
                or r.get("application") == args.application]
    if args.search:
        s = args.search.lower()
        def _match(r):
            if s in (r.get("name") or "").lower():
                return True
            t = r.get("title")
            if isinstance(t, dict):
                for v in t.values():
                    if isinstance(v, str) and s in v.lower():
                        return True
            return False
        rows = [r for r in rows if _match(r)]
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    print("{0:<6} {1:<10} {2:<14} {3:<35} {4}".format(
        "ID", "INITIATOR", "TYPE", "NAME", "TITLE"))
    print("-" * 100)
    for r in rows:
        t = r.get("title")
        title = ""
        if isinstance(t, dict):
            title = t.get("en") or t.get("uk") or next(
                (v for v in t.values() if isinstance(v, str)), "")
        print("{0:<6} {1:<10} {2:<14} {3:<35} {4}".format(
            r.get("id", ""),
            (r.get("initiator") or "")[:10],
            (r.get("type") or "")[:14],
            (r.get("name") or "")[:35],
            title,
        ))
    print("-" * 100)
    print("total: {0}".format(len(rows)))


def cmd_describe_entity(args):
    schema = describe_entity_schema(args.name)
    if args.format == "json":
        if args.custom_only and isinstance(schema, dict):
            schema = dict(schema)
            schema["fields"] = [f for f in (schema.get("fields") or [])
                                if f.get("initiator") == "client"]
        print(json.dumps(schema, indent=2, ensure_ascii=False))
        return
    if not isinstance(schema, dict):
        print(json.dumps(schema, indent=2, ensure_ascii=False))
        return
    title = schema.get("title")
    if isinstance(title, dict):
        title = title.get("en") or title.get("uk") or ""
    print("Entity: {0}  (id={1})".format(schema.get("name"), schema.get("id")))
    print("Title:     {0}".format(title or ""))
    print("Type:      {0}".format(schema.get("type")))
    print("Initiator: {0}".format(schema.get("initiator")))
    rep = schema.get("representativeField")
    if rep:
        print("Repr field: {0}".format(rep))
    opts = schema.get("options") or {}
    if opts:
        enabled = [k for k, v in opts.items() if v]
        print("Options enabled: {0}".format(", ".join(enabled) if enabled else "(none)"))
    fields = schema.get("fields") or []
    if args.custom_only:
        fields = [f for f in fields if f.get("initiator") == "client"]
    print("Fields ({0}):".format(len(fields)))
    print("  {0:<6} {1:<10} {2:<22} {3:<18} {4:<8} {5}".format(
        "ID", "INITIATOR", "NAME", "TYPE", "NOTNULL", "TITLE/RELATION"))
    print("  " + "-" * 96)
    for f in fields:
        t = f.get("title")
        ftitle = ""
        if isinstance(t, dict):
            ftitle = t.get("en") or t.get("uk") or ""
        extra = ftitle
        if f.get("relationTarget"):
            extra = "{0}  ->{1}".format(extra, f["relationTarget"]).strip()
        if f.get("subType"):
            extra = "{0}  sub={1}".format(extra, f["subType"]).strip()
        print("  {0:<6} {1:<10} {2:<22} {3:<18} {4:<8} {5}".format(
            f.get("id", ""),
            (f.get("initiator") or "")[:10],
            (f.get("name") or "")[:22],
            (f.get("type") or "")[:18],
            "yes" if f.get("notNull") else "",
            extra,
        ))


def cmd_search(args):
    """Generic search against /api/core/data/{Entity}/search."""
    filters = [_parse_filter_expr(f) for f in (args.filter or [])]
    if args.fields:
        fields = _parse_fields_arg(args.fields)
    elif args.fields_json:
        fields = json.loads(args.fields_json)
    else:
        fields = {"id": True}

    order_by = None
    if args.order_by:
        order_by = []
        for spec in args.order_by:
            field, _, order = spec.partition(":")
            order_by.append({"field": field, "order": (order or "asc").lower()})

    res = search_entity(
        args.entity,
        filters=filters,
        fields=fields,
        limit=args.limit,
        offset=args.offset,
        order_by=order_by,
        search_value=args.search_value or "",
        include_deleted=args.include_deleted,
    )
    if args.count_only:
        n = len(res) if isinstance(res, list) else len((res or {}).get("data") or [])
        print(n)
        return
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_create_entity(args):
    title = json.loads(args.title_json) if args.title_json else (
        {"en": args.title_en} if args.title_en else {}
    )
    options = json.loads(args.options_json) if args.options_json else {}
    for k in ("comments", "favorites", "approvals", "timeTracking", "browsingHistory",
              "trackChangeHistory", "globalSearch", "notificationMutes",
              "reminders", "reactions"):
        v = getattr(args, "enable_" + k.lower().replace("_", ""), None)
        if v is not None:
            options[k] = bool(v)
    fields = json.loads(args.fields_json) if args.fields_json else []
    res = create_entity(args.name, title=title, options=options, fields=fields)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_add_field(args):
    if args.fields_json:
        fields = json.loads(args.fields_json)
        if isinstance(fields, dict):
            fields = [fields]
    else:
        title = None
        if args.title_json:
            title = json.loads(args.title_json)
        elif args.title_en:
            title = {"en": args.title_en}
        default_value = None
        if args.default_value is not None:
            try:
                default_value = json.loads(args.default_value)
            except (json.JSONDecodeError, ValueError):
                default_value = args.default_value
        options = json.loads(args.options_json) if args.options_json else None
        fields = [build_field(
            args.name, args.type,
            title=title,
            default_value=default_value,
            default_is_null=args.default_is_null,
            required=args.required,
            unique=args.unique,
            relation_target=args.relation_target,
            sub_type=args.sub_type,
            decimal_places=args.decimal_places,
            max_length=args.max_length,
            min_length=args.min_length,
            max_value=args.max_value,
            min_value=args.min_value,
            is_only_positive=args.only_positive,
            is_array=args.array,
            options=options,
        )]
    res = add_fields(args.entity, fields)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_add_enum_values(args):
    enum_name = args.enum
    if "." not in enum_name:
        raise SystemExit("--enum must be '<Entity>.<fieldName>'")
    entity_name = enum_name.split(".", 1)[0]
    entity_id = args.entity_id
    if entity_id is None:
        entity_id = get_entity_id(entity_name)
        if entity_id is None:
            raise SystemExit("Could not resolve entity id for '{0}'".format(entity_name))
    icons = args.icon if args.icon else None
    titles = None
    if args.titles_json:
        titles = json.loads(args.titles_json)
        if not isinstance(titles, list):
            raise SystemExit("--titles-json must be a JSON array")
    res = add_enum_values(enum_name, args.value, int(entity_id), icons=icons, titles=titles)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_list_field_types(args):
    """Print supported field types with example spec each."""
    examples = {}
    for k in sorted(FIELD_TYPES):
        rt = None
        if k in ("relation", "many-to-one"):
            rt = "Users"
        elif k == "many-to-many":
            rt = "Tags"
        elif k == "enum":
            rt = "MyEntity.myEnumField"
        try:
            ex = build_field("sample_" + k.replace("-", "_"), k, relation_target=rt)
        except Exception as exc:
            ex = {"error": str(exc)}
        examples[k] = ex
    print(json.dumps(examples, indent=2, ensure_ascii=False))


def cmd_raw(args):
    """Run an arbitrary POST against any entity action."""
    if args.body:
        body = json.loads(args.body)
    else:
        body = json.loads(sys.stdin.read())
    res = make_request("POST", _data_url(args.entity, args.action or "search"), body)
    print(json.dumps(res, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(
        prog="suppa_api.py",
        description="Suppa Entity Builder & Schema API client for modern.suppa.me",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("get-me", help="Current authenticated user").set_defaults(func=cmd_get_me)

    # ---- Schema discovery ----
    le = sub.add_parser("list-entities",
                        help="List every entity on the tenant (GET /api/core/schema)")
    le.add_argument("--initiator", choices=["system", "client"],
                    help="Filter: system = built-in, client = custom-built")
    le.add_argument("--type", choices=["entity", "tabular-part"],
                    help="Filter by entity type")
    le.add_argument("--application", help="Filter by owning application name")
    le.add_argument("--search", help="Case-insensitive substring match on name or title")
    le.add_argument("--format", choices=["table", "json"], default="table")
    le.set_defaults(func=cmd_list_entities)

    de = sub.add_parser("describe-entity",
                        help="Show one entity's schema (fields, options)")
    de.add_argument("name", help="Entity name, e.g. Tasks, Users, MyCustomEntity")
    de.add_argument("--custom-only", action="store_true",
                    help="Show only client-added (custom) fields")
    de.add_argument("--format", choices=["table", "json"], default="table")
    de.set_defaults(func=cmd_describe_entity)

    sr = sub.add_parser("search",
                        help="Generic instance search on any entity")
    sr.add_argument("entity", help="Entity name, e.g. Tasks, Users, MyCustomEntity")
    sr.add_argument("--filter", action="append", default=[],
                    help=("Simple filter expression (repeatable). "
                          "Forms: field=value | field!=value | field~substring | "
                          "field>N | field>=N | field<N | field<=N | "
                          "field=null | field!=null | field=v1,v2,v3"))
    sr.add_argument("--field", dest="fields", action="append", default=[],
                    help="Field to return (repeatable). Dot notation OK.")
    sr.add_argument("--fields-json", help="Full nested fields dict as JSON")
    sr.add_argument("--search-value", help="Server-side full-text search value")
    sr.add_argument("--order-by", action="append", default=[],
                    help="Order spec 'field:asc|desc' (repeatable)")
    sr.add_argument("--limit", type=int, default=50)
    sr.add_argument("--offset", type=int, default=0)
    sr.add_argument("--include-deleted", action="store_true")
    sr.add_argument("--count-only", action="store_true",
                    help="Print just the number of matching rows")
    sr.set_defaults(func=cmd_search)

    # ---- Builder API ----
    ce = sub.add_parser(
        "create-entity",
        help="Create a new entity (POST /api/core/builder/create-entity)",
    )
    ce.add_argument("name", help="Entity name (camelCase/PascalCase)")
    ce.add_argument("--title-en", help="English title shown in UI")
    ce.add_argument("--title-json", help='Localized title JSON, e.g. {"en":"Test","uk":"Тест"}')
    ce.add_argument("--options-json",
                    help="Override entity options as JSON dict")
    ce.add_argument("--fields-json",
                    help="Optional initial field specs as JSON array")
    for opt in ("comments", "favorites", "approvals", "timetracking",
                "browsinghistory", "trackchangehistory", "globalsearch",
                "notificationmutes", "reminders", "reactions"):
        ce.add_argument("--enable-" + opt,
                        dest="enable_" + opt,
                        action="store_true", default=None,
                        help="Enable {0} feature on the entity".format(opt))
    ce.set_defaults(func=cmd_create_entity)

    af = sub.add_parser(
        "add-field",
        help="Add field(s) to an entity (POST /api/core/builder/{entity}/add-fields)",
    )
    af.add_argument("entity", help="Entity name (existing entity to extend)")
    af.add_argument("--name", help="Field name (camelCase)")
    af.add_argument("--type", choices=sorted(FIELD_TYPES),
                    help="Field kind. See `list-field-types` for spec details.")
    af.add_argument("--title-en", help="English title")
    af.add_argument("--title-json", help="Localized title JSON")
    af.add_argument("--default-value", help="Default value (JSON-parsed if possible)")
    af.add_argument("--default-is-null", action="store_true")
    af.add_argument("--required", action="store_true", help="notNull=true")
    af.add_argument("--unique", action="store_true")
    af.add_argument("--array", action="store_true", help="isArray=true")
    af.add_argument("--relation-target",
                    help="For relation/enum/file: target entity name")
    af.add_argument("--sub-type", help="Override subType (timestamp/date/etc.)")
    af.add_argument("--decimal-places", type=int)
    af.add_argument("--max-length", type=int)
    af.add_argument("--min-length", type=int)
    af.add_argument("--max-value", type=float)
    af.add_argument("--min-value", type=float)
    af.add_argument("--only-positive", action="store_true")
    af.add_argument("--options-json",
                    help="Override field options as JSON dict")
    af.add_argument("--fields-json",
                    help="Raw JSON array of full field specs (skips CLI builder)")
    af.set_defaults(func=cmd_add_field)

    lft = sub.add_parser(
        "list-field-types",
        help="Show all supported field types with example shapes",
    )
    lft.set_defaults(func=cmd_list_field_types)

    aev = sub.add_parser(
        "add-enum-values",
        help="Insert allowed values for an enum field (data-bulk/Enums)",
    )
    aev.add_argument("--enum", required=True,
                     help="Qualified enum name '<Entity>.<fieldName>'")
    aev.add_argument("--value", action="append", required=True,
                     help="Enum value (repeatable)")
    aev.add_argument("--icon", action="append",
                     help="Icon per value (repeatable, parallel to --value)")
    aev.add_argument("--titles-json",
                     help='JSON array of titles per value')
    aev.add_argument("--entity-id", type=int,
                     help="Owning entity id (auto-resolved if omitted)")
    aev.set_defaults(func=cmd_add_enum_values)

    # ---- Power-user ----
    rs = sub.add_parser("raw", help="Raw POST to /api/core/data/{entity}/{action}")
    rs.add_argument("entity", help="e.g. Tasks, Projects, Users")
    rs.add_argument("--action", default="search", help="search|select|insert|update|remove")
    rs.add_argument("--body", help="JSON body (else read stdin)")
    rs.set_defaults(func=cmd_raw)

    return p


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
