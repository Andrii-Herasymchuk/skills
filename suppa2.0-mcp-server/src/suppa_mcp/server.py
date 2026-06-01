"""Suppa MCP Server — unified gateway to the Suppa platform."""

from mcp.server.fastmcp import FastMCP

from suppa_mcp.tools import tasks, docs, entity, forms

mcp = FastMCP(
    "suppa",
    instructions="""Suppa Platform MCP Server — provides tools to manage Tasks, Docs/Pages, Entities, and Forms on modern.suppa.me.

Key concepts:
- IDs are integers (not UUIDs)
- Dates are ISO-8601 strings
- HTML content: wrap plain text in <p>...</p>, or pass raw HTML starting with <
- Relations: pass as {"id": N} when writing
- Filters: {"field": "name", "value": "...", "comparator": "="} — comparators: =, !=, <, >, <=, >=, like, in, is null, is not null
- The 'like' comparator requires SQL wildcards: %substring%
- Magic value "$current-user" resolves to the authenticated user's ID
""",
)


# ---------------------------------------------------------------------------
# Tasks tools
# ---------------------------------------------------------------------------

@mcp.tool()
def suppa_get_me() -> str:
    """Get the current authenticated user's profile (name, position, roles)."""
    return tasks.get_me()


@mcp.tool()
def suppa_search_tasks(
    search: str = "",
    my: bool = False,
    active: bool = False,
    overdue: bool = False,
    due_today: bool = False,
    project_id: int | None = None,
    workflow_id: int | None = None,
    stage_id: int | None = None,
    assigned_to_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Search tasks. Use my=true for your tasks, active=true for open tasks, or search by title substring."""
    return tasks.search_tasks(search, my, active, overdue, due_today,
                             project_id, workflow_id, stage_id, assigned_to_id, limit, offset)


@mcp.tool()
def suppa_count_tasks(
    my: bool = False,
    active: bool = False,
    project_id: int | None = None,
    workflow_id: int | None = None,
    search: str = "",
) -> str:
    """Count tasks matching filters without returning full data."""
    return tasks.count_tasks(my, active, project_id, workflow_id, search)


@mcp.tool()
def suppa_get_task(task_id: int) -> str:
    """Get full details of a task by its ID."""
    return tasks.get_task(task_id)


@mcp.tool()
def suppa_create_task(
    title: str,
    description: str = "",
    assigned_to_id: int | None = None,
    project_id: int | None = None,
    workflow_id: int | None = None,
    stage_id: int | None = None,
    type_id: int | None = None,
    priority_id: int | None = None,
    deadline: str | None = None,
    parent_id: int | None = None,
) -> str:
    """Create a new task. Deadline accepts: 'today', 'tomorrow', '+3d', '+2h', or ISO datetime."""
    return tasks.create_task(title, description, assigned_to_id, project_id,
                            workflow_id, stage_id, type_id, priority_id, deadline, parent_id)


@mcp.tool()
def suppa_update_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    assigned_to_id: int | None = None,
    project_id: int | None = None,
    workflow_id: int | None = None,
    stage_id: int | None = None,
    type_id: int | None = None,
    priority_id: int | None = None,
    deadline: str | None = None,
) -> str:
    """Update fields on an existing task. Only provided fields are changed."""
    return tasks.update_task(task_id, title, description, assigned_to_id, project_id,
                           workflow_id, stage_id, type_id, priority_id, deadline)


@mcp.tool()
def suppa_delete_task(task_id: int) -> str:
    """Soft-delete a task."""
    return tasks.delete_task(task_id)


@mcp.tool()
def suppa_move_task(task_id: int, stage_id: int) -> str:
    """Move a task to a different workflow stage."""
    return tasks.move_task(task_id, stage_id)


@mcp.tool()
def suppa_close_task(task_id: int) -> str:
    """Close a task by moving it to the workflow's completed stage."""
    return tasks.close_task(task_id)


@mcp.tool()
def suppa_add_comment(
    task_id: int,
    content: str,
    mention_ids: str | None = None,
) -> str:
    """Add a comment to a task. Supports HTML. mention_ids: comma-separated 'userId:Name' pairs for @mentions."""
    return tasks.add_comment(task_id, content, mention_ids)


@mcp.tool()
def suppa_get_comments(task_id: int, limit: int = 30) -> str:
    """Get comments on a task."""
    return tasks.get_comments(task_id, limit)


@mcp.tool()
def suppa_attach_file(task_id: int, file_path: str) -> str:
    """Upload a local file and attach it to a task."""
    return tasks.attach_file(task_id, file_path)


@mcp.tool()
def suppa_list_workflows(name: str | None = None) -> str:
    """List all workflows. Optionally filter by name."""
    return tasks.list_workflows(name)


@mcp.tool()
def suppa_list_stages(workflow_id: int) -> str:
    """List all stages in a specific workflow."""
    return tasks.list_stages(workflow_id)


@mcp.tool()
def suppa_list_task_types() -> str:
    """List all available task types."""
    return tasks.list_task_types()


@mcp.tool()
def suppa_search_users(name: str = "", limit: int = 20) -> str:
    """Search users by name."""
    return tasks.search_users(name, limit)


# ---------------------------------------------------------------------------
# Docs tools
# ---------------------------------------------------------------------------

@mcp.tool()
def suppa_list_docs(search: str = "", limit: int = 20) -> str:
    """List documents, optionally filtering by title."""
    return docs.list_docs(search, limit)


@mcp.tool()
def suppa_get_doc(doc_id: int) -> str:
    """Get a document by ID including its page tree."""
    return docs.get_doc(doc_id)


@mcp.tool()
def suppa_create_doc(title: str, is_public: bool = False) -> str:
    """Create a new document."""
    return docs.create_doc(title, is_public)


@mcp.tool()
def suppa_update_doc(doc_id: int, title: str | None = None, is_public: bool | None = None) -> str:
    """Update a document's title or visibility."""
    return docs.update_doc(doc_id, title, is_public)


@mcp.tool()
def suppa_delete_doc(doc_id: int) -> str:
    """Delete a document."""
    return docs.delete_doc(doc_id)


@mcp.tool()
def suppa_list_pages(doc_id: int, limit: int = 50) -> str:
    """List all pages in a document."""
    return docs.list_pages(doc_id, limit)


@mcp.tool()
def suppa_get_page(page_id: int) -> str:
    """Get a page's metadata."""
    return docs.get_page(page_id)


@mcp.tool()
def suppa_create_page(
    doc_id: int,
    title: str,
    parent_id: int | None = None,
    description: str | None = None,
    icon: str | None = None,
) -> str:
    """Create a new page in a document."""
    return docs.create_page(doc_id, title, parent_id, description, icon)


@mcp.tool()
def suppa_update_page(
    page_id: int,
    title: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    is_public: bool | None = None,
) -> str:
    """Update a page's metadata."""
    return docs.update_page(page_id, title, description, icon, is_public)


@mcp.tool()
def suppa_delete_page(page_id: int) -> str:
    """Delete a page."""
    return docs.delete_page(page_id)


@mcp.tool()
def suppa_get_blocks(page_id: int) -> str:
    """Get all content blocks on a page in order (raw JSON with IDs and properties)."""
    return docs.get_blocks(page_id)


@mcp.tool()
def suppa_read_page(page_id: int) -> str:
    """Read a page as human-readable markdown-like text."""
    return docs.read_page(page_id)


@mcp.tool()
def suppa_create_blocks(page_id: int, blocks_json: str) -> str:
    """Create content blocks on a page (appended at end). blocks_json: JSON array of {type, title} objects.
    Types: text, head1, head2, head3, bulletList, numberedList, checkList, quote, callout, divider, code, table, toggle."""
    return docs.create_blocks(page_id, blocks_json)


@mcp.tool()
def suppa_insert_block(
    page_id: int,
    blocks_json: str,
    after_id: int | None = None,
    before_id: int | None = None,
) -> str:
    """Insert block(s) at a specific position. Provide after_id OR before_id as anchor.
    blocks_json: JSON array of {type, title} objects."""
    return docs.insert_block(page_id, blocks_json, after_id, before_id)


@mcp.tool()
def suppa_update_block(block_id: int, title: str | None = None, properties_json: str | None = None) -> str:
    """Update a block's content. Provide title (text/HTML) or full properties_json."""
    return docs.update_block(block_id, title, properties_json)


@mcp.tool()
def suppa_delete_block(block_id: int) -> str:
    """Delete a content block."""
    return docs.delete_block(block_id)


@mcp.tool()
def suppa_reorder_blocks(
    page_id: int,
    block_ids: str,
    after_id: int | None = None,
    before_id: int | None = None,
) -> str:
    """Reorder blocks on a page. block_ids: comma-separated IDs to move. Provide after_id or before_id as anchor."""
    return docs.reorder_blocks(page_id, block_ids, after_id, before_id)


# ---------------------------------------------------------------------------
# Entity tools
# ---------------------------------------------------------------------------

@mcp.tool()
def suppa_list_entities(search: str = "") -> str:
    """List all entities (database tables) on the platform. Optionally filter by name."""
    return entity.list_entities(search)


@mcp.tool()
def suppa_describe_entity(entity_name: str) -> str:
    """Get the full schema of an entity — all fields, types, relations, and constraints."""
    return entity.describe_entity(entity_name)


@mcp.tool()
def suppa_search_records(
    entity_name: str,
    filters_json: str = "[]",
    fields_json: str = '{"id": true}',
    limit: int = 20,
    offset: int = 0,
    search: str = "",
    order_by: str = "createdAt:desc",
) -> str:
    """Search records of any entity. filters_json: [{field, value, comparator}]. fields_json: {field: true}."""
    return entity.search_records(entity_name, filters_json, fields_json, limit, offset, search, order_by)


@mcp.tool()
def suppa_create_entity(name: str, title: str, title_field_name: str = "title") -> str:
    """Create a new entity (database table)."""
    return entity.create_entity(name, title, title_field_name)


@mcp.tool()
def suppa_add_field(
    entity_name: str,
    field_name: str,
    field_type: str,
    title: str | None = None,
    required: bool = False,
    unique: bool = False,
    relation_entity: str | None = None,
    enum_name: str | None = None,
) -> str:
    """Add a field to an entity. Types: text, integer, numeric, boolean, date, datetime, enum, relation, file, json, richtext, email, url, phone."""
    return entity.add_field(entity_name, field_name, field_type, title, required, unique, relation_entity, enum_name)


@mcp.tool()
def suppa_add_enum_values(enum_name: str, values: str) -> str:
    """Add values to an enum (lookup table). values: comma-separated list."""
    return entity.add_enum_values(enum_name, values)


@mcp.tool()
def suppa_list_field_types() -> str:
    """List all available field types for entity/form creation."""
    return entity.list_field_types()


@mcp.tool()
def suppa_create_record(entity_name: str, fields_json: str) -> str:
    """Create a record in any entity. fields_json: JSON object of field values."""
    return entity.create_record(entity_name, fields_json)


@mcp.tool()
def suppa_update_record(entity_name: str, record_id: int, fields_json: str) -> str:
    """Update a record in any entity. fields_json: JSON object of fields to change."""
    return entity.update_record(entity_name, record_id, fields_json)


@mcp.tool()
def suppa_delete_record(entity_name: str, record_id: int) -> str:
    """Delete a record from any entity."""
    return entity.delete_record(entity_name, record_id)


# ---------------------------------------------------------------------------
# Forms tools
# ---------------------------------------------------------------------------

@mcp.tool()
def suppa_list_forms(
    entity_name: str | None = None,
    form_type: str | None = None,
    limit: int = 50,
) -> str:
    """List forms. Optionally filter by entity name or form type (e.g. 'elementForm')."""
    return forms.list_forms(entity_name, form_type, limit)


@mcp.tool()
def suppa_get_form(form_id: int) -> str:
    """Get a form by ID with full schema (data.formShema) and settings."""
    return forms.get_form(form_id)


@mcp.tool()
def suppa_create_form(
    name: str,
    form_type: str = "elementForm",
    entity_name: str | None = None,
    alias: str | None = None,
    is_public: bool = False,
    schema_json: str | None = None,
    settings_json: str | None = None,
    generate_from_entity: bool = False,
    fields: str | None = None,
    columns: int = 1,
    module_code: str | None = None,
) -> str:
    """Create a new form. Provide schema_json (array of fields or {formShema}), or set
    generate_from_entity=True with entity_name to auto-build fields from the entity."""
    return forms.create_form(
        name, form_type, entity_name, alias, is_public, schema_json,
        settings_json, generate_from_entity, fields, columns, module_code,
    )


@mcp.tool()
def suppa_update_form(
    form_id: int,
    name: str | None = None,
    schema_json: str | None = None,
    settings_json: str | None = None,
    module_code: str | None = None,
) -> str:
    """Update a form's name, schema (data.formShema), settings, or module code."""
    return forms.update_form(form_id, name, schema_json, settings_json, module_code)


@mcp.tool()
def suppa_generate_form_schema(
    entity_name: str,
    columns: int = 1,
    fields: str | None = None,
) -> str:
    """Auto-generate a form schema (formShema + formSettings) from an entity's fields.
    Returns JSON usable as create_form's schema_json. 'fields' limits/orders included fields."""
    return forms.generate_form_schema(entity_name, columns, fields)


@mcp.tool()
def suppa_add_field_to_form(
    form_id: int,
    field_name: str,
    field_type: str = "text",
    label: str | None = None,
    required: bool = False,
    extra_json: str | None = None,
) -> str:
    """Append a field to a form's schema. Types: text, textarea, richtext, date, select, userSelect, files, toogle, etc."""
    return forms.add_field_to_form(form_id, field_name, field_type, label, required, extra_json)


@mcp.tool()
def suppa_list_form_field_types() -> str:
    """List the available form field types."""
    return forms.list_form_field_types()
