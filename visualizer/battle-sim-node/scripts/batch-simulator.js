#!/usr/bin/env node
/**
 * BATCH SIMULATOR - Overnight/Extended Testing
 * 
 * Runs hundreds of simulations headless and exports results.
 * Usage: node batch-simulator.js [count] [--export=csv|json]
 */

import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// Parse arguments
const args = process.argv.slice(2);
const SIM_COUNT = parseInt(args.find(a => !a.startsWith('--')) || '100');
const EXPORT_FORMAT = args.find(a => a.startsWith('--export='))?.split('=')[1] || 'json';
const OUTPUT_DIR = join(ROOT, 'simulation-results');

// Ensure output directory exists
if (!existsSync(OUTPUT_DIR)) {
  mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Colors
const C = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m',
  red: '\x1b[31m'
};

function log(msg, color = 'reset') {
  console.log(`${C[color]}${msg}${C.reset}`);
}

function timestamp() {
  return new Date().toISOString().replace('T', ' ').slice(0, 19);
}

// Import the simulation manager (we'll run it in Node context)
async function runBatchSimulations() {
  log(`\n${'='.repeat(70)}`, 'cyan');
  log(`BATCH SIMULATOR - ${SIM_COUNT} Runs`, 'bright');
  log(`${'='.repeat(70)}\n`, 'cyan');
  
  const startTime = Date.now();
  const results = [];
  let completed = 0;
  let failed = 0;
  
  // Simulation configs to test different scenarios
  const configs = [
    { name: 'Standard', maxDuration: 300, maxWave: 15, speed: 100, useSmartAI: true, startWave: 1 },
    { name: 'Survival', maxDuration: 600, maxWave: 50, speed: 100, useSmartAI: true, startWave: 1 },
    { name: 'Quick', maxDuration: 120, maxWave: 10, speed: 100, useSmartAI: true, startWave: 1 },
    { name: 'NoAI', maxDuration: 300, maxWave: 15, speed: 100, useSmartAI: false, startWave: 1 },
  ];
  
  log(`Running ${SIM_COUNT} simulations across ${configs.length} configurations...\n`, 'cyan');
  
  // We'll create a headless browser script to run the simulations
  const playwright = await import('playwright');
  
  const browser = await playwright.chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  // Load the game
  log(`Loading game...`, 'gray');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  
  // Wait for game to initialize
  await page.waitForTimeout(3000);
  
  // Run simulations
  for (let i = 0; i < SIM_COUNT; i++) {
    const config = configs[i % configs.length];
    const simId = `sim-${Date.now()}-${i}`;
    
    try {
      // Start simulation via console
      const result = await page.evaluate(async (simConfig) => {
        // Access the simulation manager from the window
        const manager = window.simulationManager;
        if (!manager) {
          throw new Error('SimulationManager not found on window');
        }
        
        const result = await manager.start({
          maxDuration: simConfig.maxDuration,
          maxWave: simConfig.maxWave,
          speed: simConfig.speed,
          useSmartAI: simConfig.useSmartAI,
          startWave: simConfig.startWave
        });
        
        return {
          ...result,
          configName: simConfig.name
        };
      }, config);
      
      results.push({
        id: simId,
        config: config.name,
        ...result,
        timestamp: new Date().toISOString()
      });
      
      completed++;
      
    } catch (error) {
      failed++;
      results.push({
        id: simId,
        config: config.name,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
    
    // Progress bar
    const progress = ((i + 1) / SIM_COUNT * 100).toFixed(1);
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
    const rate = completed / ((Date.now() - startTime) / 60000);
    const eta = ((SIM_COUNT - (i + 1)) / rate).toFixed(1);
    
    process.stdout.write(
      `\r${C.cyan}[${progress}%] ${i + 1}/${SIM_COUNT} | ` +
      `${C.green}✓${completed}${C.reset} | ` +
      `${C.red}✗${failed}${C.reset} | ` +
      `${C.gray}${elapsed}s elapsed | ~${eta}m remaining${C.reset}    `
    );
    
    // Small delay between simulations
    await page.waitForTimeout(100);
  }
  
  await browser.close();
  
  const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log('\n');
  
  // Generate reports
  await generateReports(results, totalTime);
  
  log(`\n✅ Batch complete: ${completed} succeeded, ${failed} failed in ${totalTime}s`, 'green');
}

async function generateReports(results, totalTime) {
  const timestamp = Date.now();
  const dateStr = new Date().toISOString().slice(0, 10);
  
  // JSON export
  if (EXPORT_FORMAT === 'json' || EXPORT_FORMAT === 'all') {
    const jsonPath = join(OUTPUT_DIR, `batch-${dateStr}-${timestamp}.json`);
    writeFileSync(jsonPath, JSON.stringify({
      meta: {
        timestamp: new Date().toISOString(),
        count: results.length,
        totalTime,
        exportFormat: 'json'
      },
      results
    }, null, 2));
    log(`📄 JSON report: ${jsonPath}`, 'gray');
  }
  
  // CSV export
  if (EXPORT_FORMAT === 'csv' || EXPORT_FORMAT === 'all') {
    const csvPath = join(OUTPUT_DIR, `batch-${dateStr}-${timestamp}.csv`);
    const headers = [
      'id', 'config', 'timestamp', 'duration', 'wavesCompleted', 
      'enemiesKilled', 'score', 'survived', 'finalHealth', 'error'
    ];
    
    const csvRows = results.map(r => [
      r.id,
      r.config,
      r.timestamp,
      r.duration || '',
      r.wavesCompleted || '',
      r.enemiesKilled || '',
      r.score || '',
      r.survived || '',
      r.finalHealth || '',
      r.error || ''
    ].map(v => `"${v}"`).join(','));
    
    const csvContent = [headers.join(','), ...csvRows].join('\n');
    writeFileSync(csvPath, csvContent);
    log(`📊 CSV report: ${csvPath}`, 'gray');
  }
  
  // Summary report
  const summary = calculateSummary(results);
  const summaryPath = join(OUTPUT_DIR, `summary-${dateStr}-${timestamp}.json`);
  writeFileSync(summaryPath, JSON.stringify({
    meta: {
      timestamp: new Date().toISOString(),
      count: results.length,
      totalTime
    },
    summary
  }, null, 2));
  
  // Print summary
  log(`\n${'='.repeat(50)}`, 'cyan');
  log('SUMMARY', 'bright');
  log(`${'='.repeat(50)}`, 'cyan');
  log(`Total Runs: ${summary.total}`, 'cyan');
  log(`Success Rate: ${(summary.successRate * 100).toFixed(1)}%`, summary.successRate > 0.8 ? 'green' : 'yellow');
  log(`Avg Waves: ${summary.avgWaves.toFixed(1)}`, 'cyan');
  log(`Avg Score: ${summary.avgScore.toFixed(0)}`, 'cyan');
  log(`Best Run: ${summary.bestScore} points`, 'green');
  log(`${'='.repeat(50)}\n`, 'cyan');
}

function calculateSummary(results) {
  const successful = results.filter(r => !r.error);
  const failed = results.filter(r => r.error);
  
  if (successful.length === 0) {
    return { total: results.length, successRate: 0, avgWaves: 0, avgScore: 0, bestScore: 0 };
  }
  
  const avgWaves = successful.reduce((a, r) => a + (r.wavesCompleted || 0), 0) / successful.length;
  const avgScore = successful.reduce((a, r) => a + (r.score || 0), 0) / successful.length;
  const bestScore = Math.max(...successful.map(r => r.score || 0));
  
  return {
    total: results.length,
    successRate: successful.length / results.length,
    avgWaves,
    avgScore,
    bestScore,
    byConfig: successful.reduce((acc, r) => {
      if (!acc[r.config]) acc[r.config] = { count: 0, avgWaves: 0, avgScore: 0 };
      acc[r.config].count++;
      return acc;
    }, {})
  };
}

// Run
runBatchSimulations().catch(err => {
  log(`Error: ${err.message}`, 'red');
  process.exit(1);
});
