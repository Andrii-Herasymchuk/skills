#!/usr/bin/env python3
"""
Suppa Tasks API Client (new platform: modern.suppa.me)

REST-style API rooted at /api/core/data/{Entity}/{action} using integer IDs and
camelCase field names. Auth: Bearer token via Authorization header (API key OR
JWT extracted from accessToken cookie both work).

No external dependencies — Python stdlib only.

Quick start:
    $env:SUPPA_API_KEY = "<token>"
    python suppa_api.py get-me
    python suppa_api.py search-tasks --my --active --limit 20

Commands:
    get-me            Current authenticated user
    search-tasks      Search tasks with filters
    count-tasks       Count tasks matching a filter
    get-task          Get a single task by integer id
    create-task       Create a new task
    update-task       Update fields on an existing task
    delete-task       Soft-delete (remove) a task by id
    move-task         Move task to another stage
    close-task        Move task to its workflow's closed stage (by id)
    add-comment       Add a comment to a task (supports @mentions)
    get-comments      Get comments for a task
    list-workflows    List workflows (StageWorkflows, grouped)
    list-stages       List stages of a workflow
    list-task-types   List allowed TasksTypes
    search-users      Search users by name / fetch by id
    attach-file       Upload a file as attachment to a task
    discover          Probe API to discover hardcodable constants for this tenant
    raw               Power-user: POST arbitrary body to any /api/core/data/{Entity}/{action}
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("SUPPA_BASE_URL", "https://modern.suppa.me")
DEFAULT_LANG = os.environ.get("SUPPA_LANG", "en")
DEFAULT_TZ = os.environ.get("SUPPA_TZ", "Europe/Kyiv")

# Entity names used in URL paths (PascalCase, plural).
ENTITY_TASKS = "Tasks"
ENTITY_TASK_COMMENTS = "TasksComments"
ENTITY_USERS = "Users"
ENTITY_WORKFLOWS = "StageWorkflows"
ENTITY_TASK_TYPES = "TasksTypes"
ENTITY_FILES = "Files"

# Numeric schema id of the Tasks entity (needed for /api/core/files/upload).
TASKS_ENTITY_ID = int(os.environ.get("SUPPA_TASKS_ENTITY_ID", "37")) or None

# Stage status values on the new platform.
STAGE_STATUS_OPEN_VALUES = ["active", "inprogress"]
STAGE_STATUS_CLOSED_VALUES = ["completed", "cancelled"]


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


def count_entity(entity, *, filters=None, token=None):
    """Count via the magic '#count' field projection."""
    res = search_entity(
        entity,
        filters=filters,
        fields={"id": "#count"},
        limit=1,
        offset=0,
        order_by=[],
        token=token,
    )
    rows = res if isinstance(res, list) else None
    if rows is None and isinstance(res, dict):
        for key in ("data", "rows", "items", "result"):
            if isinstance(res.get(key), list):
                rows = res[key]
                break
    if rows:
        row = rows[0]
        for ck in ("count", "id", "value"):
            if ck in row:
                try:
                    return int(row[ck])
                except (TypeError, ValueError):
                    pass
    if isinstance(res, dict) and "total" in res:
        try:
            return int(res["total"])
        except (TypeError, ValueError):
            pass
    return res


def select_entity_by_id(entity, instance_id, *, fields=None, token=None):
    """POST /api/core/data/{entity}/select — single-record fetch via id filter."""
    body = {
        "conditions": {
            "operator": "and",
            "filters": [_filter("id", instance_id, "=")],
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
    if isinstance(res, dict):
        for key in ("data", "rows", "items", "result"):
            arr = res.get(key)
            if isinstance(arr, list):
                return arr[0] if arr else None
    if isinstance(res, list):
        return res[0] if res else None
    return res


def insert_entity(entity, fields_list, *, returning=None, token=None):
    """POST /api/core/data/{entity}/insert"""
    body = {
        "fields": fields_list if isinstance(fields_list, list) else [fields_list],
    }
    if returning is not None:
        body["returning"] = returning
    return make_request("POST", _data_url(entity, "insert"), body, token=token)


def update_entity_by_id(entity, instance_id, fields, *, token=None):
    """POST /api/core/data/{entity}/update/{id}"""
    body = {"fields": fields}
    return make_request(
        "POST",
        _data_url(entity, "update") + "/" + str(int(instance_id)),
        body,
        token=token,
    )


def remove_entity(entity, *, filters, token=None):
    """POST /api/core/data/{entity}/remove"""
    body = {
        "conditions": {
            "operator": "and",
            "filters": _normalize_filters(filters),
        }
    }
    return make_request("POST", _data_url(entity, "remove"), body, token=token)


# ---------------------------------------------------------------------------
# File upload (multipart)
# ---------------------------------------------------------------------------

def _build_multipart(meta, file_path):
    """Build a minimal multipart/form-data body."""
    boundary = "----SuppaBoundary" + uuid.uuid4().hex
    fname = os.path.basename(file_path)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    with open(file_path, "rb") as fh:
        file_bytes = fh.read()
    crlf = b"\r\n"
    parts = []
    parts.append(("--" + boundary).encode())
    parts.append(b'Content-Disposition: form-data; name="meta"')
    parts.append(b"")
    parts.append(json.dumps(meta, ensure_ascii=False).encode("utf-8"))
    parts.append(("--" + boundary).encode())
    parts.append(
        ('Content-Disposition: form-data; name="files"; filename="'
         + fname + '"').encode("utf-8")
    )
    parts.append(("Content-Type: " + ctype).encode())
    parts.append(b"")
    parts.append(file_bytes)
    parts.append(("--" + boundary + "--").encode())
    parts.append(b"")
    body = crlf.join(parts)
    return body, "multipart/form-data; boundary=" + boundary


def upload_file_to_attachments(record_id, file_path, *,
                               tasks_entity_id=None, token=None):
    """POST /api/core/files/upload as multipart."""
    eid = tasks_entity_id or TASKS_ENTITY_ID
    if not eid:
        raise RuntimeError(
            "Tasks numeric entity id unknown. Run `discover` and set "
            "SUPPA_TASKS_ENTITY_ID env var, or pass --tasks-entity-id."
        )
    meta = {
        "entityId": int(eid),
        "recordId": int(record_id),
        "entityFieldName": "attachments",
        "entityName": None,
        "type": None,
    }
    body, content_type = _build_multipart(meta, file_path)
    url = BASE_URL.rstrip("/") + "/api/core/files/upload"
    headers = {
        "Authorization": "Bearer " + (token or _get_token()),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": content_type,
        "x-current-language": DEFAULT_LANG,
        "x-timezone": DEFAULT_TZ,
        "x-view-mode": "view",
    }
    req = Request(url, data=body, method="POST", headers=headers)
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        sys.stderr.write(
            "HTTP {0} {1}\n{2}\nResponse:\n{3}\n".format(
                e.code, e.reason, url, raw[:4000]
            )
        )
        sys.exit(1)
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return raw


# ---------------------------------------------------------------------------
# Filter / field helpers
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
# Domain field shapes — task searches
# ---------------------------------------------------------------------------

TASK_LIST_FIELDS = {
    "id": True,
    "title": True,
    "createdAt": True,
    "updatedAt": True,
    "deadline": True,
    "estimatedDuration": True,
    "plannedDuration": True,
    "assignedTo": {
        "id": True, "firstName": True, "lastName": True, "fullName": True,
    },
    "author": {"id": True, "fullName": True},
    "project": {"id": True, "title": True},
    "parent": {"id": True, "title": True},
    "stage": {
        "id": True, "name": True, "color": True,
        "workflow": {"id": True, "name": True},
        "status": {"value": True},
    },
    "workflow": {"id": True, "name": True},
    "priority": {"id": True, "title": True, "name": True, "value": True},
    "type": {"id": True, "title": True, "color": True},
    "tags": {"id": True, "name": True},
}

TASK_DETAIL_FIELDS = dict(TASK_LIST_FIELDS, **{
    "htmlDescription": True,
    "plainDescription": True,
    "closedAt": True,
    "closedBy": {"id": True, "fullName": True},
    "editors": {"id": True, "fullName": True},
    "watchers": {"id": True, "fullName": True},
    "children": {"id": True, "title": True},
    "attachments": {"id": True, "fileName": True, "filePath": True},
})

USER_FIELDS = {
    "id": True, "firstName": True, "lastName": True, "fullName": True,
    "position": True, "avatar": {"id": True, "fileName": True},
}


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

def parse_human_date(s):
    """Accept ISO, Y-m-d, 'today', 'tomorrow', '+Nd|+Nh|+Nm'. Returns ISO-8601."""
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    now = datetime.now().astimezone()
    if s.lower() == "today":
        dt = now.replace(hour=18, minute=0, second=0, microsecond=0)
    elif s.lower() == "tomorrow":
        dt = (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
    elif re.match(r"^\+(\d+)([dhm])$", s):
        m = re.match(r"^\+(\d+)([dhm])$", s)
        n = int(m.group(1))
        unit = m.group(2)
        delta = {"d": timedelta(days=n), "h": timedelta(hours=n), "m": timedelta(minutes=n)}[unit]
        dt = now + delta
    else:
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(s, fmt).astimezone()
                break
            except ValueError:
                continue
        else:
            return s
    return dt.isoformat()


# ---------------------------------------------------------------------------
# CLI command implementations
# ---------------------------------------------------------------------------

def cmd_get_me(args):
    body = {
        "fields": dict(USER_FIELDS, **{
            "createdAt": True, "updatedAt": True,
            "roles": {"id": True, "name": True},
        }),
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


def cmd_search_tasks(args):
    filters = []
    if args.my:
        filters.append(_filter("assignedTo", "$current-user", "="))
    if args.assigned_to:
        filters.append(_filter("assignedTo.id", int(args.assigned_to), "="))
    if args.active:
        filters.append(_filter("stage.status.value", STAGE_STATUS_OPEN_VALUES, "in"))
    if args.project:
        filters.append(_filter("project.id", int(args.project), "="))
    if args.workflow:
        filters.append(_filter("workflow.id", int(args.workflow), "="))
    if args.stage:
        filters.append(_filter("stage.id", int(args.stage), "="))
    if args.search:
        filters.append(_filter("title", args.search, "like"))
    if args.filter_json:
        for f in json.loads(args.filter_json):
            filters.append(f)

    order_by = [{"field": args.order_by, "order": args.order_dir}] if args.order_by else None
    res = search_entity(
        ENTITY_TASKS,
        filters=filters,
        fields=TASK_LIST_FIELDS,
        limit=args.limit,
        offset=args.offset,
        order_by=order_by,
        search_value=args.search_value or "",
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_count_tasks(args):
    filters = []
    if args.my:
        filters.append(_filter("assignedTo", "$current-user", "="))
    if args.active:
        filters.append(_filter("stage.status.value", STAGE_STATUS_OPEN_VALUES, "in"))
    if args.filter_json:
        for f in json.loads(args.filter_json):
            filters.append(f)
    n = count_entity(ENTITY_TASKS, filters=filters)
    print(json.dumps({"count": n}, indent=2))


def cmd_get_task(args):
    res = select_entity_by_id(ENTITY_TASKS, int(args.id), fields=TASK_DETAIL_FIELDS)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_create_task(args):
    fields = {"title": args.title}
    if args.description:
        fields["htmlDescription"] = args.description
    if args.assigned_to:
        fields["assignedTo"] = {"id": int(args.assigned_to)}
    if args.project:
        fields["project"] = {"id": int(args.project)}
    if args.parent:
        fields["parent"] = {"id": int(args.parent)}
    if args.type_id:
        fields["type"] = {"id": int(args.type_id)}
    if args.workflow:
        fields["workflow"] = {"id": int(args.workflow)}
    if args.stage:
        fields["stage"] = {"id": int(args.stage)}
    if args.priority:
        fields["priority"] = {"id": int(args.priority)}
    if args.deadline:
        fields["deadline"] = parse_human_date(args.deadline)
    if args.fields_json:
        fields.update(json.loads(args.fields_json))

    returning = TASK_DETAIL_FIELDS
    res = insert_entity(ENTITY_TASKS, [fields], returning=returning)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_update_task(args):
    fields = {}
    if args.title is not None:
        fields["title"] = args.title
    if args.description is not None:
        fields["htmlDescription"] = args.description
    if args.assigned_to is not None:
        fields["assignedTo"] = {"id": int(args.assigned_to)}
    if args.priority is not None:
        fields["priority"] = {"id": int(args.priority)}
    if args.stage is not None:
        fields["stage"] = {"id": int(args.stage)}
    if args.deadline is not None:
        fields["deadline"] = parse_human_date(args.deadline)
    if args.fields_json:
        fields.update(json.loads(args.fields_json))
    if not fields:
        sys.stderr.write("Nothing to update. Pass at least one of --title, --description, --assigned-to, --priority, --stage, --deadline, --fields-json.\n")
        sys.exit(2)
    res = update_entity_by_id(ENTITY_TASKS, int(args.id), fields)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_delete_task(args):
    res = remove_entity(ENTITY_TASKS, filters=[_filter("id", int(args.id), "=")])
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_move_task(args):
    res = update_entity_by_id(
        ENTITY_TASKS, int(args.id), {"stage": {"id": int(args.stage)}}
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_close_task(args):
    """Move a task to its workflow's first stage with status.value in CLOSED set."""
    task = select_entity_by_id(
        ENTITY_TASKS, int(args.id),
        fields={"id": True, "workflow": {"id": True}},
    )
    if not task or not task.get("workflow", {}).get("id"):
        sys.stderr.write("Could not resolve workflow for task " + args.id + "\n")
        sys.exit(1)
    wf_id = int(task["workflow"]["id"])
    stages = _list_stages(wf_id)
    closed = next(
        (s for s in stages
         if (s.get("status") or {}).get("value") in STAGE_STATUS_CLOSED_VALUES),
        None,
    )
    if not closed:
        sys.stderr.write("No stage with status.value in {0} found in workflow ".format(STAGE_STATUS_CLOSED_VALUES) + str(wf_id) + "\n")
        sys.exit(1)
    res = update_entity_by_id(
        ENTITY_TASKS, int(args.id), {"stage": {"id": int(closed["id"])}}
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_add_comment(args):
    user_id = int(args.user) if args.user else _resolve_current_user_id()
    content = args.content

    if args.mention:
        for spec in args.mention:
            uid_str, _, display = spec.partition(":")
            uid = int(uid_str.strip())
            disp = display.strip() or ("User " + str(uid))
            mention_html = (
                '<a class="mention-user" id="mention-' + str(uid)
                + '" data-id="' + str(uid) + '">@' + _html_escape(disp)
                + '</a>&nbsp;'
            )
            content = mention_html + content

    if not content.lstrip().startswith("<"):
        content = "<p>" + _html_escape(content) + "</p>"
    body = {
        "fields": [
            {
                "owner": {"id": int(args.task)},
                "user": {"id": user_id},
                "content": content,
            }
        ]
    }
    res = make_request("POST", _data_url(ENTITY_TASK_COMMENTS, "insert"), body)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_get_comments(args):
    filters = [_filter("owner.id", int(args.task), "=")]
    res = search_entity(
        ENTITY_TASK_COMMENTS,
        filters=filters,
        fields={
            "id": True,
            "content": True,
            "createdAt": True,
            "updatedAt": True,
            "user": {"id": True, "fullName": True, "avatar": {"id": True, "fileName": True}},
            "owner": {"id": True},
        },
        limit=args.limit,
        offset=args.offset,
        order_by=[{"field": "createdAt", "order": "asc"}],
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_list_workflows(args):
    filters = []
    if args.name:
        filters.append(_filter("workflow.name", args.name, "like"))
    body = {
        "conditions": {"operator": "and", "filters": _normalize_filters(filters)},
        "limit": args.limit,
        "offset": 0,
        "orderBy": [{"field": "workflow.name", "order": "asc"}],
        "searchValue": "",
        "fields": {"workflow": {"id": True, "name": True}, "id": "#count"},
        "groupBy": [{"field": "workflow.id"}],
        "includeDeletedRelations": True,
    }
    res = make_request("POST", _data_url(ENTITY_WORKFLOWS, "search"), body)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def _list_stages(workflow_id):
    """Internal helper: returns list of stages for a workflow."""
    body = {
        "conditions": {
            "operator": "and",
            "filters": [_filter("workflow.id", int(workflow_id), "=")],
        },
        "fields": {
            "id": True, "name": True, "color": True,
            "status": {"id": True, "name": True, "value": True, "title": True},
            "workflow": {"id": True, "name": True},
            "createdAt": True,
        },
        "limit": 200, "offset": 0,
        "orderBy": [{"field": "order", "order": "asc"}],
        "searchValue": "",
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    res = make_request("POST", _data_url(ENTITY_WORKFLOWS, "search"), body)
    if isinstance(res, dict):
        for k in ("data", "rows", "items", "result"):
            if isinstance(res.get(k), list):
                return res[k]
    if isinstance(res, list):
        return res
    return []


def cmd_list_stages(args):
    res = _list_stages(int(args.workflow))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_list_task_types(args):
    body = {
        "fields": {
            "id": True, "title": True, "color": True,
            "icon": {"name": True, "id": True},
            "allowedTypes": {"id": True, "title": True},
        },
        "conditions": {
            "operator": "and",
            "filters": [_filter("title", args.name or "", "like")],
        },
    }
    res = make_request("POST", _data_url(ENTITY_TASK_TYPES, "select"), body)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_attach_file(args):
    res = upload_file_to_attachments(
        record_id=int(args.task),
        file_path=args.file,
        tasks_entity_id=int(args.tasks_entity_id) if args.tasks_entity_id else None,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_discover(args):
    """Probe API for hardcodable per-tenant constants."""
    report = {}

    report["current_user_id"] = _resolve_current_user_id()

    # Workflows + stages
    wf_body = {
        "conditions": {"operator": "and", "filters": []},
        "limit": 200, "offset": 0,
        "orderBy": [{"field": "workflow.name", "order": "asc"}],
        "searchValue": "",
        "fields": {"workflow": {"id": True, "name": True}, "id": "#count"},
        "groupBy": [{"field": "workflow.id"}],
        "includeDeletedRelations": False,
    }
    wf_res = make_request("POST", _data_url(ENTITY_WORKFLOWS, "search"), wf_body)
    workflows = []
    arr = wf_res if isinstance(wf_res, list) else (
        (wf_res or {}).get("data") or (wf_res or {}).get("rows") or []
    )
    for row in arr if isinstance(arr, list) else []:
        wf = row.get("workflow") or {}
        if wf.get("id"):
            workflows.append({"id": wf["id"], "name": wf.get("name")})
    report["workflows"] = workflows

    # Stages per workflow grouped by status
    status_index = {}
    for wf in workflows:
        stages = _list_stages(wf["id"])
        for s in stages:
            sv = ((s.get("status") or {}).get("value")) or "unknown"
            status_index.setdefault(sv, []).append({
                "stage_id": s.get("id"),
                "stage_name": s.get("name"),
                "workflow_id": wf["id"],
                "workflow_name": wf["name"],
            })
    report["stages_by_status_value"] = status_index

    # Task types
    try:
        tt_body = {
            "conditions": {"operator": "and", "filters": []},
            "fields": {"id": True, "title": True, "color": True},
            "limit": 200, "offset": 0,
            "orderBy": [{"field": "title", "order": "asc"}],
            "searchValue": "",
            "getAccessByFields": False,
            "includeDeletedRelations": False,
        }
        tt_res = make_request("POST", _data_url(ENTITY_TASK_TYPES, "search"), tt_body)
        tt_arr = tt_res if isinstance(tt_res, list) else (
            (tt_res or {}).get("data") or (tt_res or {}).get("rows") or []
        )
        report["task_types"] = [
            {"id": t.get("id"), "title": t.get("title")}
            for t in tt_arr if isinstance(t, dict)
        ]
    except (SystemExit, Exception) as exc:
        report["task_types"] = "<request failed: {0}>".format(exc)

    # Tasks numeric entity id
    try:
        schema = make_request("GET", "/api/core/schema/Tasks", body=None)
        ent_id = None
        if isinstance(schema, dict):
            ent_id = schema.get("id") or schema.get("entityId")
        report["tasks_entity_id"] = ent_id
    except (SystemExit, Exception) as exc:
        report["tasks_entity_id"] = "<schema endpoint failed: {0}>".format(exc)

    # Priorities
    try:
        sample_body = {
            "conditions": {"operator": "and", "filters": []},
            "fields": {
                "id": True, "title": True,
                "priority": {"id": True, "title": True, "name": True, "value": True, "icon": True},
            },
            "limit": 10, "offset": 0,
            "orderBy": [{"field": "createdAt", "order": "desc"}],
            "searchValue": "",
            "getAccessByFields": False,
            "includeDeletedRelations": False,
        }
        sample = make_request("POST", _data_url(ENTITY_TASKS, "search"), sample_body)
        seen = {}
        for row in (sample if isinstance(sample, list) else []):
            p = row.get("priority") if isinstance(row, dict) else None
            if isinstance(p, dict) and p.get("id") and p["id"] not in seen:
                seen[p["id"]] = {k: p.get(k) for k in ("id", "title", "name", "value", "icon")}
        report["priorities_seen_on_tasks"] = list(seen.values())
    except (SystemExit, Exception) as exc:
        report["priorities_seen_on_tasks"] = "<request failed: {0}>".format(exc)

    print(json.dumps(report, indent=2, ensure_ascii=False))


def cmd_search_users(args):
    filters = []
    if args.id:
        filters.append(_filter("id", int(args.id), "="))
    if args.name:
        filters.append(_filter("fullName", args.name, "like"))
    res = search_entity(
        ENTITY_USERS,
        filters=filters,
        fields=USER_FIELDS,
        limit=args.limit,
        offset=0,
        order_by=[{"field": "fullName", "order": "asc"}],
        search_value=args.search_value or "",
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_raw(args):
    """Run an arbitrary POST against any entity action."""
    if args.body:
        body = json.loads(args.body)
    else:
        body = json.loads(sys.stdin.read())
    res = make_request("POST", _data_url(args.entity, args.action or "search"), body)
    print(json.dumps(res, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def _html_escape(text):
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


_CACHED_ME_ID = None
def _resolve_current_user_id():
    global _CACHED_ME_ID
    if _CACHED_ME_ID is not None:
        return _CACHED_ME_ID
    body = {
        "fields": {"id": True, "firstName": True, "lastName": True, "fullName": True},
        "conditions": {"operator": "and", "filters": [_filter("id", "$current-user", "=")]},
        "limit": 1,
        "offset": 0,
        "orderBy": [{"field": "id", "order": "asc"}],
        "searchValue": "",
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    res = make_request("POST", _data_url(ENTITY_USERS, "select") + "?markAsView=false", body)
    if isinstance(res, dict):
        for k in ("data", "rows", "items", "result"):
            arr = res.get(k)
            if isinstance(arr, list) and arr and isinstance(arr[0], dict) and "id" in arr[0]:
                _CACHED_ME_ID = int(arr[0]["id"])
                return _CACHED_ME_ID
    if isinstance(res, list) and res and isinstance(res[0], dict) and "id" in res[0]:
        _CACHED_ME_ID = int(res[0]["id"])
        return _CACHED_ME_ID
    raise RuntimeError(
        "Could not resolve current user id from response: " + json.dumps(res)[:500]
    )


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(
        prog="suppa_api.py",
        description="Suppa Tasks API client for modern.suppa.me",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("get-me", help="Current authenticated user").set_defaults(func=cmd_get_me)

    st = sub.add_parser("search-tasks", help="Search tasks")
    st.add_argument("--my", action="store_true", help="Only tasks assigned to me")
    st.add_argument("--active", action="store_true", help="Only open/in-progress tasks")
    st.add_argument("--assigned-to", help="User ID")
    st.add_argument("--project", help="Project ID")
    st.add_argument("--workflow", help="Workflow ID")
    st.add_argument("--stage", help="Stage ID")
    st.add_argument("--search", help="Substring match on title")
    st.add_argument("--search-value", help="Server-side full-text search value")
    st.add_argument("--filter-json", help="Extra filters as JSON array")
    st.add_argument("--order-by", default="createdAt")
    st.add_argument("--order-dir", default="desc", choices=["asc", "desc"])
    st.add_argument("--limit", type=int, default=50)
    st.add_argument("--offset", type=int, default=0)
    st.set_defaults(func=cmd_search_tasks)

    ct = sub.add_parser("count-tasks", help="Count tasks")
    ct.add_argument("--my", action="store_true")
    ct.add_argument("--active", action="store_true")
    ct.add_argument("--filter-json")
    ct.set_defaults(func=cmd_count_tasks)

    gt = sub.add_parser("get-task", help="Get a task by id")
    gt.add_argument("id", help="Integer task id")
    gt.set_defaults(func=cmd_get_task)

    ct2 = sub.add_parser("create-task", help="Create a task")
    ct2.add_argument("--title", required=True)
    ct2.add_argument("--description")
    ct2.add_argument("--assigned-to")
    ct2.add_argument("--project")
    ct2.add_argument("--parent")
    ct2.add_argument("--type-id", help="Task type id")
    ct2.add_argument("--workflow")
    ct2.add_argument("--stage")
    ct2.add_argument("--priority")
    ct2.add_argument("--deadline", help="ISO date, 'today', 'tomorrow', '+3d', etc.")
    ct2.add_argument("--fields-json", help="Extra fields as JSON object")
    ct2.set_defaults(func=cmd_create_task)

    ut = sub.add_parser("update-task", help="Update fields on an existing task")
    ut.add_argument("id", help="Integer task id")
    ut.add_argument("--title")
    ut.add_argument("--description", help="HTML for htmlDescription")
    ut.add_argument("--assigned-to")
    ut.add_argument("--priority")
    ut.add_argument("--stage")
    ut.add_argument("--deadline")
    ut.add_argument("--fields-json", help="Extra fields as JSON object (merged)")
    ut.set_defaults(func=cmd_update_task)

    dt = sub.add_parser("delete-task", help="Soft-delete a task by id")
    dt.add_argument("id")
    dt.set_defaults(func=cmd_delete_task)

    mt = sub.add_parser("move-task", help="Move task to another stage")
    mt.add_argument("id")
    mt.add_argument("--stage", required=True, help="Target stage id")
    mt.set_defaults(func=cmd_move_task)

    ko = sub.add_parser("close-task", help="Move task to its workflow's closed stage")
    ko.add_argument("id")
    ko.set_defaults(func=cmd_close_task)

    ac = sub.add_parser("add-comment", help="Add comment to a task")
    ac.add_argument("--task", required=True, help="Task ID (integer)")
    ac.add_argument("--content", required=True, help="HTML or plain text")
    ac.add_argument("--user", help="Author user id (defaults to current user)")
    ac.add_argument("--mention", action="append",
                    help="Prepend a mention. Format: 'USER_ID:Display Name' (repeatable)")
    ac.set_defaults(func=cmd_add_comment)

    gc = sub.add_parser("get-comments", help="Get comments for a task")
    gc.add_argument("--task", required=True)
    gc.add_argument("--limit", type=int, default=100)
    gc.add_argument("--offset", type=int, default=0)
    gc.set_defaults(func=cmd_get_comments)

    lw = sub.add_parser("list-workflows", help="List workflows")
    lw.add_argument("--name", help="Substring filter on workflow.name")
    lw.add_argument("--limit", type=int, default=100)
    lw.set_defaults(func=cmd_list_workflows)

    ls = sub.add_parser("list-stages", help="List stages of a workflow")
    ls.add_argument("--workflow", required=True, help="Workflow id (int)")
    ls.set_defaults(func=cmd_list_stages)

    ltt = sub.add_parser("list-task-types", help="List TasksTypes")
    ltt.add_argument("--name", help="Substring filter on title")
    ltt.set_defaults(func=cmd_list_task_types)

    af = sub.add_parser("attach-file", help="Upload a file as attachment to a task")
    af.add_argument("--task", required=True, help="Task id (integer)")
    af.add_argument("--file", required=True, help="Local path to file")
    af.add_argument("--tasks-entity-id",
                    help="Numeric entityId of Tasks (env SUPPA_TASKS_ENTITY_ID also works)")
    af.set_defaults(func=cmd_attach_file)

    dc = sub.add_parser("discover", help="Probe API for per-tenant constants")
    dc.set_defaults(func=cmd_discover)

    su = sub.add_parser("search-users", help="Search users")
    su.add_argument("--name", help="Substring filter on fullName")
    su.add_argument("--id", help="Exact user id")
    su.add_argument("--search-value", help="Server-side full-text search value")
    su.add_argument("--limit", type=int, default=50)
    su.set_defaults(func=cmd_search_users)

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
