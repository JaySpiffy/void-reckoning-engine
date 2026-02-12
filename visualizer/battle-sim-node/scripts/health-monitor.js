#!/usr/bin/env node
/**
 * HEALTH MONITOR - Continuous health checks with auto-repair
 * 
 * Monitors:
 * - Dev server status
 * - Build health
 * - Test status
 * - Disk space
 * - Dependencies
 * 
 * Auto-repairs common issues
 */

import { spawn, exec } from 'child_process';
import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

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

function log(msg, color = 'reset') {
  console.log(`${C[color]}[${new Date().toLocaleTimeString()}] ${msg}${C.reset}`);
}

// Health check results
const health = {
  server: { status: 'unknown', lastCheck: null },
  build: { status: 'unknown', lastSuccess: null },
  tests: { status: 'unknown', lastRun: null },
  dependencies: { status: 'unknown', outdated: [] },
  disk: { status: 'unknown', free: 0 },
  autoFixes: []
};

// ============================================
// HEALTH CHECKS
// ============================================

async function checkDevServer() {
  return new Promise((resolve) => {
    const req = spawn('curl', ['-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:5173'], {
      stdio: 'pipe'
    });
    
    let code = '';
    req.stdout.on('data', d => code += d);
    req.on('close', () => {
      const isHealthy = code === '200';
      health.server = {
        status: isHealthy ? 'healthy' : 'down',
        lastCheck: Date.now()
      };
      resolve(isHealthy);
    });
  });
}

async function autoRestartServer() {
  log('🔄 Auto-restarting dev server...', 'yellow');
  
  // Kill existing
  exec('pkill -f vite 2>/dev/null || true');
  await new Promise(r => setTimeout(r, 2000));
  
  // Start new
  const proc = spawn('npm', ['run', 'dev:quick'], {
    cwd: ROOT,
    detached: true,
    stdio: 'ignore'
  });
  proc.unref();
  
  // Wait for startup
  await new Promise(r => setTimeout(r, 5000));
  
  const isUp = await checkDevServer();
  if (isUp) {
    health.autoFixes.push({ type: 'server-restart', time: Date.now() });
    log('✅ Server restarted successfully', 'green');
  } else {
    log('❌ Server restart failed', 'red');
  }
}

