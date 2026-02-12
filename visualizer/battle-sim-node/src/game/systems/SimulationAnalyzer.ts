/**
 * SIMULATION ANALYZER - Data processing and balance insights
 * 
 * Processes simulation batch results and generates:
 * - Statistical summaries
 * - Balance recommendations
 * - Trend analysis
 * - Difficulty curve validation
 */

import type { SimulationResult } from './SimulationManager';

export interface BatchAnalysis {
  meta: {
    totalRuns: number;
    timestamp: string;
    duration: number;
  };
  survival: {
    overallRate: number;
    byWave: Record<number, number>;
    averageWaves: number;
    medianWaves: number;
  };
  performance: {
    averageScore: number;
    bestScore: number;
    averageKills: number;
    averageDuration: number;
  };
  dna: {
    typeDistribution: Record<string, number>;
    mostAcquired: string;
    leastAcquired: string;
    correlationWithSuccess: Record<string, number>;
  };
  evolution: {
    popularPaths: Array<{ path: string; count: number; winRate: number }>;
    pathEffectiveness: Record<string, number>;
  };
  balance: {
    difficultyCurve: Array<{ wave: number; survivalRate: number }>;
    recommendedAdjustments: BalanceRecommendation[];
    fairness: number; // 0-1 score
  };
}

export interface BalanceRecommendation {
  type: 'enemy' | 'dna' | 'evolution' | 'difficulty';
  severity: 'critical' | 'warning' | 'info';
  issue: string;
  recommendation: string;
  data: unknown;
}

export class SimulationAnalyzer {
  private results: SimulationResult[] = [];
  
  loadResults(results: SimulationResult[]): void {
    this.results = results.filter(r => r.success !== undefined);
  }
  
  analyze(): BatchAnalysis {
    if (this.results.length === 0) {
      return this.getEmptyAnalysis();
    }
    
    return {
      meta: this.analyzeMeta(),
      survival: this.analyzeSurvival(),
      performance: this.analyzePerformance(),
      dna: this.analyzeDNA(),
      evolution: this.analyzeEvolution(),
      balance: this.analyzeBalance()
    };
  }
  
  private analyzeMeta() {
    return {
      totalRuns: this.results.length,
      timestamp: new Date().toISOString(),
      duration: this.results.reduce((sum, r) => sum + r.duration, 0)
    };
  }
  
  private analyzeSurvival() {
    const total = this.results.length;
    const survived = this.results.filter(r => r.success).length;
    
    // Wave distribution
    const waveCounts: Record<number, number> = {};
    this.results.forEach(r => {
      waveCounts[r.wavesCompleted] = (waveCounts[r.wavesCompleted] || 0) + 1;
    });
    
    // Survival by wave (what % made it TO this wave)
    const byWave: Record<number, number> = {};
    const maxWave = Math.max(...this.results.map(r => r.wavesCompleted));
    for (let w = 1; w <= maxWave; w++) {
      const madeIt = this.results.filter(r => r.wavesCompleted >= w).length;
      byWave[w] = madeIt / total;
    }
    
    const waves = this.results.map(r => r.wavesCompleted || 0).sort((a, b) => a - b);
    const mid = Math.floor(waves.length / 2);
    
    return {
      overallRate: survived / total,
      byWave,
      averageWaves: waves.reduce((a, b) => a + b, 0) / waves.length,
      medianWaves: waves.length % 2 ? waves[mid] : (waves[mid - 1] + waves[mid]) / 2
    };
  }
  
  private analyzePerformance() {
    const scores = this.results.map(r => r.score);
    const kills = this.results.map(r => r.enemiesKilled);
    const durations = this.results.map(r => r.duration);
    
    return {
      averageScore: scores.reduce((a, b) => a + b, 0) / scores.length,
      bestScore: Math.max(...scores),
      averageKills: kills.reduce((a, b) => a + b, 0) / kills.length,
      averageDuration: durations.reduce((a, b) => a + b, 0) / durations.length
    };
  }
  
