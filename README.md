# Suppa Skills

Copilot custom skills for the [Suppa platform](https://modern.suppa.me). Each skill gives GitHub Copilot (in VS Code) the ability to interact with Suppa APIs — managing tasks, entities, fields, and more — via natural language.

## Available Skills

| Skill | Folder | Description |
|-------|--------|-------------|
| `suppa-tasks` | `suppa-tasks-2.0/` | Create, search, update, delete tasks; comments; workflows; stages |
| `suppa-entity` | `suppa-entity-2.0/` | Create entities, add fields, define enums, search records |

---

## Connecting Skills in VS Code

### Option 1: User-level installation (available in all workspaces)

Copy (or symlink) the skill folder into your global Copilot skills directory:

```powershell
# Windows
Copy-Item -Recurse .\suppa-tasks-2.0 "$env:USERPROFILE\.copilot\skills\suppa-tasks"
Copy-Item -Recurse .\suppa-entity-2.0 "$env:USERPROFILE\.copilot\skills\suppa-entity"

# Or create symlinks (run as Admin)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.copilot\skills\suppa-tasks" -Target "D:\skills\suppa-tasks-2.0"
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.copilot\skills\suppa-entity" -Target "D:\skills\suppa-entity-2.0"
```

```bash
# macOS / Linux
cp -r ./suppa-tasks-2.0 ~/.copilot/skills/suppa-tasks
cp -r ./suppa-entity-2.0 ~/.copilot/skills/suppa-entity

# Or symlinks
ln -s "$(pwd)/suppa-tasks-2.0" ~/.copilot/skills/suppa-tasks
ln -s "$(pwd)/suppa-entity-2.0" ~/.copilot/skills/suppa-entity
```

### Option 2: Workspace-level installation (available only in one project)

Copy the skill folder into your project's `.copilot/skills/` directory:

```powershell
# From your project root
Copy-Item -Recurse D:\skills\suppa-tasks-2.0 .\.copilot\skills\suppa-tasks
Copy-Item -Recurse D:\skills\suppa-entity-2.0 .\.copilot\skills\suppa-entity
```

### Option 3: Install via npx

First, configure the registry (one-time):

```bash
npm set @suppa-skills:registry=https://git.modern-expo.com/api/v4/projects/204/packages/npm/
npm set //git.modern-expo.com/api/v4/projects/204/packages/npm/:_authToken=<YOUR_GITLAB_TOKEN>
```

Then install skills:

```bash
npx @suppa-skills/suppa-tasks
npx @suppa-skills/suppa-entity
```

### Verify installation

After installing, restart VS Code (or reload the window). The skills will appear in Copilot's skill list. Test by asking Copilot:

> "Show my active tasks in Suppa"

or

> "List all entities on the tenant"

### Required environment variables

Before using the skills, set these in your terminal:

```powershell
$env:SUPPA_API_KEY = "<your-token>"          # Required
$env:SUPPA_BASE_URL = "https://modern.suppa.me"  # Optional, this is the default
$env:PYTHONIOENCODING = "utf-8"              # Recommended on Windows
```

---

## Publishing Skills (so others can install via `npx`)

### Skill folder structure

Each skill must follow this layout:

```
suppa-tasks/
├── SKILL.md              # Entry point — YAML frontmatter + instructions
├── package.json          # npm package metadata + bin entry
├── install.js            # CLI script that copies skill to ~/.copilot/skills/
├── references/
│   ├── api-endpoints.md
│   └── field-formats.md
└── scripts/
    └── suppa_api.py
```

### Step 1: Add `package.json` to each skill

Create a `package.json` in the skill folder:

```json
{
  "name": "@modern-expo/suppa-tasks",
  "version": "2.0.0",
  "description": "Copilot skill for Suppa Tasks management",
  "bin": {
    "suppa-tasks": "./install.js"
  },
  "files": [
    "SKILL.md",
    "install.js",
    "references/**",
    "scripts/**"
  ],
  "keywords": ["copilot", "skill", "suppa", "tasks"],
  "repository": {
    "type": "git",
    "url": "https://git.modern-expo.com/asu/me-development/skills.git"
  },
  "license": "UNLICENSED"
}
```

### Step 2: Create `install.js` (the CLI entry point)

```js
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILL_NAME = 'suppa-tasks'; // change per skill
const src = __dirname;
const dest = path.join(os.homedir(), '.copilot', 'skills', SKILL_NAME);

// Create target directory
fs.mkdirSync(dest, { recursive: true });

// Copy all skill files
function copyDir(srcDir, destDir) {
  fs.mkdirSync(destDir, { recursive: true });
  for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
    const srcPath = path.join(srcDir, entry.name);
    const destPath = path.join(destDir, entry.name);
    if (entry.name === 'node_modules' || entry.name === 'package.json' || entry.name === 'install.js') continue;
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

copyDir(src, dest);
console.log(`✓ Skill "${SKILL_NAME}" installed to ${dest}`);
console.log('  Reload VS Code to activate.');
```

### Step 3: Publish to GitLab npm registry

#### Configure `.npmrc` in the skill folder

```ini
@modern-expo:registry=https://git.modern-expo.com/api/v4/projects/<PROJECT_ID>/packages/npm/
//git.modern-expo.com/api/v4/projects/<PROJECT_ID>/packages/npm/:_authToken=${GITLAB_TOKEN}
```

#### Publish

```bash
# Authenticate (one-time)
export GITLAB_TOKEN="<your-gitlab-personal-access-token>"

# From the skill folder
cd suppa-tasks-2.0
npm publish
```

### Step 4: Users install via npx

Once published, anyone with registry access can install:

```bash
# Install to ~/.copilot/skills/ (one-time)
npx @modern-expo/suppa-tasks

# Or with explicit registry
npx --registry=https://git.modern-expo.com/api/v4/projects/<PROJECT_ID>/packages/npm/ @modern-expo/suppa-tasks
```

---

## Alternative: Universal `skill` CLI tool

If you want a single `npx skill install <repo>` command that works with any skill repo, create a separate package (e.g. `@modern-expo/skill`):

```json
{
  "name": "@modern-expo/skill",
  "version": "1.0.0",
  "bin": { "skill": "./cli.js" }
}
```

The CLI (`cli.js`) would:
1. Accept a GitLab repo URL + skill name
2. Clone/download the skill folder to a temp dir
3. Copy it into `~/.copilot/skills/<skill-name>/`

```js
#!/usr/bin/env node
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const [,, command, repoUrl, ...args] = process.argv;

if (command === 'install') {
  const skillFlag = args.indexOf('--skill');
  const skillName = skillFlag !== -1 ? args[skillFlag + 1] : null;

  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-'));
  execSync(`git clone --depth 1 "${repoUrl}" "${tmp}"`, { stdio: 'inherit' });

  const folders = skillName
    ? [fs.readdirSync(tmp).find(f => f.includes(skillName))]
    : fs.readdirSync(tmp).filter(f => fs.existsSync(path.join(tmp, f, 'SKILL.md')));

  for (const folder of folders) {
    const name = folder.replace(/-[\d.]+$/, ''); // strip version suffix
    const dest = path.join(os.homedir(), '.copilot', 'skills', name);
    fs.cpSync(path.join(tmp, folder), dest, { recursive: true });
    console.log(`✓ Installed "${name}" → ${dest}`);
  }

  fs.rmSync(tmp, { recursive: true });
  console.log('Reload VS Code to activate.');
} else {
  console.log('Usage: skill install <git-repo-url> [--skill <name>]');
}
```

After publishing this CLI package:

```bash
npx @modern-expo/skill install https://git.modern-expo.com/asu/me-development/skills.git --skill suppa-tasks
```

---

## Repository structure

```
skills/
├── README.md
├── suppa-tasks-2.0/
│   ├── SKILL.md
│   ├── references/
│   │   ├── api-endpoints.md
│   │   └── field-formats.md
│   └── scripts/
│       └── suppa_api.py
└── suppa-entity-2.0/
    ├── SKILL.md
    ├── references/
    │   ├── api-endpoints.md
    │   └── field-formats.md
    └── scripts/
        └── suppa_api.py
```
