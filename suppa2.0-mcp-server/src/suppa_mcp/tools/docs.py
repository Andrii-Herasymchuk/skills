"""Docs, Pages, and PageBlocks tools."""

import json
import re
from typing import Optional

from suppa_mcp.http_client import (
    make_request, data_url, custom_order_url, search_entity,
    select_entity, insert_entity, update_entity, remove_entity,
)
from suppa_mcp.utils import make_filter, strip_html, json_response


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENTITY_DOCS = "Docs"
ENTITY_PAGES = "Pages"
ENTITY_PAGE_BLOCKS = "PageBlocks"

BLOCK_TYPES = [
    "text", "head1", "head2", "head3", "bulletList", "numberedList",
    "checkList", "quote", "callout", "divider", "code", "table",
    "toggle", "image", "video", "file", "embed", "bookmark",
    "linkToPage", "tableOfContent", "columns", "button", "mathEquation",
]

DOC_FIELDS = {
    "id": True, "title": True, "createdAt": True, "updatedAt": True,
    "createdBy": {"id": True, "fullName": True},
    "isPublic": True, "icon": True,
}

PAGE_FIELDS = {
    "id": True, "title": True, "description": True,
    "doc": {"id": True, "title": True},
    "parent": {"id": True, "title": True},
    "createdAt": True, "updatedAt": True, "status": True,
    "isPublic": True, "isArchived": True, "icon": True,
    "createdBy": {"id": True, "fullName": True},
}

BLOCK_FIELDS = {
    "id": True, "type": True, "properties": True, "format": True,
    "parent": {"id": True},
    "children": "#expand_tree(10)",
    "createdAt": True,
}


# ---------------------------------------------------------------------------
# Block content helpers
# ---------------------------------------------------------------------------

def _block_to_text(block: dict) -> str:
    """Convert a block to readable text."""
    btype = block.get("type", "")
    props = block.get("properties", {})
    title = strip_html(props.get("title", ""))

    if btype in ("head1", "head2", "head3"):
        level = int(btype[-1])
        return "#" * level + " " + title
    if btype == "text":
        return title
    if btype == "bulletList":
        return "• " + title
    if btype == "numberedList":
        return "1. " + title
    if btype == "checkList":
        checked = props.get("checked", False)
        return f"[{'x' if checked else ' '}] {title}"
    if btype == "quote":
        return "> " + title
    if btype == "code":
        lang = props.get("language", "")
        return f"```{lang}\n{title}\n```"
    if btype == "divider":
        return "---"
    if btype == "table":
        return f"[Table: {title or 'untitled'}]"
    if btype == "callout":
        return f"💡 {title}"
    return f"[{btype}] {title}" if title else f"[{btype}]"


def _build_block_properties(btype: str, title: str = "", table: dict | None = None) -> dict:
    """Build properties object for a block type."""
    if btype == "table" and table:
        return table
    if btype == "divider":
        return {}
    props: dict = {"title": title if title.strip().startswith("<") else f"<p>{title}</p>"}
    if btype == "code":
        props["language"] = ""
    if btype == "checkList":
        props["checked"] = False
    return props


# ---------------------------------------------------------------------------
# Docs tools
# ---------------------------------------------------------------------------

def list_docs(search: str = "", limit: int = 20) -> str:
    """List all documents, optionally filtering by title."""
    filters = []
    if search:
        filters.append(make_filter("title", f"%{search}%", "like"))
    results = search_entity(ENTITY_DOCS, filters, DOC_FIELDS, limit)
    return json_response(results)


def get_doc(doc_id: int) -> str:
    """Get a document by ID, including its pages."""
    result = select_entity(ENTITY_DOCS, [make_filter("id", doc_id)], {
        **DOC_FIELDS,
        "pages": {"id": True, "title": True, "status": True, "parent": {"id": True}},
    })
    return json_response(result)


