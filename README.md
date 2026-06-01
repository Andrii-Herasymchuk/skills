# Suppa 2.0 MCP Server

This repository hosts the **Suppa 2.0 MCP Server** — a Model Context Protocol
server that gives AI agents secure tools to manage **Tasks, Docs/Pages,
Entities, and Forms** on the [Suppa platform](https://modern.suppa.me).

It replaces the previous standalone skills (suppa-tasks, suppa-docs,
suppa-entity, suppa-forms) with a single local server. Your API key stays on
your machine and is never exposed to the AI agent.

## Contents

- [`suppa2.0-mcp-server/`](suppa2.0-mcp-server/) — the server (50 tools)
  - [README](suppa2.0-mcp-server/README.md) — install, configuration, tool reference
  - [CONNECT.md](suppa2.0-mcp-server/CONNECT.md) — step‑by‑step plan to connect it
    to any agent (Claude Desktop, VS Code Copilot, Cursor, Windsurf) and use it
    for development

## Quick start

```bash
cd suppa2.0-mcp-server
pip install -e .
cp .env.example .env   # then add your SUPPA_API_KEY
python -m suppa_mcp
```

See [suppa2.0-mcp-server/CONNECT.md](suppa2.0-mcp-server/CONNECT.md) for the full
connection and usage guide.
