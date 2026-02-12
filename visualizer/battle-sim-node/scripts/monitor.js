#!/usr/bin/env node
/**
 * MONITOR - Real-time development monitoring
 * 
 * Shows live stats about:
 * - Dev server status
 * - Test results
 * - Simulation progress
 * - File changes
 * - Error tracking
 */

import { spawn } from 'child_process';
import { readFileSync, existsSync, watch } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const C = {
  reset: '\x1b[0m',
  clear: '\x1B[2J\x1B[H',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
  white: '\x1b[37m',
  gray: '\x1b[90m'
};

let lastReport = null;
let serverStatus = 'checking...';
let lastTestResult = null;
let recentErrors = [];

function clear() {
  process.stdout.write(C.clear);
}

function box(title, content, color = 'cyan') {
  const width = 50;
  const line = '─'.repeat(width);
  console.log(`${C[color]}┌${line}┐${C.reset}`);
  console.log(`${C[color]}│${C.bright} ${title.padEnd(width - 1)}${C.reset}${C[color]}│${C.reset}`);
  console.log(`${C[color]}├${line}┤${C.reset}`);
  
  const lines = content.split('\n').slice(0, 10);
  lines.forEach(l => {
    const truncated = l.slice(0, width - 2).padEnd(width - 2);
    console.log(`${C[color]}│ ${C.reset}${truncated}${C[color]} │${C.reset}`);
  });
  
  console.log(`${C[color]}└${line}┘${C.reset}`);
}

function checkServer() {
  return new Promise((resolve) => {
    const req = spawn('curl', ['-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5173'], {
      stdio: 'pipe'
    });
    
    let code = '';
    req.stdout.on('data', (d) => code += d);
    req.on('close', () => {
      serverStatus = code === '200' ? `${C.green}● Online${C.reset}` : `${C.red}● Offline${C.reset}`;
      resolve(code === '200');
    });
  });
}

function loadLatestReport() {
  const reportsDir = join(ROOT, 'reports');
  if (!existsSync(reportsDir)) return null;
  
  try {
    const files = require('fs').readdirSync(reportsDir)
      .filter(f => f.startsWith('report-') && f.endsWith('.json'))
      .sort().reverse();
    
    if (files.length === 0) return null;
    
    return JSON.parse(readFileSync(join(reportsDir, files[0]), 'utf8'));
  } catch (e) {
    return null;
  }
}

async function render() {
  clear();
  
  console.log(`${C.bright}${C.cyan}`);
  console.log('  ╔══════════════════════════════════════════════════════════════╗');
  console.log('  ║           🎮 DARWIN\'S ISLAND - DEV MONITOR 🎮               ║');
  console.log('  ╚══════════════════════════════════════════════════════════════╝');
  console.log(`${C.reset}`);
  
  await checkServer();
  
  const report = loadLatestReport();
  
  // Server Status
  console.log(`\n${C.bright}SERVER STATUS${C.reset}`);
  console.log(`  Dev Server: ${serverStatus}`);
  console.log(`  Monitor:    ${C.green}● Running${C.reset}`);
  
  // Quick Stats
  if (report) {
    console.log(`\n${C.bright}QUICK STATS${C.reset}`);
    console.log(`  Tests Passed: ${report.summary.testsPassed}/${report.summary.totalTests} ${report.summary.testsPassed === report.summary.totalTests ? C.green + '✓' : C.yellow + '⚠'}${C.reset}`);
    console.log(`  Simulations:  ${report.summary.totalSimulations}`);
    console.log(`  Last Build:   ${report.summary.lastBuild || 'N/A'}`);
    console.log(`  Errors:       ${report.summary.totalErrors} ${report.summary.totalErrors === 0 ? C.green + '✓' : C.red + '✗'}${C.reset}`);
  }
  
  // Recent Test Results
  if (report && report.testResults.length > 0) {
    console.log(`\n${C.bright}RECENT TESTS${C.reset}`);
    report.testResults.slice(-5).forEach((test, i) => {
      const status = test.passed ? `${C.green}✓ PASS` : `${C.red}✗ FAIL`;
      console.log(`  ${i + 1}. ${status}${C.reset} ${test.timestamp} (${test.duration})`);
    });
  }
  
  // Recent Simulations
  if (report && report.simulationResults.length > 0) {
    console.log(`\n${C.bright}RECENT SIMULATIONS${C.reset}`);
    report.simulationResults.slice(-3).forEach((sim, i) => {
      console.log(`  ${i + 1}. ${C.cyan}${sim.count} runs${C.reset} - Avg ${sim.avgWaves} waves - ${sim.timestamp}`);
    });
  }
  
  // Recent Errors
  if (report && report.errors.length > 0) {
    console.log(`\n${C.bright}${C.red}RECENT ERRORS${C.reset}`);
    report.errors.slice(-3).forEach((err, i) => {
      console.log(`  ${i + 1}. [${err.type}] ${err.time}`);
    });
  }
  
  // Controls
  console.log(`\n${C.dim}${'─'.repeat(60)}${C.reset}`);
  console.log(`${C.gray}Controls: [r] Run tests  [s] Run sims  [b] Build  [q] Quit${C.reset}`);
  
  lastReport = report;
}

function runCommand(cmd) {
  console.log(`\n${C.yellow}Running: ${cmd}...${C.reset}`);
  const proc = spawn('npm', ['run', cmd], {
    cwd: ROOT,
    stdio: 'inherit'
  });
  proc.on('close', () => {
    console.log(`\n${C.gray}Press any key to continue...${C.reset}`);
  });
}

// Initial render
render();

// Auto-refresh every 5 seconds
setInterval(render, 5000);

// Keyboard controls
process.stdin.setRawMode(true);
process.stdin.resume();
process.stdin.on('data', (key) => {
  const k = key.toString();
  
  if (k === 'q' || k === '\u0003') { // q or Ctrl+C
    console.log(`\n${C.yellow}Goodbye!${C.reset}`);
    process.exit(0);
  } else if (k === 'r') {
    runCommand('test:headless');
  } else if (k === 's') {
    runCommand('sim:batch');
  } else if (k === 'b') {
    runCommand('build');
  }
});

// Watch for report changes
const reportsDir = join(ROOT, 'reports');
if (existsSync(reportsDir)) {
  watch(reportsDir, () => {
    render();
  });
}
