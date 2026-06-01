"""Tasks, Comments, Workflows, Stages, Users tools."""

import json
import os
import uuid
from typing import Optional

from suppa_mcp.http_client import (
    make_request, make_request_raw_bytes, data_url, search_entity,
    select_entity, insert_entity, update_entity, remove_entity,
)
from suppa_mcp.utils import make_filter, parse_deadline, wrap_html, json_response
from suppa_mcp import config


# ---------------------------------------------------------------------------
# Field projections
# ---------------------------------------------------------------------------

TASK_LIST_FIELDS = {
    "id": True, "title": True, "shortID": True,
    "deadline": True, "createdAt": True, "updatedAt": True,
    "estimatedDuration": True,
    "assignedTo": {"id": True, "firstName": True, "lastName": True, "fullName": True},
    "author": {"id": True, "fullName": True},
    "project": {"id": True, "title": True},
    "parent": {"id": True, "title": True},
    "stage": {"id": True, "name": True, "color": True,
              "workflow": {"id": True, "name": True},
              "status": {"value": True}},
    "workflow": {"id": True, "name": True},
    "priority": {"id": True, "title": True, "name": True, "value": True},
    "type": {"id": True, "title": True, "color": True},
    "tags": {"id": True, "name": True},
}

TASK_DETAIL_FIELDS = {
    **TASK_LIST_FIELDS,
    "htmlDescription": True,
    "plainDescription": True,
    "closedAt": True,
    "closedBy": {"id": True, "fullName": True},
    "editors": {"id": True, "fullName": True},
    "watchers": {"id": True, "fullName": True},
    "children": {"id": True, "title": True},
    "attachments": {"id": True, "fileName": True, "filePath": True},
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def get_me() -> str:
    """Get the current authenticated user's profile."""
    result = select_entity(
        "Users",
        [make_filter("id", "$current-user")],
        {"id": True, "firstName": True, "lastName": True, "fullName": True,
         "position": True, "avatar": {"id": True, "fileName": True},
         "createdAt": True, "roles": {"id": True, "name": True}},
    )
    return json_response(result)


def search_tasks(
    search: str = "",
    my: bool = False,
    active: bool = False,
    overdue: bool = False,
    due_today: bool = False,
    project_id: Optional[int] = None,
    workflow_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search tasks with filters. Use 'my' for current user's tasks, 'active' for open tasks."""
    filters = []
    if my:
        filters.append(make_filter("assignedTo", "$current-user"))
    if active:
        filters.append(make_filter("stage.status.value", ["active", "inprogress"], "in"))
    if overdue:
        from datetime import datetime, timezone
        filters.append(make_filter("deadline", datetime.now(timezone.utc).isoformat(), "<"))
        filters.append(make_filter("stage.status.value", ["active", "inprogress"], "in"))
    if due_today:
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0).isoformat()
        end = now.replace(hour=23, minute=59, second=59).isoformat()
        filters.append(make_filter("deadline", start, ">="))
        filters.append(make_filter("deadline", end, "<="))
    if project_id:
        filters.append(make_filter("project", {"id": project_id}))
    if workflow_id:
        filters.append(make_filter("workflow", {"id": workflow_id}))
    if stage_id:
        filters.append(make_filter("stage", {"id": stage_id}))
    if assigned_to_id:
        filters.append(make_filter("assignedTo", {"id": assigned_to_id}))

    results = search_entity("Tasks", filters, TASK_LIST_FIELDS, limit, offset,
                           search_value=search)
    return json_response(results)


def count_tasks(
    my: bool = False,
    active: bool = False,
    project_id: Optional[int] = None,
    workflow_id: Optional[int] = None,
    search: str = "",
) -> str:
    """Count tasks matching filters without returning full data."""
    filters = []
    if my:
        filters.append(make_filter("assignedTo", "$current-user"))
    if active:
        filters.append(make_filter("stage.status.value", ["active", "inprogress"], "in"))
    if project_id:
        filters.append(make_filter("project", {"id": project_id}))
    if workflow_id:
        filters.append(make_filter("workflow", {"id": workflow_id}))

    body = {
        "conditions": {"operator": "and", "filters": filters},
        "fields": {},
        "limit": 0, "offset": 0,
        "orderBy": [],
        "searchValue": search,
        "aggregates": [{"function": "count", "field": "id", "alias": "total"}],
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    result = make_request("POST", data_url("Tasks", "search"), body)
    if isinstance(result, dict) and "aggregates" in result:
        return json_response({"count": result["aggregates"].get("total", 0)})
    return json_response({"count": 0})


def get_task(task_id: int) -> str:
    """Get full details of a single task by ID."""
    result = select_entity("Tasks", [make_filter("id", task_id)], TASK_DETAIL_FIELDS)
    return json_response(result)


def create_task(
    title: str,
    description: str = "",
    assigned_to_id: Optional[int] = None,
    project_id: Optional[int] = None,
    workflow_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    type_id: Optional[int] = None,
    priority_id: Optional[int] = None,
    deadline: Optional[str] = None,
    parent_id: Optional[int] = None,
) -> str:
    """Create a new task. Description supports HTML. Deadline accepts 'today', 'tomorrow', '+3d', or ISO datetime."""
    fields: dict = {"title": title}
    if description:
        fields["htmlDescription"] = wrap_html(description)
    if assigned_to_id:
        fields["assignedTo"] = {"id": assigned_to_id}
    if project_id:
        fields["project"] = {"id": project_id}
    if workflow_id:
        fields["workflow"] = {"id": workflow_id}
    if stage_id:
        fields["stage"] = {"id": stage_id}
    if type_id:
        fields["type"] = {"id": type_id}
    if priority_id:
        fields["priority"] = {"id": priority_id}
    if deadline:
        fields["deadline"] = parse_deadline(deadline)
    if parent_id:
        fields["parent"] = {"id": parent_id}

    result = insert_entity("Tasks", [fields])
    return json_response(result[0] if result else None)


def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    project_id: Optional[int] = None,
    workflow_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    type_id: Optional[int] = None,
    priority_id: Optional[int] = None,
    deadline: Optional[str] = None,
) -> str:
    """Update fields on an existing task."""
    fields: dict = {}
    if title is not None:
        fields["title"] = title
    if description is not None:
        fields["htmlDescription"] = wrap_html(description)
    if assigned_to_id is not None:
        fields["assignedTo"] = {"id": assigned_to_id}
    if project_id is not None:
        fields["project"] = {"id": project_id}
    if workflow_id is not None:
        fields["workflow"] = {"id": workflow_id}
    if stage_id is not None:
        fields["stage"] = {"id": stage_id}
    if type_id is not None:
        fields["type"] = {"id": type_id}
    if priority_id is not None:
        fields["priority"] = {"id": priority_id}
    if deadline is not None:
        fields["deadline"] = parse_deadline(deadline)

    if not fields:
        return json_response({"error": "No fields to update"})

    result = update_entity("Tasks", task_id, fields)
    return json_response(result)


def delete_task(task_id: int) -> str:
    """Soft-delete a task by ID."""
    result = remove_entity("Tasks", [make_filter("id", task_id)])
    return json_response(result)


def move_task(task_id: int, stage_id: int) -> str:
    """Move a task to a different stage."""
    result = update_entity("Tasks", task_id, {"stage": {"id": stage_id}})
    return json_response(result)


def close_task(task_id: int) -> str:
    """Close a task by moving it to the workflow's completed stage."""
    # Get task's workflow
    task = select_entity("Tasks", [make_filter("id", task_id)],
                        {"id": True, "workflow": {"id": True, "name": True},
                         "stage": {"id": True, "name": True, "status": {"id": True, "value": True}}})
    if not task or not task.get("workflow"):
        return json_response({"error": "Task has no workflow — cannot close"})

    wf_id = task["workflow"]["id"]
    # Find the completed stage
    stages = search_entity("StageWorkflows",
                          [make_filter("workflow", {"id": wf_id}),
                           make_filter("status.value", "completed")],
                          {"id": True, "name": True, "status": {"id": True, "value": True}},
                          limit=5)
    if not stages:
        return json_response({"error": f"No completed stage found in workflow {wf_id}"})

    closed_stage_id = stages[0]["id"]
    result = update_entity("Tasks", task_id, {"stage": {"id": closed_stage_id}})
    return json_response(result)


def _resolve_current_user_id() -> int:
    """Resolve the numeric id of the authenticated user."""
    me = select_entity("Users", [make_filter("id", "$current-user")],
                       {"id": True, "fullName": True})
    if isinstance(me, dict) and me.get("id") is not None:
        return int(me["id"])
    raise RuntimeError("Could not resolve current user id")


def add_comment(
    task_id: int,
    content: str,
    mention_ids: Optional[str] = None,
) -> str:
    """Add a comment to a task. Content supports HTML. mention_ids: comma-separated 'id:Name' pairs."""
    html = content

    # Process mentions (prepended, matching platform format)
    if mention_ids:
        for part in mention_ids.split(","):
            part = part.strip()
            if ":" in part:
                uid, name = part.split(":", 1)
                uid = uid.strip()
                name = name.strip()
                mention_tag = (
                    f'<a class="mention-user" id="mention-{uid}" '
                    f'data-id="{uid}">@{name}</a>&nbsp;'
                )
                html = mention_tag + html

    if not html.lstrip().startswith("<"):
        html = wrap_html(html)

    fields: dict = {
        "owner": {"id": task_id},
        "user": {"id": _resolve_current_user_id()},
        "content": html,
    }
    result = insert_entity("TasksComments", [fields])
    return json_response(result[0] if result else None)


def get_comments(task_id: int, limit: int = 30) -> str:
    """Get comments for a task."""
    results = search_entity(
        "TasksComments",
        [make_filter("owner.id", task_id)],
        {"id": True, "content": True, "createdAt": True, "updatedAt": True,
         "user": {"id": True, "fullName": True}},
        limit=limit,
        order_by=[{"field": "createdAt", "order": "asc"}],
    )
    return json_response(results)


def attach_file(task_id: int, file_path: str) -> str:
    """Upload a file and attach it to a task. Provide the absolute file path."""
    if not os.path.isfile(file_path):
        return json_response({"error": f"File not found: {file_path}"})

    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_data = f.read()

    import mimetypes
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    meta = {
        "entityId": int(config.TASKS_ENTITY_ID),
        "recordId": int(task_id),
        "entityFieldName": "attachments",
        "entityName": None,
        "type": None,
    }

    # Build multipart body (meta JSON part + files part), matching platform API
    boundary = "----SuppaBoundary" + uuid.uuid4().hex
    lines = []
    lines.append(f"--{boundary}".encode())
    lines.append(b'Content-Disposition: form-data; name="meta"')
    lines.append(b"")
    lines.append(json.dumps(meta, ensure_ascii=False).encode("utf-8"))
    lines.append(f"--{boundary}".encode())
    lines.append(
        f'Content-Disposition: form-data; name="files"; filename="{filename}"'.encode("utf-8")
    )
    lines.append(f"Content-Type: {ctype}".encode())
    lines.append(b"")
    lines.append(file_data)
    lines.append(f"--{boundary}--".encode())
    lines.append(b"")

    body = b"\r\n".join(lines)
    content_type = f"multipart/form-data; boundary={boundary}"

    result = make_request_raw_bytes("POST", "/api/core/files/upload", body, content_type)
    return json_response(result)


def list_workflows(name: Optional[str] = None) -> str:
    """List all workflows (StageWorkflows grouped). Optionally filter by name."""
    filters = []
    if name:
        filters.append(make_filter("name", f"%{name}%", "like"))

    # Get unique workflows via stages
    results = search_entity(
        "StageWorkflows",
        filters,
        {"id": True, "name": True, "workflow": {"id": True, "name": True},
         "status": {"id": True, "value": True}, "order": True},
        limit=200,
        order_by=[{"field": "order", "order": "asc"}],
    )
    return json_response(results)


def list_stages(workflow_id: int) -> str:
    """List all stages in a workflow."""
    results = search_entity(
        "StageWorkflows",
        [make_filter("workflow", {"id": workflow_id})],
        {"id": True, "name": True, "status": {"id": True, "value": True}, "order": True},
        limit=100,
        order_by=[{"field": "order", "order": "asc"}],
    )
    return json_response(results)


def list_task_types() -> str:
    """List all available task types."""
    results = search_entity(
        "TasksTypes",
        [],
        {"id": True, "title": True},
        limit=100,
    )
    return json_response(results)


def search_users(name: str = "", limit: int = 20) -> str:
    """Search users by name."""
    filters = []
    if name:
        filters.append(make_filter("fullName", f"%{name}%", "like"))
    results = search_entity(
        "Users", filters,
        {"id": True, "fullName": True, "firstName": True, "lastName": True,
         "position": True, "avatar": {"id": True, "fileName": True}},
        limit=limit,
    )
    return json_response(results)
