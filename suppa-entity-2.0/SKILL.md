---
name: suppa-entity
description: Manage Entities, Fields, Enums, and Schema on the Suppa platform (modern.suppa.me) via direct HTTP API calls. Use this skill whenever the user wants to create a new entity, add fields to an entity, define enum values, list/describe entities, search records of any entity, inspect custom fields, or run ad-hoc queries against any Suppa entity. Trigger phrases (English) — "create entity", "add field", "add enum value", "list field types", "list entities", "all entities", "describe entity", "show schema", "custom fields", "search records", "search instances", "find records"; (Ukrainian / Українська) — "створити сутність", "створити entity", "додати поле", "додати field", "значення enum", "довідник", "типи полів", "список сутностей", "усі сутності", "які сутності", "опиши сутність", "схема сутності", "кастомні поля", "користувацькі поля", "знайти записи", "пошук записів", "інстанси"; (transliteration) — "spysok sutnostei", "kastomni polia". Works via plain HTTP — no MCP server required.
---

# Suppa Entity Builder (modern.suppa.me)

Direct HTTP client for the Suppa Builder & Schema APIs. All commands
go through `scripts/suppa_api.py`, a single-file Python script with **no
external dependencies** (uses only the Python standard library).

This skill is **tenant-portable** — it works on any Suppa tenant regardless
of which applications are installed.

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

### 0.2 Decision tree — pick the right command for the user's intent

| If the user wants to…                                | Use this command |
| ---------------------------------------------------- | ---------------- |
| **List ALL entities on the tenant**                  | `list-entities` (filters: `--initiator`, `--type`, `--search`, `--application`) |
| **Show one entity's fields / custom fields**         | `describe-entity NAME [--custom-only] [--format json]` |
| **Search records of ANY entity**                     | `search ENTITY --filter "f=v" --field x --field y` |
| **Count records**                                    | `search ENTITY --filter "..." --count-only` |
| Build a new entity                                   | `create-entity` |
| Add fields to an entity                              | `add-field` |
| Define allowed enum values                           | `add-enum-values` |
| See all supported field types                        | `list-field-types` |
| One-off body the wrappers can't express              | `raw ENTITY --action search\|select\|insert\|update\|remove --body '{...}'` |

### 0.3 Hard rules

- **Always** use the script's CLI commands. Don't reinvent the body via `raw`
  if a wrapper already exists.
- **Never** assume an entity exists. If the user names an unknown entity, run
  `list-entities --search NAME` first. A 404 on `/api/core/data/X/...` means
  the entity is not installed on this tenant.
- **Never** embed JSON inside `python -c "..."` on Windows PowerShell — the
  shell mangles quotes. Either use the skill's CLI flags, or write the JSON to
  a temp file and pipe it.
- **Never** chain shell commands with `&&` on Windows PowerShell. Use `;` or
  separate invocations.
- **Always** verify writes. After `create-entity`/`add-field`/`add-enum-values`
  run a read-back (`describe-entity` or a `search`) to confirm the change.
  The server sometimes returns `"title": null` from `create-entity` even when
  the title was saved — only the schema GET is authoritative.

### 0.4 Error-code cheat-sheet

| Status                     | Meaning                                              | Agent action |
| -------------------------- | ---------------------------------------------------- | ------------ |
| `401 Unauthorized`         | Token missing/expired                                | Ask user for fresh JWT or API key |
| `404 Not Found` on `/schema/X` or `/data/X/...` | Entity does not exist on this tenant | Run `list-entities --search X` to discover the real name |
| `400 Bad Request` mentioning `current transaction is aborted` (`25P02`) | Transient Postgres pool state | Retry the SAME command |
| `400` "Field X already exists" after a prior 500 from `add-fields` | Non-transactional partial success | Continue with a fresh field name; the column is already there |
| `500` from `data-bulk/Enums` mentioning `enums_entityid_value_name_uindex` | Duplicate `(entityId, value, name)` | The value already exists; use `raw Enums --action update` or skip |

### 0.5 Authentication

Both **integrator API keys** and **real user JWTs** work for all entity/builder
operations. API keys are sufficient for: `list-entities`, `describe-entity`,
`search`, `create-entity`, `add-field`, `add-enum-values`, `raw`.

## 1. Authentication

The script reads the Bearer token from the `SUPPA_API_KEY` environment variable.

```powershell
$env:SUPPA_API_KEY = "<token>"
```

Optional environment variables:

