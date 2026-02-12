/**
 * SIMULATION METRICS & ANALYTICS
 * 
 * Collects, processes, and visualizes simulation data
 * Provides insights on AI performance, balance, and trends
 */

import type { SimulationResult } from './SimulationManager';
import type { SimulationSession } from './SimulationLogger';

export interface MetricTimeSeries {
  timestamps: number[];
  values: number[];
  label: string;
  unit: string;
}

export interface ComparativeAnalysis {
  baseline: SimulationResult[];
  current: SimulationResult[];
  improvements: {
    category: string;
    metric: string;
    before: number;
    after: number;
    percentChange: number;
  }[];
  regressions: {
    category: string;
    metric: string;
    before: number;
    after: number;
    percentChange: number;
  }[];
}

export interface AIPerformanceMetrics {
  decisionAccuracy: {
    evolution: number;
    mutation: number;
    building: number;
    combat: number;
  };
  reactionTime: {
    average: number;
    byCategory: Record<string, number>;
  };
  efficiency: {
    resourceUtilization: number;
    dnaOptimization: number;
    survivalOptimization: number;
  };
}

export interface BalanceReport {
  dnaTypeBalance: Record<string, {
    usageRate: number;
    successRate: number;
    avgWavesSurvived: number;
    powerScore: number;
  }>;
  evolutionPathBalance: Record<string, {
    popularity: number;
    winRate: number;
    avgScore: number;
  }>;
  difficultyCurve: {
    wave: number;
    survivalRate: number;
    avgHealth: number;
  }[];
  recommendations: string[];
}

export interface MetricsSnapshot {
  timestamp: number;
  gameTime: number;
  wave: number;
  playerHealth: number;
  playerPosition: { x: number; y: number };
  enemyCount: number;
  dnaDistribution: Record<string, number>;
  activeAbilities: string[];
}

class SimulationMetrics {
  private currentSnapshots: MetricsSnapshot[] = [];
  private currentSessionId: string | null = null;
  
  /**
   * Start a new metrics collection session
   */
  startSession(sessionId: string): void {
    this.currentSessionId = sessionId;
    this.currentSnapshots = [];
  }
  
  /**
   * Record a snapshot of game state
   */
  recordSnapshot(snapshot: MetricsSnapshot): void {
    if (!this.currentSessionId) return;
    this.currentSnapshots.push(snapshot);
    
    // Limit memory usage - keep last 10000 snapshots
    if (this.currentSnapshots.length > 10000) {
      this.currentSnapshots.shift();
    }
  }
  
  /**
   * End session and return collected snapshots
   */
  endSession(_result?: SimulationResult): MetricsSnapshot[] {
    const snapshots = [...this.currentSnapshots];
    this.currentSnapshots = [];
    this.currentSessionId = null;
    return snapshots;
  }
  
  /**
   * Calculate comprehensive metrics from a batch of results
   */
  calculateBatchMetrics(results: SimulationResult[]): {
    survival: {
      rate: number;
      avgWaves: number;
      medianWaves: number;
      bestRun: number;
    };
    performance: {
      avgScore: number;
      avgKills: number;
      avgDuration: number;
      totalEvolutions: number;
    };
    dna: {
      typeDistribution: Record<string, number>;
      purityDistribution: { low: number; medium: number; high: number };
      dominantTypes: Record<string, number>;
    };
    buildings: {
      avgPerRun: number;
      typeDistribution: Record<string, number>;
    };
    mutations: {
      avgPerRun: number;
      typeDistribution: Record<string, number>;
    };
  } {
    if (results.length === 0) {
      return this.getEmptyMetrics();
    }

    const successful = results.filter(r => r.success);
    const waves = results.map(r => r.wavesCompleted);
    
    // Sort for median
    waves.sort((a, b) => a - b);
    const medianWaves = waves.length % 2 === 0
      ? (waves[waves.length / 2 - 1] + waves[waves.length / 2]) / 2
      : waves[Math.floor(waves.length / 2)];

    // DNA analysis
    const dnaTypes: Record<string, number> = {};
    const dominantTypes: Record<string, number> = {};
    let puritySum = 0;
    
    results.forEach(r => {
      // Track DNA types
      for (const [type, amount] of Object.entries(r.dnaAcquired)) {
        dnaTypes[type] = (dnaTypes[type] || 0) + amount;
      }
      
      // Track purity (approximated from evolution history)
      if (r.evolutionHistory.length > 0) {
        puritySum += Math.min(1, r.evolutionHistory.length * 0.2);
      }
    });

    // Calculate purity distribution (avgPurity available for future use)
    void puritySum;

    return {
      survival: {
        rate: successful.length / results.length,
        avgWaves: results.reduce((a, r) => a + r.wavesCompleted, 0) / results.length,
        medianWaves,
        bestRun: Math.max(...waves),
      },
      performance: {
        avgScore: results.reduce((a, r) => a + r.score, 0) / results.length,
        avgKills: results.reduce((a, r) => a + r.enemiesKilled, 0) / results.length,
        avgDuration: results.reduce((a, r) => a + r.duration, 0) / results.length,
        totalEvolutions: results.reduce((a, r) => a + r.evolutionHistory.length, 0),
      },
      dna: {
        typeDistribution: dnaTypes,
        purityDistribution: {
          low: results.filter(r => r.evolutionHistory.length < 2).length / results.length,
          medium: results.filter(r => r.evolutionHistory.length >= 2 && r.evolutionHistory.length < 4).length / results.length,
          high: results.filter(r => r.evolutionHistory.length >= 4).length / results.length,
        },
        dominantTypes,
      },
      buildings: {
        avgPerRun: results.reduce((a, r) => a + ((r as unknown as { buildingsConstructed?: number }).buildingsConstructed ?? 0), 0) / results.length,
        typeDistribution: {}, // Would need building type data
      },
      mutations: {
        avgPerRun: results.reduce((a, r) => a + ((r as unknown as { mutationsPurchased?: number }).mutationsPurchased ?? 0), 0) / results.length,
        typeDistribution: {}, // Would need mutation type data
      },
    };
  }

