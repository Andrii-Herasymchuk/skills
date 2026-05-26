---
name: suppa-docs
description: "Manage Docs, Pages, and PageBlocks on the Suppa platform (modern.suppa.me) via direct HTTP API calls. Use this skill whenever the user wants to list/search/create/update/delete documents, pages within documents, or page blocks (content blocks) within pages, write articles, create documentation, fill pages with content, or manipulate page structure. Trigger phrases (English) \u2014 \"list docs\", \"search docs\", \"get doc\", \"create doc\", \"update doc\", \"delete doc\", \"list pages\", \"get page\", \"create page\", \"update page\", \"delete page\", \"get blocks\", \"page blocks\", \"create block\", \"update block\", \"delete block\", \"page content\", \"doc content\", \"read page\", \"write page\", \"fill page\", \"add content\", \"write article\", \"create documentation\", \"batch blocks\", \"clear page\"; (Ukrainian) \u2014 \"\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0438\", \"\u0434\u043e\u043a\u0438\", \"\u0441\u043f\u0438\u0441\u043e\u043a \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0456\u0432\", \"\u0437\u043d\u0430\u0439\u0442\u0438 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\", \"\u0441\u0442\u0432\u043e\u0440\u0438\u0442\u0438 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\", \"\u043e\u043d\u043e\u0432\u0438\u0442\u0438 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\", \"\u0432\u0438\u0434\u0430\u043b\u0438\u0442\u0438 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\", \"\u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0438\", \"\u0441\u043f\u0438\u0441\u043e\u043a \u0441\u0442\u043e\u0440\u0456\u043d\u043e\u043a\", \"\u0441\u0442\u0432\u043e\u0440\u0438\u0442\u0438 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0443\", \"\u043e\u043d\u043e\u0432\u0438\u0442\u0438 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0443\", \"\u0432\u0438\u0434\u0430\u043b\u0438\u0442\u0438 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0443\", \"\u0431\u043b\u043e\u043a\u0438\", \"\u043a\u043e\u043d\u0442\u0435\u043d\u0442 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0438\", \"\u0441\u0442\u0432\u043e\u0440\u0438\u0442\u0438 \u0431\u043b\u043e\u043a\", \"\u043e\u043d\u043e\u0432\u0438\u0442\u0438 \u0431\u043b\u043e\u043a\", \"\u0432\u0438\u0434\u0430\u043b\u0438\u0442\u0438 \u0431\u043b\u043e\u043a\", \"\u043d\u0430\u043f\u0438\u0441\u0430\u0442\u0438 \u0441\u0442\u0430\u0442\u0442\u044e\", \"\u0437\u0430\u043f\u043e\u0432\u043d\u0438\u0442\u0438 \u0441\u0442\u043e\u0440\u0456\u043d\u043a\u0443\", \"\u0434\u043e\u0434\u0430\u0442\u0438 \u043a\u043e\u043d\u0442\u0435\u043d\u0442\". Works via plain HTTP \u2014 no MCP server required."
---

# Suppa Docs (modern.suppa.me)

Direct HTTP client for the Suppa Docs module REST API. Manages **Documents**,
**Pages** (within documents), and **PageBlocks** (content blocks within pages).

All commands go through `scripts/suppa_api.py`, a single-file Python script
with **no external dependencies** (uses only the Python standard library).

---

## 0. Agent operating instructions (READ FIRST)

### 0.1 Pre-flight checklist (run before the FIRST command of a turn)

1. **Token present?** `$env:SUPPA_API_KEY` must be set. If empty, ask the user
   for a token (API key OR an `accessToken` JWT copied from a logged-in
   browser). NEVER hardcode a token in a script.
2. **Right tenant?** The default base URL is `https://modern.suppa.me`. If the
   user pastes a token whose JWT payload `tenant.clientUrl` differs, set
   `$env:SUPPA_BASE_URL` to match before running anything.
3. **Encoding.** On Windows always set `$env:PYTHONIOENCODING = "utf-8"` once
   per shell to avoid Unicode garbling in output.
4. **Smoke test.** Run `python scripts/suppa_api.py get-me` first. If it
   returns the user object you have a working token + URL.

### 0.2 Decision tree \u2014 pick the right command for the user's intent