| Var                      | Default                       | Purpose                                  |
| ------------------------ | ----------------------------- | ---------------------------------------- |
| `SUPPA_BASE_URL`         | `https://modern.suppa.me`     | Override host (staging, on-prem, etc.)   |
| `SUPPA_LANG`             | `en`                          | Sent as `x-current-language` (`en`/`uk`) |
| `SUPPA_TZ`               | `Europe/Kyiv`                 | Sent as `x-timezone`                     |

## 2. Commands — quick reference

```
python scripts/suppa_api.py <command> [options]
```

### Schema discovery
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `get-me`           | Current authenticated user (smoke test)                  |
| `list-entities`    | List ALL entities on the tenant (`GET /api/core/schema`). Filters: `--initiator system\|client`, `--type entity\|tabular-part`, `--application NAME`, `--search SUBSTR`, `--format json` |
| `describe-entity`  | Show one entity's fields + options (`GET /api/core/schema/{name}`). Use `--custom-only` to hide system fields; `--format json` for raw schema |
| `search`           | Generic instance search on ANY entity with simple `--filter` syntax |

### Builder (schema management)
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `create-entity`    | Create a new entity (`POST /api/core/builder/create-entity`) |
| `add-field`        | Add one or more fields to an existing entity             |
| `list-field-types` | Show all supported field types with example shapes       |
| `add-enum-values`  | Insert allowed values for an enum field                  |

### Power-user
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `raw`              | POST arbitrary body to any `/api/core/data/{Entity}/{action}` |

## 3. Common recipes

### Discover entities & inspect custom fields

```powershell
# List every entity on the tenant
python scripts/suppa_api.py list-entities

# Only custom-built entities (excludes system ones like Users, Files, Tasks)
python scripts/suppa_api.py list-entities --initiator client --type entity

# Substring match across name + title
python scripts/suppa_api.py list-entities --search invoice

# Show one entity's full schema (fields, options, custom-vs-system marker)
python scripts/suppa_api.py describe-entity Tasks

# Only client-added (custom) fields
python scripts/suppa_api.py describe-entity Tasks --custom-only

# Raw JSON for programmatic consumption
python scripts/suppa_api.py describe-entity MyEntity --format json
```

### Generic instance search (any entity, simple filter syntax)

```powershell
# All rows of any entity
python scripts/suppa_api.py search Projects --field id --field title --limit 50

# Simple equality + dot-notation projection
python scripts/suppa_api.py search Tasks `
  --field id --field title --field stage.status.value `
  --filter "assignedTo=`$current-user" `
  --filter "stage.status.value=active,inprogress" `
  --order-by "createdAt:desc" --limit 20

# Substring (LIKE), null check, count only
python scripts/suppa_api.py search Users --filter "fullName~Andrii" --field id --field fullName
python scripts/suppa_api.py search Tasks --filter "deletedAt=null" --count-only
python scripts/suppa_api.py search Tasks --filter "assignedTo=*" --count-only   # not null

# Numeric range
python scripts/suppa_api.py search Invoices --filter "amount>=100" --filter "amount<1000"
```

### Create a new entity

```powershell
python scripts/suppa_api.py create-entity myEntity --title-en "My Entity" --enable-comments
```

Toggles: `--enable-comments`, `--enable-favorites`, `--enable-approvals`,
`--enable-time-tracking`, `--enable-browsing-history`,
`--enable-track-change-history`, `--enable-global-search`,
`--enable-notification-mutes`, `--enable-reminders`, `--enable-reactions`
(all default OFF).

Pass a multi-language title with `--title-json '{"en":"My Entity","uk":"Моя сутність"}'`.

### Add fields

```powershell
python scripts/suppa_api.py add-field myEntity --name title    --type text          --title-en "Title" --required
python scripts/suppa_api.py add-field myEntity --name count    --type integer       --title-en "Count" --default-value 0
python scripts/suppa_api.py add-field myEntity --name score    --type numeric       --title-en "Score" --decimal-places 2 --min-value 0 --max-value 100
python scripts/suppa_api.py add-field myEntity --name due      --type date          --title-en "Due"
python scripts/suppa_api.py add-field myEntity --name at       --type datetime      --title-en "At"
python scripts/suppa_api.py add-field myEntity --name owner    --type many-to-one   --title-en "Owner"    --relation-target Users
python scripts/suppa_api.py add-field myEntity --name watchers --type many-to-many  --title-en "Watchers" --relation-target Users
python scripts/suppa_api.py add-field myEntity --name photo    --type file          --title-en "Photo"
python scripts/suppa_api.py add-field myEntity --name files    --type multi-file    --title-en "Files"
python scripts/suppa_api.py add-field myEntity --name meta     --type json          --title-en "Metadata"
python scripts/suppa_api.py add-field myEntity --name name     --type multi-language --title-en "Display Name"
python scripts/suppa_api.py add-field myEntity --name key      --type uuid          --title-en "Key" --unique
python scripts/suppa_api.py add-field myEntity --name ic       --type icon          --title-en "Icon"
python scripts/suppa_api.py add-field myEntity --name status   --type enum          --title-en "Status" --relation-target myEntity.status --sub-type myEntity.status
```

