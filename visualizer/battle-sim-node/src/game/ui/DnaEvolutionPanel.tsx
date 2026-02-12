import { useState, useEffect } from 'react';
import type { EvolutionPath, Genome } from '../systems/DNACore';
import { dnaSystem } from '../systems/DNASystem';
import { globalEvents } from '../utils';
import { GameEvent } from '../types/events';
import type { DNAType } from '../types';

interface DnaEvolutionPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

// DNA type colors for visual appeal
const DNA_TYPE_COLORS: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  aquatic: { bg: 'bg-blue-900/40', text: 'text-blue-300', border: 'border-blue-500/50', glow: 'shadow-blue-500/20' },
  arcane: { bg: 'bg-purple-900/40', text: 'text-purple-300', border: 'border-purple-500/50', glow: 'shadow-purple-500/20' },
  beast: { bg: 'bg-orange-900/40', text: 'text-orange-300', border: 'border-orange-500/50', glow: 'shadow-orange-500/20' },
  chaos: { bg: 'bg-red-900/40', text: 'text-red-300', border: 'border-red-500/50', glow: 'shadow-red-500/20' },
  crystal: { bg: 'bg-cyan-900/40', text: 'text-cyan-300', border: 'border-cyan-500/50', glow: 'shadow-cyan-500/20' },
  earth: { bg: 'bg-amber-900/40', text: 'text-amber-300', border: 'border-amber-500/50', glow: 'shadow-amber-500/20' },
  fire: { bg: 'bg-red-800/40', text: 'text-red-300', border: 'border-red-500/50', glow: 'shadow-red-500/20' },
  fungus: { bg: 'bg-emerald-900/40', text: 'text-emerald-300', border: 'border-emerald-500/50', glow: 'shadow-emerald-500/20' },
  grass: { bg: 'bg-green-900/40', text: 'text-green-300', border: 'border-green-500/50', glow: 'shadow-green-500/20' },
  ice: { bg: 'bg-sky-900/40', text: 'text-sky-300', border: 'border-sky-500/50', glow: 'shadow-sky-500/20' },
  insect: { bg: 'bg-lime-900/40', text: 'text-lime-300', border: 'border-lime-500/50', glow: 'shadow-lime-500/20' },
  lightning: { bg: 'bg-yellow-900/40', text: 'text-yellow-300', border: 'border-yellow-500/50', glow: 'shadow-yellow-500/20' },
  light: { bg: 'bg-amber-100/10', text: 'text-amber-100', border: 'border-amber-200/30', glow: 'shadow-amber-100/10' },
  mech: { bg: 'bg-slate-800/60', text: 'text-slate-300', border: 'border-slate-500/50', glow: 'shadow-slate-500/20' },
  physical: { bg: 'bg-stone-800/60', text: 'text-stone-300', border: 'border-stone-500/50', glow: 'shadow-stone-500/20' },
  poison: { bg: 'bg-fuchsia-900/40', text: 'text-fuchsia-300', border: 'border-fuchsia-500/50', glow: 'shadow-fuchsia-500/20' },
  reptile: { bg: 'bg-teal-900/40', text: 'text-teal-300', border: 'border-teal-500/50', glow: 'shadow-teal-500/20' },
  slime: { bg: 'bg-pink-900/40', text: 'text-pink-300', border: 'border-pink-500/50', glow: 'shadow-pink-500/20' },
  void: { bg: 'bg-indigo-900/40', text: 'text-indigo-300', border: 'border-indigo-500/50', glow: 'shadow-indigo-500/20' },
  water: { bg: 'bg-blue-800/40', text: 'text-blue-300', border: 'border-blue-500/50', glow: 'shadow-blue-500/20' },
  wind: { bg: 'bg-gray-700/40', text: 'text-gray-300', border: 'border-gray-400/50', glow: 'shadow-gray-400/20' },
};

