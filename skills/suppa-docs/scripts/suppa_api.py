#!/usr/bin/env python3
"""
Suppa Docs API Client (modern.suppa.me)

REST-style API rooted at /api/core/data/{Entity}/{action} using integer IDs and
camelCase field names. Manages Docs, Pages, and PageBlocks.

No external dependencies - Python stdlib only.

Quick start:
    $env:SUPPA_API_KEY = "<token>"
    python suppa_api.py get-me
    python suppa_api.py list-docs
    python suppa_api.py get-blocks --page 5

Commands:
    get-me              Current authenticated user
    list-docs           List/search documents
    get-doc             Get a single document by id (with pages)
    create-doc          Create a new document
    update-doc          Update document properties
    delete-doc          Soft-delete a document
    list-pages          List pages of a document
    get-page            Get a single page by id
    create-page         Create a page in a document
    update-page         Update page properties
    delete-page         Soft-delete a page
    get-blocks          Get all blocks of a page (tree-expanded)
    read-page           Read page content as plain text / markdown
    insert-block        Insert block(s) after a specific block
    create-block        Create a single block in a page
    create-blocks       Batch-create multiple blocks in a page
    update-block        Update block content/type/format
    delete-block        Soft-delete a single block
    delete-blocks       Bulk-delete multiple blocks
    move-block          Move a block (change parent or page)
    raw                 Power-user: POST arbitrary body to any entity/action
"""

import argparse
import json
import os
import random
import re
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

# Entity names used in URL paths.
ENTITY_DOCS = "Docs"
ENTITY_PAGES = "Pages"
ENTITY_PAGE_BLOCKS = "PageBlocks"
ENTITY_USERS = "Users"

# ---------------------------------------------------------------------------
# Block types reference
# ---------------------------------------------------------------------------

BLOCK_TYPES = [
    "text",          # paragraph
    "head1",         # h1
    "head2",         # h2
    "head3",         # h3
    "bulletList",    # bullet item
    "numberedList",  # numbered list item
    "checkList",     # checkbox / to-do item
    "quote",         # blockquote
    "divider",       # horizontal rule
    "callout",       # callout/alert box
    "code",          # code block (plain text, NO <p> tags)
    "toggle",        # collapsible toggle
    "column_list",   # column layout
    "table",         # table with rows/cells
    "banner",        # banner block
    "embed",         # embedded content
    "links",         # links block
    "attachment",    # file attachment
    "page",          # page reference/embed
]


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


def _custom_order_url(entity):
    return "/api/core/data/custom-order/{0}".format(entity)


def _filter(field, value, comparator="="):
    return {
        "id": str(uuid.uuid4())[:8],
        "field": field,
        "value": value,
        "disabled": False,
        "comparator": comparator,
    }


def _conditions(filters, operator="and"):
    return {"operator": operator, "filters": filters}


# ---------------------------------------------------------------------------
# Field projections
# ---------------------------------------------------------------------------

DOC_LIST_FIELDS = {
    "id": True,
    "title": True,
    "description": True,
    "icon": {"icon": True, "color": True},
    "isPublic": True,
    "isArchived": True,
    "isTemplate": True,
    "createdAt": True,
    "updatedAt": True,
    "createdBy": {
        "id": True, "firstName": True, "lastName": True, "fullName": True,
        "avatar": {"id": True, "fileName": True, "deletedAt": True},
    },
}

DOC_DETAIL_FIELDS = {
    "id": True,
    "title": True,
    "description": True,
    "coverImage": True,
    "icon": {"icon": True, "color": True},
    "isTemplate": True,
    "isPublic": True,
    "isArchived": True,
    "pages": {"id": True, "title": True, "icon": True, "parent": {"id": True}},
    "adminUsers": {"id": True, "fullName": True},
    "adminGroups": {"id": True, "title": True},
    "editUsers": {"id": True, "fullName": True},
    "editGroups": {"id": True, "title": True},
    "viewUsers": {"id": True, "fullName": True},
    "viewGroups": {"id": True, "title": True},
    "createdAt": True,
    "updatedAt": True,
    "deletedAt": True,
    "createdBy": {"id": True, "fullName": True},
}

PAGE_LIST_FIELDS = {
    "id": True,
    "title": True,
    "icon": True,
    "parent": {"id": True, "title": True},
    "doc": {"id": True, "title": True},
    "coverImage": True,
    "createdAt": True,
    "updatedAt": True,
}

PAGE_DETAIL_FIELDS = {
    "id": True,
    "title": True,
    "description": True,
    "icon": True,
    "parent": {"id": True, "title": True},
    "doc": {"id": True, "title": True},
    "coverImage": True,
    "isTemplate": True,
    "shouldBeIndexed": True,
    "status": True,
    "adminUsers": {"id": True, "fullName": True},
    "adminGroups": {"id": True, "title": True},
    "editUsers": {"id": True, "fullName": True},
    "editGroups": {"id": True, "title": True},
    "viewUsers": {"id": True, "fullName": True},
    "viewGroups": {"id": True, "title": True},
    "createdAt": True,
    "updatedAt": True,
}

PAGE_BLOCK_FIELDS = {
    "id": True,
    "externalId": True,
    "type": True,
    "page": {"id": True},
    "parent": {"id": True},
    "children": "#expand_tree(10)",
    "format": True,
    "properties": True,
    "createdAt": True,
    "updatedAt": True,
}