| If the user wants to\u2026                              | Use this command |
| ---------------------------------------------------- | ---------------- |
| List all documents                                   | `list-docs [--search "..."]` |
| Get a single document with its pages                 | `get-doc ID` |
| Create a new document                                | `create-doc --title "..."` |
| Update a document (title, public, archive)           | `update-doc ID --title "..." [--public] [--archive]` |
| Delete a document                                    | `delete-doc ID` |
| List pages of a document                             | `list-pages --doc ID [--parent PID]` |
| Get a single page                                    | `get-page ID` |
| Create a page in a document                          | `create-page --doc ID --title "..." [--parent PID]` |
| Create a nested (child) page                         | `create-page --doc ID --title "..." --parent PARENT_PAGE_ID` |
| Update a page (rename, reparent)                    | `update-page ID --title "..." [--parent PID]` |
| Delete a page                                        | `delete-page ID` |
| Get all blocks (content) of a page                   | `get-blocks --page ID` |
| Get blocks as flat list (for bulk ops/reordering)    | `get-blocks --page ID --flat` |
| Create a single block                                | `create-block --page ID --type TYPE --title "..."` |
| **Write multi-block content (articles, docs)**       | `create-blocks --page ID --blocks-json '[...]'` |
| Update a block's content                             | `update-block ID --title "new content"` |
| Update block type/format                             | `update-block ID --type head1 [--color blue]` |
| Delete a single block                                | `delete-block ID` |
| **Bulk-delete multiple blocks (clear page)**         | `delete-blocks ID1 ID2 ID3 ...` |
| Move/reparent a block                                | `move-block ID --parent PID [--page NEW_PAGE_ID]` |
| Arbitrary API call                                   | `raw ENTITY --action ACTION --body '{...}'` |

### 0.3 Hard rules

- **Always** use the script's CLI commands. Don't reinvent the body via `raw`
  if a wrapper already exists.
- **Never** embed JSON inside `python -c "..."` on Windows PowerShell \u2014 the
  shell mangles quotes. Either use the skill's CLI flags, or write JSON to a
  temp file and pipe it.
- **Never** chain shell commands with `&&` on Windows PowerShell. Use `;` or
  separate invocations.
- **Always** verify writes. After create/update operations, run a read-back
  to confirm the change.
- **PageBlocks are tree-structured.** Top-level blocks have `parent = null`.
  Child blocks nest under a parent via the `parent` relation. Use
  `#expand_tree(10)` on `children` to fetch the full tree in one call.
- **Block ordering** uses a special `#custom_order` function in `orderBy`.
  The script handles this automatically when fetching blocks.
- **CRITICAL: How to split text into blocks.** On a Suppa page, every
  paragraph, heading, bullet item, numbered list item, checkbox, and quote is
  its own SEPARATE PageBlock. When generating multi-block content (articles,
  docs, reports), you MUST split the content into separate blocks using the
  `create-blocks` batch command.
- **Always wrap content in `<p>` tags.** Block content lives in
  `properties.title` as HTML. Exception: code blocks use plain text.
- **For multi-block content, ALWAYS use `create-blocks`** (batch) instead of
  calling `create-block` multiple times. This is faster and atomic.

### 0.4 Error-code cheat-sheet

| Status                     | Meaning                                              | Agent action |
| -------------------------- | ---------------------------------------------------- | ------------ |
| `401 Unauthorized`         | Token missing/expired                                | Ask user for fresh JWT or API key |
| `404 Not Found`            | Entity/record does not exist                         | Verify the ID; the Docs module may not be installed |
| `400 Bad Request`          | Malformed body or missing required fields            | Check the request body structure |
| `403 Forbidden`            | No permission to this document/page                  | User needs admin/edit access |
| `[]` empty response        | No records match the filter                          | Verify the filter values |

### 0.5 Data model

```
Docs (document)
 \u251c\u2500\u2500 Pages (pages within a doc, support nesting via parent)
 \u2502    \u251c\u2500\u2500 Pages (child pages, nested via parent relation)
 \u2502    \u2514\u2500\u2500 PageBlocks (content blocks, tree-structured via parent/children)
 \u2502         \u2514\u2500\u2500 PageBlocks (child blocks, nested)
```

- **Docs**: id, title, description, icon{icon,color}, isPublic, isArchived,
  isTemplate, coverImage, pages[], adminUsers[], editUsers[], viewUsers[],
  adminGroups[], editGroups[], viewGroups[], createdBy, createdAt, updatedAt
