# Suppa API Field Formats — Tasks Domain

## ID & date conventions

| Thing             | Type / format                                  |
| ----------------- | ---------------------------------------------- |
| Record id         | **integer** (e.g. `806528`)                    |
| Relation value    | object `{"id": 9295}` (when WRITING)           |
| Relation in filter| use dotted path `"field":"assignedTo.id"`      |
| Timestamps        | ISO-8601 string `"2026-06-01T18:00:00+03:00"`  |
| Booleans          | JSON `true` / `false`                          |
| HTML content      | string with raw HTML tags (`<p>...</p>`)       |

## Filter object

```json
{
  "id":         "any-uuid-or-short-string",
  "field":      "stage.status.value",
  "value":      ["active","inprogress"],
  "comparator": "in",
  "disabled":   false
}
```

## Comparators

| Comparator   | Value shape                              | Notes                              |
| ------------ | ---------------------------------------- | ---------------------------------- |
| `=`          | scalar or `"$current-user"`              | exact match                        |
| `!=`         | scalar                                   |                                    |
| `<`, `<=`, `>`, `>=` | scalar / ISO date                |                                    |
| `like`       | string with SQL wildcards `%foo%`        | CLI auto-wraps bare strings        |
| `in`         | array of `{"id":N}` for relations, or raw values for scalars | |
| `empty`      | (no value)                               |                                    |
| `not empty`  | (no value)                               |                                    |

> Stage status values (live-verified, 5 distinct only):
> `active`, `inprogress`, `completed`, `cancelled`, `deferred`

## Magic values

| Token            | Meaning                                  |
| ---------------- | ---------------------------------------- |
| `$current-user`  | caller's user id (real user JWTs only)   |

## Fields projection (nested boolean leaves)

```json
{
  "id": true,
  "title": true,
  "assignedTo": { "id": true, "fullName": true },
  "stage":      { "id": true, "name": true,
                  "status": { "value": true } }
}
```

## orderBy

```json
"orderBy": [
  { "field": "stage.name", "order": "asc"  },
  { "field": "createdAt",  "order": "desc" }
]
```

## Common search-body extras

| Key                       | Type     | Purpose                                         |
| ------------------------- | -------- | ----------------------------------------------- |
| `limit`                   | int      | page size (required)                            |
| `offset`                  | int      | page offset (required)                          |
| `searchValue`             | string   | full-text search; **must always be a string**   |
| `orderBy`                 | array    | required; pass `[]` for `#count` aggregates     |
| `getAccessByFields`       | bool     | include per-field ACL info                      |
| `includeDeletedRelations` | bool     | include soft-deleted relation targets           |

## Response shape

All `/search` and `/select` calls return a **bare JSON array** of rows.

## Insert body

```json
{
  "fields":    [ { "title":"x", "assignedTo": {"id": 9295} } ],
  "returning": { "id": true, "title": true }
}
```

## Known Task fields (from `GET /api/core/schema/Tasks`)

Scalar text/numeric:
`title`, `htmlDescription`, `plainDescription`, `resultText`, `shortID`,
`shortUID`, `deadline`, `closedAt`, `estimatedDuration`, `plannedDuration`,
`spentTime`, `spentTimeTotal`, `plannedStartDate`, `plannedEndDate`.

Relations (write as `{id:N}`, filter via dotted path):
`assignedTo` → Users, `author` → Users, `closedBy` → Users, `editors` → Users[],
`watchers` → Users[], `project` → Projects, `parent` → Tasks,
`children` → Tasks[], `type` → TasksTypes, `priority` → Enums,
`workflow` → StageWorkflows, `stage` → StageWorkflows,
`tags` → Tags[], `attachments` → Files[], `comments` → TasksComments[].
