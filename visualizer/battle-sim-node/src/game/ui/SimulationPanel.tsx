import { useState, useEffect } from 'react';
import { SimulationManager, type SimulationResult, type SimulationConfig } from '../systems/SimulationManager';
import { smartAutoplaySystem } from '../systems/SmartAutoplaySystem';

interface SimulationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SimulationPanel = ({ isOpen, onClose }: SimulationPanelProps) => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [results, setResults] = useState<SimulationResult[]>([]);
  const [currentResult, setCurrentResult] = useState<SimulationResult | null>(null);
  const [config, setConfig] = useState<SimulationConfig>({
    maxDuration: 300,
    maxWave: 15,
    speed: 100,
    useSmartAI: true,
    startWave: 1,
  });
  
  const [simulationManager] = useState(() => new SimulationManager(config));
  
  useEffect(() => {
    return () => {
      if (isSimulating) {
        simulationManager.stop();
      }
    };
  }, [isSimulating, simulationManager]);
  
  const runSingleSimulation = async () => {
    if (isSimulating) return;
    
    setIsSimulating(true);
    setCurrentResult(null);
    
    try {
      const result = await simulationManager.runSimulation();
      setCurrentResult(result);
      setResults(prev => [result, ...prev].slice(0, 10));
    } catch (error) {
      console.error('Simulation failed:', error);
    } finally {
      setIsSimulating(false);
    }
  };
  
  const runBatchSimulations = async (count: number) => {
    if (isSimulating) return;
    
    setIsSimulating(true);
    const batchResults: SimulationResult[] = [];
    
    for (let i = 0; i < count; i++) {
      try {
        const result = await simulationManager.runSimulation();
        batchResults.push(result);
        setCurrentResult(result);
      } catch (error) {
        console.error(`Simulation ${i + 1} failed:`, error);
      }
    }
    
    setResults(prev => [...batchResults, ...prev].slice(0, 50));
    setIsSimulating(false);
  };
  
  const toggleSmartAI = () => {
    const newValue = !config.useSmartAI;
    setConfig({ ...config, useSmartAI: newValue });
    if (newValue) {
      smartAutoplaySystem.enable();
    } else {
      smartAutoplaySystem.disable();
    }
  };
  
  if (!isOpen) return null;
  
  // Calculate statistics from results
  const stats = results.length > 0 ? {
    avgDuration: results.reduce((a, r) => a + r.duration, 0) / results.length,
    avgWaves: results.reduce((a, r) => a + r.wavesCompleted, 0) / results.length,
    avgKills: results.reduce((a, r) => a + r.enemiesKilled, 0) / results.length,
    survivalRate: results.filter(r => r.success).length / results.length,
  } : null;
  
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 pointer-events-auto animate-fade-in">
      <div className="bg-gradient-to-b from-gray-900 to-gray-950 rounded-2xl border border-gray-700/50 max-w-4xl w-full max-h-[90vh] overflow-auto p-8 shadow-2xl">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <span className="text-4xl">🧪</span>
              Simulation Lab
            </h2>
            <p className="text-gray-400">Run automated game simulations for balance testing</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl hover:rotate-90 transition-all duration-300 p-2 hover:bg-white/10 rounded-full"
          >
            ✕
          </button>
        </div>
        
        {/* Configuration */}
        <div className="mb-6 p-4 bg-gray-800/50 rounded-xl border border-gray-700/50">
          <h3 className="text-lg font-bold text-white mb-4">Configuration</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-gray-400 uppercase">Max Duration</label>
              <input
                type="number"
                value={config.maxDuration}
                onChange={(e) => setConfig({ ...config, maxDuration: Number(e.target.value) })}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white"
                disabled={isSimulating}
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Max Wave</label>
              <input
                type="number"
                value={config.maxWave}
                onChange={(e) => setConfig({ ...config, maxWave: Number(e.target.value) })}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white"
                disabled={isSimulating}
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Speed</label>
              <select
                value={config.speed}
                onChange={(e) => setConfig({ ...config, speed: Number(e.target.value) })}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white"
                disabled={isSimulating}
              >
                <option value={10}>10x</option>
                <option value={50}>50x</option>
                <option value={100}>100x</option>
                <option value={500}>500x</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Start Wave</label>
              <input
                type="number"
                value={config.startWave}
                onChange={(e) => setConfig({ ...config, startWave: Number(e.target.value) })}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white"
                disabled={isSimulating}
                min={1}
                max={20}
              />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2">
            <input
              type="checkbox"
              id="smartAI"
              checked={config.useSmartAI}
              onChange={toggleSmartAI}
              className="w-4 h-4"
              disabled={isSimulating}
            />
            <label htmlFor="smartAI" className="text-sm text-gray-300">
              Use Smart AI (auto-evolve, better combat)
            </label>
          </div>
        </div>
        
        {/* Controls */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={runSingleSimulation}
            disabled={isSimulating}
            className="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 text-white rounded-lg font-bold transition-colors"
          >
            {isSimulating ? 'Running...' : '▶ Run Single Simulation'}
          </button>
          <button
            onClick={() => runBatchSimulations(10)}
            disabled={isSimulating}
            className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white rounded-lg font-bold transition-colors"
          >
            {isSimulating ? 'Running...' : '▶▶ Run Batch (10)'}
          </button>
          {isSimulating && (
            <button
              onClick={() => simulationManager.stop()}
              className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg font-bold transition-colors"
            >
              ⏹ Stop
            </button>
          )}
        </div>
        
        {/* Current Result */}
        {currentResult && (
          <div className="mb-6 p-4 bg-green-900/30 border border-green-700/50 rounded-xl">
            <h3 className="text-lg font-bold text-green-400 mb-2">
              {currentResult.success ? '✓ Simulation Complete' : '✗ Simulation Failed'}
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-400">Duration</div>
                <div className="text-white font-bold">{currentResult.duration.toFixed(1)}s</div>
              </div>
              <div>
                <div className="text-gray-400">Waves</div>
                <div className="text-white font-bold">{currentResult.wavesCompleted}</div>
              </div>
              <div>
                <div className="text-gray-400">Kills</div>
                <div className="text-white font-bold">{currentResult.enemiesKilled}</div>
              </div>
              <div>
                <div className="text-gray-400">Evolutions</div>
                <div className="text-white font-bold">{currentResult.evolutionHistory.length}</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Statistics */}
        {stats && (
          <div className="mb-6 p-4 bg-blue-900/30 border border-blue-700/50 rounded-xl">
            <h3 className="text-lg font-bold text-blue-400 mb-3">
              Statistics ({results.length} runs)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-xs text-gray-400 uppercase">Avg Duration</div>
                <div className="text-xl font-bold text-white">{stats.avgDuration.toFixed(1)}s</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-xs text-gray-400 uppercase">Avg Waves</div>
                <div className="text-xl font-bold text-white">{stats.avgWaves.toFixed(1)}</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-xs text-gray-400 uppercase">Avg Kills</div>
                <div className="text-xl font-bold text-white">{stats.avgKills.toFixed(0)}</div>
              </div>
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-xs text-gray-400 uppercase">Survival Rate</div>
                <div className="text-xl font-bold text-white">{(stats.survivalRate * 100).toFixed(0)}%</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Recent Results */}
        {results.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-bold text-white mb-3">Recent Results</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {results.map((result) => (
                <div
                  key={result.id}
                  className="flex items-center gap-4 p-3 bg-gray-800/50 rounded-lg text-sm"
                >
                  <div className={`w-2 h-2 rounded-full ${result.success ? 'bg-green-500' : 'bg-red-500'}`} />
                  <div className="flex-1 grid grid-cols-4 gap-4">
                    <div>
                      <span className="text-gray-400">Duration:</span>{' '}
                      <span className="text-white">{result.duration.toFixed(0)}s</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Waves:</span>{' '}
                      <span className="text-white">{result.wavesCompleted}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Kills:</span>{' '}
                      <span className="text-white">{result.enemiesKilled}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Evos:</span>{' '}
                      <span className="text-white">{result.evolutionHistory.length}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
