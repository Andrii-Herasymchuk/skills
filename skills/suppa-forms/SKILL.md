---
name: suppa-forms
description: Create, update, list, and manage Dynamic Forms on the Suppa platform (modern.suppa.me) via direct HTTP API calls. Use this skill whenever the user wants to create a form, build a form schema, add fields to a form, configure form settings, create entity forms, custom forms, dashboards, webforms, or programmatically generate form schemas. Trigger phrases (English) — "create form", "build form", "form schema", "add field to form", "form settings", "entity form", "custom form", "dashboard form", "webform", "form layout", "form columns", "form builder", "form module", "form conditions", "form validation"; (Ukrainian / Українська) — "створити форму", "побудувати форму", "схема форми", "додати поле до форми", "налаштування форми", "форма сутності", "кастомна форма", "дашборд", "вебформа", "макет форми", "колонки форми", "конструктор форм", "модуль форми", "умови форми", "валідація форми"; (transliteration) — "stvoriti formu", "shema formi", "nalashtuvannia formi". Works via plain HTTP — no MCP server required.
---

# Suppa Forms (modern.suppa.me)

Direct HTTP client for the Suppa Dynamic Forms REST API. All commands
go through `scripts/suppa_api.py`, a single-file Python script with **no
external dependencies** (uses only the Python standard library).

## 0. Agent operating instructions (READ FIRST)

This section is the playbook for the AI agent invoking this skill. Follow it
literally — most failures observed in the wild come from skipping these steps.

### 0.1 Pre-flight checklist (run before the FIRST command of a turn)

1. **Token present?** `$env:SUPPA_API_KEY` must be set. If empty, ask the user
   for a token (API key OR an `accessToken` JWT copied from a logged-in
   browser). NEVER hardcode a token in a script.
2. **Right tenant?** The default base URL is `https://modern.suppa.me`. If the
   user pastes a token whose JWT payload `tenant.clientUrl` differs (e.g.
   `testing-stage.test.suppa.me`), set `$env:SUPPA_BASE_URL` to match before
   running anything. Decode the JWT payload (second segment, base64url) to
   confirm `accountId` and `tenant.clientUrl`.
3. **Encoding.** On Windows always set `$env:PYTHONIOENCODING = "utf-8"` once
   per shell to avoid Unicode garbling in output.
4. **Smoke test.** Run `python scripts/suppa_api.py get-me` first. If it
   returns the user object you have a working token + URL. If it 401s, the
   token is wrong/expired. If it 404s, the base URL is wrong.

### 0.2 Decision tree — pick the right command for the user's intent

| If the user wants to…                                     | Use this command |
| --------------------------------------------------------- | ---------------- |
| List all forms for an entity                              | `list-forms --entity NAME` |
| List custom/dashboard/webform forms                       | `list-forms --type customForm` |
| Get full form (schema + settings + module)                | `get-form ID` |
| Create an entity form (CRM, Tasks, custom entity)         | `create-form --entity NAME --type elementForm --name "..."` |
| Create a custom standalone form                           | `create-form --type customForm --name "..."` |
| Create a dashboard                                        | `create-form --type dashboard --name "..."` |
| Create from a template                                    | `create-form --template task-form --name "..."` |
| Auto-generate form from entity fields                     | `create-form --entity NAME --generate-all --columns 2` |
| Generate schema JSON without saving                       | `generate-schema --entity NAME --fields "a,b,c"` |
| Update an existing form's schema/settings/module          | `update-form ID --schema-file FILE` |
| Add a single field to an existing form                    | `add-field ID --name "x" --type text --label "X"` |
| Lock/unlock a form for editing                            | `lock-form ID` / `unlock-form ID` |
| List available field types                                | `list-field-types` |
| List available templates                                  | `list-templates` |
| Validate a schema JSON file locally                       | `validate-schema FILE` |

### 0.3 Hard rules

