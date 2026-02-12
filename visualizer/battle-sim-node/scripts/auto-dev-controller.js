#!/usr/bin/env node
/**
 * AUTO DEV CONTROLLER - Headless Development Automation
 * 
 * Manages the entire development workflow automatically:
 * - Starts dev server
 * - Runs headless tests
 * - Executes simulations
 * - Monitors for changes
 * - Auto-rebuilds and deploys
 * - Generates reports
 */

import { spawn, exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

// ANSI colors
const C = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m'
};

function log(msg, color = 'reset') {
  console.log(`${C[color]}${msg}${C.reset}`);
}

function timestamp() {
  return new Date().toISOString().replace('T', ' ').slice(0, 19);
}

// State management
const state = {
  serverPid: null,
  testResults: [],
  simulationResults: [],
  lastBuild: null,
  errors: [],
  isRunning: true
};

// ============================================
// DEV SERVER MANAGEMENT
// ============================================

function startDevServer() {
  return new Promise((resolve) => {
    log(`[${timestamp()}] Starting dev server...`, 'cyan');
    
    const proc = spawn('npx', ['vite', '--host', '--port', '5173'], {
      cwd: ROOT,
      stdio: 'pipe',
      detached: false
    });
    
    state.serverPid = proc.pid;
    
    proc.stdout.on('data', (data) => {
      const output = data.toString();
      if (output.includes('ready') || output.includes('5173')) {
        log(`[${timestamp()}] ✅ Dev server ready at http://localhost:5173`, 'green');
        resolve(true);
      }
    });
    
    proc.stderr.on('data', (data) => {
      const output = data.toString();
      if (!output.includes('sourcemap') && !output.includes('favicon')) {
        log(`[${timestamp()}] Server error: ${output}`, 'red');
        state.errors.push({ type: 'server', message: output, time: timestamp() });
      }
    });
    
    proc.on('close', (code) => {
      if (code !== 0 && state.isRunning) {
        log(`[${timestamp()}] Server crashed, restarting...`, 'yellow');
        setTimeout(() => startDevServer(), 2000);
      }
    });
  });
}

function restartDevServer() {
  if (state.serverPid) {
    try {
      process.kill(state.serverPid, 'SIGTERM');
    } catch (e) {
      // Process already dead
    }
  }
  return startDevServer();
}

// ============================================
// HEADLESS TESTING
// ============================================

