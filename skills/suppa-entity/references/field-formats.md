# Suppa API Field Formats — Entity Builder

## ID & date conventions

| Thing             | Type / format                                  |
| ----------------- | ---------------------------------------------- |
| Record id         | **integer** (e.g. `249`)                       |
| Relation value    | object `{"id": 9295}` (when WRITING)           |
| Relation in filter| use dotted path `"field":"owner.id"`           |
| Timestamps        | ISO-8601 string `"2026-06-01T18:00:00+03:00"`  |
| Booleans          | JSON `true` / `false`                          |

## Filter object

```json
{
  "id":         "any-uuid-or-short-string",
  "field":      "name",
  "value":      "foo",
  "comparator": "like",
  "disabled":   false
}
```

## Comparators

| Comparator   | Value shape                              |
| ------------ | ---------------------------------------- |
| `=`          | scalar or `"$current-user"`              |
| `!=`         | scalar                                   |
| `<`, `<=`, `>`, `>=` | scalar / ISO date                |
| `like`       | string with `%wildcards%`                |
| `in`         | array of `{"id":N}` or raw values        |
| `is null`    | (no value needed)                        |
| `is not null` | (no value needed)                       |

## Fields projection (nested boolean leaves)

```json
{
  "id": true,
  "title": true,
  "owner": { "id": true, "fullName": true }
}
```

## Common search-body keys

| Key                       | Type     | Purpose                                         |
| ------------------------- | -------- | ----------------------------------------------- |
| `limit`                   | int      | page size (required)                            |
| `offset`                  | int      | page offset (required)                          |
| `searchValue`             | string   | full-text search; `""` OK                       |
| `orderBy`                 | array    | required; pass `[]` for aggregates              |
| `getAccessByFields`       | bool     | include per-field ACL info                      |
| `includeDeletedRelations` | bool     | include soft-deleted relation targets           |
| `groupBy`                 | array    | for aggregation                                 |

## Response shape

All `/search` and `/select` calls return a **bare JSON array** of rows.

## Insert body

```json
{
  "fields":    [ { "title":"x", "owner": {"id": 9295} } ],
  "returning": { "id": true, "title": true }
}
```

---

## Builder API — field type catalog

| UI label              | CLI `--type`       | Internal `type`    | Required extras                                          |
| --------------------- | ------------------ | ------------------ | -------------------------------------------------------- |
| Text                  | `text`             | `text`             |                                                          |
| Number (whole)        | `integer`          | `integer`          |                                                          |
| Number (decimal)      | `numeric`          | `numeric`          | `decimalPlaces` (default 2)                              |
| Boolean               | `boolean`          | `boolean`          |                                                          |
| Date (date-only)      | `date`             | `timestamp`        | `subType: "date"`                                        |
| Date+time             | `datetime`         | `timestamp`        | `subType: "timestamp"`                                   |
| JSON                  | `json`             | `json`             |                                                          |
| Enum                  | `enum`             | `enum`             | `subType` AND `relationTarget` = `"<Entity>.<field>"`    |
| Icon                  | `icon`             | `icon`             |                                                          |
| UUID                  | `uuid`             | `uuid`             |                                                          |
| Relation (single)     | `many-to-one`      | `many-to-one`      | `relationTarget: "<Entity>"`                             |
| Relation (multi)      | `many-to-many`     | `many-to-many`     | `relationTarget: "<Entity>"`                             |
| File (single)         | `file`             | `file`             | `relationTarget: "Files"` (auto-set)                     |
| File (multi)          | `multi-file`       | `multi-file`       | `relationTarget: "Files"` (auto-set)                     |
| Multi-language string | `multi-language`   | `multi-language`   |                                                          |

### Optional per-field properties

| Property             | CLI flag             | Meaning                                              |
| -------------------- | -------------------- | ---------------------------------------------------- |
| `notNull`            | `--required`         | Required field                                       |
| `unique`             | `--unique`           | Unique constraint                                    |
| `defaultValue`       | `--default-value`    | Default value                                        |
| `defaultValueIsNull` | `--default-is-null`  | Explicit NULL default                                |
| `isArray`            | `--array`            | PostgreSQL array column                              |
| `maxLength` / `minLength` | `--max-length` / `--min-length` | Text length bounds               |
| `maxValue` / `minValue`   | `--max-value` / `--min-value`   | Numeric bounds                   |
| `isOnlyPositive`     | `--only-positive`    | Reject negative numbers                              |
| `options`            | `--options-json`     | UI options (canGroup, canSort, canFilter, etc.)       |

### Default UI options (auto-applied to fields)

```json
{ "canGroup": true, "canSort": true, "canFilter": true,
  "showInTable": true, "editFromTable": true }
```

### Entity default options (all 10 toggles default OFF)

`comments`, `favorites`, `approvals`, `timeTracking`,
`browsingHistory`, `trackChangeHistory`, `globalSearch`,
`notificationMutes`, `reminders`, `reactions`.

## Enums API

```
POST /api/core/data-bulk/Enums
{
  "insert": [
    {"name":"<Entity>.<field>", "value":"open", "icon":"check", "entity":{"id":<entityId>}, "title": null}
  ],
  "update": [],
  "remove": []
}
```

- `name` MUST match the enum field's `subType`/`relationTarget`.
- `entity.id` is from `GET /api/core/schema/<Entity>`.
- Unique constraint rejects duplicate `(entityId, value, name)` triples → HTTP 500.