> **Enum naming convention** — both `subType` and `relationTarget` must equal
> `<EntityName>.<fieldName>` for the field to validate.

> **Server quirk.** When `/add-fields` returns HTTP 500 mid-request, the column
> may already be created in the database (non-transactional). Retrying the same
> field name then errors `Column "X" already exists`. Use a fresh name on retry.

### Define allowed enum values

```powershell
python scripts/suppa_api.py add-enum-values --enum myEntity.status `
  --value open --value closed --value blocked `
  --icon check --icon x --icon ban
```

- `--enum` (required): qualified name `<Entity>.<fieldName>`.
- `--value` (repeatable, required): one per option.
- `--icon` (repeatable, parallel to `--value`).
- `--titles-json` (optional): JSON array of localized titles per slot.
- `--entity-id N` (optional): auto-resolved from the prefix.

> Re-inserting the same `(entityId, value, name)` triple violates the unique
> index → HTTP 500. To change an existing value, send `update`/`remove` arrays
> via `raw Enums`.

### Power-user — arbitrary entity query

```powershell
python scripts/suppa_api.py raw Projects --body '{
  "conditions":{"operator":"and","filters":[]},
  "fields":{"id":true,"title":true},
  "limit":10,"offset":0,
  "orderBy":[{"field":"createdAt","order":"desc"}],
  "searchValue":"","getAccessByFields":true,"includeDeletedRelations":false
}'
```

## 4. Filter & field shapes

- **Filter**: `{"field":"stage.status.value","value":["active","inprogress"],"comparator":"in"}`
- **`in` over a relation**: value is `[{"id":N},{"id":N}]`; over a string column it's raw strings.
- **`like`**: value MUST use SQL wildcards `%substring%` (the script auto-wraps bare strings).
- **Field projection**: nested booleans, e.g. `{"id":true,"owner":{"id":true,"fullName":true}}`.
- **orderBy**: `[{"field":"createdAt","order":"desc"}]`.
- **Required on every search body**: `searchValue` (string), `orderBy`, `limit`, `offset`.
- **Response**: bare JSON array (NOT wrapped in `{data:[...]}`).
- **IDs are integers** (not UUIDs).

### Quick filter syntax for the `search` command

| CLI form                       | Comparator      | Notes                                  |
| ------------------------------ | --------------- | -------------------------------------- |
| `--filter "id=42"`             | `=`             | JSON-decoded value (numbers, bools)    |
| `--filter "name!=foo"`         | `!=`            |                                        |
| `--filter "title~report"`      | `like`          | Auto-wraps as `%report%`               |
| `--filter "createdAt>=2026-01-01"` | `>=`        |                                        |
| `--filter "amount<100"`        | `<`             |                                        |
| `--filter "id=1,2,3"`          | `in`            | Comma-separated list                   |
| `--filter "deletedAt=null"`    | `is null`       |                                        |
| `--filter "assignedTo=*"`      | `is not null`   |                                        |

## 5. Supported field types

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
| `defaultValue`       | `--default-value`    | Default value (parsed as JSON; falls back to string) |
| `defaultValueIsNull` | `--default-is-null`  | Explicit NULL default                                |
| `isArray`            | `--array`            | PostgreSQL array column                              |
| `maxLength` / `minLength` | `--max-length` / `--min-length` | Text length bounds               |
| `maxValue` / `minValue`   | `--max-value` / `--min-value`   | Numeric bounds                   |
| `isOnlyPositive`     | `--only-positive`    | Reject negative numbers                              |

## 6. PowerShell JSON tips

For complex `--body` arguments, write the JSON to a temp file:

```powershell
$json = @'
{"conditions":{"operator":"and","filters":[]},"fields":{"id":true,"title":true},"limit":10,"offset":0,"orderBy":[{"field":"createdAt","order":"desc"}],"searchValue":"","getAccessByFields":true,"includeDeletedRelations":false}
'@
$json | Set-Content -Encoding UTF8 "$env:TEMP\q.json"
Get-Content "$env:TEMP\q.json" -Raw | python scripts/suppa_api.py raw MyEntity
```

Full reference: see [references/api-endpoints.md](references/api-endpoints.md)
and [references/field-formats.md](references/field-formats.md).
