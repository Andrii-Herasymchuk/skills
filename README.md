# Suppa Skills

Agent skills for the [Suppa platform](https://modern.suppa.me). Works with GitHub Copilot, Claude Code, Cursor, Codex, and [50+ other agents](https://github.com/vercel-labs/skills#supported-agents).

## Available Skills

| Skill | Description |
|-------|-------------|
| `suppa-tasks` | Create, search, update, delete tasks; comments; workflows; stages |
| `suppa-entity` | Create entities, add fields, define enums, search records |
| `suppa-docs` | Manage documents, pages, and page blocks (content); write articles |

---

## Installation

```bash
npx skills add Andrii-Herasymchuk/skills
```

This will auto-detect your installed agents and install the skills to the correct locations.

### Options

```bash
# Install globally (available in all projects)
npx skills add Andrii-Herasymchuk/skills -g

# Install a specific skill only
npx skills add Andrii-Herasymchuk/skills --skill suppa-docs

# Install to specific agents
npx skills add Andrii-Herasymchuk/skills -a github-copilot -a claude-code

# Non-interactive
npx skills add Andrii-Herasymchuk/skills --all -y
```

### After installation

Set the required environment variable in your terminal:

```powershell
$env:SUPPA_API_KEY = "<your-suppa-token>"         # Required
$env:SUPPA_BASE_URL = "https://modern.suppa.me"   # Optional (default)
$env:PYTHONIOENCODING = "utf-8"                   # Recommended on Windows
```

Test by asking your agent: "list docs", "create page", or "get blocks"

---

## Repository structure

```
skills/
├── README.md
└── skills/
    ├── suppa-tasks/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── api-endpoints.md
    │   │   └── field-formats.md
    │   └── scripts/
    │       └── suppa_api.py
    ├── suppa-entity/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── api-endpoints.md
    │   │   └── field-formats.md
    │   └── scripts/
    │       └── suppa_api.py
    └── suppa-docs/
        ├── SKILL.md
        ├── references/
        │   ├── api-endpoints.md
        │   └── field-formats.md
        └── scripts/
            └── suppa_api.py
```
