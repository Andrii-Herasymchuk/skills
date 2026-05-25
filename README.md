# Suppa Skills

Copilot custom skills for the [Suppa platform](https://modern.suppa.me). Each skill gives GitHub Copilot (in VS Code) the ability to interact with Suppa APIs — managing tasks, entities, fields, and more — via natural language.

## Available Skills

| Skill | Package | Description |
|-------|---------|-------------|
| `suppa-tasks` | `@suppa-skills/suppa-tasks` | Create, search, update, delete tasks; comments; workflows; stages |
| `suppa-entity` | `@suppa-skills/suppa-entity` | Create entities, add fields, define enums, search records |

---

## Installation

### Option 1: Install via npx (recommended)

```bash
npx @suppa-skills/suppa-tasks
npx @suppa-skills/suppa-entity
```

This downloads the skill from npm and copies it into `~/.copilot/skills/` automatically. No tokens or registry config needed.

### Option 2: Clone and copy manually

```powershell
# Windows
git clone https://github.com/Andrii-Herasymchuk/skills.git
Copy-Item -Recurse .\skills\suppa-tasks-2.0 "$env:USERPROFILE\.copilot\skills\suppa-tasks"
Copy-Item -Recurse .\skills\suppa-entity-2.0 "$env:USERPROFILE\.copilot\skills\suppa-entity"
```

```bash
# macOS / Linux
git clone https://github.com/Andrii-Herasymchuk/skills.git
cp -r ./skills/suppa-tasks-2.0 ~/.copilot/skills/suppa-tasks
cp -r ./skills/suppa-entity-2.0 ~/.copilot/skills/suppa-entity
```

### After installation

1. Reload VS Code window (`Ctrl+Shift+P` → "Reload Window")
2. Set the required environment variable in your terminal:

```powershell
$env:SUPPA_API_KEY = "<your-suppa-token>"         # Required
$env:SUPPA_BASE_URL = "https://modern.suppa.me"   # Optional (default)
$env:PYTHONIOENCODING = "utf-8"                   # Recommended on Windows
```

3. Test by asking Copilot: "мої задачі" or "list all entities"

---

## Publishing (for maintainers)

### Publish to npm

```bash
npm login
cd suppa-tasks-2.0 && npm publish
cd ../suppa-entity-2.0 && npm publish
```

### Bump version

Edit `version` in `package.json`, then run `npm publish` again.

---

## Repository structure

```
skills/
├── README.md
├── suppa-tasks-2.0/
│   ├── SKILL.md
│   ├── package.json
│   ├── install.js
│   ├── references/
│   │   ├── api-endpoints.md
│   │   └── field-formats.md
│   └── scripts/
│       └── suppa_api.py
└── suppa-entity-2.0/
    ├── SKILL.md
    ├── package.json
    ├── install.js
    ├── references/
    │   ├── api-endpoints.md
    │   └── field-formats.md
    └── scripts/
        └── suppa_api.py
```
