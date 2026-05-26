# Field Formats — Docs, Pages, PageBlocks

This document describes the field shapes and data formats used by the Docs module
on the `modern.suppa.me` platform.

---

## 1. Docs fields

| Field          | Type           | Description                                         |
| -------------- | -------------- | --------------------------------------------------- |
| `id`           | integer        | Auto-incremented primary key                        |
| `title`        | string         | Document title                                      |
| `description`  | string (HTML)  | Rich-text description                               |
| `coverImage`   | object/null    | Cover image file reference                          |
| `icon`         | object         | `{"icon": "name", "color": "blue"}` or null         |
| `isPublic`     | boolean        | Publicly accessible                                 |
| `isArchived`   | boolean        | Archived / hidden from main list                    |
| `isTemplate`   | boolean        | Template document (for cloning)                     |
| `pages`        | relation[]     | Array of page objects `{id, title, icon, parent}`   |
| `adminUsers`   | relation[]     | Users with full admin access                        |
| `adminGroups`  | relation[]     | Groups with full admin access                       |
| `editUsers`    | relation[]     | Users with edit access                              |
| `editGroups`   | relation[]     | Groups with edit access                             |
| `viewUsers`    | relation[]     | Users with view-only access                         |
| `viewGroups`   | relation[]     | Groups with view-only access                        |
| `createdBy`    | relation       | `{id, fullName}` — creator                          |
| `createdAt`    | ISO-8601       | Creation timestamp                                  |
| `updatedAt`    | ISO-8601       | Last update timestamp                               |
| `deletedAt`    | ISO-8601/null  | Soft-delete timestamp                               |

### Icon object format

```json
{
  "icon": "book",
  "color": "blue"
}
```

Valid icon colors (observed): `""` (default), `"blue"`, `"green"`, `"red"`, `"yellow"`, `"purple"`, `"orange"`.

---

## 2. Pages fields

| Field              | Type           | Description                                    |
| ------------------ | -------------- | ---------------------------------------------- |
| `id`               | integer        | Auto-incremented primary key                   |
| `title`            | string         | Page title                                     |
| `description`      | string         | Page description                               |
| `icon`             | string/null    | Emoji or icon name                             |
| `coverImage`       | object/null    | Cover image file reference                     |
| `parent`           | relation/null  | `{id, title}` — parent page (for nesting)      |
| `doc`              | relation       | `{id, title}` — owning document                |
| `isTemplate`       | boolean        | Template page                                  |
| `shouldBeIndexed`  | boolean        | Whether indexed for search                     |
| `status`           | string         | Page status (e.g. "draft", "active")           |
| `adminUsers`       | relation[]     | Admin-level access users                       |
| `adminGroups`      | relation[]     | Admin-level access groups                      |
| `editUsers`        | relation[]     | Edit-level access users                        |
| `editGroups`       | relation[]     | Edit-level access groups                       |
| `viewUsers`        | relation[]     | View-level access users                        |
| `viewGroups`       | relation[]     | View-level access groups                       |
| `createdAt`        | ISO-8601       | Creation timestamp                             |
| `updatedAt`        | ISO-8601       | Last update timestamp                          |

### Page nesting

Pages support hierarchical nesting via the `parent` field. Top-level pages have
`parent: null`. Child pages reference their parent: `parent: {"id": 11}`.

---

## 3. PageBlocks fields

| Field          | Type           | Description                                         |
| -------------- | -------------- | --------------------------------------------------- |
| `id`           | integer        | Auto-incremented primary key                        |
| `externalId`   | string/null    | Client-generated UUID for tracking                  |
| `type`         | string         | Block type (see table below)                        |
| `page`         | relation       | `{id}` — owning page                               |
| `parent`       | relation/null  | `{id}` — parent block (for nesting, e.g. in toggle) |
| `children`     | tree           | Child blocks (expanded via `#expand_tree(10)`)      |
| `properties`   | object         | Block content (see below)                           |
| `format`       | object         | Block visual format (see below)                     |
| `attachments`  | relation[]     | File attachments                                    |
| `createdAt`    | ISO-8601       | Creation timestamp                                  |
| `updatedAt`    | ISO-8601       | Last update timestamp                               |

### Block types

| Type            | Description                    | Content in `properties.title`        |
| --------------- | ------------------------------ | ------------------------------------ |
| `text`          | Paragraph                      | HTML in `<p>` tags                   |
| `head1`         | H1 heading                     | HTML in `<p>` tags                   |
| `head2`         | H2 heading                     | HTML in `<p>` tags                   |
| `head3`         | H3 heading                     | HTML in `<p>` tags                   |
| `bulletList`    | Bullet list item               | HTML in `<p>` tags                   |
| `numberedList`  | Numbered list item             | HTML in `<p>` tags                   |
| `checkList`     | Checkbox / to-do item          | HTML in `<p>` tags                   |
| `quote`         | Blockquote                     | HTML in `<p>` tags                   |
| `divider`       | Horizontal rule                | `"<p></p>"` (empty)                  |
| `callout`       | Callout/alert box              | HTML in `<p>` tags                   |
| `code`          | Code block                     | **Plain text** (NO `<p>` tags)       |
| `toggle`        | Collapsible section            | HTML in `<p>` tags (header)          |
| `column_list`   | Multi-column layout            | Complex nested structure             |
| `table`         | Table                          | Empty string; data in `properties.table` |
| `banner`        | Banner block                   | HTML in `<p>` tags                   |
| `embed`         | Embedded content               | Uses properties                      |
| `links`         | Links block                    | Uses properties                      |
| `attachment`    | File attachment                | Uses attachments field               |
| `page`          | Page reference/embed           | Uses properties                      |

