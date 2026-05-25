# Suppa API Endpoints — Entity Builder & Schema

> All examples use `Authorization: Bearer <token>`. Both API keys and user JWTs
> work for all builder/schema operations.

## Required headers (every request)

```
Authorization: Bearer <token>
Content-Type:  application/json; charset=UTF-8
Accept:        application/json, text/plain, */*
x-current-language: en        # or 'uk'
x-timezone:        Europe/Kyiv
x-view-mode:       view
```

## URL patterns

```
GET   /api/core/schema                                # LIST ALL entities on the tenant
GET   /api/core/schema/{Entity}                       # field schema (returns id, name, fields[])
POST  /api/core/builder/create-entity                 # create new entity
POST  /api/core/builder/{Entity}/add-fields           # add fields (body is a bare array)
POST  /api/core/data-bulk/Enums                       # bulk insert/update/remove enum values
POST  /api/core/data/{Entity}/search                  # paged list with filters
POST  /api/core/data/{Entity}/select                  # single-row fetch via filter
POST  /api/core/data/{Entity}/insert                  # create row(s)
POST  /api/core/data/{Entity}/update/{id}             # update a single record by id
POST  /api/core/data/{Entity}/remove                  # soft-delete by filter
```

Entity names are PascalCase, plural. IDs are **integers**.

---

## 1. List ALL entities on the tenant

```bash
curl 'https://modern.suppa.me/api/core/schema' \
  -H 'Authorization: Bearer <token>' \
  -H 'Accept: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view'
```

Returns a JSON array. Each row contains:

| Field                 | Notes                                                |
| --------------------- | ---------------------------------------------------- |
| `id`                  | Numeric entity id                                    |
| `name`                | URL slug used in `/api/core/data/{name}/...`         |
| `title`               | Localized `{id, key, en, ...}` or `null`             |
| `type`                | `entity` or `tabular-part`                           |
| `initiator`           | `system` (built-in) or `client` (user-built)         |
| `icon`                | Icon name or null                                    |
| `application`         | `{id, name, title}` or null                          |
| `parentEntity`        | `{id, name}` for child entities                      |
| `representativeField` | `{id, name}` — the field shown as the "label"        |

---

## 2. Inspect one entity's fields

```bash
curl 'https://modern.suppa.me/api/core/schema/Tasks' \
  -H 'Authorization: Bearer <token>' \
  -H 'Accept: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view'
```

Returns `{id, name, title, type, initiator, options, fields[]}`. Each entry of
`fields[]` has its own `initiator: system | client` marking.

---

## 3. Create entity

```bash
curl -X POST 'https://modern.suppa.me/api/core/builder/create-entity' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "name":"myEntity",
    "title":{"en":"My Entity"},
    "options":{"comments":true,"favorites":false,"approvals":false,
               "timeTracking":false,"browsingHistory":false,
               "trackChangeHistory":false,"globalSearch":false,
               "notificationMutes":false,"reminders":false,"reactions":false},
    "fields":[]
  }'
```

---

## 4. Add fields

```bash
curl -X POST 'https://modern.suppa.me/api/core/builder/myEntity/add-fields' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '[
    {"name":"title","type":"text","notNull":true,
     "options":{"canGroup":true,"canSort":true,"canFilter":true,
                "showInTable":true,"editFromTable":true},
     "title":{"en":"Title"}},
    {"name":"owner","type":"many-to-one","relationTarget":"Users",
     "options":{"canGroup":true,"canSort":true,"canFilter":true,
                "showInTable":true,"editFromTable":true},
     "title":{"en":"Owner"}}
  ]'
```

> The body is a **bare JSON array**, not wrapped in any object.

---

## 5. Bulk-Enums (allowed values for `enum` fields)

```bash
curl -X POST 'https://modern.suppa.me/api/core/data-bulk/Enums' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "insert":[
      {"name":"myEntity.status","value":"open",  "icon":"check","entity":{"id":249},"title":null},
      {"name":"myEntity.status","value":"closed","icon":"x",    "entity":{"id":249},"title":{"en":"Closed"}}
    ],
    "update":[],
    "remove":[]
  }'
```

- `name` MUST match the enum field's `subType`/`relationTarget` (`<Entity>.<field>`).
- `entity.id` is the **numeric entity id** (from `GET /api/core/schema/<Entity>`).
- Unique constraint `enums_entityid_value_name_uindex` rejects duplicate triples.

---

## 6. Generic search (any entity)

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Users/search' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "conditions":{"operator":"and","filters":[
      {"id":"f","field":"fullName","value":"%Andrii%","comparator":"like","disabled":false}
    ]},
    "fields":{"id":true,"firstName":true,"lastName":true,"fullName":true},
    "limit":50,"offset":0,
    "orderBy":[{"field":"fullName","order":"asc"}],
    "searchValue":"","getAccessByFields":true,"includeDeletedRelations":false
  }'
```

Response is always a **bare JSON array**.
