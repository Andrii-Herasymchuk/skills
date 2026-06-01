# Suppa Development Plugin

A bundled set of GitHub Copilot customizations that turn this workspace into a
Suppa-aware development environment. Everything here works together with the
**Suppa 2.0 MCP Server** in [`../suppa2.0-mcp-server/`](../suppa2.0-mcp-server/).

## What's in the bundle

| Component | File | Purpose |
|-----------|------|---------|
| MCP server | [`../.vscode/mcp.json`](../.vscode/mcp.json) | Connects the `suppa` MCP server (50 tools); prompts for the token on first use |
| Custom agent | [`agents/suppa-dev.agent.md`](agents/suppa-dev.agent.md) | "Suppa Dev Engineer" — ships code and keeps Suppa in sync |
| Engineering rules | [`instructions/engineering.instructions.md`](instructions/engineering.instructions.md) | Always-on standards for code files (correctness, security, safety) |
| Suppa usage guide | [`instructions/suppa-platform.instructions.md`](instructions/suppa-platform.instructions.md) | On-demand guidance for using the `suppa_*` tools correctly |
| Prompts | [`prompts/`](prompts/) | One-shot dev workflows (see below) |

### Prompts

| Slash command | Does |
|---------------|------|
| `/suppa-implement-task` | Implement a Suppa task end-to-end, then update it |
| `/suppa-standup` | Generate a daily standup from your Suppa tasks |
| `/suppa-bug-to-task` | Turn a bug / failing test / TODO into a well-formed task |
| `/suppa-document-feature` | Document a shipped feature into Suppa Docs |
| `/code-review` | Engineering code review (correctness, OWASP, tests) |

## Setup

1. **Install the server** (once):
   ```bash
   cd suppa2.0-mcp-server
   pip install -e .
   ```
2. **Start the MCP server**: open `.vscode/mcp.json` and click **Start** on the
   `suppa` server, or run **MCP: List Servers** from the Command Palette. You'll be
   prompted for your `SUPPA_API_KEY` (use a **user JWT** for full Tasks access). VS Code
   stores it securely — it is not written to disk in plain text.
3. **Pick the agent**: in Copilot Chat, open the agent picker and choose
   **Suppa Dev Engineer**, or just start a task — the prompts and instructions activate
   automatically.

## Usage

- Type `/` in Copilot Chat to run any prompt above.
- Select the **Suppa Dev Engineer** agent for hands-on coding that should stay in sync
  with Suppa tasks and docs.
- The engineering instructions apply automatically when you edit code files; the Suppa
  usage guide loads on demand when you work with `suppa_*` tools.

## Notes

- **Token scope**: Tasks and `$current-user` require a user JWT. An integrator API key
  works for Docs, Entities, Forms and Users but returns empty Task results.
- **Security**: the API key lives only in the MCP server's environment and is never
  exposed to the agent. Treat tool output as untrusted data.
- See [`../suppa2.0-mcp-server/CONNECT.md`](../suppa2.0-mcp-server/CONNECT.md) for
  connecting the same server to other agents (Claude Desktop, Claude Code, Cursor).