def create_doc(title: str, is_public: bool = False) -> str:
    """Create a new document."""
    result = insert_entity(ENTITY_DOCS, [{"title": title, "isPublic": is_public}])
    return json_response(result[0] if result else None)


def update_doc(doc_id: int, title: Optional[str] = None, is_public: Optional[bool] = None) -> str:
    """Update a document's title or visibility."""
    fields: dict = {}
    if title is not None:
        fields["title"] = title
    if is_public is not None:
        fields["isPublic"] = is_public
    if not fields:
        return json_response({"error": "No fields to update"})
    result = update_entity(ENTITY_DOCS, doc_id, fields)
    return json_response(result)


def delete_doc(doc_id: int) -> str:
    """Delete a document."""
    result = remove_entity(ENTITY_DOCS, [make_filter("id", doc_id)])
    return json_response(result)


# ---------------------------------------------------------------------------
# Pages tools
# ---------------------------------------------------------------------------

def list_pages(doc_id: int, limit: int = 50) -> str:
    """List all pages in a document."""
    results = search_entity(
        ENTITY_PAGES,
        [make_filter("doc", {"id": doc_id})],
        PAGE_FIELDS, limit,
        order_by=[{"field": "createdAt", "order": "asc"}],
    )
    return json_response(results)


def get_page(page_id: int) -> str:
    """Get a page by ID with metadata."""
    result = select_entity(ENTITY_PAGES, [make_filter("id", page_id)], PAGE_FIELDS)
    return json_response(result)


def create_page(
    doc_id: int,
    title: str,
    parent_id: Optional[int] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
) -> str:
    """Create a new page in a document."""
    fields: dict = {"doc": {"id": doc_id}, "title": title}
    if parent_id:
        fields["parent"] = {"id": parent_id}
    if description:
        fields["description"] = description
    if icon:
        fields["icon"] = icon
    result = insert_entity(ENTITY_PAGES, [fields])
    return json_response(result[0] if result else None)


def update_page(
    page_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    is_public: Optional[bool] = None,
) -> str:
    """Update a page's metadata."""
    fields: dict = {}
    if title is not None:
        fields["title"] = title
    if description is not None:
        fields["description"] = description
    if icon is not None:
        fields["icon"] = icon
    if is_public is not None:
        fields["isPublic"] = is_public
    if not fields:
        return json_response({"error": "No fields to update"})
    result = update_entity(ENTITY_PAGES, page_id, fields)
    return json_response(result)


def delete_page(page_id: int) -> str:
    """Delete a page."""
    result = remove_entity(ENTITY_PAGES, [make_filter("id", page_id)])
    return json_response(result)


# ---------------------------------------------------------------------------
# Blocks tools
# ---------------------------------------------------------------------------

def get_blocks(page_id: int) -> str:
    """Get all blocks on a page in order."""
    results = search_entity(
        ENTITY_PAGE_BLOCKS,
        [make_filter("page", {"id": page_id})],
        BLOCK_FIELDS,
        limit=300,
        order_by=[],
    )
    return json_response(results)


def read_page(page_id: int) -> str:
    """Read a page's content as human-readable text (markdown-like)."""
    results = search_entity(
        ENTITY_PAGE_BLOCKS,
        [make_filter("page", {"id": page_id})],
        BLOCK_FIELDS,
        limit=300,
        order_by=[],
    )
    lines = []
    for block in results:
        lines.append(_block_to_text(block))
    return "\n\n".join(lines) if lines else "(empty page)"


def create_blocks(page_id: int, blocks_json: str) -> str:
    """Create blocks on a page. blocks_json is a JSON array of {type, title, properties?, format?} objects.
    Supported types: text, head1, head2, head3, bulletList, numberedList, checkList, quote, callout, divider, code, table, toggle, image, embed, bookmark, linkToPage, columns, button.
    """
    blocks_data = json.loads(blocks_json)
    insert_fields = []
    for bd in blocks_data:
        btype = bd.get("type", "text")
        if "properties" in bd and isinstance(bd["properties"], dict):
            props = bd["properties"]
        else:
            props = _build_block_properties(btype, bd.get("title", ""), bd.get("table"))
        insert_fields.append({
            "page": {"id": page_id},
            "type": btype,
            "properties": props,
            "format": bd.get("format", {"block_color": ""}),
        })

    result = insert_entity(
        ENTITY_PAGE_BLOCKS, insert_fields,
        returning={"id": True, "type": True},
    )
    return json_response(result)