- **Pages**: id, title, description, icon, coverImage, isTemplate,
  doc (relation → Docs), parent (self-relation for nesting),
  adminUsers[], editUsers[], viewUsers[], adminGroups[], editGroups[],
  viewGroups[], createdAt, updatedAt
- **PageBlocks**: id, externalId, type, properties{title, content, table},
  format{block_color,...}, page (relation → Pages),
  parent (self-relation), children (tree), attachments, createdAt, updatedAt

---

## 1. Authentication

The script reads the Bearer token from the `SUPPA_API_KEY` environment variable.
Accepts both an API key OR a JWT extracted from the `accessToken` cookie.

```powershell
$env:SUPPA_API_KEY = "<token>"
```

Optional environment variables:

| Var                      | Default                       | Purpose                                  |
| ------------------------ | ----------------------------- | ---------------------------------------- |
| `SUPPA_BASE_URL`         | `https://modern.suppa.me`     | Override host (staging, on-prem, etc.)   |
| `SUPPA_LANG`             | `en`                          | Sent as `x-current-language` (`en`/`uk`) |
| `SUPPA_TZ`               | `Europe/Kyiv`                 | Sent as `x-timezone`                     |

---

## 2. Commands \u2014 quick reference

```
python scripts/suppa_api.py <command> [options]
```

### Documents
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `get-me`           | Current authenticated user (smoke test)                  |
| `list-docs`        | List/search documents                                    |
| `get-doc ID`       | Get a document with its pages list & permissions         |
| `create-doc`       | Create a new document                                    |
| `update-doc ID`    | Update document properties                               |
| `delete-doc ID`    | Soft-delete a document                                   |

### Pages
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `list-pages`       | List pages of a document (`--doc ID`)                    |
| `get-page ID`      | Get a single page by id                                  |
| `create-page`      | Create a new page in a document (supports `--parent`)    |
| `update-page ID`   | Update page properties (title, parent, etc.)             |
| `delete-page ID`   | Soft-delete a page                                       |

### Page Blocks (content)
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `get-blocks`       | Get all blocks of a page (`--page ID`), tree-expanded    |
| `create-block`     | Create a single block in a page                          |
| `create-blocks`    | **Batch-create multiple blocks** from JSON array         |
| `update-block ID`  | Update block content, type, or format                    |
| `delete-block ID`  | Soft-delete a single block                               |
| `delete-blocks`    | **Bulk-delete multiple blocks** (positional IDs)     |
| `move-block ID`    | Move a block (change parent or page)                     |

### Power-user
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `raw`              | POST arbitrary body to any `/api/core/data/{Entity}/{action}` |

---

## 3. Block types and HTML content rules

### 3.1 Supported block types

| Type           | Description                             | Content format                |
| -------------- | --------------------------------------- | ----------------------------- |
| `text`         | Regular paragraph (default)             | `<p>Your text here</p>`      |
| `head1`        | Large heading (H1)                      | `<p>Heading Text</p>`        |
| `head2`        | Medium heading (H2)                     | `<p>Heading Text</p>`        |
| `head3`        | Small heading (H3)                      | `<p>Heading Text</p>`        |
| `bulletList`   | Bullet point (one per block)            | `<p>Bullet text</p>`         |
| `numberedList` | Numbered list item (one per block)      | `<p>Item text</p>`           |
| `checkList`    | Checkbox / to-do item                   | `<p>Todo text</p>`           |
| `quote`        | Blockquote                              | `<p>Quoted text</p>`         |
| `callout`      | Callout / highlight box                 | `<p>Important note</p>`      |
| `code`         | Code snippet                            | Plain text, NO `<p>` tags    |
| `divider`      | Horizontal rule / separator             | `<p></p>` (empty)            |
| `toggle`       | Collapsible section                     | `<p>Toggle header</p>`       |
| `column_list`  | Multi-column layout                     | (uses content array)          |
| `table`        | Table with rows and columns             | (uses table property)         |
| `banner`       | Banner block                            | `<p>Banner text</p>`         |
| `embed`        | Embedded content (video, iframe, etc.)  | (uses properties)             |
| `links`        | Links block                             | (uses properties)             |
| `attachment`   | File attachment                         | (uses attachments field)      |
| `page`         | Page reference/embed                    | (uses properties)             |