USER_FIELDS = {
    "id": True, "firstName": True, "lastName": True, "fullName": True,
    "position": True, "avatar": {"id": True, "fileName": True},
}


# ---------------------------------------------------------------------------
# Table builder utility (mirrors MCP server's buildTableData)
# ---------------------------------------------------------------------------

def _short_id():
    """Generate an 8-char alphanumeric ID matching Suppa's short-id format."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(chars) for _ in range(8))


def build_table_data(columns_count, rows_data, header_row=True):
    """
    Convert simplified table input into the Suppa API table structure.

    Args:
        columns_count: Number of columns
        rows_data: List of rows, each row is a list of cell content strings.
                   First row is the header row.
        header_row: Whether the first row is a header (default True)

    Returns:
        { columns: [{id, width}], headerRow: bool, rows: [{id, cells: [{columnId, content}]}] }
    """
    column_ids = [_short_id() for _ in range(columns_count)]
    columns = [{"id": cid, "width": 180} for cid in column_ids]
    rows = []
    for row_cells in rows_data:
        cells = []
        for col_idx, col_id in enumerate(column_ids):
            content = row_cells[col_idx] if col_idx < len(row_cells) else ""
            cells.append({"columnId": col_id, "content": content})
        rows.append({"id": _short_id(), "cells": cells})
    return {"columns": columns, "headerRow": header_row, "rows": rows}


# ---------------------------------------------------------------------------
# Block content helpers
# ---------------------------------------------------------------------------

def _wrap_html(text):
    """Ensure text is wrapped in <p> tags if not already HTML."""
    if not text:
        return "<p></p>"
    text = text.strip()
    if text.startswith("<"):
        return text
    return "<p>{0}</p>".format(text)


def _build_block_properties(block_type, title, table_json=None):
    """Build the properties object for a block based on its type."""
    props = {}
    if block_type == "code":
        # Code blocks use plain text, no <p> wrapping
        props["title"] = title or ""
    elif block_type == "table" and table_json:
        # Table blocks have special properties.table structure
        props["title"] = title or ""
        tdata = json.loads(table_json) if isinstance(table_json, str) else table_json
        props["table"] = build_table_data(
            tdata["columns"],
            tdata["rows"],
            tdata.get("headerRow", True),
        )
    elif block_type == "divider":
        props["title"] = "<p></p>"
    else:
        props["title"] = _wrap_html(title or "")
    props["content"] = []
    return props


# ---------------------------------------------------------------------------
# CLI command implementations - get-me
# ---------------------------------------------------------------------------

def cmd_get_me(args):
    body = {
        "fields": dict(USER_FIELDS, **{
            "createdAt": True, "updatedAt": True,
            "roles": {"id": True, "name": True},
        }),
        "conditions": _conditions([_filter("id", "$current-user", "=")]),
        "limit": 1,
        "getAccessByFields": True,
        "includeDeletedRelations": False,
    }
    res = make_request(
        "POST",
        _data_url(ENTITY_USERS, "select") + "?markAsView=false",
        body,
    )
    _print(res)


# ---------------------------------------------------------------------------
# CLI command implementations - Docs
# ---------------------------------------------------------------------------

def cmd_list_docs(args):
    filters = []
    if args.search:
        filters.append(_filter("title", "%" + args.search + "%", "like"))
    if getattr(args, "public", False):
        filters.append(_filter("isPublic", True, "="))
    if getattr(args, "archived", False):
        filters.append(_filter("isArchived", True, "="))
    if getattr(args, "template", False):
        filters.append(_filter("isTemplate", True, "="))
    body = {
        "fields": DOC_LIST_FIELDS,
        "limit": args.limit,
        "offset": args.offset,
        "getAccessByFields": True,
        "searchValue": getattr(args, "search_value", "") or "",
        "orderBy": [{"field": "updatedAt", "order": "desc"}],
        "conditions": _conditions(filters),
        "includeDeletedRelations": False,
    }
    res = make_request("POST", _data_url(ENTITY_DOCS, "search"), body)
    _print(res)


def cmd_get_doc(args):
    body = {
        "fields": DOC_DETAIL_FIELDS,
        "includeDeletedRelations": False,
        "conditions": _conditions([_filter("id", str(args.id), "=")]),
        "limit": 1,
        "getAccessByFields": True,
    }
    res = make_request("POST", _data_url(ENTITY_DOCS, "select") + "?markAsView=false", body)
    _print(res)


def cmd_create_doc(args):
    fields = {"title": args.title}
    if args.description:
        fields["description"] = args.description
    if args.public:
        fields["isPublic"] = True
    if args.icon:
        fields["icon"] = {"icon": args.icon, "color": args.icon_color or ""}
    if args.admin_users:
        fields["adminUsers"] = [{"id": int(uid)} for uid in args.admin_users]
    if args.edit_users:
        fields["editUsers"] = [{"id": int(uid)} for uid in args.edit_users]
    if args.view_users:
        fields["viewUsers"] = [{"id": int(uid)} for uid in args.view_users]
    if args.fields_json:
        fields.update(json.loads(args.fields_json))
    body = {
        "fields": [fields],
        "returning": DOC_DETAIL_FIELDS,
    }
    res = make_request("POST", _data_url(ENTITY_DOCS, "insert"), body)
    _print(res)


def cmd_update_doc(args):
    fields = {}
    if args.title is not None:
        fields["title"] = args.title
    if args.description is not None:
        fields["description"] = args.description
    if getattr(args, "public", False):
        fields["isPublic"] = True
    if getattr(args, "private", False):
        fields["isPublic"] = False
    if getattr(args, "archive", False):
        fields["isArchived"] = True
    if getattr(args, "unarchive", False):
        fields["isArchived"] = False
    if args.icon:
        fields["icon"] = {"icon": args.icon, "color": getattr(args, "icon_color", "") or ""}
    if args.admin_users:
        fields["adminUsers"] = [{"id": int(uid)} for uid in args.admin_users]
    if args.edit_users:
        fields["editUsers"] = [{"id": int(uid)} for uid in args.edit_users]
    if args.view_users:
        fields["viewUsers"] = [{"id": int(uid)} for uid in args.view_users]
    if args.fields_json:
        fields.update(json.loads(args.fields_json))
    if not fields:
        sys.stderr.write("Nothing to update. Provide at least one field flag.\n")
        sys.exit(2)
    body = {"fields": fields}
    res = make_request("POST", _data_url(ENTITY_DOCS, "update") + "/" + str(int(args.id)), body)
    _print(res)


def cmd_delete_doc(args):
    body = {"conditions": _conditions([_filter("id", int(args.id), "=")])}
    res = make_request("POST", _data_url(ENTITY_DOCS, "remove"), body)
    _print(res)


# ---------------------------------------------------------------------------
# CLI command implementations - Pages
# ---------------------------------------------------------------------------

def cmd_list_pages(args):
    filters = [_filter("doc.id", int(args.doc), "=")]
    if args.search:
        filters.append(_filter("title", "%" + args.search + "%", "like"))
    if getattr(args, "parent", None):
        filters.append(_filter("parent.id", int(args.parent), "="))
    body = {
        "fields": PAGE_LIST_FIELDS,
        "limit": args.limit,
        "offset": 0,
        "getAccessByFields": True,
        "searchValue": "",
        "orderBy": [{"field": "updatedAt", "order": "desc"}],
        "conditions": _conditions(filters),
        "includeDeletedRelations": False,
    }
    res = make_request("POST", _data_url(ENTITY_PAGES, "search"), body)
    _print(res)


def cmd_get_page(args):
    body = {
        "fields": PAGE_DETAIL_FIELDS,
        "includeDeletedRelations": False,
        "conditions": _conditions([_filter("id", str(args.id), "=")]),
        "limit": 1,
        "getAccessByFields": True,
    }
    res = make_request("POST", _data_url(ENTITY_PAGES, "select") + "?markAsView=false", body)
    _print(res)


def cmd_create_page(args):
    fields = {"doc": {"id": int(args.doc)}}
    if args.title:
        fields["title"] = args.title
    if args.description:
        fields["description"] = args.description
    if args.icon:
        fields["icon"] = args.icon
    if args.parent:
        fields["parent"] = {"id": int(args.parent)}
    if getattr(args, "template", False):
        fields["isTemplate"] = True
    if getattr(args, "public", False):
        fields["isPublic"] = True
    if getattr(args, "index", False):
        fields["shouldBeIndexed"] = True
    if args.admin_users:
        fields["adminUsers"] = [{"id": int(uid)} for uid in args.admin_users]
    if args.edit_users:
        fields["editUsers"] = [{"id": int(uid)} for uid in args.edit_users]
    if args.view_users:
        fields["viewUsers"] = [{"id": int(uid)} for uid in args.view_users]
    if args.fields_json:
        fields.update(json.loads(args.fields_json))
    body = {
        "fields": [fields],
        "returning": PAGE_DETAIL_FIELDS,
    }
    res = make_request("POST", _data_url(ENTITY_PAGES, "insert"), body)
    _print(res)


def cmd_update_page(args):
    fields = {}
    if args.title is not None:
        fields["title"] = args.title
    if args.description is not None:
        fields["description"] = args.description
    if args.icon is not None:
        fields["icon"] = args.icon
    if args.parent is not None:
        if args.parent == "null" or args.parent == "0":
            fields["parent"] = None
        else:
            fields["parent"] = {"id": int(args.parent)}
    if args.fields_json:
        fields.update(json.loads(args.fields_json))
    if not fields:
        sys.stderr.write("Nothing to update. Provide at least one field flag.\n")
        sys.exit(2)
    body = {"fields": fields}
    res = make_request("POST", _data_url(ENTITY_PAGES, "update") + "/" + str(int(args.id)), body)
    _print(res)


def cmd_delete_page(args):
    body = {"conditions": _conditions([_filter("id", int(args.id), "=")])}
    res = make_request("POST", _data_url(ENTITY_PAGES, "remove"), body)
    _print(res)





# ---------------------------------------------------------------------------
# CLI command implementations - PageBlocks
# ---------------------------------------------------------------------------

def cmd_get_blocks(args):
    """Get all blocks of a page with tree expansion and custom ordering."""
    page_id = int(args.page)

    if getattr(args, "flat", False):
        # Flat mode: get all blocks (including children) without tree expansion
        flat_fields = dict(PAGE_BLOCK_FIELDS)
        flat_fields["children"] = True  # just presence, no expansion
        body = {
            "fields": flat_fields,
            "conditions": _conditions([
                _filter("page.id", str(page_id), "="),
            ]),
            "orderBy": [{"field": "page", "order": "desc",
                         "function": "#custom_order", "args": [page_id]}],
            "includeDeletedRelations": True,
        }
    else:
        # Tree mode: top-level blocks with children expanded
        body = {
            "fields": PAGE_BLOCK_FIELDS,
            "conditions": _conditions([
                _filter("page.id", str(page_id), "="),
                _filter("parent", None, "="),
            ]),
            "orderBy": [{"field": "page", "order": "desc",
                         "function": "#custom_order", "args": [page_id]}],
            "includeDeletedRelations": True,
        }
    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "select") + "?markAsView=false", body)
    _print(res)


def _strip_html(html):
    """Strip HTML tags and decode entities, returning plain text."""
    if not html:
        return ""
    # Replace <br> and </p><p> with newlines
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'</p>\s*<p[^>]*>', '\n', text)
    # Strip all remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode common HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return text.strip()


def _block_to_text(block, fmt="markdown", indent=0):
    """Convert a single block to readable text."""
    btype = block.get("type", "text")
    props = block.get("properties", {})
    title = props.get("title", "")
    text = _strip_html(title) if btype != "code" else title
    prefix = "  " * indent

    if fmt == "markdown":
        if btype == "head1":
            return prefix + "# " + text
        elif btype == "head2":
            return prefix + "## " + text
        elif btype == "head3":
            return prefix + "### " + text
        elif btype == "bulletList":
            return prefix + "- " + text
        elif btype == "numberedList":
            return prefix + "1. " + text
        elif btype == "checkList":
            checked = props.get("checked", False)
            mark = "x" if checked else " "
            return prefix + "- [{0}] {1}".format(mark, text)
        elif btype == "quote":
            return prefix + "> " + text
        elif btype == "callout":
            color = block.get("format", {}).get("block_color", "")
            label = {"blue": "INFO", "yellow": "WARNING", "red": "DANGER",
                     "green": "SUCCESS"}.get(color, "NOTE")
            return prefix + "> **{0}:** {1}".format(label, text)
        elif btype == "code":
            lang = props.get("language", "")
            lines = text.split('\n')
            return prefix + "```{0}\n".format(lang) + prefix + ('\n' + prefix).join(lines) + "\n" + prefix + "```"
        elif btype == "divider":
            return prefix + "---"
        elif btype == "table":
            table = props.get("table", {})
            rows = table.get("rows", [])
            if not rows:
                return prefix + "[empty table]"
            lines = []
            for i, row in enumerate(rows):
                cells = [_strip_html(c.get("content", "")) for c in row.get("cells", [])]
                lines.append(prefix + "| " + " | ".join(cells) + " |")
                if i == 0 and table.get("headerRow"):
                    lines.append(prefix + "| " + " | ".join(["---"] * len(cells)) + " |")
            return "\n".join(lines)
        elif btype == "toggle":
            return prefix + "<details> " + text
        elif btype == "youtube":
            url = props.get("youtube_url", "")
            return prefix + "[youtube] " + url
        elif btype == "links":
            url = props.get("url", "") or text
            label = text if text != url else ""
            if label:
                return prefix + "[{0}]({1})".format(label, url)
            return prefix + url
        elif btype == "embed":
            url = props.get("embed_url", "") or text
            label = text if text and text != url else ""
            if label:
                return prefix + "[embed: {0}]({1})".format(label, url)
            return prefix + "[embed] " + url
        elif btype in ("banner", "attachment", "page", "column_list"):
            return prefix + "[{0}] {1}".format(btype, text) if text else prefix + "[{0}]".format(btype)
        else:
            return prefix + text
    else:  # plain text
        if btype in ("head1", "head2", "head3"):
            return prefix + text.upper() if text else ""
        elif btype == "bulletList":
            return prefix + "* " + text
        elif btype == "numberedList":
            return prefix + "- " + text
        elif btype == "checkList":
            checked = props.get("checked", False)
            mark = "[x]" if checked else "[ ]"
            return prefix + mark + " " + text
        elif btype == "divider":
            return prefix + "---"
        elif btype == "table":
            table = props.get("table", {})
            rows = table.get("rows", [])
            lines = []
            for row in rows:
                cells = [_strip_html(c.get("content", "")) for c in row.get("cells", [])]
                lines.append(prefix + " | ".join(cells))
            return "\n".join(lines)
        elif btype == "youtube":
            return prefix + props.get("youtube_url", "")
        elif btype == "links":
            return prefix + (props.get("url", "") or text)
        elif btype == "embed":
            return prefix + (props.get("embed_url", "") or text)
        else:
            return prefix + text


def cmd_read_page(args):
    """Read all blocks of a page and output as readable text."""
    page_id = int(args.page)
    fmt = getattr(args, "format", "markdown") or "markdown"
    with_ids = getattr(args, "with_ids", False)

    # Fetch all blocks in order
    body = {
        "fields": {
            "id": True, "type": True, "format": True, "properties": True,
            "parent": {"id": True}, "children": True,
        },
        "conditions": _conditions([
            _filter("page.id", str(page_id), "="),
        ]),
        "orderBy": [{"field": "page", "order": "desc",
                     "function": "#custom_order", "args": [page_id]}],
        "includeDeletedRelations": True,
    }
    blocks = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "select") + "?markAsView=false", body)

    if not blocks:
        sys.stderr.write("No blocks found on page {0}.\n".format(page_id))
        sys.exit(0)

    # Convert to text
    lines = []
    for block in blocks:
        line = _block_to_text(block, fmt)
        if line:
            if with_ids:
                block_id = block.get("id", "?")
                lines.append("[{0}] {1}".format(block_id, line))
            else:
                lines.append(line)

    output = "\n".join(lines)
    if getattr(args, "output", None):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        sys.stderr.write("Written to {0} ({1} blocks)\n".format(args.output, len(blocks)))
    else:
        print(output)


def cmd_insert_block(args):
    """Insert block(s) after (or before) a specific block.

    Strategy: batch-create new blocks (appended at end) → reorder them
    to the desired position via the custom-order API.
    """
    page_id = int(args.page)
    after_id = int(args.after) if args.after else None
    before_id = int(args.before) if getattr(args, "before", None) else None

    if not after_id and not before_id:
        sys.stderr.write("Provide --after or --before to position the block(s).\n")
        sys.exit(2)

    # Build the new block(s) to insert
    if args.blocks_file:
        with open(args.blocks_file, "r", encoding="utf-8-sig") as f:
            new_blocks_data = json.load(f)
    elif args.blocks_json:
        new_blocks_data = json.loads(args.blocks_json)
    else:
        # Single block from flags
        block_type = args.type or "text"
        props = _build_block_properties(
            block_type, args.title, getattr(args, "table_json", None))
        new_blocks_data = [{"type": block_type, "title": None, "properties": props,
                            "format": json.loads(args.format_json) if args.format_json else {"block_color": ""}}]

    if not isinstance(new_blocks_data, list):
        new_blocks_data = [new_blocks_data]

    # Step 1: Batch-create blocks (appended at end of page)
    insert_fields = []
    for bd in new_blocks_data:
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

    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "insert"),
                      {"fields": insert_fields, "returning": {"id": True, "type": True}})

    new_ids = [r["id"] for r in res]

    # Step 2: Reorder — move new blocks after/before the target.
    # API semantics: "beforeInstanceId" = anchor comes BEFORE items = items go AFTER anchor
    #               "afterInstanceId"  = anchor comes AFTER items  = items go BEFORE anchor
    # NOTE: The API reverses multi-block order in both cases,
    #       so we always reverse the list to get correct final order.
    reorder_body = {
        "instanceIds": list(reversed(new_ids)),
        "contextFieldName": "page",
        "contextValue": page_id,
        "updates": {},
    }
    if after_id:
        reorder_body["beforeInstanceId"] = after_id
    elif before_id:
        reorder_body["afterInstanceId"] = before_id

    make_request("POST", _custom_order_url(ENTITY_PAGE_BLOCKS), reorder_body)

    sys.stderr.write("Inserted {0} block(s) {1} [{2}]. New IDs: {3}\n".format(
        len(new_ids),
        "after" if after_id else "before",
        after_id or before_id,
        new_ids,
    ))
    _print(res)


def cmd_create_block(args):
    """Create a single block in a page."""
    page_id = int(args.page)
    block_type = args.type or "text"

    # Build properties
    props = _build_block_properties(
        block_type,
        args.title,
        getattr(args, "table_json", None),
    )
    if args.properties_json:
        props.update(json.loads(args.properties_json))

    fields = {
        "page": {"id": page_id},
        "type": block_type,
        "properties": props,
    }
    if args.parent:
        fields["parent"] = {"id": int(args.parent)}
    if args.format_json:
        fields["format"] = json.loads(args.format_json)
    else:
        fields["format"] = {"block_color": ""}
    if args.external_id:
        fields["externalId"] = args.external_id
    if args.fields_json:
        fields.update(json.loads(args.fields_json))

    body = {
        "fields": [fields],
        "returning": {
            "id": True, "externalId": True, "type": True,
            "page": {"id": True}, "parent": {"id": True},
            "format": True, "properties": True,
            "createdAt": True, "updatedAt": True,
        },
    }
    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "insert"), body)
    _print(res)


def cmd_create_blocks(args):
    """
    Batch-create multiple blocks in a page from a JSON array.

    Each block in the array should have:
      - type (string): block type (default: "text")
      - title (string): HTML content (wrapped in <p> if not already)
      - order (number, optional): sort order (auto-incremented if omitted)
      - format (object, optional): e.g. {"block_color": "blue"}
      - table (object, optional): for table blocks {columns, rows, headerRow}
      - parent (number, optional): parent block id for nesting
    """
    page_id = int(args.page)

    # Parse blocks from --blocks-json or stdin
    if args.blocks_json:
        blocks_data = json.loads(args.blocks_json)
    elif args.blocks_file:
        with open(args.blocks_file, "r", encoding="utf-8-sig") as f:
            blocks_data = json.load(f)
    else:
        blocks_data = json.loads(sys.stdin.read())

    if not isinstance(blocks_data, list) or not blocks_data:
        sys.stderr.write("ERROR: blocks must be a non-empty JSON array.\n")
        sys.exit(2)

    # Build insert fields for each block
    insert_fields = []
    for idx, block in enumerate(blocks_data):
        block_type = block.get("type", "text")
        title = block.get("title", "")
        table_data = block.get("table")

        props = _build_block_properties(block_type, title, table_data)
        if "properties" in block and isinstance(block["properties"], dict):
            props.update(block["properties"])

        fields = {
            "page": {"id": page_id},
            "type": block_type,
            "properties": props,
            "format": block.get("format", {"block_color": ""}),
        }
        if block.get("parent"):
            fields["parent"] = {"id": int(block["parent"])}
        if block.get("externalId"):
            fields["externalId"] = block["externalId"]

        insert_fields.append(fields)

    body = {
        "fields": insert_fields,
        "returning": {
            "id": True, "externalId": True, "type": True,
            "page": {"id": True}, "parent": {"id": True},
            "format": True, "properties": True,
            "createdAt": True,
        },
    }
    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "insert"), body)
    _print(res)


def cmd_update_block(args):
    """Update an existing block's content, type, order, or format."""
    fields = {}
    if args.title is not None:
        block_type = args.type  # may be None
        props = _build_block_properties(block_type or "text", args.title,
                                        getattr(args, "table_json", None))
        fields["properties"] = props
    elif args.properties_json is not None:
        fields["properties"] = json.loads(args.properties_json)
    if args.type is not None:
        fields["type"] = args.type
    if args.format_json is not None:
        fields["format"] = json.loads(args.format_json)
    if args.parent is not None:
        if args.parent == "null" or args.parent == "0":
            fields["parent"] = None
        else:
            fields["parent"] = {"id": int(args.parent)}
    if args.fields_json:
        fields.update(json.loads(args.fields_json))
    if not fields:
        sys.stderr.write("Nothing to update. Provide at least --title, --type, --format-json, or --properties-json.\n")
        sys.exit(2)
    body = {"fields": fields}
    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "update") + "/" + str(int(args.id)), body)
    _print(res)


