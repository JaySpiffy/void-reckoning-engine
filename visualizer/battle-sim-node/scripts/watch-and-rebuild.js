#!/usr/bin/env node
/**
 * WATCH AND REBUILD - File watcher with smart rebuilds
 * 
 * Watches src/ for changes and:
 * - Runs quick tests on TS/TSX changes
 * - Rebuilds if tests pass
 * - Reports errors without stopping
 */

import { watch } from 'fs';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { debounce } from './utils.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const C = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m'
};

let isBuilding = false;
let pendingBuild = false;

function log(msg, color = 'reset') {
  console.log(`${C[color]}[${new Date().toLocaleTimeString()}] ${msg}${C.reset}`);
}

async function runQuickTests() {
  return new Promise((resolve) => {
    const proc = spawn('npx', ['playwright', 'test', '--grep', '@quick', '--reporter=dot'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    proc.on('close', (code) => {
      resolve(code === 0);
    });
  });
}

async function runBuild() {
  if (isBuilding) {
    pendingBuild = true;
    return;
  }
  
  isBuilding = true;
  log('Running quick validation...', 'cyan');
  
  // Quick lint check
  const lintProc = spawn('npm', ['run', 'lint'], {
    cwd: ROOT,
    stdio: 'pipe'
  });
  
  const lintSuccess = await new Promise((resolve) => {
    lintProc.on('close', (code) => resolve(code === 0));
  });
  
  if (!lintSuccess) {
    log('❌ Lint failed, fix errors before building', 'red');
    isBuilding = false;
    return;
  }
  
  log('✓ Lint passed, building...', 'green');
  
  const buildProc = spawn('npm', ['run', 'build'], {
    cwd: ROOT,
    stdio: 'pipe'
  });
  
  let output = '';
  buildProc.stdout.on('data', (d) => output += d);
  buildProc.stderr.on('data', (d) => output += d);
  
  const buildSuccess = await new Promise((resolve) => {
    buildProc.on('close', (code) => resolve(code === 0));
  });
  
  if (buildSuccess) {
    log('✓ Build successful!', 'green');
  } else {
    log('❌ Build failed', 'red');
    console.log(output.slice(-500)); // Show last 500 chars
  }
  
  isBuilding = false;
  
  if (pendingBuild) {
    pendingBuild = false;
    runBuild();
  }
}

const debouncedBuild = debounce(runBuild, 1000);

// Watch src directory
log('👀 Watching src/ for changes...', 'cyan');
log('Press Ctrl+C to stop', 'gray');

watch(join(ROOT, 'src'), { recursive: true }, (eventType, filename) => {
  if (!filename) return;
  
  // Only watch TS/TSX files
  if (!filename.match(/\.(ts|tsx)$/)) return;
  
  log(`📝 ${filename} changed`, 'yellow');
  debouncedBuild();
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  log('\n👋 Stopping watcher', 'gray');
  process.exit(0);
});
