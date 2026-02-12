import { useState, useEffect } from 'react';
import type { GameManager } from '../managers/GameManager';
import type { GameState, PlayerStats, Resources } from '../types';
import { GamePhase, type BuildingType, ElementType, ELEMENT_CONFIGS } from '../types';
import { GameEvent } from '../types/events';
import { ActionBar } from './ActionBar';
import { ElementEvolutionPanel } from './ElementEvolutionPanel';
import { DnaEvolutionPanel } from './DnaEvolutionPanel';
import { MutationShopUI } from './MutationShopUI';
import { BuildMenu } from './BuildMenu';
import { DebugPanel } from './DebugPanel';
import { KeybindingSettings } from './KeybindingSettings';
import { LootNotifications } from './LootNotifications';
import { SimulationPanel } from './SimulationPanel';
import { SimulationDashboard } from './SimulationDashboard';
import { NameEntryModal } from './NameEntryModal';
import { Leaderboard } from './Leaderboard';
import { abilitySystem } from '../systems/AbilitySystem';
import { buildingSystem } from '../systems/BuildingSystem';
import { autoplaySystem } from '../systems/AutoplaySystem';

import { keybindingSystem, BindableAction } from '../systems/KeybindingSystem';
import { globalEvents } from '../utils';

interface GameUIProps {
  gameState: GameState;
  playerStats: PlayerStats | null;
  resources: Resources;
  phase: GamePhase;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onRestart: () => void;
  gameManager: GameManager | null;
}

const ELEMENT_NAMES: Record<ElementType, string> = {
  [ElementType.NONE]: 'None',
  [ElementType.FIRE]: 'Fire',
  [ElementType.ICE]: 'Ice',
  [ElementType.LIGHTNING]: 'Lightning',
  [ElementType.POISON]: 'Poison',
  [ElementType.ARCANE]: 'Arcane',
};

const ELEMENT_ICONS: Record<ElementType, string> = {
  [ElementType.NONE]: '⚪',
  [ElementType.FIRE]: '🔥',
  [ElementType.ICE]: '❄️',
  [ElementType.LIGHTNING]: '⚡',
  [ElementType.POISON]: '☠️',
  [ElementType.ARCANE]: '✨',
};

