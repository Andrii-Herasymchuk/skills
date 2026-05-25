---
name: suppa-tasks
description: Manage Tasks, Comments, Users, Workflows, and Stages on the Suppa platform (modern.suppa.me) via direct HTTP API calls. Use this skill whenever the user wants to create/search/update/delete tasks, comment on a task, find "my tasks", attach a file, list workflows/stages/users, or run task-related queries. Trigger phrases (English) — "search task", "create task", "update task", "delete task", "close task", "add comment", "my tasks", "active tasks", "attach file", "list workflows", "list stages", "list task types", "search user"; (Ukrainian / Українська) — "задача", "задачі", "таск", "таски", "мої задачі", "мої таски", "активні задачі", "створити задачу", "створи таск", "редагувати задачу", "оновити задачу", "видалити задачу", "закрити задачу", "перенести задачу", "коментар", "коментар до задачі", "додати коментар", "вкласти файл", "прикріпити файл", "знайди задачу", "знайти задачу", "знайти користувача", "користувачі", "робочий процес", "воркфлоу", "стадії", "етапи", "типи задач"; (transliteration) — "zadacha", "tasky", "moi tasky", "komentar". Works via plain HTTP — no MCP server required.
---

# Suppa Tasks (modern.suppa.me)

Direct HTTP client for the Suppa Tasks module REST API. All commands
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

| If the user wants to…                                | Use this command |
| ---------------------------------------------------- | ---------------- |
| Find their own / active / overdue / due-today tasks  | `search-tasks --my [--active] [--overdue] [--due today]` |
| Search tasks by title substring                      | `search-tasks --search "..."` |
| Count tasks matching a filter                        | `count-tasks ...` (NEVER use `search-tasks` + length) |
| Read one task in full                                | `get-task ID` |
| Create / edit / move / close / delete a task         | `create-task` / `update-task ID` / `move-task ID --stage S` / `close-task ID` / `delete-task ID` |
| Comment on a task or read its comments               | `add-comment` / `get-comments --task ID` |
| Attach a file                                        | `attach-file --task ID --file PATH` |
| List workflows, stages, task types, users            | `list-workflows`, `list-stages --workflow W`, `list-task-types`, `search-users` |
| Probe per-tenant constants (workflows, types, etc.)  | `discover` |

### 0.3 Hard rules

- **Always** use the script's CLI commands. Don't reinvent the body via `raw`
  if a wrapper already exists — the wrappers handle filter normalization,
  required keys (`searchValue`, `orderBy`, `limit`, `offset`), and
  paging-with-aggregates quirks.
- **Never** embed JSON inside `python -c "..."` on Windows PowerShell — the
  shell mangles quotes. Either use the skill's CLI flags, or write the JSON to
  a temp file and pipe it (`Get-Content q.json -Raw | python scripts/suppa_api.py raw ...`).
- **Never** chain shell commands with `&&` on Windows PowerShell. Use `;` or
  separate invocations.
- **Always** verify writes. After `create-task`/`update-task` run a read-back
  (`get-task`) to confirm the change.

### 0.4 Error-code cheat-sheet

| Status                     | Meaning                                              | Agent action |
| -------------------------- | ---------------------------------------------------- | ------------ |
| `401 Unauthorized`         | Token missing/expired                                | Ask user for fresh JWT or API key |
| `404 Not Found` on `/data/Tasks/...` | Tasks module not installed on this tenant | Tell user the Tasks app is not available on this tenant |
| `400 Bad Request` mentioning `current transaction is aborted` (`25P02`) | Transient Postgres pool state | Wait briefly, retry the SAME command |
| `403 Forbidden` on Tasks ops with an integrator API key | API keys can't read Tasks | Ask user for a real user JWT (cookie `accessToken`) |
| `[]` returned from `search-tasks` with an API key       | Same root cause as above | Same fix |

### 0.5 Authentication requirement

Tasks operations **require a real user JWT** (not an integrator API key).
Integrator API keys are limited to Users, Files, TasksComments,
TasksApproves, TasksFavorites — they return `[]` on Tasks searches.

The magic value `"$current-user"` only resolves with real user JWTs.

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
| `SUPPA_TASKS_ENTITY_ID`  | `37`                          | Numeric entityId of Tasks (file upload)  |

