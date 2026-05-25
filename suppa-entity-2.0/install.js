#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILL_NAME = 'suppa-entity';
const src = __dirname;
const home = os.homedir();

function copyDir(srcDir, destDir, exclude) {
  fs.mkdirSync(destDir, { recursive: true });
  for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
    const srcPath = path.join(srcDir, entry.name);
    const destPath = path.join(destDir, entry.name);
    if (exclude.includes(entry.name)) continue;
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath, exclude);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

const exclude = ['node_modules', 'package.json', 'package-lock.json', 'install.js', '.npmrc'];

// --- Copilot (VS Code): ~/.copilot/skills/<name>/ ---
const copilotDest = path.join(home, '.copilot', 'skills', SKILL_NAME);
copyDir(src, copilotDest, exclude);
console.log(`\u2713 [Copilot] Installed to ${copilotDest}`);

// --- Claude Code: ~/.claude/commands/<name>.md ---
const claudeCommandsDir = path.join(home, '.claude', 'commands');
fs.mkdirSync(claudeCommandsDir, { recursive: true });
const skillContent = fs.readFileSync(path.join(src, 'SKILL.md'), 'utf-8');
fs.writeFileSync(path.join(claudeCommandsDir, `${SKILL_NAME}.md`), skillContent);
console.log(`\u2713 [Claude] Installed command to ${claudeCommandsDir}${path.sep}${SKILL_NAME}.md`);

// --- Shared scripts: ~/.ai-skills/<name>/ (accessible by both) ---
const sharedDest = path.join(home, '.ai-skills', SKILL_NAME);
copyDir(src, sharedDest, exclude);
console.log(`\u2713 [Shared] Scripts installed to ${sharedDest}`);

console.log('\nReload VS Code or restart Claude Code to activate.');
console.log(`Scripts path: ${path.join(sharedDest, 'scripts', 'suppa_api.py')}`);