def cmd_delete_block(args):
    """Soft-delete a single block."""
    body = {"conditions": _conditions([_filter("id", int(args.id), "=")])}
    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "remove"), body)
    _print(res)


def cmd_delete_blocks(args):
    """Bulk-delete multiple blocks by their IDs."""
    block_ids = [int(bid) for bid in args.ids]
    filters = [_filter("id", bid, "=") for bid in block_ids]
    body = {"conditions": _conditions(filters, operator="or")}
    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "remove"), body)
    _print(res)


def cmd_move_block(args):
    """Move a block to a new parent or different page."""
    fields = {}
    if args.parent is not None:
        if args.parent == "null" or args.parent == "0":
            fields["parent"] = None
        else:
            fields["parent"] = {"id": int(args.parent)}
    if args.page is not None:
        fields["page"] = {"id": int(args.page)}
    if not fields:
        sys.stderr.write("Provide --parent or --page to move the block.\n")
        sys.exit(2)
    body = {"fields": fields}
    res = make_request("POST", _data_url(ENTITY_PAGE_BLOCKS, "update") + "/" + str(int(args.id)), body)
    _print(res)


def cmd_reorder_blocks(args):
    """Reorder blocks within a page using the custom-order API.

    API semantics (counter-intuitive naming):
      - "beforeInstanceId" = anchor stays BEFORE the moved items = items go AFTER anchor
      - "afterInstanceId"  = anchor stays AFTER the moved items  = items go BEFORE anchor
    """
    page_id = int(args.page)
    block_ids = [int(bid) for bid in args.ids]

    after_id = int(args.after) if args.after else None
    before_id = int(args.before) if args.before else None

    if not after_id and not before_id:
        sys.stderr.write("Provide --after or --before to specify target position.\n")
        sys.exit(2)

    # NOTE: The API reverses multi-block order in both cases,
    #       so we always reverse the list to get correct final order.
    body = {
        "instanceIds": list(reversed(block_ids)),
        "contextFieldName": "page",
        "contextValue": page_id,
        "updates": {},
    }
    if after_id:
        body["beforeInstanceId"] = after_id
    elif before_id:
        body["afterInstanceId"] = before_id

    res = make_request("POST", _custom_order_url(ENTITY_PAGE_BLOCKS), body)
    sys.stderr.write("Reordered {0} block(s) {1} [{2}] on page {3}.\n".format(
        len(block_ids),
        "after" if after_id else "before",
        after_id or before_id,
        page_id,
    ))
    _print(res)


