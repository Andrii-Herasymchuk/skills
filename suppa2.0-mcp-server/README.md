# Suppa 2.0 MCP Server

MCP (Model Context Protocol) server for the [Suppa platform](https://modern.suppa.me) — provides AI agents with tools to manage Tasks, Docs/Pages, Entities, and Forms.

## Why MCP?

- **API key stays local** — never sent to the AI agent, stored only in `.env`
- **Works with any MCP client** — Claude Desktop, VS Code Copilot, Cursor, Windsurf, etc.
- **No CORS/proxy issues** — runs locally, makes direct HTTPS calls to Suppa
- **40+ tools** covering Tasks, Documents, Entity schema, and Forms

## Quick Start

### 1. Install

From a local clone:

```bash
cd suppa2.0-mcp-server
pip install -e .
```

Or straight from the repository:

```bash
pip install "git+https://git.modern-expo.com/asu/me-development/skills.git#subdirectory=suppa2.0-mcp-server"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your SUPPA_API_KEY
```

### 3. Connect to your AI agent

**Claude Desktop** — edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "suppa": {
      "command": "python",
      "args": ["-m", "suppa_mcp"],
      "cwd": "C:/path/to/suppa2.0-mcp-server",
      "env": {
        "SUPPA_API_KEY": "your-token-here",
        "SUPPA_BASE_URL": "https://modern.suppa.me"
      }
    }
  }
}
```

**VS Code Copilot** — create `.vscode/mcp.json` in your workspace:
```json
{
  "servers": {
    "suppa": {
      "command": "python",
      "args": ["-m", "suppa_mcp"],
      "cwd": "${workspaceFolder}/suppa2.0-mcp-server",
      "env": {
        "SUPPA_API_KEY": "your-token-here"
      }
    }
  }
}
```

**Cursor** — Settings → MCP Servers → Add:
```json
{
  "suppa": {
    "command": "python",
    "args": ["-m", "suppa_mcp"],
    "env": { "SUPPA_API_KEY": "your-token-here" }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPPA_API_KEY` | (required) | JWT token or API key |
| `SUPPA_BASE_URL` | `https://modern.suppa.me` | Platform URL |
| `SUPPA_LANG` | `en` | Language (`en`/`uk`) |
| `SUPPA_TZ` | `Europe/Kyiv` | Timezone |
| `SUPPA_TASKS_ENTITY_ID` | `37` | Entity ID for file uploads |

## Available Tools (43 total)

### Tasks (16 tools)
| Tool | Description |
|------|-------------|
| `suppa_get_me` | Current user profile |
| `suppa_search_tasks` | Search with filters (my, active, overdue, etc.) |
| `suppa_count_tasks` | Count matching tasks |
| `suppa_get_task` | Full task details |
| `suppa_create_task` | Create task |
| `suppa_update_task` | Update task fields |
| `suppa_delete_task` | Soft-delete task |
| `suppa_move_task` | Move to another stage |
| `suppa_close_task` | Close (completed stage) |
| `suppa_add_comment` | Comment with @mentions |
| `suppa_get_comments` | List task comments |
| `suppa_attach_file` | Upload & attach file |
| `suppa_list_workflows` | Available workflows |
| `suppa_list_stages` | Stages in a workflow |
| `suppa_list_task_types` | Task type options |
| `suppa_search_users` | Find users by name |

### Docs & Pages (13 tools)
| Tool | Description |
|------|-------------|
| `suppa_list_docs` | List documents |
| `suppa_get_doc` | Document with page tree |
| `suppa_create_doc` | Create document |
| `suppa_update_doc` | Update document |
| `suppa_delete_doc` | Delete document |
| `suppa_list_pages` | Pages in a document |
| `suppa_get_page` | Page metadata |
| `suppa_create_page` | Create page |
| `suppa_update_page` | Update page |
| `suppa_delete_page` | Delete page |
| `suppa_get_blocks` | Raw block data |
| `suppa_read_page` | Readable text output |
| `suppa_create_blocks` | Add blocks to page |
| `suppa_insert_block` | Insert at position |
| `suppa_update_block` | Edit block content |
| `suppa_delete_block` | Remove block |
| `suppa_reorder_blocks` | Reorder blocks |

### Entity & Schema (8 tools)
| Tool | Description |
|------|-------------|
| `suppa_list_entities` | All entities/tables |
| `suppa_describe_entity` | Full schema |
| `suppa_search_records` | Query any entity |
| `suppa_create_entity` | Create new table |
| `suppa_add_field` | Add field to entity |
| `suppa_add_enum_values` | Add enum options |
| `suppa_list_field_types` | Available types |
| `suppa_create_record` | Insert record |
| `suppa_update_record` | Update record |
| `suppa_delete_record` | Delete record |

### Forms (6 tools)
| Tool | Description |
|------|-------------|
| `suppa_list_forms` | List forms |
| `suppa_get_form` | Form with schema |
| `suppa_create_form` | Create form |
| `suppa_update_form` | Update form |
| `suppa_generate_form_schema` | Auto-generate from entity |
| `suppa_add_field_to_form` | Add field to form |
| `suppa_list_form_field_types` | Field type catalog |

## Authentication

The server authenticates with a single bearer token supplied via `SUPPA_API_KEY`:

- **User JWT** (account token, e.g. copied from the browser cookie `accessToken`) —
  full access to all domains including Tasks and the `$current-user` magic value.
- **Integrator API key** — works for Docs, Entities, Forms and Users. Task
  endpoints and `$current-user` may return empty results because they are scoped
  to a real user. Use a user JWT for Task workflows.

The token is read only from the environment, sent solely in the `Authorization`
header to `SUPPA_BASE_URL`, and is **never** exposed to the AI agent.

## Development

```bash
# Run directly
python -m suppa_mcp

# Test with MCP inspector
mcp dev src/suppa_mcp/server.py
```
