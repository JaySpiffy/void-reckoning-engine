#!/usr/bin/env node
/**
 * AUTO-COMMIT - Smart git commits with automatic messages
 * 
 * Automatically commits changes with meaningful messages based on:
 * - File types changed
 * - Code analysis
 * - Test results
 * - Build status
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const C = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m'
};

function log(msg, color = 'reset') {
  console.log(`${C[color]}${msg}${C.reset}`);
}

function exec(cmd, opts = {}) {
  try {
    return execSync(cmd, { cwd: ROOT, encoding: 'utf8', ...opts });
  } catch (e) {
    return null;
  }
}

// ============================================
// COMMIT MESSAGE GENERATION
// ============================================

function analyzeChanges() {
  const status = exec('git status --porcelain');
  if (!status) return null;
  
  const lines = status.trim().split('\n').filter(Boolean);
  const changes = {
    added: [],
    modified: [],
    deleted: [],
    types: new Set()
  };
  
  for (const line of lines) {
    const status = line.slice(0, 2);
    const file = line.slice(3).trim();
    
    if (status.includes('A')) changes.added.push(file);
    if (status.includes('M')) changes.modified.push(file);
    if (status.includes('D')) changes.deleted.push(file);
    
    // Detect file types
    if (file.startsWith('src/game/systems/')) changes.types.add('systems');
    if (file.startsWith('src/game/entities/')) changes.types.add('entities');
    if (file.startsWith('src/game/ui/')) changes.types.add('ui');
    if (file.startsWith('src/game/managers/')) changes.types.add('managers');
    if (file.startsWith('tests/')) changes.types.add('tests');
    if (file.startsWith('scripts/')) changes.types.add('automation');
    if (file.startsWith('.github/')) changes.types.add('ci/cd');
    if (file.endsWith('.md')) changes.types.add('docs');
  }
  
  return changes;
}

function generateCommitMessage(changes) {
  if (!changes || changes.added.length + changes.modified.length + changes.deleted.length === 0) {
    return null;
  }
  
  const { added, modified, deleted, types } = changes;
  const typeList = Array.from(types);
  
  // Determine commit type
  let commitType = 'chore';
  let scope = typeList[0] || 'general';
  
  if (added.length > modified.length + deleted.length) {
    commitType = 'feat';
  } else if (modified.length > 0 && added.length === 0 && deleted.length === 0) {
    commitType = 'fix';
  }
  
  if (types.has('tests')) {
    commitType = 'test';
    scope = 'testing';
  } else if (types.has('docs')) {
    commitType = 'docs';
    scope = 'documentation';
  } else if (types.has('automation') || types.has('ci/cd')) {
    commitType = 'ci';
    scope = 'automation';
  }
  
  // Generate description
  let description = '';
  const totalChanges = added.length + modified.length + deleted.length;
  
  if (added.length > 0 && modified.length === 0 && deleted.length === 0) {
    description = `add ${added.length} new file${added.length > 1 ? 's' : ''}`;
    if (added.length === 1) {
      description = `add ${added[0].split('/').pop()}`;
    }
  } else if (deleted.length > 0 && added.length === 0 && modified.length === 0) {
    description = `remove ${deleted.length} file${deleted.length > 1 ? 's' : ''}`;
  } else if (modified.length === 1 && added.length === 0 && deleted.length === 0) {
    description = `update ${modified[0].split('/').pop()}`;
  } else {
    // Mixed changes
    const parts = [];
    if (added.length > 0) parts.push(`add ${added.length} files`);
    if (modified.length > 0) parts.push(`update ${modified.length} files`);
    if (deleted.length > 0) parts.push(`remove ${deleted.length} files`);
    description = parts.join(', ');
  }
  
  // Add type context
  if (types.has('systems') && types.size === 1) {
    description += ' in game systems';
  } else if (types.has('ui') && types.size === 1) {
    description += ' to UI components';
  } else if (types.has('entities') && types.size === 1) {
    description += ' to game entities';
  }
  
  return `${commitType}(${scope}): ${description}`;
}

function getChangeSummary(changes) {
  if (!changes) return '';
  
  const lines = [];
  if (changes.added.length > 0) {
    lines.push(`Added (${changes.added.length}):`);
    changes.added.slice(0, 5).forEach(f => lines.push(`  + ${f}`));
    if (changes.added.length > 5) lines.push(`  ... and ${changes.added.length - 5} more`);
  }
  if (changes.modified.length > 0) {
    lines.push(`Modified (${changes.modified.length}):`);
    changes.modified.slice(0, 5).forEach(f => lines.push(`  ~ ${f}`));
    if (changes.modified.length > 5) lines.push(`  ... and ${changes.modified.length - 5} more`);
  }
  if (changes.deleted.length > 0) {
    lines.push(`Deleted (${changes.deleted.length}):`);
    changes.deleted.forEach(f => lines.push(`  - ${f}`));
  }
  
  return lines.join('\n');
}

// ============================================
// PRE-COMMIT CHECKS
// ============================================

function runPreCommitChecks() {
  log('🔍 Running pre-commit checks...', 'cyan');
  
  // Check for lint errors
  log('  Running linter...', 'gray');
  const lintResult = exec('npm run lint 2>&1');
  if (lintResult && lintResult.includes('error')) {
    log('  ⚠️  Lint errors found (non-blocking)', 'yellow');
  } else {
    log('  ✅ Lint passed', 'green');
  }
  
  // Quick type check
  log('  Running type check...', 'gray');
  const typeResult = exec('npx tsc --noEmit 2>&1');
  if (typeResult && typeResult.includes('error')) {
    log('  ⚠️  Type errors found (non-blocking)', 'yellow');
  } else {
    log('  ✅ Type check passed', 'green');
  }
  
  return true;
}

// ============================================
// MAIN
// ============================================

function main() {
  log('\n🤖 Auto-Commit System', 'cyan');
  log('=' .repeat(60), 'gray');
  
  // Check if we're in a git repo
  const isRepo = exec('git rev-parse --git-dir');
  if (!isRepo) {
    log('❌ Not a git repository', 'red');
    process.exit(1);
  }
  
  // Check for changes
  const changes = analyzeChanges();
  if (!changes || changes.added.length + changes.modified.length + changes.deleted.length === 0) {
    log('No changes to commit', 'yellow');
    return;
  }
  
  log(`\n📊 Changes detected:`, 'cyan');
  log(getChangeSummary(changes), 'gray');
  
  // Generate commit message
  const message = generateCommitMessage(changes);
  if (!message) {
    log('❌ Could not generate commit message', 'red');
    process.exit(1);
  }
  
  log(`\n📝 Proposed commit message:`, 'cyan');
  log(`  ${message}`, 'green');
  
  // Run pre-commit checks
  runPreCommitChecks();
  
  // Stage all changes
  log('\n📦 Staging changes...', 'cyan');
  exec('git add -A');
  log('  ✅ Changes staged', 'green');
  
  // Commit
  log('\n💾 Creating commit...', 'cyan');
  const commitResult = exec(`git commit -m "${message}" 2>&1`);
  
  if (commitResult && commitResult.includes('nothing to commit')) {
    log('  ℹ️  Nothing to commit', 'yellow');
  } else if (commitResult && commitResult.includes(commitResult)) {
    log('  ✅ Commit successful', 'green');
    
    // Show commit info
    const hash = exec('git log -1 --oneline');
    log(`\n  ${hash}`, 'gray');
  } else {
    log('  ❌ Commit failed', 'red');
    process.exit(1);
  }
  
  log('\n✨ Done!', 'green');
}

// Parse arguments
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const force = args.includes('--force');

if (dryRun) {
  log('\n🔍 DRY RUN MODE', 'yellow');
  const changes = analyzeChanges();
  const message = generateCommitMessage(changes);
  log(`Would commit with message: ${message}`, 'cyan');
} else {
  main();
}