  /**
   * Generate a balance report from session data
   */
  generateBalanceReport(sessions: SimulationSession[]): BalanceReport {
    const allResults = sessions.flatMap(s => s.results);
    
    // DNA type balance
    const dnaTypeStats: Record<string, { count: number; waves: number; score: number }> = {};
    
    allResults.forEach(r => {
      // Find dominant DNA type
      let dominantType = 'UNKNOWN';
      let maxAmount = 0;
      
      for (const [type, amount] of Object.entries(r.dnaAcquired)) {
        if (amount > maxAmount) {
          maxAmount = amount;
          dominantType = type;
        }
      }
      
      if (!dnaTypeStats[dominantType]) {
        dnaTypeStats[dominantType] = { count: 0, waves: 0, score: 0 };
      }
      
      dnaTypeStats[dominantType].count++;
      dnaTypeStats[dominantType].waves += r.wavesCompleted;
      dnaTypeStats[dominantType].score += r.score;
    });

    // Calculate DNA type balance scores
    const dnaTypeBalance: BalanceReport['dnaTypeBalance'] = {};
    
    for (const [type, stats] of Object.entries(dnaTypeStats)) {
      const usageRate = stats.count / allResults.length;
      const avgWaves = stats.waves / stats.count;
      const successRate = allResults
        .filter(r => {
          let dominant = 'UNKNOWN';
          let max = 0;
          for (const [t, a] of Object.entries(r.dnaAcquired)) {
            if (a > max) { max = a; dominant = t; }
          }
          return dominant === type;
        })
        .filter(r => r.success).length / stats.count;
      
      dnaTypeBalance[type] = {
        usageRate,
        successRate,
        avgWavesSurvived: avgWaves,
        powerScore: (successRate * 0.5 + (avgWaves / 20) * 0.5) * 100,
      };
    }

    // Evolution path balance
    const pathStats: Record<string, { count: number; wins: number; score: number }> = {};
    
    allResults.forEach(r => {
      r.evolutionHistory.forEach(evo => {
        if (!pathStats[evo.path]) {
          pathStats[evo.path] = { count: 0, wins: 0, score: 0 };
        }
        pathStats[evo.path].count++;
        if (r.success) pathStats[evo.path].wins++;
        pathStats[evo.path].score += r.score;
      });
    });

    const evolutionPathBalance: BalanceReport['evolutionPathBalance'] = {};
    
    for (const [path, stats] of Object.entries(pathStats)) {
      evolutionPathBalance[path] = {
        popularity: stats.count / allResults.length,
        winRate: stats.wins / stats.count,
        avgScore: stats.score / stats.count,
      };
    }

    // Difficulty curve
    const difficultyCurve: BalanceReport['difficultyCurve'] = [];
    
    for (let wave = 1; wave <= 20; wave++) {
      const waveResults = allResults.filter(r => r.wavesCompleted >= wave);
      // Track survival rate for this wave
      void allResults;
      difficultyCurve.push({
        wave,
        survivalRate: waveResults.length / Math.max(allResults.length * 0.8, 1),
        avgHealth: 50, // Would need health data per wave
      });
    }

    // Generate recommendations
    const recommendations: string[] = [];
    
    // Check for overpowered/underpowered DNA types
    for (const [type, stats] of Object.entries(dnaTypeBalance)) {
      if (stats.powerScore > 70) {
        recommendations.push(`${type} appears overpowered (${stats.powerScore.toFixed(0)} power score). Consider nerfing.`);
      } else if (stats.powerScore < 30) {
        recommendations.push(`${type} appears underpowered (${stats.powerScore.toFixed(0)} power score). Consider buffing.`);
      }
    }

    // Check for popular but low-win-rate paths
    for (const [path, stats] of Object.entries(evolutionPathBalance)) {
      if (stats.popularity > 0.3 && stats.winRate < 0.4) {
        recommendations.push(`${path} is popular (${(stats.popularity * 100).toFixed(0)}%) but has low win rate (${(stats.winRate * 100).toFixed(0)}%). Review balance.`);
      }
    }

    return {
      dnaTypeBalance,
      evolutionPathBalance,
      difficultyCurve,
      recommendations,
    };
  }