export const GameUI = ({
  gameState,
  playerStats,
  resources,
  phase,
  onStart,
  onPause,
  onResume,
  onRestart,
  gameManager,
}: GameUIProps) => {
  const [showEvolutionPanel, setShowEvolutionPanel] = useState(false);
  const [showDnaPanel, setShowDnaPanel] = useState(false);
  const [showMutationShop, setShowMutationShop] = useState(false);
  const [showBuildMenu, setShowBuildMenu] = useState(false);
  const [activeBuildingType, setActiveBuildingType] = useState<BuildingType | null>(null);
  const [showKeybindingSettings, setShowKeybindingSettings] = useState(false);
  const [showSimulationPanel, setShowSimulationPanel] = useState(false);
  const [showSimulationDashboard, setShowSimulationDashboard] = useState(false);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [showNameEntry, setShowNameEntry] = useState(false);
  const [playerName, setPlayerName] = useState('');
  const [autoplayEnabled, setAutoplayEnabled] = useState(() => autoplaySystem.isEnabled());
  const [, forceUpdate] = useState({});

  // Force update for cooldown animations
  useEffect(() => {
    if (phase === GamePhase.PLAYING) {
      const interval = setInterval(() => {
        forceUpdate({});
      }, 50);
      return () => clearInterval(interval);
    }
  }, [phase]);

  // Show name entry when game over
  useEffect(() => {
    if (phase === GamePhase.GAME_OVER) {
      setShowNameEntry(true);
    }
  }, [phase]);

  // Start keybinding system when playing
  useEffect(() => {
    if (phase === GamePhase.PLAYING) {
      keybindingSystem.startListening();
    } else {
      keybindingSystem.stopListening();
    }

    return () => {
      keybindingSystem.stopListening();
    };
  }, [phase]);

  // Handle keybinding events
  useEffect(() => {
    const handleKeybindingPress = (data: { action: BindableAction; pressed: boolean }) => {
      if (phase !== GamePhase.PLAYING || !data.pressed) return;

      const slot = keybindingSystem.getAbilitySlot(data.action);
      if (slot !== null && gameManager) {
        const worldPos = gameManager.screenToWorld(gameManager.getLastMousePosition());
        abilitySystem.useAbilitySlot(slot, worldPos);
      }

      if (data.action === BindableAction.OPEN_EVOLUTION) {
        setShowEvolutionPanel(prev => !prev);
      }

      if (data.action === BindableAction.TOGGLE_BUILD_MODE) {
        setShowBuildMenu(prev => !prev);
      }

      if (data.action === BindableAction.PAUSE) {
        onPause();
      }

      if (data.action === BindableAction.TOGGLE_DEBUG) {
        globalEvents.emit(GameEvent.TOGGLE_DEBUG_PANEL, {});
      }
    };

    globalEvents.on(GameEvent.KEYBINDING_PRESSED, handleKeybindingPress);
    return () => {
      globalEvents.off(GameEvent.KEYBINDING_PRESSED, handleKeybindingPress);
    };
  }, [phase, gameManager, onPause]);

  // Handle Mouse Click for Building Placement
  useEffect(() => {
    if (!activeBuildingType || !gameManager) return;

    const handleMouseDown = () => {
      const mousePos = gameManager.getLastMousePosition();
      const worldPos = gameManager.screenToWorld(mousePos);
      
      const success = buildingSystem.placeBuilding(activeBuildingType, worldPos, resources);
      if (success) {
        setActiveBuildingType(null);
      }
    };

    window.addEventListener('mousedown', handleMouseDown);
    return () => window.removeEventListener('mousedown', handleMouseDown);
  }, [activeBuildingType, gameManager, resources, setActiveBuildingType]);

  // Listen for DNA evolution availability
  useEffect(() => {
    const handleEvolutionAvailable = () => {
      setShowDnaPanel(true);
    };

    globalEvents.on(GameEvent.EVOLUTION_AVAILABLE, handleEvolutionAvailable);
    return () => {
      globalEvents.off(GameEvent.EVOLUTION_AVAILABLE, handleEvolutionAvailable);
    };
  }, []);

  // Listen for simulation panel open
  useEffect(() => {
    const handleOpenSimulation = () => {
      setShowSimulationPanel(true);
    };

    const handleOpenDashboard = () => {
      setShowSimulationDashboard(true);
    };

    globalEvents.on(GameEvent.OPEN_SIMULATION_PANEL, handleOpenSimulation);
    globalEvents.on(GameEvent.OPEN_SIMULATION_DASHBOARD, handleOpenDashboard);
    return () => {
      globalEvents.off(GameEvent.OPEN_SIMULATION_PANEL, handleOpenSimulation);
      globalEvents.off(GameEvent.OPEN_SIMULATION_DASHBOARD, handleOpenDashboard);
    };
  }, []);

  // Sync autoplay state periodically (for when F9 is pressed)
  useEffect(() => {
    if (phase !== GamePhase.PLAYING) return;
    const interval = setInterval(() => {
      setAutoplayEnabled(autoplaySystem.isEnabled());
    }, 100);
    return () => clearInterval(interval);
  }, [phase]);

  // Legacy keyboard shortcuts (fallback)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Start game with space in menu
      if (e.key === ' ' && phase === GamePhase.MENU) {
        onStart();
        return;
      }

      if (phase !== GamePhase.PLAYING) return;

      // Fallback for keys not in keybinding system
      if (e.key === 'Escape' || e.key === 'p' || e.key === 'P') {
        if (activeBuildingType) {
          setActiveBuildingType(null);
          return;
        }
        onPause();
      }

      // DNA Panel hotkey
      if (e.key === 'y' || e.key === 'Y') {
        setShowDnaPanel(prev => !prev);
      }

      // Mutation Shop hotkey
      if (e.key === 'm' || e.key === 'M') {
        setShowMutationShop(prev => !prev);
      }

      // Autoplay toggle (F9) - sync UI state
      if (e.key === 'F9') {
        setAutoplayEnabled(autoplaySystem.isEnabled());
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [phase, onPause, onStart, activeBuildingType, setActiveBuildingType]);

  const renderMenu = () => (
    <div className="absolute inset-0 flex items-center justify-center bg-black/80" style={{ zIndex: 100 }}>
      <div className="text-center max-w-2xl px-4">
        <h1 className="text-6xl font-bold text-white mb-4">Darwin's Island ReHelixed</h1>
        <p className="text-gray-300 mb-6 text-xl">Master the elements. Evolve your power. Survive.</p>

        <div className="bg-black/50 rounded-lg p-4 mb-8 text-left">
          <div className="text-gray-400 text-sm mb-3">Controls:</div>
          <div className="grid grid-cols-2 gap-2 text-sm text-gray-300">
            <div><span className="text-yellow-400">WASD</span> - Move</div>
            <div><span className="text-yellow-400">1-5</span> - Use Abilities</div>
            <div><span className="text-yellow-400">Mouse</span> - Aim</div>
            <div><span className="text-yellow-400">T</span> - Ability Evolution</div>
            <div><span className="text-yellow-400">Y</span> - DNA Evolution</div>
            <div><span className="text-yellow-400">ESC/P</span> - Pause</div>
            <div><span className="text-yellow-400">SPACE</span> - Start</div>
            <div><span className="text-yellow-400">F9</span> - Toggle Autoplay</div>
          </div>
        </div>

        <div className="flex justify-center gap-4 mb-8">
          <div className="text-center">
            <div className="text-3xl mb-1">🔥❄️⚡</div>
            <div className="text-xs text-gray-500">5 Elements</div>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-1">⚔️🛡️✨</div>
            <div className="text-xs text-gray-500">15 Abilities</div>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-1">📈🎯🏆</div>
            <div className="text-xs text-gray-500">Evolve & Survive</div>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <button
            onClick={onStart}
            className="px-10 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white text-xl font-bold rounded-lg transition-all transform hover:scale-105 cursor-pointer shadow-lg"
            style={{ pointerEvents: 'auto' }}
          >
            Start Game
          </button>
          <button
            onClick={() => setShowLeaderboard(true)}
            className="px-8 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white text-lg font-bold rounded-lg transition-all transform hover:scale-105 cursor-pointer shadow-lg"
            style={{ pointerEvents: 'auto' }}
          >
            🏆 Leaderboard
          </button>
        </div>
      </div>
    </div>
  );

  const renderPaused = () => (
    <div className="absolute inset-0 flex items-center justify-center bg-black/60" style={{ zIndex: 100 }}>
      <div className="text-center">
        <h2 className="text-4xl font-bold text-white mb-4">Paused</h2>
        <button
          onClick={onResume}
          className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white text-lg font-bold rounded-lg transition-colors cursor-pointer"
          style={{ pointerEvents: 'auto' }}
        >
          Resume
        </button>
      </div>
    </div>
  );

  const renderGameOver = () => (
    <div className="absolute inset-0 flex items-center justify-center bg-black/80" style={{ zIndex: 100 }}>
      <div className="text-center">
        <h2 className="text-5xl font-bold text-red-500 mb-4">Game Over</h2>
        <div className="text-white mb-6">
          <p className="text-2xl">Wave Reached: {gameState.wave}</p>
          <p className="text-2xl">Score: {gameState.score}</p>
          <p className="text-xl text-gray-400">
            Survived: {Math.floor(gameState.gameTime)}s
          </p>
        </div>
        <div className="flex gap-4 justify-center">
          <button
            onClick={onRestart}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white text-xl font-bold rounded-lg transition-colors cursor-pointer"
            style={{ pointerEvents: 'auto' }}
          >
            Play Again
          </button>
          <button
            onClick={() => setShowLeaderboard(true)}
            className="px-6 py-4 bg-yellow-600 hover:bg-yellow-700 text-white text-xl font-bold rounded-lg transition-colors cursor-pointer"
            style={{ pointerEvents: 'auto' }}
          >
            🏆 Leaderboard
          </button>
        </div>
      </div>
    </div>
  );

  const renderElementIndicator = () => {
    if (!playerStats) return null;

    const element = playerStats.element;
    const config = ELEMENT_CONFIGS[element];
    const hasElement = element !== ElementType.NONE;
    const evolution = abilitySystem.getElementEvolution(element);

    return (
      <div
        className="absolute top-20 left-4 bg-black/70 px-4 py-2 rounded-lg flex items-center gap-3 border border-gray-700"
        style={{ zIndex: 50 }}
      >
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-xl"
          style={{
            backgroundColor: hasElement ? config.color : '#4b5563',
            boxShadow: hasElement ? `0 0 15px ${config.color}` : 'none'
          }}
        >
          {ELEMENT_ICONS[element]}
        </div>
        <div>
          <div className="text-white font-bold">{ELEMENT_NAMES[element]}</div>
          {hasElement && evolution && (
            <div className="text-xs">
              <span className="text-purple-400">Level {evolution.level}</span>
              <span className="text-gray-500"> • </span>
              <span className="text-gray-400">{Math.ceil(playerStats.elementDuration)}s</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderHUD = () => (
    <>
      {/* Top Bar - Wave & Score */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-start" style={{ zIndex: 50 }}>
        <div className="flex gap-4">
          {/* Wave Indicator - Enhanced */}
          <div className="bg-gradient-to-r from-gray-900 to-gray-800 px-5 py-3 rounded-xl border border-yellow-600/50 shadow-lg shadow-yellow-500/10">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🌊</span>
              <div>
                <div className="text-xs text-yellow-500/70 uppercase tracking-wider font-semibold">Current Wave</div>
                <div className="text-2xl font-bold text-yellow-400 leading-none">{gameState.wave}</div>
              </div>
            </div>
          </div>
          {/* Score Indicator - Enhanced */}
          <div className="bg-gradient-to-r from-gray-900 to-gray-800 px-5 py-3 rounded-xl border border-white/20 shadow-lg">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⭐</span>
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Score</div>
                <div className="text-2xl font-bold text-white leading-none">{gameState.score.toLocaleString()}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setShowBuildMenu(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors cursor-pointer font-bold"
            style={{ pointerEvents: 'auto' }}
          >
            🏗️ Build (B)
          </button>
          <button
            onClick={() => setShowDnaPanel(true)}
            className="px-4 py-2 bg-purple-700 hover:bg-purple-600 text-white rounded-lg transition-colors cursor-pointer font-bold"
            style={{ pointerEvents: 'auto' }}
          >
            🧬 DNA (Y)
          </button>
          <button
            onClick={() => setShowMutationShop(true)}
            className="px-4 py-2 bg-pink-700 hover:bg-pink-600 text-white rounded-lg transition-colors cursor-pointer font-bold"
            style={{ pointerEvents: 'auto' }}
          >
            ⚛️ Mutation (M)
          </button>
          <button
            onClick={() => setShowEvolutionPanel(true)}
            className="px-4 py-2 bg-blue-700 hover:bg-blue-600 text-white rounded-lg transition-colors cursor-pointer font-bold"
            style={{ pointerEvents: 'auto' }}
          >
            ✨ Ability (T)
          </button>
          <button
            onClick={onPause}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors cursor-pointer"
            style={{ pointerEvents: 'auto' }}
          >
            Pause
          </button>

          <button
            onClick={() => setShowKeybindingSettings(true)}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors cursor-pointer"
            style={{ pointerEvents: 'auto' }}
            title="Keybindings"
          >
            ⚙️
          </button>
        </div>
      </div>

      {/* Element Indicator */}
      {renderElementIndicator()}

      {/* Bottom Left - Player Stats */}
      {playerStats && (
        <div className="absolute bottom-32 left-4 bg-black/70 p-4 rounded-lg min-w-[200px] border border-gray-700" style={{ zIndex: 50 }}>
          {/* Health Bar */}
          <div className="mb-3">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-red-400 font-bold">Health</span>
              <span className="text-white">
                {Math.floor(playerStats.health)}/{playerStats.maxHealth}
              </span>
            </div>
            <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden border border-gray-700">
              <div
                className="h-full bg-gradient-to-r from-red-600 to-red-400 transition-all duration-200"
                style={{
                  width: `${(playerStats.health / playerStats.maxHealth) * 100}%`,
                }}
              />
            </div>
          </div>

          {/* Experience Bar - Enhanced */}
          <div className="relative">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-purple-400 font-bold flex items-center gap-1">
                <span className="text-lg">📈</span>
                Level {playerStats.level}
              </span>
              <span className="text-purple-300/70 text-xs">
                {Math.floor(playerStats.experience)}/{playerStats.experienceToNext} XP
              </span>
            </div>
            <div className="w-full h-2.5 bg-gray-800 rounded-full overflow-hidden border border-gray-700 relative">
              {/* Background shimmer */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-shimmer" />
              {/* XP fill */}
              <div
                className="h-full bg-gradient-to-r from-purple-600 via-purple-400 to-purple-300 transition-all duration-300 relative"
                style={{
                  width: `${(playerStats.experience / playerStats.experienceToNext) * 100}%`,
                  boxShadow: '0 0 10px rgba(168, 85, 247, 0.5)',
                }}
              >
                <div className="absolute inset-0 bg-white/20 animate-pulse" />
              </div>
            </div>
            {/* Level up indicator */}
            {playerStats.experience / playerStats.experienceToNext > 0.9 && (
              <div className="absolute -right-1 -top-1 w-3 h-3 bg-purple-400 rounded-full animate-pulse shadow-lg shadow-purple-500" />
            )}
          </div>

          {/* Stats Grid - Enhanced with icons */}
          <div className="mt-3 pt-3 border-t border-gray-700/50 grid grid-cols-2 gap-2 text-sm">
            <div className="flex items-center gap-2 bg-black/20 rounded-lg p-2">
              <span className="text-red-400">⚔️</span>
              <div>
                <div className="text-gray-500 text-xs">Damage</div>
                <div className="text-white font-bold">{Math.floor(playerStats.damage)}</div>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-black/20 rounded-lg p-2">
              <span className="text-blue-400">💨</span>
              <div>
                <div className="text-gray-500 text-xs">Speed</div>
                <div className="text-white font-bold">{playerStats.speed}</div>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-black/20 rounded-lg p-2">
              <span className="text-yellow-400">⚡</span>
              <div>
                <div className="text-gray-500 text-xs">Attack Speed</div>
                <div className="text-white font-bold">{playerStats.attackSpeed.toFixed(1)}/s</div>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-black/20 rounded-lg p-2">
              <span className="text-green-400">🎯</span>
              <div>
                <div className="text-gray-500 text-xs">Range</div>
                <div className="text-white font-bold">{playerStats.attackRange}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Right - Resources - Enhanced */}
      <div className="absolute bottom-32 right-4 bg-gradient-to-br from-gray-900/90 to-black/90 p-4 rounded-xl border border-gray-700/50 shadow-xl" style={{ zIndex: 50 }}>
        <div className="grid grid-cols-2 gap-x-4 gap-y-3">
          <div className="flex items-center gap-2 bg-yellow-900/20 rounded-lg p-2 border border-yellow-700/30">
            <span className="text-lg">🪙</span>
            <div>
              <div className="text-yellow-600 text-xs">Gold</div>
              <div className="text-yellow-400 font-bold">{resources.gold}</div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-amber-900/20 rounded-lg p-2 border border-amber-700/30">
            <span className="text-lg">🪵</span>
            <div>
              <div className="text-amber-600 text-xs">Wood</div>
              <div className="text-amber-500 font-bold">{resources.wood}</div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg p-2 border border-gray-600/30">
            <span className="text-lg">🪨</span>
            <div>
              <div className="text-gray-500 text-xs">Stone</div>
              <div className="text-gray-400 font-bold">{resources.stone}</div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-blue-900/20 rounded-lg p-2 border border-blue-700/30">
            <span className="text-lg">💎</span>
            <div>
              <div className="text-blue-500 text-xs">Mana</div>
              <div className="text-blue-400 font-bold">{resources.mana}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Bar */}
      {playerStats && (
        <ActionBar
          abilitySystem={abilitySystem}
          currentMana={playerStats.mana}
          maxMana={playerStats.maxMana}
          currentElement={playerStats.element}
          gameManager={gameManager}
        />
      )}

      {/* Keybinding Settings */}
      <KeybindingSettings
        key={showKeybindingSettings ? 'open' : 'closed'}
        isOpen={showKeybindingSettings}
        onClose={() => setShowKeybindingSettings(false)}
      />

      {/* Evolution Panel */}
      {showEvolutionPanel && (
        <ElementEvolutionPanel
          abilitySystem={abilitySystem}
          isOpen={showEvolutionPanel}
          onClose={() => setShowEvolutionPanel(false)}
        />
      )}

      {/* Build Menu */}
      {showBuildMenu && (
        <BuildMenu
          isOpen={showBuildMenu}
          onClose={() => setShowBuildMenu(false)}
          resources={resources}
          onSelect={(type) => {
            setActiveBuildingType(type);
            setShowBuildMenu(false);
          }}
        />
      )}

      {/* DNA Panel */}
      {showDnaPanel && (
        <DnaEvolutionPanel
          isOpen={showDnaPanel}
          onClose={() => setShowDnaPanel(false)}
        />
      )}

      {/* Mutation Shop */}
      {showMutationShop && (
        <MutationShopUI
          isOpen={showMutationShop}
          onClose={() => setShowMutationShop(false)}
        />
      )}

      {/* Building Placement UI */}
      {activeBuildingType && (
        <div className="absolute top-1/4 left-1/2 transform -translate-x-1/2 bg-blue-600/80 text-white px-6 py-3 rounded-full font-bold animate-bounce" style={{ zIndex: 100 }}>
          Click on the Map to place {activeBuildingType.replace('_', ' ')} (ESC to cancel)
        </div>
      )}
    </>
  );

  return (
    <div className="relative w-full h-full" style={{ pointerEvents: 'none' }}>
      {phase === GamePhase.MENU && renderMenu()}
      {phase === GamePhase.PAUSED && renderPaused()}
      {phase === GamePhase.GAME_OVER && renderGameOver()}
      {(phase === GamePhase.PLAYING || phase === GamePhase.PAUSED) && renderHUD()}

      {/* Loot Notifications */}
      <LootNotifications />

      {/* Simulation Panel */}
      <SimulationPanel
        isOpen={showSimulationPanel}
        onClose={() => setShowSimulationPanel(false)}
      />
      <SimulationDashboard
        isOpen={showSimulationDashboard}
        onClose={() => setShowSimulationDashboard(false)}
      />

      {/* Center Screen - Autoplay Toggle */}
      <div 
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-40"
        style={{ pointerEvents: 'auto' }}
      >
        <button
          onClick={() => {
            const newState = autoplaySystem.toggle();
            setAutoplayEnabled(newState);
          }}
          className={`px-6 py-3 rounded-full transition-all duration-300 cursor-pointer font-bold shadow-lg hover:shadow-xl hover:scale-105 ${
            autoplayEnabled 
              ? 'bg-green-600 hover:bg-green-500 text-white shadow-green-900/50' 
              : 'bg-gray-700 hover:bg-gray-600 text-gray-200 shadow-gray-900/50'
          }`}
          title="Toggle Autoplay (F9)"
        >
          <span className="flex items-center gap-2">
            <span className="text-xl">{autoplayEnabled ? '🤖' : '👤'}</span>
            <span>{autoplayEnabled ? 'Auto ON' : 'Auto OFF'}</span>
          </span>
        </button>
      </div>

      {/* Debug Panel - Bottom right */}
      <DebugPanel gameManager={gameManager} />

      {/* Name Entry Modal */}
      {showNameEntry && phase === GamePhase.GAME_OVER && (
        <NameEntryModal
          score={gameState.score}
          gameMode="survival"
          metadata={{
            wavesSurvived: gameState.wave,
            timeAlive: Math.floor(gameState.gameTime),
          }}
          onSubmit={(name) => {
            setPlayerName(name);
            setShowNameEntry(false);
          }}
          onSkip={() => setShowNameEntry(false)}
        />
      )}

      {/* Leaderboard Modal */}
      {showLeaderboard && (
        <Leaderboard
          gameMode="survival"
          limit={10}
          onClose={() => setShowLeaderboard(false)}
          highlightPlayer={playerName}
        />
      )}
    </div>
  );
};
