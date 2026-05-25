# Suppa API Endpoints — Tasks Domain

> All examples use `Authorization: Bearer <token>`. Token must be a real user JWT
> for Tasks operations (API keys return empty results on Tasks).

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
POST  /api/core/data/{Entity}/select                  # single-row fetch via filter
POST  /api/core/data/{Entity}/insert                  # create row(s)
POST  /api/core/data/{Entity}/update/{id}             # update a single record by id
POST  /api/core/data/{Entity}/remove                  # soft-delete by filter
```

Entity names are PascalCase, plural: `Tasks`, `Users`, `TasksComments`,
`StageWorkflows`, `TasksTypes`. IDs are **integers**.

---

## 1. Current user (`get-me`)

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Users/select?markAsView=false' \
  -H 'authorization: Bearer <token>' \
  -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "fields":{"id":true,"firstName":true,"lastName":true,"fullName":true,
              "position":true,"avatar":{"id":true,"fileName":true},
              "roles":{"id":true,"name":true}},
    "conditions":{"operator":"and","filters":[
      {"field":"id","comparator":"=","value":"$current-user"}
    ]},
    "limit":1,"getAccessByFields":true,"includeDeletedRelations":false
  }'
```

`"$current-user"` is a server-side magic value resolved to the caller's id.

---

## 2. Search Tasks

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Tasks/search' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "conditions":{"operator":"and","filters":[
      {"id":"f1","field":"stage.status.value","value":["active","inprogress"],
       "disabled":false,"comparator":"in"},
      {"id":"f2","field":"assignedTo","value":"$current-user",
       "disabled":false,"comparator":"="}
    ]},
    "fields":{
      "id":true,"title":true,"createdAt":true,"deadline":true,
      "assignedTo":{"id":true,"fullName":true},
      "stage":{"id":true,"name":true,"status":{"value":true},
               "workflow":{"id":true,"name":true}},
      "priority":{"id":true,"title":true,"value":true},
      "type":{"id":true,"title":true,"color":true}
    },
    "limit":100,"offset":0,
    "orderBy":[{"field":"stage.name","order":"asc"}],
    "getAccessByFields":true,"searchValue":"","includeDeletedRelations":false
  }'
```

Live-verified distinct stage status values (modern.suppa.me, 2026-05-25): `active`, `inprogress`, `completed`, `cancelled`, `deferred` (5 only).

---

## 3. Get one Task

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Tasks/select' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "conditions":{"operator":"and","filters":[
      {"id":"f","field":"id","value":1214,"comparator":"=","disabled":false}
    ]},
    "fields":{"id":true,"title":true,"htmlDescription":true,
              "assignedTo":{"id":true,"fullName":true}},
    "limit":1,"getAccessByFields":true,"includeDeletedRelations":false
  }'
```

---

## 4. Create Task

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Tasks/insert' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "fields":[
      {"title":"New task from API",
       "htmlDescription":"<p>hi</p>",
       "assignedTo":{"id":9295},
       "type":{"id":25},
       "deadline":"2026-06-01T18:00:00+03:00"}
    ],
    "returning":{"id":true,"title":true,"createdAt":true,
                 "assignedTo":{"id":true,"fullName":true},
                 "stage":{"id":true,"name":true,"status":{"value":true}}}
  }'
```

---

## 5. Update a Task

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Tasks/update/806528' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{"fields":{"title":"New title","stage":{"id":503}}}'
```

Returns `[]` (HTTP 200) if the id does not exist.

---

## 6. Soft-delete a Task

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Tasks/remove' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{"conditions":{"operator":"and","filters":[
    {"id":"f","field":"id","value":806528,"comparator":"=","disabled":false}
  ]}}'
```

---

## 7. Add comment to a Task

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/TasksComments/insert' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "fields":[
      {"owner":{"id":806528},
       "user":{"id":9295},
       "content":"<p>Comment text</p>"}
    ]
  }'
```

- `owner.id` → task id
- `user.id`  → author id (usually current user)
- `content`  → HTML string

---

## 8. Get comments on a Task

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/TasksComments/search' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "conditions":{"operator":"and","filters":[
      {"id":"f","field":"owner.id","value":806528,"comparator":"=","disabled":false}
    ]},
    "fields":{"id":true,"content":true,"createdAt":true,
              "user":{"id":true,"fullName":true}},
    "limit":100,"offset":0,
    "orderBy":[{"field":"createdAt","order":"asc"}],
    "getAccessByFields":true,"searchValue":"","includeDeletedRelations":false
  }'
```

---

## 9. List Workflows (StageWorkflows entity, grouped)

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/StageWorkflows/search' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "conditions":{"operator":"and","filters":[]},
    "limit":100,"offset":0,
    "orderBy":[{"field":"workflow.name","order":"asc"}],
    "searchValue":"",
    "fields":{"workflow":{"id":true,"name":true},"id":"#count"},
    "groupBy":[{"field":"workflow.id"}],
    "includeDeletedRelations":true
  }'
```

---

## 10. Search Users

```bash
curl -X POST 'https://modern.suppa.me/api/core/data/Users/search' \
  -H 'authorization: Bearer <token>' -H 'content-type: application/json' \
  -H 'x-current-language: en' -H 'x-timezone: Europe/Kyiv' -H 'x-view-mode: view' \
  --data-raw '{
    "conditions":{"operator":"and","filters":[
      {"id":"f","field":"fullName","value":"Andrii","comparator":"like","disabled":false}
    ]},
    "fields":{"id":true,"firstName":true,"lastName":true,"fullName":true,
              "avatar":{"id":true,"fileName":true}},
    "limit":50,"offset":0,
    "orderBy":[{"field":"fullName","order":"asc"}],
    "searchValue":"","getAccessByFields":true,"includeDeletedRelations":false
  }'
```