  /**
   * Compare two sets of results (before/after changes)
   */
  compareResults(baseline: SimulationResult[], current: SimulationResult[]): ComparativeAnalysis {
    const baselineMetrics = this.calculateBatchMetrics(baseline);
    const currentMetrics = this.calculateBatchMetrics(current);

    const improvements: ComparativeAnalysis['improvements'] = [];
    const regressions: ComparativeAnalysis['regressions'] = [];

    // Compare survival rate
    const survivalChange = ((currentMetrics.survival.rate - baselineMetrics.survival.rate) / baselineMetrics.survival.rate) * 100;
    if (survivalChange > 5) {
      improvements.push({
        category: 'Survival',
        metric: 'Success Rate',
        before: baselineMetrics.survival.rate,
        after: currentMetrics.survival.rate,
        percentChange: survivalChange,
      });
    } else if (survivalChange < -5) {
      regressions.push({
        category: 'Survival',
        metric: 'Success Rate',
        before: baselineMetrics.survival.rate,
        after: currentMetrics.survival.rate,
        percentChange: survivalChange,
      });
    }

    // Compare waves survived
    const wavesChange = ((currentMetrics.survival.avgWaves - baselineMetrics.survival.avgWaves) / baselineMetrics.survival.avgWaves) * 100;
    if (wavesChange > 5) {
      improvements.push({
        category: 'Performance',
        metric: 'Avg Waves',
        before: baselineMetrics.survival.avgWaves,
        after: currentMetrics.survival.avgWaves,
        percentChange: wavesChange,
      });
    } else if (wavesChange < -5) {
      regressions.push({
        category: 'Performance',
        metric: 'Avg Waves',
        before: baselineMetrics.survival.avgWaves,
        after: currentMetrics.survival.avgWaves,
        percentChange: wavesChange,
      });
    }

    // Compare score
    const scoreChange = ((currentMetrics.performance.avgScore - baselineMetrics.performance.avgScore) / baselineMetrics.performance.avgScore) * 100;
    if (scoreChange > 5) {
      improvements.push({
        category: 'Performance',
        metric: 'Avg Score',
        before: baselineMetrics.performance.avgScore,
        after: currentMetrics.performance.avgScore,
        percentChange: scoreChange,
      });
    } else if (scoreChange < -5) {
      regressions.push({
        category: 'Performance',
        metric: 'Avg Score',
        before: baselineMetrics.performance.avgScore,
        after: currentMetrics.performance.avgScore,
        percentChange: scoreChange,
      });
    }

    return {
      baseline,
      current,
      improvements,
      regressions,
    };
  }

  /**
   * Generate time series data for visualization
   */
  generateTimeSeries(results: SimulationResult[]): {
    wavesOverTime: MetricTimeSeries;
    scoreOverTime: MetricTimeSeries;
    killsOverTime: MetricTimeSeries;
  } {
    return {
      wavesOverTime: {
        timestamps: results.map((_, i) => i),
        values: results.map(r => r.wavesCompleted),
        label: 'Waves Survived',
        unit: 'waves',
      },
      scoreOverTime: {
        timestamps: results.map((_, i) => i),
        values: results.map(r => r.score),
        label: 'Score',
        unit: 'points',
      },
      killsOverTime: {
        timestamps: results.map((_, i) => i),
        values: results.map(r => r.enemiesKilled),
        label: 'Enemies Killed',
        unit: 'kills',
      },
    };
  }

  /**
   * Export metrics to CSV
   */
  exportToCSV(results: SimulationResult[]): string {
    const headers = [
      'ID',
      'Timestamp',
      'Success',
      'Waves',
      'Score',
      'Kills',
      'Duration',
      'Evolutions',
      'Cause of Death',
    ].join(',');

    const rows = results.map(r => [
      r.id,
      r.duration,
      r.success,
      r.wavesCompleted,
      r.score,
      r.enemiesKilled,
      r.duration,
      r.evolutionHistory.length,
      r.causeOfDeath || 'N/A',
    ].join(','));

    return [headers, ...rows].join('\n');
  }

  // Private helpers
  private getEmptyMetrics() {
    return {
      survival: { rate: 0, avgWaves: 0, medianWaves: 0, bestRun: 0 },
      performance: { avgScore: 0, avgKills: 0, avgDuration: 0, totalEvolutions: 0 },
      dna: { typeDistribution: {}, purityDistribution: { low: 0, medium: 0, high: 0 }, dominantTypes: {} },
      buildings: { avgPerRun: 0, typeDistribution: {} },
      mutations: { avgPerRun: 0, typeDistribution: {} },
    };
  }
}

export const simulationMetrics = new SimulationMetrics();
