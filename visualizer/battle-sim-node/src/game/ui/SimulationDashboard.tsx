import { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import { SimulationAnalyzer, type BatchAnalysis, type BalanceRecommendation } from '../systems/SimulationAnalyzer';
import type { SimulationResult } from '../systems/SimulationManager';
import type { DNAType } from '../types';

interface SimulationDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

const COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1'];

export const SimulationDashboard = ({ isOpen, onClose }: SimulationDashboardProps) => {
  const [results, setResults] = useState<SimulationResult[]>([]);
  const [analysis, setAnalysis] = useState<BatchAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'dna' | 'evolution' | 'balance'>('overview');
  const [refreshKey, setRefreshKey] = useState(0);

  // Load data when opened
  useEffect(() => {
    // Reset loading when closed
    if (!isOpen) {
      return;
    }
    
    // Use timeout to avoid synchronous setState in effect
    const timeoutId = setTimeout(() => {
      setLoading(true);
      
      // Try to load from localStorage first (for demo/persistence)
      const saved = localStorage.getItem('simulation_results');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setResults(parsed);
          const analyzer = new SimulationAnalyzer();
          analyzer.loadResults(parsed);
          setAnalysis(analyzer.analyze());
        } catch {
          // Ignore parse errors
        }
      }
      
      setLoading(false);
    }, 0);
    
    return () => clearTimeout(timeoutId);
  }, [isOpen, refreshKey]);
  
  // Reset loading state when panel closes
  useEffect(() => {
    if (!isOpen) {
      setLoading(false);
    }
  }, [isOpen]);

  // Generate sample data for demonstration
  const generateSampleData = () => {
    const sample: SimulationResult[] = [];
    const dnaTypes = ['GRASS', 'VOID', 'BEAST', 'ARCANE', 'FIRE', 'WATER', 'POISON'];
    const paths = ['spike', 'cub', 'sprout', 'crystal', 'flame', 'tide'];
    
    for (let i = 0; i < 100; i++) {
      const waves = Math.floor(Math.random() * 15) + 1;
      const success = waves >= 10 && Math.random() > 0.3;
      
      const dnaAcquired: Record<string, number> = {};
      dnaTypes.forEach(type => {
        if (Math.random() > 0.3) {
          dnaAcquired[type] = Math.floor(Math.random() * 20);
        }
      });
      
      const evolutionHistory: Array<{ wave: number; path: string; name: string }> = [];
      if (Math.random() > 0.5) {
        evolutionHistory.push({
          wave: Math.floor(Math.random() * waves) + 1,
          path: paths[Math.floor(Math.random() * paths.length)],
          name: 'Evolution'
        });
      }
      
      sample.push({
        id: `sim-${i}`,
        config: { maxDuration: 300, maxWave: 15, speed: 100, useSmartAI: true, startWave: 1 },
        duration: waves * 20 + Math.random() * 60,
        wavesCompleted: waves,
        enemiesKilled: waves * 5 + Math.floor(Math.random() * 20),
        score: waves * 150 + Math.floor(Math.random() * 500),
        dnaAcquired: dnaAcquired as Record<DNAType, number>,
        evolutionHistory,
        success,
        finalStats: {
          health: success ? Math.random() * 50 : 0,
          maxHealth: 100,
          damage: 10 + waves,
          speed: 100,
          level: Math.floor(waves / 2)
        }
      });
    }
    
    localStorage.setItem('simulation_results', JSON.stringify(sample));
    setRefreshKey(k => k + 1);
  };

  // Export analysis as JSON
  const exportAnalysis = () => {
    if (!analysis) return;
    
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-${Date.now()}.json`;
    a.click();
  };

  // Chart data preparations
  const survivalCurveData = useMemo(() => {
    if (!analysis) return [];
    return Object.entries(analysis.survival.byWave)
      .map(([wave, rate]) => ({ wave: parseInt(wave), survivalRate: rate * 100 }))
      .sort((a, b) => a.wave - b.wave);
  }, [analysis]);

  const dnaDistributionData = useMemo(() => {
    if (!analysis) return [];
    return Object.entries(analysis.dna.typeDistribution)
      .map(([type, amount]) => ({ type, amount }))
      .sort((a, b) => b.amount - a.amount);
  }, [analysis]);

  const evolutionPathData = useMemo(() => {
    if (!analysis) return [];
    return analysis.evolution.popularPaths.map(p => ({
      path: p.path,
      uses: p.count,
      winRate: p.winRate * 100
    }));
  }, [analysis]);

  const scoreDistribution = useMemo(() => {
    if (!results.length) return [];
    const buckets: Record<string, number> = { '0-500': 0, '500-1000': 0, '1000-1500': 0, '1500-2000': 0, '2000+': 0 };
    results.forEach(r => {
      if (r.score < 500) buckets['0-500']++;
      else if (r.score < 1000) buckets['500-1000']++;
      else if (r.score < 1500) buckets['1000-1500']++;
      else if (r.score < 2000) buckets['1500-2000']++;
      else buckets['2000+']++;
    });
    return Object.entries(buckets).map(([range, count]) => ({ range, count }));
  }, [results]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="w-[95vw] h-[90vh] bg-slate-900 rounded-xl border border-slate-700 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div>
            <h2 className="text-2xl font-bold text-white">📊 Simulation Analytics</h2>
            <p className="text-slate-400 text-sm">
              {analysis ? `${analysis.meta.totalRuns} runs analyzed` : 'No data loaded'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={generateSampleData}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm text-white transition-colors"
            >
              Generate Sample Data
            </button>
            <button
              onClick={exportAnalysis}
              disabled={!analysis}
              className="px-3 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg text-sm text-white transition-colors"
            >
              Export JSON
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 p-2 border-b border-slate-700 bg-slate-800/50">
          {(['overview', 'dna', 'evolution', 'balance'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-cyan-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
            </div>
          ) : !analysis || analysis.meta.totalRuns === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <div className="text-6xl mb-4">📈</div>
              <p className="text-lg mb-2">No simulation data available</p>
              <p className="text-sm mb-4">Run simulations or generate sample data to see analytics</p>
              <button
                onClick={generateSampleData}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white"
              >
                Generate Sample Data
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {activeTab === 'overview' && (
                <OverviewTab analysis={analysis} survivalCurveData={survivalCurveData} scoreDistribution={scoreDistribution} />
              )}
              {activeTab === 'dna' && (
                <DNATab analysis={analysis} dnaDistributionData={dnaDistributionData} />
              )}
              {activeTab === 'evolution' && (
                <EvolutionTab analysis={analysis} evolutionPathData={evolutionPathData} />
              )}
              {activeTab === 'balance' && (
                <BalanceTab analysis={analysis} />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ============== TAB COMPONENTS ==============

interface ChartDataPoint {
  wave?: number;
  survivalRate?: number;
  range?: string;
  count?: number;
  type?: string;
  amount?: number;
  path?: string;
  uses?: number;
  winRate?: number;
}

const OverviewTab = ({ analysis, survivalCurveData, scoreDistribution }: {
  analysis: BatchAnalysis;
  survivalCurveData: ChartDataPoint[];
  scoreDistribution: ChartDataPoint[];
}) => (
  <div className="space-y-6">
    {/* Stats Grid */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard
        title="Survival Rate"
        value={`${(analysis.survival.overallRate * 100).toFixed(1)}%`}
        color={analysis.survival.overallRate > 0.3 ? 'green' : analysis.survival.overallRate > 0.1 ? 'yellow' : 'red'}
      />
      <StatCard
        title="Average Waves"
        value={analysis.survival.averageWaves.toFixed(1)}
        color="cyan"
      />
      <StatCard
        title="Best Score"
        value={analysis.performance.bestScore.toLocaleString()}
        color="purple"
      />
      <StatCard
        title="Fairness Score"
        value={`${(analysis.balance.fairness * 100).toFixed(0)}/100`}
        color={analysis.balance.fairness > 0.8 ? 'green' : analysis.balance.fairness > 0.5 ? 'yellow' : 'red'}
      />
    </div>

    {/* Charts */}
    <div className="grid md:grid-cols-2 gap-6">
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Survival Curve</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={survivalCurveData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="wave" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" unit="%" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
            <Area type="monotone" dataKey="survivalRate" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Score Distribution</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={scoreDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="range" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
            <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>

    {/* Performance Details */}
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Metric label="Avg Score" value={Math.round(analysis.performance.averageScore).toLocaleString()} />
        <Metric label="Avg Kills" value={Math.round(analysis.performance.averageKills)} />
        <Metric label="Avg Duration" value={`${Math.round(analysis.performance.averageDuration)}s`} />
        <Metric label="Median Waves" value={analysis.survival.medianWaves} />
      </div>
    </div>
  </div>
);

const DNATab = ({ analysis, dnaDistributionData }: {
  analysis: BatchAnalysis;
  dnaDistributionData: ChartDataPoint[];
}) => (
  <div className="space-y-6">
    <div className="grid md:grid-cols-2 gap-6">
      {/* DNA Distribution */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">DNA Type Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={dnaDistributionData}
              cx="50%"
              cy="50%"
              outerRadius={100}
              fill="#8884d8"
              dataKey="amount"
              nameKey="type"
              label={({ type, percent }) => `${type}: ${(percent * 100).toFixed(0)}%`}
            >
              {dnaDistributionData.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* DNA Success Correlation */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">DNA Success Rate</h3>
        <div className="space-y-3">
          {Object.entries(analysis.dna.correlationWithSuccess)
            .sort(([, a], [, b]) => b - a)
            .map(([type, rate]) => (
              <div key={type} className="flex items-center gap-3">
                <span className="w-20 text-sm text-slate-300">{type}</span>
                <div className="flex-1 h-6 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-green-500 rounded-full transition-all"
                    style={{ width: `${rate * 100}%` }}
                  />
                </div>
                <span className="w-12 text-sm text-right text-slate-400">{(rate * 100).toFixed(0)}%</span>
              </div>
            ))}
        </div>
      </div>
    </div>

    {/* DNA Insights */}
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">DNA Insights</h3>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="p-4 bg-slate-700/50 rounded-lg">
          <p className="text-sm text-slate-400">Most Acquired</p>
          <p className="text-xl font-bold text-green-400">{analysis.dna.mostAcquired}</p>
        </div>
        <div className="p-4 bg-slate-700/50 rounded-lg">
          <p className="text-sm text-slate-400">Least Acquired</p>
          <p className="text-xl font-bold text-red-400">{analysis.dna.leastAcquired}</p>
        </div>
      </div>
    </div>
  </div>
);

const EvolutionTab = ({ analysis: _analysis, evolutionPathData }: {
  analysis: BatchAnalysis;
  evolutionPathData: ChartDataPoint[];
}) => (
  <div className="space-y-6">
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">Evolution Path Popularity</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={evolutionPathData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis type="number" stroke="#94a3b8" />
          <YAxis dataKey="path" type="category" stroke="#94a3b8" width={80} />
          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
          <Bar dataKey="uses" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>

    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">Path Win Rates</h3>
      <div className="space-y-3">
        {evolutionPathData.map((path) => (
          <div key={path.path} className="flex items-center gap-3">
            <span className="w-24 text-sm text-slate-300">{path.path}</span>
            <div className="flex-1 h-6 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  (path.winRate ?? 0) > 50 ? 'bg-green-500' : (path.winRate ?? 0) > 30 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${path.winRate ?? 0}%` }}
              />
            </div>
            <span className="w-12 text-sm text-right text-slate-400">{(path.winRate ?? 0).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const BalanceTab = ({ analysis }: { analysis: BatchAnalysis }) => (
  <div className="space-y-6">
    {/* Fairness Score */}
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Balance Fairness Score</h3>
        <span className={`text-3xl font-bold ${
          analysis.balance.fairness > 0.8 ? 'text-green-400' :
          analysis.balance.fairness > 0.5 ? 'text-yellow-400' : 'text-red-400'
        }`}>
          {(analysis.balance.fairness * 100).toFixed(0)}/100
        </span>
      </div>
      <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            analysis.balance.fairness > 0.8 ? 'bg-green-500' :
            analysis.balance.fairness > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
          }`}
          style={{ width: `${analysis.balance.fairness * 100}%` }}
        />
      </div>
    </div>

    {/* Recommendations */}
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">Balance Recommendations</h3>
      {analysis.balance.recommendedAdjustments.length === 0 ? (
        <p className="text-green-400 flex items-center gap-2">
          <span>✓</span> No balance issues detected!
        </p>
      ) : (
        <div className="space-y-3">
          {analysis.balance.recommendedAdjustments.map((rec, i) => (
            <RecommendationCard key={i} recommendation={rec} />
          ))}
        </div>
      )}
    </div>

    {/* Difficulty Curve */}
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4">Difficulty Curve Analysis</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={analysis.balance.difficultyCurve}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="wave" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" unit="%" domain={[0, 100]} />
          <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
          <Line type="monotone" dataKey="survivalRate" stroke="#ef4444" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
);

// ============== HELPER COMPONENTS ==============

const StatCard = ({ title, value, color }: { title: string; value: string; color: string }) => {
  const colorClasses: Record<string, string> = {
    green: 'bg-green-500/20 border-green-500/50 text-green-400',
    yellow: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400',
    red: 'bg-red-500/20 border-red-500/50 text-red-400',
    cyan: 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400',
    purple: 'bg-purple-500/20 border-purple-500/50 text-purple-400'
  };

  return (
    <div className={`p-4 rounded-xl border ${colorClasses[color]}`}>
      <p className="text-sm opacity-80">{title}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
};

const Metric = ({ label, value }: { label: string; value: string | number }) => (
  <div className="p-3 bg-slate-700/50 rounded-lg">
    <p className="text-sm text-slate-400">{label}</p>
    <p className="text-lg font-semibold text-white">{value}</p>
  </div>
);

const RecommendationCard = ({ recommendation }: { recommendation: BalanceRecommendation }) => {
  const severityColors = {
    critical: 'bg-red-500/20 border-red-500/50 text-red-400',
    warning: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400',
    info: 'bg-blue-500/20 border-blue-500/50 text-blue-400'
  };

  return (
    <div className={`p-4 rounded-lg border ${severityColors[recommendation.severity]}`}>
      <div className="flex items-start gap-3">
        <span className="text-xl">
          {recommendation.severity === 'critical' ? '🔴' :
           recommendation.severity === 'warning' ? '⚠️' : 'ℹ️'}
        </span>
        <div className="flex-1">
          <p className="font-semibold">{recommendation.issue}</p>
          <p className="text-sm opacity-80 mt-1">→ {recommendation.recommendation}</p>
        </div>
        <span className="text-xs uppercase tracking-wider opacity-60">{recommendation.type}</span>
      </div>
    </div>
  );
};

export default SimulationDashboard;
