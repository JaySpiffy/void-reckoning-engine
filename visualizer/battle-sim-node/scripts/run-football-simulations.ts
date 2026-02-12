#!/usr/bin/env tsx
// ===== FOOTBALL BATCH SIMULATION RUNNER =====
// Run 1000s of simulations and export results for analysis

import { SimulationAPI, type BatchSimulationResult, type DetailedPlayResult } from '../src/football/systems/SimulationAPI';
import { ALL_PLAYS, PASS_PLAYS, RUN_PLAYS } from '../src/football/data/Playbook';
import * as fs from 'fs';
import * as path from 'path';

// ===== CONFIGURATION =====

interface RunnerConfig {
  iterations: number;
  playsToTest: 'all' | 'pass' | 'run' | string[];
  outputDir: string;
  verbose: boolean;
}

const DEFAULT_CONFIG: RunnerConfig = {
  iterations: 100,
  playsToTest: 'all',
  outputDir: './simulation-results',
  verbose: true,
};

// ===== MAIN RUNNER =====

class BatchRunner {
  private api: SimulationAPI;
  private config: RunnerConfig;
  
  constructor(config: Partial<RunnerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.api = new SimulationAPI({
      speed: 'instant',
      captureFrames: false, // Don't capture frames for batch runs (save memory)
      trackPlayerPaths: false,
      trackMatchups: true,
      trackStatistics: true,
    });
  }
  
  async run(): Promise<void> {
    console.log('🏈 Football Batch Simulation Runner');
    console.log('=====================================\n');
    
    const startTime = Date.now();
    
    // Select plays to test
    const plays = this.selectPlays();
    console.log(`Running ${this.config.iterations} iterations per play`);
    console.log(`Testing ${plays.length} plays: ${plays.map(p => p.name).join(', ')}\n`);
    
    // Run simulations
    const results: DetailedPlayResult[] = [];
    
    for (let i = 0; i < plays.length; i++) {
      const play = plays[i];
      console.log(`[${i + 1}/${plays.length}] Testing "${play.name}"...`);
      
      for (let iter = 0; iter < this.config.iterations; iter++) {
        try {
          const result = this.api.runPlay(play);
          results.push(result);
          
          if (this.config.verbose && iter % 20 === 0) {
            process.stdout.write('.');
          }
        } catch (error) {
          console.error(`\n  Error on iteration ${iter}:`, error);
        }
      }
      
      if (this.config.verbose) {
        console.log(' ✓');
      }
    }
    
    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;
    
    console.log(`\n✅ Completed ${results.length} simulations in ${duration.toFixed(2)}s`);
    console.log(`   (${(results.length / duration).toFixed(1)} sims/sec)\n`);
    
    // Generate report
    const report = this.generateReport(results, plays);
    await this.saveResults(results, report);
    
    // Print summary
    this.printSummary(report);
  }
  
  private selectPlays() {
    switch (this.config.playsToTest) {
      case 'all': return ALL_PLAYS;
      case 'pass': return PASS_PLAYS;
      case 'run': return RUN_PLAYS;
      default: 
        // Filter by IDs if array provided
        if (Array.isArray(this.config.playsToTest)) {
          return ALL_PLAYS.filter(p => this.config.playsToTest.includes(p.id));
        }
        return ALL_PLAYS;
    }
  }
  
  private generateReport(
    results: DetailedPlayResult[],
    plays: typeof ALL_PLAYS
  ): BatchSimulationResult {
    // Use the API's aggregation
    const batchResult = this.api['aggregateResults'](results);
    
    // Add play details
    for (const [playId, stats] of batchResult.byPlay) {
      const play = plays.find(p => p.id === playId);
      if (play) {
        // Extend the stats with play info
        (stats as any).playName = play.name;
        (stats as any).category = play.category;
        (stats as any).riskLevel = play.riskLevel;
      }
    }
    
    return batchResult;
  }
  
