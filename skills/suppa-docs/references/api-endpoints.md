# Suppa Docs API Endpoints (modern.suppa.me)

> All examples use `Authorization: Bearer <token>`. Token may be an API key or a
> JWT extracted from the `accessToken` cookie.

## Required headers (every request)

```
Authorization: Bearer <token>
Content-Type:  application/json; charset=UTF-8
Accept:        application/json, text/plain, */*
x-current-language: en        # or 'uk'
x-timezone:        Europe/Kyiv
x-view-mode:       view
```

## URL pattern

```
POST  /api/core/data/{Entity}/search                  # paged list with filters
POST  /api/core/data/{Entity}/select?markAsView=false  # single-row fetch (returns array)
POST  /api/core/data/{Entity}/insert                  # create row(s)
POST  /api/core/data/{Entity}/update/{id}             # update a single record by id
POST  /api/core/data/{Entity}/remove                  # soft-delete by filter
POST  /api/core/data/custom-order/{Entity}            # reorder records (custom ordering)
POST  /api/auth/accounts/login                        # exchange creds -> JWT
```

## Entities used by this skill

| Entity        | Purpose                                |
| ------------- | -------------------------------------- |
| `Docs`        | Documents (wiki containers)            |
| `Pages`       | Pages within documents                 |
| `PageBlocks`  | Content blocks within pages            |
| `Users`       | Platform users (for get-me, permissions) |

---

## 1. Docs

### 1.1 List/search documents

```json
POST /api/core/data/Docs/search

{
  "fields": {
    "id": true, "title": true, "description": true,
    "icon": {"icon": true, "color": true},
    "isPublic": true, "isArchived": true, "isTemplate": true,
    "createdAt": true, "updatedAt": true,
    "createdBy": {"id": true, "firstName": true, "lastName": true,
                  "fullName": true, "avatar": {"id": true, "fileName": true, "deletedAt": true}}
  },
  "limit": 100,
  "offset": 0,
  "getAccessByFields": true,
  "searchValue": "",
  "orderBy": [{"field": "updatedAt", "order": "desc"}],
  "conditions": {"operator": "and", "filters": []},
  "includeDeletedRelations": false
}
```

### 1.2 Get single document (with pages and permissions)

```json
POST /api/core/data/Docs/select?markAsView=false

{
  "fields": {
    "id": true, "title": true, "description": true,
    "coverImage": true, "icon": {"icon": true, "color": true},
    "isTemplate": true, "isPublic": true, "isArchived": true,
    "pages": {"id": true, "title": true, "icon": true, "parent": {"id": true}},
    "adminUsers": {"id": true, "fullName": true},
    "adminGroups": {"id": true, "title": true},
    "editUsers": {"id": true, "fullName": true},
    "editGroups": {"id": true, "title": true},
    "viewUsers": {"id": true, "fullName": true},
    "viewGroups": {"id": true, "title": true},
    "createdAt": true, "updatedAt": true, "deletedAt": true,
    "createdBy": {"id": true, "fullName": true}
  },
  "includeDeletedRelations": false,
  "conditions": {"operator": "and", "filters": [
    {"field": "id", "comparator": "=", "value": "5"}
  ]},
  "limit": 1,
  "getAccessByFields": true
}
```

### 1.3 Create document

```json
POST /api/core/data/Docs/insert

{
  "fields": [{
    "title": "My Document",
    "description": "Optional description",
    "isPublic": false,
    "icon": {"icon": "book", "color": "blue"}
  }],
  "returning": { "...same as select fields..." }
}
```

### 1.4 Update document

```json
POST /api/core/data/Docs/update/5

{
  "fields": {
    "title": "Updated Title",
    "isPublic": true
  }
}
```

### 1.5 Delete document

```json
POST /api/core/data/Docs/remove

{
  "conditions": {
    "operator": "and",
    "filters": [{"field": "id", "comparator": "=", "value": 5}]
  }
}
```

---

## 2. Pages

### 2.1 List pages of a document