### Properties object

```json
{
  "title": "<p>Block content here</p>",
  "content": []
}
```

- `title` — the main content of the block (HTML or plain text for code)
- `content` — array for nested child content (used by toggle, columns)

### Format object

```json
{
  "block_color": ""
}
```

Valid `block_color` values: `""` (none), `"blue"`, `"green"`, `"red"`, `"yellow"`,
`"purple"`, `"orange"`, `"pink"`, `"gray"`.

### Table properties

For `type: "table"`, the properties include a `table` object:

```json
{
  "title": "",
  "content": [],
  "table": {
    "columns": [
      {"id": "abc12345", "width": 180},
      {"id": "def67890", "width": 180}
    ],
    "headerRow": true,
    "rows": [
      {
        "id": "row11111",
        "cells": [
          {"columnId": "abc12345", "content": "<p>Header 1</p>"},
          {"columnId": "def67890", "content": "<p>Header 2</p>"}
        ]
      },
      {
        "id": "row22222",
        "cells": [
          {"columnId": "abc12345", "content": "<p>Cell A</p>"},
          {"columnId": "def67890", "content": "<p>Cell B</p>"}
        ]
      }
    ]
  }
}
```

Key rules:
- `columns[].id` — 8-char alphanumeric ID (auto-generated by script)
- `columns[].width` — default 180px
- `headerRow` — whether first row is a header (default: true)
- `rows[].id` — 8-char alphanumeric ID (auto-generated)
- `rows[].cells[].columnId` — must match a column ID
- `rows[].cells[].content` — HTML cell content (`<p>text</p>` or `""` for empty)

---

## 4. HTML content formatting

All block content (except `code` and `divider`) uses HTML wrapped in `<p>` tags.

### Text formatting

| Effect          | HTML                                                    |
| --------------- | ------------------------------------------------------- |
| Bold            | `<strong>text</strong>`                                 |
| Italic          | `<em>text</em>`                                         |
| Underline       | `<u>text</u>`                                           |
| Strikethrough   | `<s>text</s>`                                           |
| Inline code     | `<code>text</code>`                                     |
| Line break      | `<br>`                                                  |
| Link            | `<a href="https://example.com">link text</a>`          |

### Styling via spans

| Effect          | HTML                                                              |
| --------------- | ----------------------------------------------------------------- |
| Text color      | `<span style="color: rgb(R, G, B);">text</span>`                 |
| Background      | `<span style="background-color: rgb(255, 255, 0);">text</span>`  |
| Font family     | `<span style="font-family: Arial, sans-serif;">text</span>`      |
| Font size       | `<span style="font-size: 18px;">text</span>`                     |

### Combination examples

```html
<p><strong>Bold text</strong> and <em>italic text</em></p>
<p><span style="color: rgb(255, 0, 0);"><strong>Red bold</strong></span></p>
<p>Visit <a href="https://suppa.me">our site</a> for details.</p>
```

---

## 5. Ordering conventions

### Block ordering within a page

Blocks are ordered server-side via the `#custom_order` function.
The `get-blocks` command uses `#custom_order` in `orderBy` to preserve
the visual layout as seen in the Suppa UI. New blocks are appended at the end.
To change hierarchy, use `move-block ID --parent PID`.

---

## 6. Permissions model

Both Docs and Pages share a common permissions structure with three access levels:

| Level   | Fields (Users)  | Fields (Groups)  | Capabilities                    |
| ------- | --------------- | ---------------- | ------------------------------- |
| Admin   | `adminUsers`    | `adminGroups`    | Full control (delete, permissions) |
| Edit    | `editUsers`     | `editGroups`     | Read + write content            |
| View    | `viewUsers`     | `viewGroups`     | Read-only access                |

Format: `[{"id": 123, "fullName": "John Doe"}]` for users,
`[{"id": 5, "title": "Developers"}]` for groups.

When creating/updating, pass: `[{"id": 123}]` (just the id is sufficient).

---

## 7. Relation value format

Relations are always passed as objects with at minimum an `id` field:

```json
// Many-to-one (page belongs to doc)
"doc": {"id": 5}

// Self-relation (page nesting)
"parent": {"id": 11}
// or null for top-level
"parent": null

// Many-to-many (permissions)
"adminUsers": [{"id": 123}, {"id": 456}]
```