# ---------------------------------------------------------------------------
# Raw command
# ---------------------------------------------------------------------------

def cmd_raw(args):
    """Run an arbitrary POST against any entity action."""
    if args.body:
        body = json.loads(args.body)
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            body = json.load(f)
    else:
        body = json.loads(sys.stdin.read())
    action = args.action or "search"
    path = _data_url(args.entity, action)
    if args.record_id:
        path += "/" + str(args.record_id)
    res = make_request("POST", path, body)
    _print(res)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _print(data):
    """Print JSON output. Handles None gracefully."""
    if data is None:
        print("null")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(
        prog="suppa_api.py",
        description="Suppa Docs API client for modern.suppa.me (Docs, Pages, PageBlocks)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Block types: text, head1, head2, head3, bulletList, numberedList,
checkList, quote, divider, callout, code, toggle, column_list, table,
banner, embed, links, attachment, page

HTML content rules:
  - Always wrap text in <p> tags: <p>Hello world</p>
  - Bold: <strong>text</strong>  Italic: <em>text</em>
  - Code blocks use plain text (NO <p> tags)
  - Dividers use empty <p></p>
  - Tables use --table-json with {columns, rows, headerRow}
""",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # --- get-me ---
    sub.add_parser("get-me", help="Current authenticated user").set_defaults(func=cmd_get_me)

    # --- Docs ---
    ld = sub.add_parser("list-docs", help="List/search documents")
    ld.add_argument("--search", help="Substring filter on title (LIKE)")
    ld.add_argument("--search-value", help="Server-side full-text search value")
    ld.add_argument("--public", action="store_true", default=False, help="Only public docs")
    ld.add_argument("--archived", action="store_true", default=False, help="Only archived docs")
    ld.add_argument("--template", action="store_true", default=False, help="Only templates")
    ld.add_argument("--limit", type=int, default=100)
    ld.add_argument("--offset", type=int, default=0)
    ld.set_defaults(func=cmd_list_docs)

    gd = sub.add_parser("get-doc", help="Get a document by id (with pages list)")
    gd.add_argument("id", type=int, help="Document id")
    gd.set_defaults(func=cmd_get_doc)

    cd = sub.add_parser("create-doc", help="Create a new document")
    cd.add_argument("--title", required=True, help="Document title")
    cd.add_argument("--description", help="Document description (HTML)")
    cd.add_argument("--public", action="store_true", help="Make publicly visible")
    cd.add_argument("--icon", help="Icon name/emoji")
    cd.add_argument("--icon-color", help="Icon color")
    cd.add_argument("--admin-users", nargs="*", help="User IDs with admin access")
    cd.add_argument("--edit-users", nargs="*", help="User IDs with edit access")
    cd.add_argument("--view-users", nargs="*", help="User IDs with view-only access")
    cd.add_argument("--fields-json", help="Extra fields as JSON object (merged)")
    cd.set_defaults(func=cmd_create_doc)

    ud = sub.add_parser("update-doc", help="Update document properties")
    ud.add_argument("id", type=int, help="Document id")
    ud.add_argument("--title", help="New title")
    ud.add_argument("--description", help="New description (HTML)")
    ud.add_argument("--public", action="store_true", default=False, help="Set isPublic=true")
    ud.add_argument("--private", action="store_true", default=False, help="Set isPublic=false")
    ud.add_argument("--archive", action="store_true", default=False, help="Set isArchived=true")
    ud.add_argument("--unarchive", action="store_true", default=False, help="Set isArchived=false")
    ud.add_argument("--icon", help="New icon name/emoji")
    ud.add_argument("--icon-color", help="New icon color")
    ud.add_argument("--admin-users", nargs="*", help="User IDs with admin access")
    ud.add_argument("--edit-users", nargs="*", help="User IDs with edit access")
    ud.add_argument("--view-users", nargs="*", help="User IDs with view-only access")
    ud.add_argument("--fields-json", help="Extra fields as JSON object (merged)")
    ud.set_defaults(func=cmd_update_doc)

    dd = sub.add_parser("delete-doc", help="Soft-delete a document")
    dd.add_argument("id", type=int, help="Document id")
    dd.set_defaults(func=cmd_delete_doc)

    # --- Pages ---
    lp = sub.add_parser("list-pages", help="List pages of a document")
    lp.add_argument("--doc", required=True, type=int, help="Document id")
    lp.add_argument("--search", help="Substring filter on title")
    lp.add_argument("--parent", help="Filter by parent page id (for nested pages)")
    lp.add_argument("--limit", type=int, default=200)
    lp.set_defaults(func=cmd_list_pages)

    gp = sub.add_parser("get-page", help="Get a single page by id (with permissions)")
    gp.add_argument("id", type=int, help="Page id")
    gp.set_defaults(func=cmd_get_page)

    cp = sub.add_parser("create-page", help="Create a page in a document")
    cp.add_argument("--doc", required=True, type=int, help="Document id")
    cp.add_argument("--title", help="Page title")
    cp.add_argument("--description", help="Page description")
    cp.add_argument("--icon", help="Icon/emoji")
    cp.add_argument("--parent", help="Parent page id (for nesting)")
    cp.add_argument("--template", action="store_true", default=False, help="Create as template")
    cp.add_argument("--public", action="store_true", default=False, help="Make publicly visible")
    cp.add_argument("--index", action="store_true", default=False, help="Index for search (default: no)")
    cp.add_argument("--admin-users", nargs="*", help="User IDs with admin access")
    cp.add_argument("--edit-users", nargs="*", help="User IDs with edit access")
    cp.add_argument("--view-users", nargs="*", help="User IDs with view-only access")
    cp.add_argument("--fields-json", help="Extra fields as JSON object (merged)")
    cp.set_defaults(func=cmd_create_page)

    up = sub.add_parser("update-page", help="Update page properties")
    up.add_argument("id", type=int, help="Page id")
    up.add_argument("--title", help="New title")
    up.add_argument("--description", help="New description")
    up.add_argument("--icon", help="New icon")
    up.add_argument("--parent", help="Move to parent page id (or 'null' for top-level)")
    up.add_argument("--fields-json", help="Extra fields as JSON object (merged)")
    up.set_defaults(func=cmd_update_page)

    dp = sub.add_parser("delete-page", help="Soft-delete a page")
    dp.add_argument("id", type=int, help="Page id")
    dp.set_defaults(func=cmd_delete_page)

    # --- PageBlocks ---
    gb = sub.add_parser("get-blocks", help="Get all blocks of a page (tree-expanded with custom order)")
    gb.add_argument("--page", required=True, type=int, help="Page id")
    gb.add_argument("--flat", action="store_true", default=False,
                    help="Flat mode: return all blocks without tree nesting (useful for bulk ops)")
    gb.set_defaults(func=cmd_get_blocks)

    # Read page content as text
    rp = sub.add_parser("read-page", help="Read page content as readable text (markdown or plain)")
    rp.add_argument("--page", required=True, type=int, help="Page id")
    rp.add_argument("--format", choices=["markdown", "plain"], default="markdown",
                    help="Output format (default: markdown)")
    rp.add_argument("--with-ids", action="store_true", default=False,
                    help="Prefix each line with [block_id] for targeted updates")
    rp.add_argument("--output", "-o", help="Write output to file instead of stdout")
    rp.set_defaults(func=cmd_read_page)

    # Insert block after/before a specific block
    ib = sub.add_parser("insert-block", help="Insert block(s) after/before a specific block (via custom-order API)")
    ib.add_argument("--page", required=True, type=int, help="Page id")
    ib.add_argument("--after", help="Block ID to insert AFTER")
    ib.add_argument("--before", help="Block ID to insert BEFORE")
    ib.add_argument("--type", default="text", choices=BLOCK_TYPES,
                    help="Block type for single-block insert (default: text)")
    ib.add_argument("--title", help="HTML content for single-block insert")
    ib.add_argument("--format-json", help='Format JSON, e.g. {"block_color":"blue"}')
    ib.add_argument("--table-json", help="Table data JSON (for table blocks)")
    ib.add_argument("--blocks-json", help="JSON array of blocks to insert (for multi-block insert)")
    ib.add_argument("--blocks-file", help="Path to JSON file with blocks array")
    ib.set_defaults(func=cmd_insert_block)

    # Single block creation
    cb = sub.add_parser("create-block", help="Create a single block in a page")
    cb.add_argument("--page", required=True, type=int, help="Page id")
    cb.add_argument("--type", default="text", choices=BLOCK_TYPES,
                    help="Block type (default: text)")
    cb.add_argument("--title", help="HTML content (auto-wrapped in <p> if needed). "
                    "For code blocks use plain text. For dividers leave empty.")
    cb.add_argument("--parent", help="Parent block id (for nested blocks)")
    cb.add_argument("--format-json", help='Format JSON, e.g. {"block_color":"blue"}')
    cb.add_argument("--table-json", help="Table data JSON: {columns:N, rows:[[...]], headerRow:bool}")
    cb.add_argument("--properties-json", help="Full properties JSON (overrides --title)")
    cb.add_argument("--external-id", help="External ID for client-side tracking")
    cb.add_argument("--fields-json", help="Extra fields as JSON (merged into insert body)")
    cb.set_defaults(func=cmd_create_block)

    # Batch block creation
    cbs = sub.add_parser("create-blocks", help="Batch-create multiple blocks in a page")
    cbs.add_argument("--page", required=True, type=int, help="Page id")
    cbs.add_argument("--blocks-json", help='JSON array of blocks: [{"type":"text","title":"<p>...</p>"},...]')
    cbs.add_argument("--blocks-file", help="Path to JSON file with blocks array")
    cbs.set_defaults(func=cmd_create_blocks)

    # Update block
    ub = sub.add_parser("update-block", help="Update block content, type, or format")
    ub.add_argument("id", type=int, help="Block id")
    ub.add_argument("--title", help="New HTML content (auto-wrapped in <p> if needed)")
    ub.add_argument("--type", choices=BLOCK_TYPES, help="Change block type")
    ub.add_argument("--parent", help="Move to parent block id (or 'null' for top-level)")
    ub.add_argument("--format-json", help='Format JSON, e.g. {"block_color":"blue"}')
    ub.add_argument("--table-json", help="Table data JSON (for table blocks)")
    ub.add_argument("--properties-json", help="Full properties JSON (replaces --title)")
    ub.add_argument("--fields-json", help="Extra fields as JSON (merged)")
    ub.set_defaults(func=cmd_update_block)

    # Delete single block
    db = sub.add_parser("delete-block", help="Soft-delete a single block")
    db.add_argument("id", type=int, help="Block id")
    db.set_defaults(func=cmd_delete_block)

    # Bulk delete blocks
    dbs = sub.add_parser("delete-blocks", help="Bulk-delete multiple blocks by ID")
    dbs.add_argument("ids", nargs="+", help="Block IDs to delete")
    dbs.set_defaults(func=cmd_delete_blocks)

    # Move block
    mb = sub.add_parser("move-block", help="Move a block (change parent or page)")
    mb.add_argument("id", type=int, help="Block id")
    mb.add_argument("--parent", help="New parent block id (or 'null' for top-level)")
    mb.add_argument("--page", type=int, help="Move to different page")
    mb.set_defaults(func=cmd_move_block)

    # Reorder blocks
    rb = sub.add_parser("reorder-blocks", help="Reorder blocks within a page (move after/before a target)")
    rb.add_argument("ids", nargs="+", help="Block IDs to move")
    rb.add_argument("--page", required=True, type=int, help="Page id")
    rb.add_argument("--after", help="Place blocks AFTER this block ID")
    rb.add_argument("--before", help="Place blocks BEFORE this block ID")
    rb.set_defaults(func=cmd_reorder_blocks)

    # --- Raw ---
    rs = sub.add_parser("raw", help="Raw POST to /api/core/data/{entity}/{action}[/{id}]")
    rs.add_argument("entity", help="Entity name (e.g. Docs, Pages, PageBlocks)")
    rs.add_argument("--action", default="search", help="search|select|insert|update|remove")
    rs.add_argument("--record-id", help="Record ID (appended to URL for update)")
    rs.add_argument("--body", help="JSON body string (else reads stdin or --file)")
    rs.add_argument("--file", help="Path to JSON file with request body")
    rs.set_defaults(func=cmd_raw)

    return p


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