- **Always** use the script's CLI commands. Don't reinvent the body via `raw`
  if a wrapper already exists — the wrappers handle UUID generation, grid
  positioning, and field structure normalization.
- **Never** embed JSON inside `python -c "..."` on Windows PowerShell — the
  shell mangles quotes. Either use the skill's CLI flags, or write the JSON to
  a temp file and pipe it.
- **Never** chain shell commands with `&&` on Windows PowerShell. Use `;` or
  separate invocations.
- **Always** verify writes. After `create-form`/`update-form` run a read-back
  (`get-form ID`) to confirm the change.
- **Never** modify a locked form without unlocking it first.
- **Always** resolve entity name/id before creating entity forms.
- **IDs are integers.** Form IDs, entity IDs, user IDs — all integers.

### 0.4 Error-code cheat-sheet

| Status                     | Meaning                                              | Agent action |
| -------------------------- | ---------------------------------------------------- | ------------ |
| `401 Unauthorized`         | Token missing/expired                                | Ask user for fresh JWT or API key |
| `404 Not Found` on `/data/Forms/...` | Forms entity not found on tenant     | Entity may be named differently; try `list-entities` from suppa-entity skill |
| `400 Bad Request` mentioning `current transaction is aborted` (`25P02`) | Transient Postgres pool state | Wait briefly, retry the SAME command |
| `409 Conflict` / `lockedBy` in response | Form locked by another user       | Show lock info, offer `unlock-form --force` |
| `400` schema validation error | Invalid field structure                        | Validate schema locally with `validate-schema` first |
| `[]` empty response from Forms search | Normal — no forms match the filter | Inform user, suggest broader filters |

### 0.5 Authentication

Both **integrator API keys** and **real user JWTs** work for form CRUD
operations. API keys are sufficient for: `list-forms`, `get-form`,
`create-form`, `update-form`, `lock-form`, `unlock-form`.

## 1. Authentication

The script reads the Bearer token from the `SUPPA_API_KEY` environment variable.
Accepts both an API key OR a JWT extracted from the `accessToken` cookie of a
logged-in browser session (`https://modern.suppa.me`).

```powershell
# PowerShell
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

### Form CRUD
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `get-me`           | Current authenticated user (smoke test)                  |
| `list-forms`       | List forms with optional entity/type filter              |
| `get-form ID`      | Get one form (full schema, settings, module)             |
| `create-form`      | Create a new form (from template, entity, or schema file)|
| `update-form ID`   | Update schema, settings, or module code                  |
| `lock-form ID`     | Lock form for editing (set lockedBy to current user)     |
| `unlock-form ID`   | Unlock form (clear lockedBy)                             |

### Schema generation
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `generate-schema`  | Generate schema JSON from entity fields (doesn't save)   |
| `add-field ID`     | Add a single field to an existing form's schema          |
| `list-field-types` | Show all available form field types                      |
| `list-templates`   | Show available pre-built form templates                  |
| `validate-schema`  | Validate a schema JSON file for common errors            |

## 3. Common recipes

### Create an entity form from specific fields

```powershell
python scripts/suppa_api.py create-form `
    --entity Tasks `
    --type elementForm `
    --name "Task Create Form" `
    --columns 2 `
    --fields "title,htmlDescription,assignedTo,deadline,priority"
```

### Create a form from ALL custom entity fields

```powershell
python scripts/suppa_api.py create-form `
    --entity Projects `
    --type elementForm `
    --name "Project Form" `
    --columns 2 `
    --generate-all `
    --submit-button
```

### Create from a template

```powershell
python scripts/suppa_api.py create-form `
    --template contact-form `
    --type customForm `
    --name "Contact Us"
```

Available templates: `entity-basic`, `contact-form`, `task-form`, `feedback`,
`wizard`, `dashboard-basic`.

### Create from a schema JSON file

```powershell
python scripts/suppa_api.py create-form `
    --type customForm `
    --name "My Form" `
    --schema-file C:\schemas\my-form.json `
    --module-file C:\modules\my-form.js