> **User JWT vs integrator API key.** Operations against Tasks / Projects /
> Workflows and the magic value `"$current-user"` require a **real user JWT**.

## 2. Commands — quick reference

```
python scripts/suppa_api.py <command> [options]
```

### Tasks & comments
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `get-me`           | Current authenticated user                               |
| `search-tasks`     | Search tasks (filters: `--my`, `--active`, `--search` …) |
| `count-tasks`      | Count tasks matching filters                             |
| `get-task ID`      | Get one task by integer id                               |
| `create-task`      | Create a task                                            |
| `update-task ID`   | Update fields on an existing task                        |
| `delete-task ID`   | Soft-delete (remove) a task                              |
| `move-task ID`     | Move task to another stage (`--stage`)                   |
| `close-task ID`    | Move task to its workflow's closed stage                 |
| `add-comment`      | Add comment to a task (`--task`, `--content`, `--mention`) |
| `get-comments`     | List comments for a task                                 |
| `attach-file`      | Upload a file as attachment to a task                    |

### Metadata
| Command            | Purpose                                                  |
| ------------------ | -------------------------------------------------------- |
| `list-workflows`   | List workflows (StageWorkflows entity, grouped)          |
| `list-stages`      | List stages of a workflow (`--workflow ID`)              |
| `list-task-types`  | List allowed TasksTypes                                  |
| `search-users`     | Find users by name / id                                  |
| `discover`         | Probe API for per-tenant constants                       |

## 3. Common recipes

### My active tasks

```powershell
python scripts/suppa_api.py search-tasks --my --active --limit 20
```

`--active` filters `stage.status.value IN ("active","inprogress")`.

### Find a task by title substring

```powershell
python scripts/suppa_api.py search-tasks --search "linkedin" --limit 10
```

### Get full task detail / create / update / move / close / delete

```powershell
python scripts/suppa_api.py get-task    806528
python scripts/suppa_api.py create-task --title "Review PR" --description "<p>Take a look.</p>" --assigned-to 9295 --deadline "+2d"
python scripts/suppa_api.py update-task 806528 --title "New title" --priority 7469
python scripts/suppa_api.py move-task   806528 --stage 503
python scripts/suppa_api.py close-task  806528
python scripts/suppa_api.py delete-task 806528
```

`--deadline` accepts `today`, `tomorrow`, `+3d`, `+2h`, or any ISO datetime.

> `close-task` requires the task to belong to a workflow that has a stage with
> `status.value = "completed"`. Tasks created without `--workflow` cannot be
> closed via this command — set a workflow first via `update-task`.

### Comment on a task

```powershell
python scripts/suppa_api.py add-comment --task 806528 --content "Looks good, merging."
```

Plain text is auto-wrapped in `<p>...</p>`. To pass raw HTML (with formatting),
start the string with `<`.

### @mention a user in a comment

```powershell
python scripts/suppa_api.py add-comment --task 806528 `
  --content "please review" `
  --mention "9295:Andrii Herasymchuk"
```

### Attach a file to a task

```powershell
python scripts/suppa_api.py attach-file --task 806528 --file .\report.pdf
```

### List workflows / stages / users

```powershell
python scripts/suppa_api.py list-workflows --name "IT"
python scripts/suppa_api.py list-stages    --workflow 2299
python scripts/suppa_api.py search-users   --name "Andrii"
```

## 4. Filter & field shapes (one-liner)

- **Filter**: `{"field":"stage.status.value","value":["active","inprogress"],"comparator":"in"}`
- **`in` over a relation**: value is `[{"id":N},{"id":N}]`; over a string column it's raw strings.
- **`like`**: value MUST use SQL wildcards `%substring%` (the script auto-wraps bare strings).
- **Field projection**: nested booleans, e.g. `{"id":true,"assignedTo":{"id":true,"fullName":true}}`.
- **orderBy**: `[{"field":"createdAt","order":"desc"}]` — pass `[]` for count/aggregate queries.
- **Required on every search body**: `searchValue` (string, `""` OK), `orderBy`, `limit`, `offset`.
- **Response**: bare JSON array (NOT wrapped in `{data:[...]}`).
- **Magic value**: `"$current-user"` resolves to the caller's user id (real-user JWTs only).
- **IDs are integers** (not UUIDs).
- **Dates are ISO-8601 strings** (not unix ms).
- **Stage status values (live-verified, 5 only)**: `active`, `inprogress`, `completed`, `cancelled`, `deferred`.