### 3.2 HTML formatting cheatsheet

All text content lives in `properties.title` as HTML wrapped in `<p>` tags:

| Effect             | HTML                                                        |
| ------------------ | ----------------------------------------------------------- |
| Plain text         | `<p>Your text here</p>`                                     |
| **Bold**           | `<strong>text</strong>`                                     |
| *Italic*           | `<em>text</em>`                                             |
| Underline          | `<u>text</u>`                                               |
| ~~Strikethrough~~  | `<s>text</s>`                                               |
| `Inline code`      | `<code>text</code>`                                         |
| Line break         | `<br>`                                                      |
| Link               | `<a href="https://example.com">link text</a>`              |
| Color text         | `<span style="color: rgb(255,0,0);">red text</span>`       |
| Highlight          | `<span style="background-color: rgb(255,255,0);">text</span>` |
| Font family        | `<span style="font-family: Arial, sans-serif;">text</span>` |
| Font size          | `<span style="font-size: 18px;">text</span>`               |
| Combined           | `<p><strong><em>Bold italic</em></strong></p>`              |

**Combinable \u2014 nest tags freely:**
```html
<p><span style="color: rgb(0,0,0); font-family: Arial;"><strong>Bold + styled</strong></span></p>
<p><em><u>Italic underlined</u></em></p>
```

### 3.3 Splitting rules (CRITICAL for agents)

Every visual element on a page is a SEPARATE block:

1. Each heading \u2192 one block (`head1`, `head2`, or `head3`)
2. Each paragraph \u2192 one `text` block (do NOT merge multiple paragraphs)
3. Each bullet point \u2192 one `bulletList` block
4. Each numbered item \u2192 one `numberedList` block
5. Each to-do / checkbox \u2192 one `checkList` block
6. Each blockquote \u2192 one `quote` block
7. Each code snippet \u2192 one `code` block (plain text, NO `<p>` tags)
8. A horizontal rule \u2192 one `divider` block (title = `"<p></p>"`)
9. A callout / important note \u2192 one `callout` block
10. A table \u2192 one `table` block with `table` property in properties

**Example conversion:**

User says: *"Write a quick start guide with a heading, intro paragraph, 3 bullet points, and a code example."*

Agent creates blocks:
```json
[
  {"type": "head1", "title": "<p>Quick Start</p>"},
  {"type": "text", "title": "<p>Follow these steps to get started.</p>"},
  {"type": "bulletList", "title": "<p>Install the package</p>"},
  {"type": "bulletList", "title": "<p>Configure your API key</p>"},
  {"type": "bulletList", "title": "<p>Run the example script</p>"},
  {"type": "code", "title": "pip install suppa-client\nexport SUPPA_API_KEY=xxx\npython example.py"}
]
```

### 3.4 Table blocks

Tables use a special structure in `properties.table`:

```json
{
  "columns": [{"id": "col1", "width": 180}, {"id": "col2", "width": 180}],
  "headerRow": true,
  "rows": [
    {"id": "row1", "cells": [
      {"columnId": "col1", "content": "<p>Name</p>"},
      {"columnId": "col2", "content": "<p>Role</p>"}
    ]},
    {"id": "row2", "cells": [
      {"columnId": "col1", "content": "<p>Alice</p>"},
      {"columnId": "col2", "content": "<p>Engineer</p>"}
    ]}
  ]
}
```

When creating table blocks via CLI, pass this as `--table-json`.
Set block `--type table` and `--title ""` (empty).

### 3.5 Block ordering

- Blocks are ordered server-side via the `#custom_order` function.
- New blocks are appended at the end by default.
- To nest blocks, use `--parent BLOCK_ID` on create or `move-block ID --parent PID`.

---

## 4. Common recipes

### 4.1 List all documents

```powershell
python scripts/suppa_api.py list-docs
python scripts/suppa_api.py list-docs --search "API"
```

### 4.2 Get a document with its pages

```powershell
python scripts/suppa_api.py get-doc 5
```

### 4.3 Create / update / delete a document

```powershell
python scripts/suppa_api.py create-doc --title "New Documentation" --icon "book"
python scripts/suppa_api.py update-doc 5 --title "Updated Title" --public
python scripts/suppa_api.py delete-doc 5
```