```

### Generate schema locally (preview without saving)

```powershell
python scripts/suppa_api.py generate-schema `
    --entity Projects `
    --fields "title,status,owner,budget,startDate" `
    --columns 2 `
    --output C:\schemas\project-form.json
```

### Update an existing form

```powershell
# Update schema
python scripts/suppa_api.py update-form 1234 --schema-file C:\schemas\updated.json

# Update settings (merge)
python scripts/suppa_api.py update-form 1234 --settings-json "{\"columnsNumber\":2,\"showSubmitButton\":true}"

# Update module code
python scripts/suppa_api.py update-form 1234 --module-file C:\modules\handlers.js

# Rename
python scripts/suppa_api.py update-form 1234 --name "New Form Name"
```

### Add a field to an existing form

```powershell
python scripts/suppa_api.py add-field 1234 `
    --name "deadline" --type date --label "Deadline" --rules "required"
```

### Lock / unlock for editing

```powershell
python scripts/suppa_api.py lock-form   1234
python scripts/suppa_api.py unlock-form 1234
```

### Validate a schema file

```powershell
python scripts/suppa_api.py validate-schema C:\schemas\my-form.json
```

## 4. Form types

| Type | Purpose | Entity? | Description |
| ---- | ------- | ------- | ----------- |
| `elementForm` | Entity record form | Yes | Create/edit/view records of an entity |
| `listForm` | Entity list view | Yes | Table/grid view configuration |
| `customForm` | Standalone form | No | Surveys, wizards, tools |
| `dashboard` | Dashboard layout | No | Charts, widgets, analytics |
| `webform` | Public form | Yes/No | Lead capture, registration |

## 5. Hardcoded tenant constants (modern.suppa.me, tenant id 5)

Live-verified May 2026.

| Constant                    | Value                                              |
| --------------------------- | -------------------------------------------------- |
| Base URL                    | `https://modern.suppa.me`                          |
| Forms entity name           | `Forms`                                            |
| Forms entity id             | (varies per tenant — resolve via schema)           |
| Backend version             | `2.0` (all operations use v2 endpoints)            |

### Backend v2 API URL pattern

```
POST  /api/core/data/Forms/search     # list/filter forms
POST  /api/core/data/Forms/select     # get single form
POST  /api/core/data/Forms/insert     # create form
POST  /api/core/data/Forms/update     # update form (with conditions filter)
GET   /api/core/schema/{EntityName}   # get entity schema (fields/properties)
```

## 6. PowerShell JSON tips

For complex `--settings-json` arguments, write the JSON to a temp file:

```powershell
$json = @'
{"columnsNumber":2,"showSubmitButton":true,"validateOnSubmit":true,"xGap":"16px","yGap":"12px"}
'@
$json | Set-Content -Encoding UTF8 "$env:TEMP\settings.json"
python scripts/suppa_api.py update-form 1234 --settings-json (Get-Content "$env:TEMP\settings.json" -Raw)
```

For schema files, always use `--schema-file` pointing to a real `.json` file.

## 7. Form schema structure (quick reference)

A form is stored as:
```json
{
    "id": 1234,
    "name": "My Form",
    "type": "elementForm",
    "entity": { "id": 42 },
    "data": {
        "formShema": [ /* TField[] — array of field objects */ ],
        "formSettings": { /* IFormConfig */ },
        "formModul": "/* JS module code string */"
    }
}
```

Each field in `formShema` has at minimum:
```json
{
    "id": "uuid-string",
    "name": "fieldName",
    "type": "text",
    "label": { "en_US": "Field Label" },
    "position": { "lg": { "x": 1, "y": 1 } },
    "columns": { "lg": { "container": 1 } },
    "rows": { "lg": { "container": 1 } }
}
```

Full reference: see [references/api-endpoints.md](references/api-endpoints.md)
and [references/field-formats.md](references/field-formats.md).