## 5. Hardcoded tenant constants (modern.suppa.me, tenant id 5)

Live-verified May 2026. Override via env vars or CLI flags when porting to
another tenant.

| Constant                    | Value                                              |
| --------------------------- | -------------------------------------------------- |
| Base URL                    | `https://modern.suppa.me`                          |
| Tenant id / schema          | `5` / `vexxqynv`                                   |
| Tasks entity id (file upl.) | `37`                                               |
| Stage status — OPEN set     | `["active","inprogress"]`                          |
| Stage status — CLOSED set   | `["completed","cancelled"]`                        |
| TasksTypes (id → title)     | 2=Task, 3=Epic, 4=Deal, 5=Service, 6=Risk, 7=Story, 8=Theme, 9=Initiative, 10=Folder, 11=Project, 12=Sales Request, 13=Development Task, 14=Documentation, 15=Bug, 16=Design Task, 17=Suggestion, 18=Defect, 19=Subtask, 20=Access Request |
| Priority entity             | NOT `TasksPriorities` (404). Priorities live in the generic `Enums` table; read on Tasks via the `priority` relation (sample row: `{id:7469, name:"Tasks.priority", value:"normal"}`) |

Re-discover for another tenant: `python scripts/suppa_api.py discover`.

## 6. PowerShell JSON tips

For complex `--filter-json` / `--body` arguments, write the JSON to a temp file
to dodge PowerShell quoting headaches:

```powershell
$json = @'
{"conditions":{"operator":"and","filters":[{"field":"assignedTo","value":"$current-user","comparator":"="}]},"fields":{"id":true,"title":true},"limit":10,"offset":0,"orderBy":[{"field":"createdAt","order":"desc"}],"searchValue":"","getAccessByFields":true,"includeDeletedRelations":false}
'@
$json | Set-Content -Encoding UTF8 "$env:TEMP\q.json"
Get-Content "$env:TEMP\q.json" -Raw | python scripts/suppa_api.py raw Tasks
```

## 7. Known Task fields (subset, from `GET /api/core/schema/Tasks`)

Scalar text/numeric:
`title`, `htmlDescription`, `plainDescription`, `resultText`, `shortID`,
`shortUID`, `sourceKey`, `externalId`, `externalIdInt`, `externalIdStr`,
`externalIdUuid`, `bonusConfirmed`, `bonusCount`, `confidence`, `ease`,
`effort`, `iceScore`, `impact`, `reach`, `riceScore`, `estimatedDuration`,
`plannedDuration`, `spentTime`, `spentTimeTotal`, `closedAt`, `deadline`,
`reviewDate`, `nextReviewDate`, `plannedStartDate`, `plannedEndDate`,
`plannedInWorkTime`, `planningModeStartAt`, `planningModeEnabled`,
`isPlanningReminderOn`, `restrictChildDates`, `useChildrenEstimate`,
`completeWhenSubtasksDone`, `needResult`.

Relations (write as `{id:N}`, filter via dotted path):
`assignedTo` → Users, `author` → Users, `closedBy` → Users, `editors` → Users[],
`watchers` → Users[], `createdBy` → Users, `removedBy` → Users,
`project` → Projects, `parent` → Tasks, `parents` → Tasks[], `rootTask` → Tasks,
`children` → Tasks[], `multiChildren` → Tasks[],
`type` → TasksTypes, `priority` → Enums,
`workflow` → StageWorkflows, `stage` → StageWorkflows rows with non-null `status`,
`tags` → Tags[], `opportunities` → Opportunities[],
`attachments` → Files[], `comments` → TasksComments[],
`approves` → TasksApproves[], `checklists` → Checklists[],
`favorites` → TasksFavorites[], `projectMatrix` → ProjectMatrix,
`timeTracking` → TimeTracking[].

Full reference: see [references/api-endpoints.md](references/api-endpoints.md)
and [references/field-formats.md](references/field-formats.md).