```json
POST /api/core/data/Pages/search

{
  "fields": {
    "id": true, "title": true, "icon": true,
    "parent": {"id": true, "title": true},
    "doc": {"id": true, "title": true},
    "coverImage": true, "createdAt": true, "updatedAt": true
  },
  "limit": 200,
  "offset": 0,
  "getAccessByFields": true,
  "searchValue": "",
  "orderBy": [{"field": "createdAt", "order": "desc"}],
  "conditions": {"operator": "and", "filters": [
    {"field": "doc.id", "comparator": "=", "value": 5}
  ]},
  "includeDeletedRelations": false
}
```

### 2.2 Get single page

```json
POST /api/core/data/Pages/select?markAsView=false

{
  "fields": {
    "id": true, "title": true, "description": true,
    "icon": true,
    "parent": {"id": true, "title": true},
    "doc": {"id": true, "title": true},
    "coverImage": true, "isTemplate": true,
    "shouldBeIndexed": true, "status": true,
    "adminUsers": {"id": true, "fullName": true},
    "adminGroups": {"id": true, "title": true},
    "editUsers": {"id": true, "fullName": true},
    "editGroups": {"id": true, "title": true},
    "viewUsers": {"id": true, "fullName": true},
    "viewGroups": {"id": true, "title": true},
    "createdAt": true, "updatedAt": true
  },
  "includeDeletedRelations": false,
  "conditions": {"operator": "and", "filters": [
    {"field": "id", "comparator": "=", "value": "12"}
  ]},
  "limit": 1,
  "getAccessByFields": true
}
```

### 2.3 Create page

```json
POST /api/core/data/Pages/insert

{
  "fields": [{
    "doc": {"id": 5},
    "title": "Getting Started",
    "icon": "rocket",
    "parent": {"id": 11},
    "shouldBeIndexed": true
  }],
  "returning": { "...page fields..." }
}
```

### 2.4 Update page

```json
POST /api/core/data/Pages/update/12

{
  "fields": {
    "title": "Quick Start Guide"
  }
}
```

### 2.5 Delete page

```json
POST /api/core/data/Pages/remove

{
  "conditions": {
    "operator": "and",
    "filters": [{"field": "id", "comparator": "=", "value": 12}]
  }
}
```

---

## 3. PageBlocks

### 3.1 Get all blocks of a page (tree-expanded)

```json
POST /api/core/data/PageBlocks/select?markAsView=false

{
  "fields": {
    "id": true, "externalId": true, "type": true,
    "page": {"id": true}, "parent": {"id": true},
    "children": "#expand_tree(10)",
    "format": true, "properties": true,
    "createdAt": true, "updatedAt": true
  },
  "conditions": {"filters": [
    {"field": "page.id", "comparator": "=", "value": "5"},
    {"field": "parent", "comparator": "=", "value": null}
  ], "operator": "and"},
  "orderBy": [{"field": "page", "order": "desc",
               "function": "#custom_order", "args": [5]}],
  "includeDeletedRelations": true
}
```

**Key points:**
- `"children": "#expand_tree(10)"` — recursively fetches child blocks (10 levels)
- `"parent": null` filter — returns only top-level blocks (children nested in response)
- `"function": "#custom_order"` — server-side ordering; `args` = [pageId]
- `includeDeletedRelations: true` — needed for block tree integrity

### 3.2 Create block(s)

```json
POST /api/core/data/PageBlocks/insert

{
  "fields": [{
    "page": {"id": 5},
    "type": "text",
    "properties": {
      "title": "<p>Hello world</p>",
      "content": []
    },
    "format": {"block_color": ""}
  }],
  "returning": {
    "id": true, "externalId": true, "type": true,
    "page": {"id": true}, "parent": {"id": true},
    "format": true, "properties": true,
    "createdAt": true, "updatedAt": true
  }
}
```

**Batch creation:** Pass multiple objects in the `fields` array:

```json
{
  "fields": [
    {"page": {"id": 5}, "type": "head1", "properties": {"title": "<p>Title</p>", "content": []}, "format": {"block_color": ""}},
    {"page": {"id": 5}, "type": "text", "properties": {"title": "<p>Paragraph</p>", "content": []}, "format": {"block_color": ""}},
    {"page": {"id": 5}, "type": "bulletList", "properties": {"title": "<p>Item 1</p>", "content": []}, "format": {"block_color": ""}}
  ],
  "returning": { "..." }
}
```

### 3.3 Update block