  private analyzeDNA() {
    // Aggregate DNA acquisition
    const typeTotals: Record<string, number> = {};
    this.results.forEach(r => {
      Object.entries(r.dnaAcquired || {}).forEach(([type, amount]) => {
        typeTotals[type] = (typeTotals[type] || 0) + amount;
      });
    });
    
    const types = Object.keys(typeTotals);
    const mostAcquired = types.length > 0 
      ? types.reduce((a, b) => typeTotals[a] > typeTotals[b] ? a : b)
      : 'N/A';
    const leastAcquired = types.length > 0
      ? types.reduce((a, b) => typeTotals[a] < typeTotals[b] ? a : b)
      : 'N/A';
    
    // Correlation with success
    const correlation: Record<string, number> = {};
    types.forEach(type => {
      const withType = this.results.filter(r => (r.dnaAcquired?.[type as keyof typeof r.dnaAcquired] || 0) > 0);
      const winRate = withType.filter(r => r.success).length / (withType.length || 1);
      correlation[type] = winRate;
    });
    
    return {
      typeDistribution: typeTotals,
      mostAcquired,
      leastAcquired,
      correlationWithSuccess: correlation
    };
  }
  
  private analyzeEvolution() {
    const pathStats: Record<string, { count: number; wins: number }> = {};
    
    this.results.forEach(r => {
      r.evolutionHistory?.forEach(evo => {
        if (!pathStats[evo.path]) {
          pathStats[evo.path] = { count: 0, wins: 0 };
        }
        pathStats[evo.path].count++;
        if (r.success) {
          pathStats[evo.path].wins++;
        }
      });
    });
    
    const popularPaths = Object.entries(pathStats)
      .map(([path, stats]) => ({
        path,
        count: stats.count,
        winRate: stats.wins / stats.count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
    
    const pathEffectiveness: Record<string, number> = {};
    Object.entries(pathStats).forEach(([path, stats]) => {
      pathEffectiveness[path] = stats.wins / stats.count;
    });
    
    return {
      popularPaths,
      pathEffectiveness
    };
  }
  
  private analyzeBalance(): BatchAnalysis['balance'] {
    const recommendations: BalanceRecommendation[] = [];
    const survival = this.analyzeSurvival();
    const dna = this.analyzeDNA();
    const evolution = this.analyzeEvolution();
    
    // Check overall survival rate
    if (survival.overallRate < 0.1) {
      recommendations.push({
        type: 'difficulty',
        severity: 'critical',
        issue: `Survival rate too low (${(survival.overallRate * 100).toFixed(1)}%)`,
        recommendation: 'Reduce early game difficulty or increase starting power',
        data: { survivalRate: survival.overallRate }
      });
    } else if (survival.overallRate > 0.8) {
      recommendations.push({
        type: 'difficulty',
        severity: 'warning',
        issue: `Game too easy (${(survival.overallRate * 100).toFixed(1)}% survival)`,
        recommendation: 'Increase enemy scaling or reduce player power',
        data: { survivalRate: survival.overallRate }
      });
    }
    
    // Check difficulty curve
    const difficultyCurve = Object.entries(survival.byWave)
      .map(([wave, rate]) => ({ wave: parseInt(wave), survivalRate: rate }))
      .sort((a, b) => a.wave - b.wave);
    
    // Find difficulty spikes
    for (let i = 1; i < difficultyCurve.length; i++) {
      const drop = difficultyCurve[i - 1].survivalRate - difficultyCurve[i].survivalRate;
      if (drop > 0.3) {
        recommendations.push({
          type: 'difficulty',
          severity: 'warning',
          issue: `Difficulty spike at wave ${difficultyCurve[i].wave}`,
          recommendation: `Smooth transition to wave ${difficultyCurve[i].wave}`,
          data: { wave: difficultyCurve[i].wave, drop }
        });
      }
    }
    
    // Check DNA balance
    const dnaValues = Object.values(dna.typeDistribution);
    if (dnaValues.length > 1) {
      const maxDNA = Math.max(...dnaValues);
      const minDNA = Math.min(...dnaValues);
      if (maxDNA / minDNA > 5) {
        recommendations.push({
          type: 'dna',
          severity: 'warning',
          issue: `DNA types imbalanced (${dna.mostAcquired} vs ${dna.leastAcquired})`,
          recommendation: 'Adjust drop rates for underrepresented DNA types',
          data: { most: dna.mostAcquired, least: dna.leastAcquired, ratio: maxDNA / minDNA }
        });
      }
    }
    
    // Check evolution balance
    const evoRates = Object.values(evolution.pathEffectiveness);
    if (evoRates.length > 1) {
      const maxRate = Math.max(...evoRates);
      const minRate = Math.min(...evoRates);
      if (maxRate - minRate > 0.4) {
        const best = Object.entries(evolution.pathEffectiveness)
          .find(([, rate]) => rate === maxRate)?.[0] || 'N/A';
        const worst = Object.entries(evolution.pathEffectiveness)
          .find(([, rate]) => rate === minRate)?.[0] || 'N/A';
        
        recommendations.push({
          type: 'evolution',
          severity: 'warning',
          issue: `Evolution paths unbalanced (${best} vs ${worst})`,
          recommendation: `Buff ${worst} or nerf ${best}`,
          data: { best, bestRate: maxRate, worst, worstRate: minRate }
        });
      }
    }
    
    // Calculate fairness score (0-1)
    const fairness = Math.max(0, 1 - recommendations.filter(r => r.severity === 'critical').length * 0.3 
      - recommendations.filter(r => r.severity === 'warning').length * 0.1);
    
    return {
      difficultyCurve,
      recommendedAdjustments: recommendations,
      fairness
    };
  }
  
  private getEmptyAnalysis(): BatchAnalysis {
    return {
      meta: { totalRuns: 0, timestamp: new Date().toISOString(), duration: 0 },
      survival: { overallRate: 0, byWave: {}, averageWaves: 0, medianWaves: 0 },
      performance: { averageScore: 0, bestScore: 0, averageKills: 0, averageDuration: 0 },
      dna: { typeDistribution: {}, mostAcquired: 'N/A', leastAcquired: 'N/A', correlationWithSuccess: {} },
      evolution: { popularPaths: [], pathEffectiveness: {} },
      balance: { difficultyCurve: [], recommendedAdjustments: [], fairness: 0 }
    };
  }
  
  // Export insights as markdown report
  generateReport(analysis: BatchAnalysis): string {
    const lines = [
      '# Simulation Analysis Report',
      '',
      `Generated: ${analysis.meta.timestamp}`,
      `Total Runs: ${analysis.meta.totalRuns}`,
      '',
      '## Summary',
      `- Survival Rate: ${(analysis.survival.overallRate * 100).toFixed(1)}%`,
      `- Average Waves: ${analysis.survival.averageWaves.toFixed(1)}`,
      `- Best Score: ${analysis.performance.bestScore}`,
      `- Fairness Score: ${(analysis.balance.fairness * 100).toFixed(0)}/100`,
      '',
      '## Balance Recommendations',
      ...analysis.balance.recommendedAdjustments.map(r => 
        `- **${r.severity.toUpperCase()}** [${r.type}]: ${r.issue}\n  → ${r.recommendation}`
      ),
      '',
      '## Popular Evolution Paths',
      ...analysis.evolution.popularPaths.slice(0, 5).map((p, i) => 
        `${i + 1}. ${p.path}: ${p.count} uses (${(p.winRate * 100).toFixed(0)}% win rate)`
      ),
      ''
    ];
    
    return lines.join('\n');
  }
}

export const simulationAnalyzer = new SimulationAnalyzer();
