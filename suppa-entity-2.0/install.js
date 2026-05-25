#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');

const SKILL_NAME = 'suppa-entity';
const src = __dirname;
const dest = path.join(os.homedir(), '.copilot', 'skills', SKILL_NAME);

function copyDir(srcDir, destDir) {
  fs.mkdirSync(destDir, { recursive: true });
  for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
    const srcPath = path.join(srcDir, entry.name);
    const destPath = path.join(destDir, entry.name);
    if (['node_modules', 'package.json', 'package-lock.json', 'install.js', '.npmrc'].includes(entry.name)) continue;
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

copyDir(src, dest);
console.log(`\u2713 Skill "${SKILL_NAME}" installed to ${dest}`);
console.log('  Reload VS Code window to activate.');