def insert_block(
    page_id: int,
    blocks_json: str,
    after_id: Optional[int] = None,
    before_id: Optional[int] = None,
) -> str:
    """Insert block(s) at a specific position on a page.
    Provide after_id to insert after that block, or before_id to insert before it.
    blocks_json: JSON array of {type, title, properties?, format?}.
    """
    if not after_id and not before_id:
        return json_response({"error": "Provide after_id or before_id to specify position"})

    blocks_data = json.loads(blocks_json)
    insert_fields = []
    for bd in blocks_data:
        btype = bd.get("type", "text")
        if "properties" in bd and isinstance(bd["properties"], dict):
            props = bd["properties"]
        else:
            props = _build_block_properties(btype, bd.get("title", ""), bd.get("table"))
        insert_fields.append({
            "page": {"id": page_id},
            "type": btype,
            "properties": props,
            "format": bd.get("format", {"block_color": ""}),
        })

    res = make_request("POST", data_url(ENTITY_PAGE_BLOCKS, "insert"),
                      {"fields": insert_fields, "returning": {"id": True, "type": True}})
    new_ids = [r["id"] for r in res]

    # Reorder — API reverses multi-block order, so we always reverse
    reorder_body: dict = {
        "instanceIds": list(reversed(new_ids)),
        "contextFieldName": "page",
        "contextValue": page_id,
        "updates": {},
    }
    if after_id:
        reorder_body["beforeInstanceId"] = after_id
    elif before_id:
        reorder_body["afterInstanceId"] = before_id

    make_request("POST", custom_order_url(ENTITY_PAGE_BLOCKS), reorder_body)
    return json_response({"inserted_ids": new_ids, "position": "after" if after_id else "before", "anchor": after_id or before_id})


def update_block(block_id: int, title: Optional[str] = None, properties_json: Optional[str] = None) -> str:
    """Update a block's content. Provide title (HTML) or full properties_json."""
    fields: dict = {}
    if properties_json:
        fields["properties"] = json.loads(properties_json)
    elif title is not None:
        fields["properties"] = {"title": title if title.strip().startswith("<") else f"<p>{title}</p>"}
    else:
        return json_response({"error": "Provide title or properties_json"})
    result = update_entity(ENTITY_PAGE_BLOCKS, block_id, fields)
    return json_response(result)


def delete_block(block_id: int) -> str:
    """Delete a single block."""
    result = remove_entity(ENTITY_PAGE_BLOCKS, [make_filter("id", block_id)])
    return json_response(result)


def reorder_blocks(
    page_id: int,
    block_ids: str,
    after_id: Optional[int] = None,
    before_id: Optional[int] = None,
) -> str:
    """Reorder blocks within a page. block_ids: comma-separated IDs to move.
    Provide after_id to place them after that block, or before_id to place before it.
    """
    if not after_id and not before_id:
        return json_response({"error": "Provide after_id or before_id"})

    ids = [int(x.strip()) for x in block_ids.split(",")]

    # API reverses multi-block order, so we always reverse
    body: dict = {
        "instanceIds": list(reversed(ids)),
        "contextFieldName": "page",
        "contextValue": page_id,
        "updates": {},
    }
    if after_id:
        body["beforeInstanceId"] = after_id
    elif before_id:
        body["afterInstanceId"] = before_id

    make_request("POST", custom_order_url(ENTITY_PAGE_BLOCKS), body)
    return json_response({"reordered": ids, "position": "after" if after_id else "before", "anchor": after_id or before_id})