### 4.4 List pages (with nesting support)

```powershell
# All pages in a document
python scripts/suppa_api.py list-pages --doc 5

# Filter by parent page (show children of page 12)
python scripts/suppa_api.py list-pages --doc 5 --parent 12
```

### 4.5 Create nested pages

```powershell
# Top-level page
python scripts/suppa_api.py create-page --doc 5 --title "Getting Started"

# Child page (nested under page 12)
python scripts/suppa_api.py create-page --doc 5 --title "Installation" --parent 12
```

### 4.6 Update / delete a page

```powershell
python scripts/suppa_api.py update-page 12 --title "Quick Start Guide"
python scripts/suppa_api.py update-page 12 --parent 8      # move under page 8
python scripts/suppa_api.py update-page 12 --parent null   # make top-level
python scripts/suppa_api.py delete-page 12
```

### 4.7 Get page content (blocks)

```powershell
# Tree mode (default) - top-level blocks with nested children expanded
python scripts/suppa_api.py get-blocks --page 5

# Flat mode - all blocks in a flat list (useful for reordering/bulk ops)
python scripts/suppa_api.py get-blocks --page 5 --flat
```

### 4.8 Create a single block

```powershell
# Simple paragraph
python scripts/suppa_api.py create-block --page 5 --type text --title "<p>Hello world</p>"

# Heading
python scripts/suppa_api.py create-block --page 5 --type head1 --title "<p>Introduction</p>"

# Code block (plain text, no <p> tags)
python scripts/suppa_api.py create-block --page 5 --type code --title "const x = 42;"

# Colored callout
python scripts/suppa_api.py create-block --page 5 --type callout --title "<p>Important!</p>" --format-json "{\"block_color\":\"yellow\"}"
```

### 4.9 Batch-create multiple blocks (PREFERRED for articles/docs)

```powershell
# Inline JSON (short content)
python scripts/suppa_api.py create-blocks --page 5 --blocks-json '[{"type":"head1","title":"<p>API Reference</p>"},{"type":"text","title":"<p>This document describes the endpoints.</p>"},{"type":"code","title":"GET /api/users"}]'
```

For longer content, use a temp file to avoid PowerShell quoting issues:

```powershell
@"
[
  {"type": "head1", "title": "<p>Project Overview</p>"},
  {"type": "text", "title": "<p>Welcome to <strong>Project Alpha</strong>.</p>"},
  {"type": "bulletList", "title": "<p>Fast and reliable</p>"},
  {"type": "bulletList", "title": "<p>Easy to configure</p>"},
  {"type": "bulletList", "title": "<p>Well documented</p>"}
]
"@ | Set-Content -Encoding UTF8 "$env:TEMP\blocks.json"
python scripts/suppa_api.py create-blocks --page 5 --blocks-file "$env:TEMP\blocks.json"
```

### 4.10 Update a block

```powershell
# Update text content
python scripts/suppa_api.py update-block 42 --title "<p>Updated paragraph</p>"

# Change block type (paragraph to heading)
python scripts/suppa_api.py update-block 42 --type head2

# Reparent a block
python scripts/suppa_api.py move-block 42 --parent 40

# Add color
python scripts/suppa_api.py update-block 42 --format-json "{\"block_color\":\"blue\"}"

# Full properties update
python scripts/suppa_api.py update-block 42 --properties-json "{\"title\":\"<p>New content</p>\",\"content\":[]}"
```

### 4.11 Delete blocks

```powershell
# Single block
python scripts/suppa_api.py delete-block 42

# Bulk delete multiple blocks (positional IDs)
python scripts/suppa_api.py delete-blocks 42 43 44 45

# Clear a page workflow:
# 1. Get all block IDs (flat mode)
python scripts/suppa_api.py get-blocks --page 5 --flat
# 2. Delete them in bulk (extract IDs from output)
python scripts/suppa_api.py delete-blocks 42 43 44 45 46
```

### 4.12 Write a full article (complete workflow)

