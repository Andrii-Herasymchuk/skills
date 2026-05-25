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

Configure the GitLab npm registry (one-time):

```bash
npm set @suppa-skills:registry=https://git.modern-expo.com/api/v4/projects/204/packages/npm/
npm set //git.modern-expo.com/api/v4/projects/204/packages/npm/:_authToken=<YOUR_GITLAB_TOKEN>
```

Then install the skills:

```bash
npx @suppa-skills/suppa-tasks
npx @suppa-skills/suppa-entity
```

This copies the skill files into `~/.copilot/skills/` automatically.

### Option 2: Manual copy (user-level, all workspaces)

Clone this repo and copy skill folders into your global Copilot skills directory:

```powershell
# Windows
git clone https://git.modern-expo.com/asu/me-development/skills.git
Copy-Item -Recurse .\skills\suppa-tasks-2.0 "$env:USERPROFILE\.copilot\skills\suppa-tasks"
Copy-Item -Recurse .\skills\suppa-entity-2.0 "$env:USERPROFILE\.copilot\skills\suppa-entity"
```

```bash
# macOS / Linux
git clone https://git.modern-expo.com/asu/me-development/skills.git
cp -r ./skills/suppa-tasks-2.0 ~/.copilot/skills/suppa-tasks
cp -r ./skills/suppa-entity-2.0 ~/.copilot/skills/suppa-entity
```

### Option 3: Workspace-level (one project only)

Copy into your project's `.copilot/skills/` directory:

```powershell
Copy-Item -Recurse path\to\suppa-tasks-2.0 .\.copilot\skills\suppa-tasks
Copy-Item -Recurse path\to\suppa-entity-2.0 .\.copilot\skills\suppa-entity
```

### After installation

1. Reload VS Code window (`Ctrl+Shift+P` → "Reload Window")
2. Set the required environment variables in your terminal:

```powershell
$env:SUPPA_API_KEY = "<your-suppa-token>"         # Required
$env:SUPPA_BASE_URL = "https://modern.suppa.me"   # Optional (default)
$env:PYTHONIOENCODING = "utf-8"                   # Recommended on Windows
```

3. Test by asking Copilot: "мої задачі" or "list all entities"

---

## Publishing (for maintainers)

### Prerequisites

- Node.js installed
- GitLab Personal Access Token with `api` scope

### Setup registry auth (one-time)

```bash
npm set @suppa-skills:registry=https://git.modern-expo.com/api/v4/projects/204/packages/npm/
npm set //git.modern-expo.com/api/v4/projects/204/packages/npm/:_authToken=<YOUR_GITLAB_TOKEN>
```

### Publish a skill

```bash
cd suppa-tasks-2.0
npm publish

cd ../suppa-entity-2.0
npm publish
```

### Skill package structure

Each skill folder contains:

```
suppa-tasks-2.0/
├── SKILL.md              # Copilot skill entry point (YAML frontmatter + instructions)
├── package.json          # npm package metadata (@suppa-skills/suppa-tasks)
├── install.js            # CLI script — copies skill to ~/.copilot/skills/
├── references/
│   ├── api-endpoints.md
│   └── field-formats.md
└── scripts/
    └── suppa_api.py      # Python API client (no external dependencies)
```

### Bumping version

Edit `package.json` → increment `version`, then `npm publish`.

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