const getDNAStyles = (type: string) => {
  return DNA_TYPE_COLORS[type.toLowerCase()] || { 
    bg: 'bg-gray-800/60', 
    text: 'text-gray-300', 
    border: 'border-gray-600',
    glow: 'shadow-gray-500/20'
  };
};

export const DnaEvolutionPanel = ({ isOpen, onClose }: DnaEvolutionPanelProps) => {
  const [availableEvolutions, setAvailableEvolutions] = useState<EvolutionPath[]>(() => 
    dnaSystem.getAvailableEvolutionPaths()
  );
  const [currentDna, setCurrentDna] = useState<Genome | null>(() => 
    dnaSystem.getGenome()
  );
  const [animatingCards, setAnimatingCards] = useState<Set<string>>(new Set());

  useEffect(() => {
    const handleEvolutionAvailable = (data: { paths: EvolutionPath[] }) => {
      setAvailableEvolutions(data.paths);
      setCurrentDna(dnaSystem.getGenome());
      // Trigger animation for new cards
      const newCards = new Set(data.paths.map(p => p.id));
      setAnimatingCards(newCards);
      setTimeout(() => setAnimatingCards(new Set()), 500);
    };

    globalEvents.on(GameEvent.EVOLUTION_AVAILABLE, handleEvolutionAvailable);

    return () => {
      globalEvents.off(GameEvent.EVOLUTION_AVAILABLE, handleEvolutionAvailable);
    };
  }, []);

  const handleEvolve = (pathId: string) => {
    dnaSystem.evolve(pathId);
    onClose();
  };

  if (!isOpen || !currentDna) return null;

  const getDnaValue = (type: string) => {
    return currentDna.strands.get(type as DNAType)?.value.toFixed(0) || '0';
  };

  const dnaTypes = Array.from(currentDna.strands.keys());
  const dominantStyles = getDNAStyles(currentDna.dominantType);

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 pointer-events-auto animate-fade-in">
      <div className="bg-gradient-to-b from-gray-900 to-gray-950 rounded-2xl border border-gray-700/50 max-w-5xl w-full max-h-[90vh] overflow-auto p-8 shadow-2xl animate-slide-in">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <span className="text-4xl">🧬</span>
              DNA Evolution
            </h2>
            <p className="text-gray-400">Choose your next form based on your genetic makeup</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl hover:rotate-90 transition-all duration-300 p-2 hover:bg-white/10 rounded-full"
          >
            ✕
          </button>
        </div>

        {/* Current DNA Summary - Enhanced */}
        <div className={`mb-8 p-6 rounded-xl border ${dominantStyles.bg} ${dominantStyles.border} shadow-lg ${dominantStyles.glow} relative overflow-hidden`}>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-shimmer" />
          <div className="relative">
            <div className={`text-sm mb-2 uppercase tracking-widest font-semibold ${dominantStyles.text}`}>Your Genome</div>
            <div className="flex items-center gap-6 mb-4">
              <div className="text-2xl font-bold text-white capitalize">
                Dominant: <span className={dominantStyles.text}>{currentDna.dominantType}</span>
              </div>
              <div className="h-8 w-px bg-white/20" />
              <div className="text-white">
                <span className="text-gray-400">Purity:</span>{' '}
                <span className="font-bold text-green-400">{(currentDna.purity * 100).toFixed(0)}%</span>
              </div>
              <div className="h-8 w-px bg-white/20" />
              <div className="text-white">
                <span className="text-gray-400">Generation:</span>{' '}
                <span className="font-bold text-purple-400">{currentDna.generation}</span>
              </div>
            </div>
            
            {/* DNA Grid */}
            <div className="grid grid-cols-5 md:grid-cols-7 gap-2">
              {dnaTypes.sort().map((type) => {
                const value = parseFloat(getDnaValue(type));
                const styles = getDNAStyles(type);
                const isDominant = type === currentDna.dominantType;
                return (
                  <div 
                    key={type} 
                    className={`flex flex-col items-center p-2 rounded-lg border transition-all duration-300 ${
                      isDominant 
                        ? `${styles.bg} ${styles.border} ${styles.glow} shadow-md` 
                        : 'bg-black/30 border-transparent hover:border-gray-600'
                    }`}
                  >
                    <span className="text-xs text-gray-500 capitalize mb-1">{type}</span>
                    <span className={`text-sm font-bold ${value > 0 ? styles.text : 'text-gray-600'}`}>
                      {getDnaValue(type)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Available Evolutions - Enhanced Cards */}
        <div className="mb-4">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span>Available Evolution Paths</span>
            <span className="text-sm font-normal text-gray-500">({availableEvolutions.length})</span>
          </h3>
          
          {availableEvolutions.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availableEvolutions.map((evo, index) => (
                <div 
                  key={evo.id} 
                  className={`group bg-gradient-to-b from-gray-800/80 to-gray-900/80 rounded-xl p-5 border border-gray-700/50 hover:border-purple-500/50 flex flex-col justify-between transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10 hover:-translate-y-1 ${
                    animatingCards.has(evo.id) ? 'animate-card-enter' : ''
                  }`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div>
                    {/* Evolution Header */}
                    <div className="flex items-center gap-4 mb-4">
                      <div
                        className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl shadow-lg transition-transform duration-300 group-hover:scale-110"
                        style={{ 
                          backgroundColor: evo.appearance.color + '30', 
                          border: `2px solid ${evo.appearance.color}`,
                          boxShadow: `0 0 20px ${evo.appearance.color}40`
                        }}
                      >
                        {evo.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-white font-bold text-lg capitalize group-hover:text-purple-300 transition-colors">
                          {evo.name}
                        </div>
                        <div className="text-gray-400 text-xs leading-relaxed">{evo.description}</div>
                      </div>
                    </div>

                    {/* Bonuses - Visual Stats */}
                    <div className="mb-4 space-y-2">
                      <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Stat Bonuses</div>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="bg-red-900/30 border border-red-700/30 rounded-lg p-2 text-center">
                          <div className="text-red-400 text-lg font-bold">{((evo.bonuses.healthMultiplier - 1) * 100).toFixed(0)}%</div>
                          <div className="text-red-300/70 text-xs">HP</div>
                        </div>
                        <div className="bg-orange-900/30 border border-orange-700/30 rounded-lg p-2 text-center">
                          <div className="text-orange-400 text-lg font-bold">{((evo.bonuses.damageMultiplier - 1) * 100).toFixed(0)}%</div>
                          <div className="text-orange-300/70 text-xs">DMG</div>
                        </div>
                        <div className="bg-blue-900/30 border border-blue-700/30 rounded-lg p-2 text-center">
                          <div className="text-blue-400 text-lg font-bold">{((evo.bonuses.speedMultiplier - 1) * 100).toFixed(0)}%</div>
                          <div className="text-blue-300/70 text-xs">SPD</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Evolve Button */}
                  <button
                    onClick={() => handleEvolve(evo.id)}
                    className="w-full px-4 py-3 bg-gradient-to-r from-purple-700 to-purple-600 hover:from-purple-600 hover:to-purple-500 text-white rounded-lg transition-all duration-300 font-bold shadow-lg shadow-purple-900/30 hover:shadow-purple-900/50 hover:scale-[1.02] active:scale-[0.98]"
                  >
                    Evolve into {evo.name}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-800/30 rounded-xl border border-gray-700/50 border-dashed">
              <div className="text-4xl mb-3">🔬</div>
              <div className="text-gray-400 font-medium">No evolutions available yet</div>
              <div className="text-gray-500 text-sm mt-1">Keep playing to meet the requirements!</div>
            </div>
          )}
        </div>

        {/* Close button */}
        <div className="mt-8 text-center">
          <button
            onClick={onClose}
            className="px-8 py-3 bg-gray-700/80 hover:bg-gray-600 text-white rounded-lg transition-all duration-300 hover:shadow-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