```powershell
# 1. Create the document
python scripts/suppa_api.py create-doc --title "Developer Guide"

# 2. Create a page (use doc id from step 1, e.g. 7)
python scripts/suppa_api.py create-page --doc 7 --title "Getting Started"

# 3. Fill with content blocks (use page id from step 2, e.g. 15)
@"
[
  {"type": "head1", "title": "<p>Getting Started</p>"},
  {"type": "text", "title": "<p>Set up your development environment.</p>"},
  {"type": "head2", "title": "<p>Prerequisites</p>"},
  {"type": "bulletList", "title": "<p>Python 3.10+</p>"},
  {"type": "bulletList", "title": "<p>Node.js 18+</p>"},
  {"type": "head2", "title": "<p>Installation</p>"},
  {"type": "numberedList", "title": "<p>Clone the repository</p>"},
  {"type": "code", "title": "git clone https://github.com/org/repo.git"},
  {"type": "numberedList", "title": "<p>Install dependencies</p>"},
  {"type": "code", "title": "pip install -r requirements.txt"},
  {"type": "divider", "title": ""},
  {"type": "callout", "title": "<p><strong>Note:</strong> Port 8000 must be available.</p>"}
]
"@ | Set-Content -Encoding UTF8 "$env:TEMP\blocks.json"
python scripts/suppa_api.py create-blocks --page 15 --blocks-file "$env:TEMP\blocks.json"

# 4. Verify
python scripts/suppa_api.py get-blocks --page 15
```

---

## 5. API shapes reference

### Docs search body

```json
{
  "fields": {
    "id": true, "title": true, "description": true,
    "icon": {"icon": true, "color": true},
    "isPublic": true, "isArchived": true,
    "updatedAt": true, "createdAt": true,
    "createdBy": {"id": true, "fullName": true, "avatar": {"id": true, "fileName": true}}
  },
  "limit": 100, "offset": 0,
  "getAccessByFields": true, "searchValue": "",
  "orderBy": [{"field": "updatedAt", "order": "desc"}],
  "conditions": {"operator": "and", "filters": []},
  "includeDeletedRelations": false
}
```

### PageBlocks select (full tree for a page)

```json
{
  "fields": {
    "id": true, "externalId": true, "type": true,
    "page": {"id": true}, "parent": {"id": true},
    "children": "#expand_tree(10)",
    "format": true, "properties": true,
    "createdAt": true, "updatedAt": true
  },
  "conditions": {"operator": "and", "filters": [
    {"field": "page.id", "comparator": "=", "value": "5"},
    {"field": "parent", "comparator": "=", "value": null}
  ]},
  "orderBy": [{"field": "page", "order": "desc",
               "function": "#custom_order", "args": [5]}],
  "includeDeletedRelations": true
}
```

### Insert (batch-create) body

```json
{
  "fields": [
    {"page": {"id": 5}, "type": "head1", "properties": {"title": "<p>Hello</p>", "content": []}, "format": {}},
    {"page": {"id": 5}, "type": "text", "properties": {"title": "<p>World</p>", "content": []}, "format": {}}
  ],
  "returning": {"id": true, "type": true, "properties": true}
}
```

### Update body (POST /api/core/data/PageBlocks/update/{id})

```json
{
  "fields": {
    "properties": {"title": "<p>Updated</p>", "content": []},
    "type": "head1"
  }
}
```

### Remove body

```json
{
  "conditions": {
    "operator": "and",
    "filters": [{"field": "id", "comparator": "=", "value": 42}]
  }
}
```

---

## 6. PowerShell JSON tips

For complex JSON arguments, write to a temp file:

```powershell
@"
[{"type":"head1","title":"<p>Hello</p>"}]
"@ | Set-Content -Encoding UTF8 "$env:TEMP\blocks.json"
python scripts/suppa_api.py create-blocks --page 5 --blocks-file "$env:TEMP\blocks.json"
```

If you see Unicode garbling:
```powershell
$env:PYTHONIOENCODING = "utf-8"
```

---

## 7. Hardcoded tenant constants (modern.suppa.me, tenant id 5)

| Constant                    | Value                                              |
| --------------------------- | -------------------------------------------------- |
| Base URL                    | `https://modern.suppa.me`                          |
| Tenant id / schema          | `5` / `vexxqynv`                                   |
| Docs entity                 | `Docs`                                             |
| Pages entity                | `Pages`                                            |
| PageBlocks entity           | `PageBlocks`                                       |

Full reference: see [references/api-endpoints.md](references/api-endpoints.md)
and [references/field-formats.md](references/field-formats.md).