  private async saveResults(
    results: DetailedPlayResult[],
    report: BatchSimulationResult
  ): Promise<void> {
    // Create output directory
    if (!fs.existsSync(this.config.outputDir)) {
      fs.mkdirSync(this.config.outputDir, { recursive: true });
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // Save raw results (compressed)
    const rawPath = path.join(this.config.outputDir, `raw-${timestamp}.json.gz`);
    const rawData = JSON.stringify(results);
    fs.writeFileSync(rawPath, rawData); // Could gzip here if needed
    console.log(`📁 Raw results saved to: ${rawPath}`);
    
    // Save summary report
    const summaryPath = path.join(this.config.outputDir, `summary-${timestamp}.json`);
    const summaryData = {
      meta: {
        timestamp: new Date().toISOString(),
        iterations: this.config.iterations,
        totalSims: results.length,
      },
      summary: report.summary,
      byPlay: Array.from(report.byPlay.entries()).map(([id, stats]) => ({
        playId: id,
        ...stats,
      })),
    };
    fs.writeFileSync(summaryPath, JSON.stringify(summaryData, null, 2));
    console.log(`📊 Summary report saved to: ${summaryPath}`);
    
    // Save CSV for easy analysis
    const csvPath = path.join(this.config.outputDir, `plays-${timestamp}.csv`);
    const csv = this.generateCSV(results);
    fs.writeFileSync(csvPath, csv);
    console.log(`📈 CSV data saved to: ${csvPath}`);
    
    // Save latest symlinks
    const latestRaw = path.join(this.config.outputDir, 'latest-raw.json');
    const latestSummary = path.join(this.config.outputDir, 'latest-summary.json');
    const latestCSV = path.join(this.config.outputDir, 'latest-plays.csv');
    
    try {
      fs.unlinkSync(latestRaw);
      fs.unlinkSync(latestSummary);
      fs.unlinkSync(latestCSV);
    } catch { /* ignore if don't exist */ }
    
    fs.copyFileSync(rawPath, latestRaw);
    fs.copyFileSync(summaryPath, latestSummary);
    fs.copyFileSync(csvPath, latestCSV);
  }
  
  private generateCSV(results: DetailedPlayResult[]): string {
    const headers = [
      'playId',
      'playName',
      'outcome',
      'yardsGained',
      'timeElapsed',
      'frameCount',
    ].join(',');
    
    const rows = results.map(r => [
      r.playId,
      r.playName,
      r.outcome,
      r.yardsGained,
      r.timeElapsed,
      r.frames.length,
    ].join(','));
    
    return [headers, ...rows].join('\n');
  }
  
  private printSummary(report: BatchSimulationResult): void {
    console.log('\n📊 SIMULATION SUMMARY');
    console.log('=====================\n');
    
    const { summary } = report;
    
    console.log(`Total Simulations: ${summary.totalPlays}`);
    console.log(`Total Yards: ${summary.totalYards}`);
    console.log(`Average Yards: ${summary.averageYards.toFixed(2)}`);
    console.log(`Big Plays (20+ yards): ${summary.bigPlays} (${((summary.bigPlays / summary.totalPlays) * 100).toFixed(1)}%)\n`);
    
    console.log('Outcomes:');
    console.log(`  Completions: ${summary.completions} (${((summary.completions / summary.totalPlays) * 100).toFixed(1)}%)`);
    console.log(`  Incompletions: ${summary.incompletions} (${((summary.incompletions / summary.totalPlays) * 100).toFixed(1)}%)`);
    console.log(`  Interceptions: ${summary.interceptions} (${((summary.interceptions / summary.totalPlays) * 100).toFixed(1)}%)`);
    console.log(`  Sacks: ${summary.sacks} (${((summary.sacks / summary.totalPlays) * 100).toFixed(1)}%)`);
    console.log(`  Runs: ${summary.runs} (${((summary.runs / summary.totalPlays) * 100).toFixed(1)}%)\n`);
    
    console.log('Top Performing Plays:');
    const sortedPlays = Array.from(report.byPlay.entries())
      .sort((a, b) => b[1].averageYards - a[1].averageYards)
      .slice(0, 5);
    
    sortedPlays.forEach(([id, stats], i) => {
      const playName = (stats as any).playName || id;
      console.log(`  ${i + 1}. ${playName}: ${stats.averageYards.toFixed(2)} yds (${stats.successRate.toFixed(1)}% success)`);
    });
    
    console.log('\n');
  }
}

// ===== CLI =====

function parseArgs(): Partial<RunnerConfig> {
  const args = process.argv.slice(2);
  const config: Partial<RunnerConfig> = {};
  
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '-n':
      case '--iterations':
        config.iterations = parseInt(args[++i], 10);
        break;
      case '-p':
      case '--plays':
        const plays = args[++i];
        if (plays === 'all' || plays === 'pass' || plays === 'run') {
          config.playsToTest = plays;
        } else {
          config.playsToTest = plays.split(',');
        }
        break;
      case '-o':
      case '--output':
        config.outputDir = args[++i];
        break;
      case '-q':
      case '--quiet':
        config.verbose = false;
        break;
      case '-h':
      case '--help':
        console.log(`
Football Batch Simulation Runner

Usage: tsx run-football-simulations.ts [options]

Options:
  -n, --iterations <num>  Iterations per play (default: 100)
  -p, --plays <type>      Plays to test: all|pass|run or comma-separated IDs
  -o, --output <dir>      Output directory (default: ./simulation-results)
  -q, --quiet             Suppress progress output
  -h, --help              Show this help

Examples:
  tsx run-football-simulations.ts
  tsx run-football-simulations.ts -n 500 -p pass
  tsx run-football-simulations.ts -n 1000 -p four_verticals,slant_combo
        `);
        process.exit(0);
        break;
    }
  }
  
  return config;
}

// ===== RUN =====

const config = parseArgs();
const runner = new BatchRunner(config);

runner.run().catch(error => {
  console.error('❌ Simulation runner failed:', error);
  process.exit(1);
});
