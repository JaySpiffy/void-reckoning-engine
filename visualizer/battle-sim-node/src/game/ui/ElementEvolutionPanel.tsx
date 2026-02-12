import { ElementType, ELEMENT_CONFIGS } from '../types';
import type { AbilityType} from '../types/abilities';
import { ABILITY_CONFIGS, getAbilitiesForElement } from '../types/abilities';
import type { AbilitySystem } from '../systems/AbilitySystem';

interface ElementEvolutionPanelProps {
  abilitySystem: AbilitySystem;
  isOpen: boolean;
  onClose: () => void;
}

const ELEMENT_GRADIENTS: Record<ElementType, string> = {
  [ElementType.NONE]: 'from-gray-700 to-gray-800',
  [ElementType.FIRE]: 'from-red-600/20 to-orange-600/20',
  [ElementType.ICE]: 'from-blue-500/20 to-cyan-600/20',
  [ElementType.LIGHTNING]: 'from-yellow-500/20 to-amber-600/20',
  [ElementType.POISON]: 'from-green-600/20 to-emerald-700/20',
  [ElementType.ARCANE]: 'from-purple-600/20 to-fuchsia-700/20',
};

export const ElementEvolutionPanel = ({ abilitySystem, isOpen, onClose }: ElementEvolutionPanelProps) => {
  if (!isOpen) return null;

  const elements = [ElementType.FIRE, ElementType.ICE, ElementType.LIGHTNING, ElementType.POISON, ElementType.ARCANE];

  const getElementIcon = (element: ElementType): string => {
    switch (element) {
      case ElementType.FIRE: return '🔥';
      case ElementType.ICE: return '❄️';
      case ElementType.LIGHTNING: return '⚡';
      case ElementType.POISON: return '☠️';
      case ElementType.ARCANE: return '✨';
      default: return '⚪';
    }
  };

  const getAbilityIcon = (abilityType: AbilityType): string => {
    return ABILITY_CONFIGS[abilityType]?.icon || '?';
  };

  const getAbilityName = (abilityType: AbilityType): string => {
    const config = ABILITY_CONFIGS[abilityType];
    return config?.name || 'Unknown';
  };

  const renderElementTree = (element: ElementType, index: number) => {
    const evolution = abilitySystem.getElementEvolution(element);
    const level = evolution?.level || 0;
    const experience = evolution?.experience || 0;
    const experienceToNext = evolution?.experienceToNext || 100;
    const unlockedAbilities = evolution?.unlockedAbilities || [];

    const abilities = getAbilitiesForElement(element, 3);
    const config = ELEMENT_CONFIGS[element];
    const isMaxLevel = level >= 3;
    const progressPercent = Math.min((experience / experienceToNext) * 100, 100);

    return (
      <div 
        key={element} 
        className={`bg-gradient-to-b ${ELEMENT_GRADIENTS[element]} rounded-xl p-5 border border-gray-700/50 hover:border-gray-600/50 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 animate-card-enter`}
        style={{ animationDelay: `${index * 100}ms` }}
      >
        {/* Element Header */}
        <div className="flex items-center gap-3 mb-5">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center text-3xl transition-transform hover:scale-110"
            style={{ 
              backgroundColor: config.color + '30', 
              border: `2px solid ${config.color}`,
              boxShadow: `0 0 20px ${config.color}40`
            }}
          >
            {getElementIcon(element)}
          </div>
          <div className="flex-1">
            <div className="text-white font-bold text-lg capitalize">{element}</div>
            <div className="text-gray-400 text-xs">{config.description}</div>
          </div>
          {isMaxLevel && (
            <div className="px-2 py-1 bg-yellow-500/20 border border-yellow-500/50 rounded text-yellow-400 text-xs font-bold">
              MAX
            </div>
          )}
        </div>

        {/* Evolution Level */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-400">Evolution Level</span>
            <span className="text-purple-400 font-bold">{level} / 3</span>
          </div>
          <div className="h-3 bg-gray-800 rounded-full overflow-hidden border border-gray-700">
            <div
              className="h-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500 relative"
              style={{ width: `${progressPercent}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-shimmer" />
            </div>
          </div>
          <div className="text-xs text-gray-500 mt-1 text-right">
            {experience} / {experienceToNext} XP
          </div>
        </div>

        {/* Kills Counter */}
        <div className="mb-5 flex items-center gap-2 text-sm bg-black/30 rounded-lg p-2">
          <span className="text-gray-400">Kills:</span>
          <span className="text-yellow-400 font-bold text-lg">{evolution?.killsWithElement || 0}</span>
          <span className="text-gray-500 text-xs ml-auto">with this element</span>
        </div>

        {/* Ability Tree */}
        <div className="space-y-2">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2 font-semibold">Ability Tree</div>
          {abilities.map((abilityType) => {
            const ability = ABILITY_CONFIGS[abilityType];
            const isUnlocked = unlockedAbilities.includes(abilityType);
            const canUnlock = ability.evolutionLevel <= level;
            const isNextUnlock = canUnlock && !isUnlocked;

            return (
              <div
                key={abilityType}
                className={`
                  flex items-center gap-3 p-3 rounded-lg transition-all duration-300
                  ${isUnlocked 
                    ? 'bg-green-900/20 border border-green-700/50 shadow-sm' 
                    : isNextUnlock
                      ? 'bg-yellow-900/10 border border-yellow-700/30'
                      : 'bg-gray-800/30 border border-gray-700/30 opacity-70'
                  }
                `}
              >
                <div
                  className={`
                    w-10 h-10 rounded-lg flex items-center justify-center text-xl transition-all
                    ${isUnlocked 
                      ? 'bg-gradient-to-br from-green-600 to-green-700 shadow-lg' 
                      : isNextUnlock
                        ? 'bg-gradient-to-br from-yellow-600/50 to-yellow-700/50'
                        : 'bg-gray-700'
                    }
                  `}
                >
                  {getAbilityIcon(abilityType)}
                </div>
                <div className="flex-1">
                  <div className={`text-sm font-bold ${isUnlocked ? 'text-white' : isNextUnlock ? 'text-yellow-200' : 'text-gray-500'}`}>
                    {getAbilityName(abilityType)}
                  </div>
                  <div className="text-xs text-gray-500">
                    Lvl {ability.evolutionLevel} • {ability.manaCost} MP • {ability.cooldown}s
                  </div>
                </div>
                {isUnlocked ? (
                  <span className="text-green-400 text-xs font-bold bg-green-900/30 px-2 py-1 rounded">✓</span>
                ) : isNextUnlock ? (
                  <span className="text-yellow-400 text-xs">🔒 {ability.evolutionKillsRequired} kills</span>
                ) : (
                  <span className="text-gray-600 text-xs">🔒 Lvl {ability.evolutionLevel}</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const currentElement = abilitySystem.getCurrentElement();
  const currentConfig = ELEMENT_CONFIGS[currentElement];

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 pointer-events-auto animate-fade-in">
      <div className="bg-gradient-to-b from-gray-900 to-gray-950 rounded-2xl border border-gray-700/50 max-w-5xl w-full max-h-[90vh] overflow-auto p-8 shadow-2xl animate-slide-in">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <span className="text-4xl">✨</span>
              Element Evolution
            </h2>
            <p className="text-gray-400">Kill enemies while using an element to evolve your abilities</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl hover:rotate-90 transition-all duration-300 p-2 hover:bg-white/10 rounded-full"
          >
            ✕
          </button>
        </div>

        {/* Current Element - Enhanced */}
        <div className="mb-8 p-6 rounded-xl bg-gradient-to-r from-purple-900/30 to-transparent border border-purple-700/50 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-shimmer" />
          <div className="relative flex items-center gap-4">
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center text-3xl"
              style={{
                backgroundColor: currentConfig.color + '30',
                border: `3px solid ${currentConfig.color}`,
                boxShadow: `0 0 30px ${currentConfig.color}50`
              }}
            >
              {getElementIcon(currentElement)}
            </div>
            <div>
              <div className="text-purple-400 text-sm uppercase tracking-wider font-semibold mb-1">Current Element</div>
              <div className="text-white font-bold text-2xl capitalize">
                {currentElement}
              </div>
            </div>
          </div>
        </div>

        {/* Element Trees */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {elements.map((element, index) => renderElementTree(element, index))}
        </div>

        {/* Close button */}
        <div className="mt-8 text-center">
          <button
            onClick={onClose}
            className="px-8 py-3 bg-gray-700/80 hover:bg-gray-600 text-white rounded-lg transition-all duration-300 hover:shadow-lg"
          >
            Close (ESC)
          </button>
        </div>
      </div>
    </div>
  );
};