async function checkBuild() {
  return new Promise((resolve) => {
    const proc = spawn('npm', ['run', 'build'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    proc.on('close', (code) => {
      const isHealthy = code === 0;
      health.build = {
        status: isHealthy ? 'healthy' : 'broken',
        lastSuccess: isHealthy ? Date.now() : health.build.lastSuccess
      };
      resolve(isHealthy);
    });
  });
}

async function checkDiskSpace() {
  return new Promise((resolve) => {
    exec('df -k . | tail -1 | awk \'{print $4}\'', (err, stdout) => {
      if (err) {
        health.disk = { status: 'unknown', free: 0 };
        resolve(false);
        return;
      }
      
      const freeKB = parseInt(stdout.trim(), 10);
      const freeMB = freeKB / 1024;
      const isHealthy = freeMB > 500; // At least 500MB free
      
      health.disk = {
        status: isHealthy ? 'healthy' : 'low',
        free: Math.round(freeMB)
      };
      resolve(isHealthy);
    });
  });
}

async function cleanupOldFiles() {
  log('🧹 Cleaning up old files...', 'yellow');
  
  // Clean old reports
  exec('find reports -name "*.json" -mtime +7 -delete 2>/dev/null || true');
  
  // Clean old simulation results
  exec('find simulation-results -name "batch-*.json" -mtime +14 -delete 2>/dev/null || true');
  
  // Clean node_modules/.cache
  exec('rm -rf node_modules/.cache 2>/dev/null || true');
  
  health.autoFixes.push({ type: 'cleanup', time: Date.now() });
  log('✅ Cleanup complete', 'green');
}

async function checkDependencies() {
  return new Promise((resolve) => {
    exec('npm outdated --json 2>/dev/null || echo "{}"', (err, stdout) => {
      try {
        const outdated = JSON.parse(stdout);
        const packages = Object.keys(outdated);
        
        health.dependencies = {
          status: packages.length === 0 ? 'healthy' : 'outdated',
          outdated: packages
        };
        
        resolve(packages.length === 0);
      } catch (e) {
        health.dependencies = { status: 'unknown', outdated: [] };
        resolve(false);
      }
    });
  });
}

async function runQuickTests() {
  return new Promise((resolve) => {
    const proc = spawn('npx', ['playwright', 'test', '--grep', '@smoke', '--reporter=line'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    proc.on('close', (code) => {
      health.tests = {
        status: code === 0 ? 'passing' : 'failing',
        lastRun: Date.now()
      };
      resolve(code === 0);
    });
  });
}

// ============================================
// HEALTH DASHBOARD
// ============================================

function renderDashboard() {
  const statusIcon = (status) => {
    if (status === 'healthy' || status === 'passing') return C.green + '✓' + C.reset;
    if (status === 'down' || status === 'broken' || status === 'failing') return C.red + '✗' + C.reset;
    if (status === 'low' || status === 'outdated') return C.yellow + '⚠' + C.reset;
    return C.gray + '?' + C.reset;
  };
  
  console.clear();
  console.log(`${C.cyan}╔══════════════════════════════════════════════════════════╗${C.reset}`);
  console.log(`${C.cyan}║${C.reset}              🏥 HEALTH MONITOR DASHBOARD                 ${C.cyan}║${C.reset}`);
  console.log(`${C.cyan}╚══════════════════════════════════════════════════════════╝${C.reset}`);
  console.log('');
  
  console.log(`${C.bright}System Health:${C.reset}`);
  console.log(`  ${statusIcon(health.server.status)} Dev Server: ${health.server.status}`);
  console.log(`  ${statusIcon(health.build.status)} Build: ${health.build.status}`);
  console.log(`  ${statusIcon(health.tests.status)} Tests: ${health.tests.status}`);
  console.log(`  ${statusIcon(health.disk.status)} Disk: ${health.disk.free}MB free`);
  console.log(`  ${statusIcon(health.dependencies.status)} Dependencies: ${health.dependencies.outdated.length} outdated`);
  
  if (health.autoFixes.length > 0) {
    console.log(`\n${C.yellow}Recent Auto-Fixes:${C.reset}`);
    health.autoFixes.slice(-5).forEach(fix => {
      const time = new Date(fix.time).toLocaleTimeString();
      console.log(`  • ${fix.type} at ${time}`);
    });
  }
  
  console.log(`\n${C.gray}Press Ctrl+C to exit${C.reset}`);
}

async function saveHealthReport() {
  const reportPath = join(ROOT, 'reports', `health-${Date.now()}.json`);
  
  if (!existsSync(join(ROOT, 'reports'))) {
    mkdirSync(join(ROOT, 'reports'));
  }
  
  writeFileSync(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    health
  }, null, 2));
}

// ============================================
// MAIN LOOP
// ============================================

async function healthCheck() {
  // Server check
  const serverHealthy = await checkDevServer();
  if (!serverHealthy) {
    await autoRestartServer();
  }
  
  // Build check (every 10 minutes)
  if (!health.build.lastSuccess || Date.now() - health.build.lastSuccess > 10 * 60 * 1000) {
    const buildHealthy = await checkBuild();
    if (!buildHealthy) {
      log('⚠️ Build is broken - run self-heal to attempt fixes', 'yellow');
    }
  }
  
  // Disk check
  const diskHealthy = await checkDiskSpace();
  if (!diskHealthy) {
    await cleanupOldFiles();
  }
  
  // Dependency check (every hour)
  if (!health.dependencies.lastCheck || Date.now() - health.dependencies.lastCheck > 60 * 60 * 1000) {
    await checkDependencies();
  }
  
  // Test check
  await runQuickTests();
  
  // Update dashboard
  renderDashboard();
  
  // Save report
  await saveHealthReport();
}

async function main() {
  log('🏥 Health Monitor Starting...', 'cyan');
  
  // Initial check
  await healthCheck();
  
  // Schedule regular checks
  setInterval(healthCheck, 30 * 1000); // Every 30 seconds
  
  log('Monitoring active. Press Ctrl+C to exit.', 'gray');
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  log('\n👋 Health monitor stopping', 'gray');
  process.exit(0);
});

main().catch(err => {
  log(`Error: ${err.message}`, 'red');
  process.exit(1);
});