```json
POST /api/core/data/PageBlocks/update/42

{
  "fields": {
    "properties": {
      "title": "<p>Updated content</p>",
      "content": []
    },
    "type": "head2"
  }
}
```

### 3.4 Delete block

```json
POST /api/core/data/PageBlocks/remove

{
  "conditions": {
    "operator": "and",
    "filters": [{"field": "id", "comparator": "=", "value": 42}]
  }
}
```

**Bulk delete (OR conditions):**

```json
{
  "conditions": {
    "operator": "or",
    "filters": [
      {"field": "id", "comparator": "=", "value": 42},
      {"field": "id", "comparator": "=", "value": 43},
      {"field": "id", "comparator": "=", "value": 44}
    ]
  }
}
```

### 3.5 Move block (change parent/page)

```json
POST /api/core/data/PageBlocks/update/42

{
  "fields": {
    "parent": {"id": 10}
  }
}
```

To move to top-level: `"parent": null`

### 3.6 Reorder blocks (custom-order API)

```json
POST /api/core/data/custom-order/PageBlocks

{
  "instanceIds": [4489, 4490],
  "beforeInstanceId": 4482,
  "contextFieldName": "page",
  "contextValue": 67,
  "updates": {}
}
```

**IMPORTANT — counter-intuitive field naming:**

| Field               | Meaning                                                      |
| ------------------- | ------------------------------------------------------------ |
| `instanceIds`       | Block IDs to move                                            |
| `beforeInstanceId`  | Anchor block that will stay BEFORE the moved items (= items go **AFTER** anchor) |
| `afterInstanceId`   | Anchor block that will stay AFTER the moved items (= items go **BEFORE** anchor) |
| `contextFieldName`  | Always `"page"` for PageBlocks                               |
| `contextValue`      | Page ID (integer)                                            |
| `updates`           | Additional field updates (usually `{}`)                      |

**IMPORTANT — multi-block ordering quirk:**

When multiple `instanceIds` are provided, the API places them in **reverse order**.
To get blocks to appear in the order [A, B, C], pass `"instanceIds": [C, B, A]` (reversed).
The script handles this automatically.

**Examples:**
- Place blocks 4489, 4490 (in that order) AFTER block 4482: `{"instanceIds": [4490,4489], "beforeInstanceId": 4482, ...}`
- Place block 4489 BEFORE block 4482: `{"instanceIds": [4489], "afterInstanceId": 4482, ...}`

Response: `null` on success.

---

## 4. Users (get-me)

```json
POST /api/core/data/Users/select?markAsView=false

{
  "fields": {
    "id": true, "firstName": true, "lastName": true, "fullName": true,
    "position": true, "avatar": {"id": true, "fileName": true},
    "createdAt": true, "updatedAt": true,
    "roles": {"id": true, "name": true}
  },
  "conditions": {"operator": "and", "filters": [
    {"field": "id", "comparator": "=", "value": "$current-user"}
  ]},
  "limit": 1,
  "getAccessByFields": true,
  "includeDeletedRelations": false
}
```

---

## 5. Filter syntax

| Comparator     | Meaning                    | Example value              |
| -------------- | -------------------------- | -------------------------- |
| `=`            | Exact match                | `5`, `"hello"`, `null`     |
| `!=`           | Not equal                  | `"draft"`                  |
| `like`         | SQL LIKE (use % wildcards) | `"%search%"`               |
| `in`           | Value in list              | `[1, 2, 3]`               |
| `>=`           | Greater or equal           | `"2026-01-01"`             |
| `<`            | Less than                  | `100`                      |
| `is null`      | Field is null              | (value ignored)            |
| `is not null`  | Field is not null          | (value ignored)            |

## 6. Ordering

Standard: `[{"field": "createdAt", "order": "desc"}]`

PageBlocks custom: `[{"field": "page", "order": "desc", "function": "#custom_order", "args": [pageId]}]`

## 7. Special directives

| Directive               | Context         | Purpose                                    |
| ----------------------- | --------------- | ------------------------------------------ |
| `"#expand_tree(10)"`    | Field value     | Recursively expand tree relation (10 levels) |
| `"#custom_order"`       | orderBy function| Server-side custom ordering for page blocks  |
| `"$current-user"`       | Filter value    | Resolves to caller's user id               |