async function runHeadlessTests() {
  log(`[${timestamp()}] 🧪 Running headless tests...`, 'cyan');
  
  return new Promise((resolve) => {
    const startTime = Date.now();
    const proc = spawn('npx', ['playwright', 'test', '--reporter=line'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    let output = '';
    
    proc.stdout.on('data', (data) => {
      output += data.toString();
      process.stdout.write(data);
    });
    
    proc.stderr.on('data', (data) => {
      output += data.toString();
    });
    
    proc.on('close', (code) => {
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      const passed = code === 0;
      
      const result = {
        type: 'test',
        passed,
        duration: `${duration}s`,
        output,
        timestamp: timestamp()
      };
      
      state.testResults.push(result);
      
      if (passed) {
        log(`[${timestamp()}] ✅ Tests passed (${duration}s)`, 'green');
      } else {
        log(`[${timestamp()}] ❌ Tests failed (${duration}s)`, 'red');
        state.errors.push({ type: 'test', time: timestamp() });
      }
      
      resolve(result);
    });
  });
}

// ============================================
// AUTOMATED SIMULATIONS
// ============================================

async function runAutomatedSimulations(count = 10) {
  log(`[${timestamp()}] 🎮 Running ${count} automated simulations...`, 'cyan');
  
  // Create a simple Node script to run simulations
  const simScript = `
    import { SimulationManager } from './src/game/systems/SimulationManager.js';
    
    async function runSims(count) {
      const results = [];
      for (let i = 0; i < count; i++) {
        const sim = new SimulationManager({
          maxDuration: 300,
          maxWave: 15,
          speed: 100,
          useSmartAI: true,
          startWave: 1
        });
        
        try {
          const result = await sim.runSimulation();
          results.push(result);
          console.log(JSON.stringify({ type: 'progress', current: i + 1, total: count }));
        } catch (e) {
          console.log(JSON.stringify({ type: 'error', message: e.message }));
        }
      }
      return results;
    }
    
    runSims(${count}).then(results => {
      console.log(JSON.stringify({ type: 'complete', results }));
    });
  `;
  
  const simPath = path.join(ROOT, 'temp-sim-runner.mjs');
  fs.writeFileSync(simPath, simScript);
  
  return new Promise((resolve) => {
    const results = [];
    const proc = spawn('node', [simPath], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    proc.stdout.on('data', (data) => {
      const lines = data.toString().trim().split('\n');
      lines.forEach(line => {
        try {
          const msg = JSON.parse(line);
          if (msg.type === 'progress') {
            process.stdout.write(`\r[${msg.current}/${msg.total}] Simulations complete...`);
          } else if (msg.type === 'complete') {
            results.push(...msg.results);
          }
        } catch (e) {
          // Not JSON, ignore
        }
      });
    });
    
    proc.on('close', () => {
      fs.unlinkSync(simPath);
      console.log(''); // New line after progress
      
      const avgDuration = results.reduce((a, r) => a + r.duration, 0) / results.length;
      const avgWaves = results.reduce((a, r) => a + r.wavesCompleted, 0) / results.length;
      
      const summary = {
        type: 'simulation',
        count: results.length,
        avgDuration: avgDuration.toFixed(1),
        avgWaves: avgWaves.toFixed(1),
        results,
        timestamp: timestamp()
      };
      
      state.simulationResults.push(summary);
      
      log(`[${timestamp()}] ✅ Simulations complete: ${results.length} runs, avg ${avgWaves.toFixed(1)} waves`, 'green');
      resolve(summary);
    });
  });
}

// ============================================
// BUILD & DEPLOY
// ============================================

async function buildAndDeploy() {
  log(`[${timestamp()}] 📦 Building for production...`, 'cyan');
  
  return new Promise((resolve) => {
    const proc = spawn('npm', ['run', 'build'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    let output = '';
    
    proc.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    proc.stderr.on('data', (data) => {
      output += data.toString();
    });
    
    proc.on('close', (code) => {
      if (code === 0) {
        state.lastBuild = timestamp();
        log(`[${timestamp()}] ✅ Build successful`, 'green');
        
        // Auto-deploy if build succeeded
        deploy().then(resolve);
      } else {
        log(`[${timestamp()}] ❌ Build failed`, 'red');
        state.errors.push({ type: 'build', time: timestamp(), output });
        resolve(false);
      }
    });
  });
}

async function deploy() {
  log(`[${timestamp()}] 🚀 Deploying to production...`, 'cyan');
  
  return new Promise((resolve) => {
    const proc = spawn('./deploy.sh', ['--skip-build'], {
      cwd: ROOT,
      stdio: 'pipe'
    });
    
    proc.on('close', (code) => {
      if (code === 0 || code === null) {
        log(`[${timestamp()}] ✅ Deployed successfully`, 'green');
        resolve(true);
      } else {
        log(`[${timestamp()}] ⚠️ Deploy may have issues`, 'yellow');
        resolve(false);
      }
    });
  });
}

// ============================================
// MONITORING & REPORTING
// ============================================

function generateReport() {
  const reportPath = path.join(ROOT, 'reports', `report-${Date.now()}.json`);
  
  // Ensure reports dir exists
  if (!fs.existsSync(path.join(ROOT, 'reports'))) {
    fs.mkdirSync(path.join(ROOT, 'reports'));
  }
  
  const report = {
    timestamp: timestamp(),
    summary: {
      totalTests: state.testResults.length,
      testsPassed: state.testResults.filter(r => r.passed).length,
      totalSimulations: state.simulationResults.reduce((a, r) => a + (r.count || 0), 0),
      lastBuild: state.lastBuild,
      totalErrors: state.errors.length
    },
    testResults: state.testResults.slice(-10),
    simulationResults: state.simulationResults.slice(-5),
    errors: state.errors.slice(-20)
  };
  
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  // Also print summary
  log(`\n${'='.repeat(60)}`, 'gray');
  log('AUTOMATION REPORT', 'bright');
  log(`${'='.repeat(60)}`, 'gray');
  log(`Tests Run: ${report.summary.totalTests}`, report.summary.testsPassed === report.summary.totalTests ? 'green' : 'yellow');
  log(`Tests Passed: ${report.summary.testsPassed}/${report.summary.totalTests}`, report.summary.testsPassed === report.summary.totalTests ? 'green' : 'red');
  log(`Simulations: ${report.summary.totalSimulations}`, 'cyan');
  log(`Last Build: ${report.summary.lastBuild || 'N/A'}`, 'cyan');
  log(`Errors: ${report.summary.totalErrors}`, report.summary.totalErrors === 0 ? 'green' : 'red');
  log(`${'='.repeat(60)}\n`, 'gray');
  
  return report;
}

function watchFiles() {
  log(`[${timestamp()}] 👀 Watching for changes...`, 'gray');
  
  const srcPath = path.join(ROOT, 'src');
  
  fs.watch(srcPath, { recursive: true }, (eventType, filename) => {
    if (filename && filename.endsWith('.ts') || filename.endsWith('.tsx')) {
      log(`[${timestamp()}] 📝 File changed: ${filename}`, 'yellow');
      // Vite handles HMR automatically, but we can trigger tests
    }
  });
}

// ============================================
// MAIN CONTROL LOOP
// ============================================

async function runFullSuite() {
  log(`\n${'='.repeat(60)}`, 'cyan');
  log('RUNNING FULL AUTOMATED SUITE', 'bright');
  log(`${'='.repeat(60)}\n`, 'cyan');
  
  // 1. Run tests
  await runHeadlessTests();
  
  // 2. Run simulations (smaller batch for quick feedback)
  await runAutomatedSimulations(5);
  
  // 3. Generate report
  generateReport();
  
  log(`\n${'='.repeat(60)}`, 'green');
  log('FULL SUITE COMPLETE', 'green');
  log(`${'='.repeat(60)}\n`, 'green');
}

async function main() {
  const command = process.argv[2] || 'start';
  
  switch (command) {
    case 'start':
    case 'dev':
      log(`${C.bright}🤖 AUTO DEV CONTROLLER${C.reset}`, 'bright');
      log('Starting automated development environment...\n', 'gray');
      
      // Start dev server
      await startDevServer();
      
      // Run initial tests
      await runHeadlessTests();
      
      // Watch for changes
      watchFiles();
      
      // Periodic full suite (every 10 minutes)
      setInterval(() => {
        if (state.isRunning) {
          runFullSuite();
        }
      }, 10 * 60 * 1000);
      
      // Report generation (every 5 minutes)
      setInterval(() => {
        if (state.isRunning) {
          generateReport();
        }
      }, 5 * 60 * 1000);
      
      log(`\n${C.green}✅ Automation running!${C.reset}`, 'green');
      log(`${C.gray}Press Ctrl+C to stop${C.reset}\n`, 'gray');
      break;
      
    case 'test':
      await runHeadlessTests();
      break;
      
    case 'sim':
    case 'simulate':
      const count = parseInt(process.argv[3]) || 10;
      await runAutomatedSimulations(count);
      break;
      
    case 'build':
      await buildAndDeploy();
      break;
      
    case 'full':
    case 'suite':
      await runFullSuite();
      break;
      
    case 'report':
      generateReport();
      break;
      
    default:
      log('Usage: node auto-dev-controller.js [command]', 'yellow');
      log('Commands:', 'bright');
      log('  start, dev    - Start dev server with automation', 'gray');
      log('  test          - Run headless tests only', 'gray');
      log('  sim [count]   - Run N simulations', 'gray');
      log('  build         - Build and deploy', 'gray');
      log('  full, suite   - Run full test suite', 'gray');
      log('  report        - Generate status report', 'gray');
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  log(`\n[${timestamp()}] Shutting down...`, 'yellow');
  state.isRunning = false;
  if (state.serverPid) {
    try {
      process.kill(state.serverPid, 'SIGTERM');
    } catch (e) {}
  }
  generateReport();
  process.exit(0);
});

main().catch(err => {
  log(`[${timestamp()}] Fatal error: ${err.message}`, 'red');
  process.exit(1);
});
