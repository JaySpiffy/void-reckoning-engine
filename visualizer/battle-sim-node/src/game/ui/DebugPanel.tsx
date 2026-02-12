import { useState, useEffect } from 'react';
import { combatSystem } from '../systems/CombatSystem';
import { abilitySystem } from '../systems/AbilitySystem';
import { entityManager } from '../managers/EntityManager';
import { waveSystem } from '../systems/WaveSystem';
import { inputSystem } from '../systems/InputSystem';
import { lootSystem } from '../systems/LootSystem';
import { dnaSystem } from '../systems/DNASystem';
import { Enemy } from '../entities/Enemy';
import { EnemyType, DNAType } from '../types';
import { GameEvent, ElementType } from '../types';
import { globalEvents } from '../utils';
import { logger, LogCategory } from '../managers/LogManager';
import type { GameManager } from '../managers/GameManager';

interface DebugPanelProps {
  gameManager?: GameManager | null;
}

export const DebugPanel = (_props: DebugPanelProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [playerPos, setPlayerPos] = useState({ x: 0, y: 0 });
  const [enemyCount, setEnemyCount] = useState(0);
  const [projectileCount, setProjectileCount] = useState(0);
  const [isMouseDown, setIsMouseDown] = useState(false);

  // Listen for toggle event
  useEffect(() => {
    const handleToggle = () => {
      setIsVisible(prev => !prev);
    };
    globalEvents.on(GameEvent.TOGGLE_DEBUG_PANEL, handleToggle);
    return () => globalEvents.off(GameEvent.TOGGLE_DEBUG_PANEL, handleToggle);
  }, []);

  const addLog = (msg: string) => {
    setLogs(prev => [msg, ...prev].slice(0, 10));
    logger.debug(LogCategory.SYSTEM, msg);
  };

  // Update stats every frame
  useEffect(() => {
    const interval = setInterval(() => {
      const player = entityManager.getPlayer();
      if (player) {
        setPlayerPos({ x: Math.floor(player.position.x), y: Math.floor(player.position.y) });
      }
      setEnemyCount(entityManager.getEnemies().length);
      setProjectileCount(combatSystem.getProjectiles().length);
      setIsMouseDown(inputSystem.isMouseDown());
    }, 100);
    return () => clearInterval(interval);
  }, []);

  const spawnEnemy = (type: EnemyType) => {
    const player = entityManager.getPlayer();
    if (!player) {
      addLog('No player! Start game first.');
      return;
    }

    // Spawn enemy near player but not on top
    const angle = Math.random() * Math.PI * 2;
    const distance = 200 + Math.random() * 200;
    const enemy = new Enemy({
      position: {
        x: player.position.x + Math.cos(angle) * distance,
        y: player.position.y + Math.sin(angle) * distance,
      },
      enemyType: type,
    });
    entityManager.addEntity(enemy);
    addLog(`Spawned ${type}`);
  };

  const testAttack = () => {
    const player = entityManager.getPlayer();
    if (!player) {
      addLog('No player! Start game first.');
      return;
    }

    // Fire projectile in random direction
    const angle = Math.random() * Math.PI * 2;
    const targetPos = {
      x: player.position.x + Math.cos(angle) * 300,
      y: player.position.y + Math.sin(angle) * 300,
    };

    combatSystem.playerAttack(player, targetPos);
    addLog(`Attack fired! Projectiles: ${combatSystem.getProjectiles().length}`);
  };

  const testAbility = (slot: number) => {
    const player = entityManager.getPlayer();
    if (!player) {
      addLog('No player! Start game first.');
      return;
    }

    const angle = Math.random() * Math.PI * 2;
    const targetPos = {
      x: player.position.x + Math.cos(angle) * 300,
      y: player.position.y + Math.sin(angle) * 300,
    };

    const result = abilitySystem.useAbilitySlot(slot, targetPos);
    addLog(`Ability slot ${slot}: ${result ? 'SUCCESS' : 'FAILED'}`);
  };

  const setElement = (element: ElementType) => {
    const player = entityManager.getPlayer();
    if (!player) {
      addLog('No player! Start game first.');
      return;
    }
    player.setElement(element, 60);
    globalEvents.emit(GameEvent.ELEMENT_CHANGED, { element, duration: 60 });
    addLog(`Set element to ${element}`);
  };

  const killAllEnemies = () => {
    const enemies = entityManager.getEnemies();
    enemies.forEach(e => e.takeDamage(9999));
    addLog(`Killed ${enemies.length} enemies`);
  };

  const clearProjectiles = () => {
    combatSystem.clear();
    addLog('Cleared all projectiles');
  };

  const startWave = (waveNum: number) => {
    waveSystem.startWave(waveNum);
    addLog(`Started wave ${waveNum}`);
  };

  const healPlayer = () => {
    const player = entityManager.getPlayer();
    if (player) {
      player.stats.health = player.stats.maxHealth;
      player.stats.mana = player.stats.maxMana;
      addLog('Player healed');
    }
  };

  const levelUpPlayer = () => {
    const player = entityManager.getPlayer();
    if (player) {
      player.gainExperience(player.stats.experienceToNext);
      addLog('Player leveled up!');
    }
  };

  const toggleTestingMode = () => {
    const newState = !lootSystem.isTestingMode();
    lootSystem.setTestingMode(newState);
    addLog(`Testing mode ${newState ? 'ENABLED' : 'DISABLED'}`);
  };

  const setLootMultiplier = (multiplier: number) => {
    lootSystem.setScaling({ dropRateMultiplier: multiplier });
    addLog(`Loot drop rate: ${multiplier}x`);
  };

  const unlockAllContent = () => {
    // Max out player stats
    const player = entityManager.getPlayer();
    if (player) {
      player.stats.maxHealth = 9999;
      player.stats.health = 9999;
      player.stats.maxMana = 9999;
      player.stats.mana = 9999;
      player.stats.damage = 500;
      player.stats.speed = 15;
      player.stats.attackSpeed = 5;
      player.stats.attackRange = 300;
      
      // Max level
      player.stats.level = 50;
      player.stats.experience = 0;
      player.stats.experienceToNext = 99999;
      
      addLog('Player stats MAXED!');
    }
    
    // Unlock all abilities
    abilitySystem.unlockAllAbilities();
    addLog('All abilities unlocked!');
    
    // Enable extreme loot
    lootSystem.setTestingMode(true);
    lootSystem.setScaling({ 
      dropRateMultiplier: 10, 
      rarityWeightMultiplier: 5,
      dnaAmountMultiplier: 5,
      itemCountMultiplier: 3
    });
    addLog('EXTREME LOOT MODE!');
    
    // Jump to wave 10 to see all enemy types
    waveSystem.startWave(10);
    addLog('Jumped to Wave 10 - All enemy types unlocked!');
  };

  const giveAllDNA = () => {
    const dnaTypes = Object.values(DNAType);
    dnaTypes.forEach((type, index) => {
      setTimeout(() => {
        dnaSystem.absorbDNA(type, 80, 'loot');
        addLog(`Gave 80 ${type} DNA`);
      }, index * 100);
    });
  };

  if (!isVisible) {
    return (
      <button
        className="fixed bottom-4 right-4 z-50 bg-gray-800 text-white px-3 py-2 rounded text-sm"
        style={{ pointerEvents: 'auto' }}
        onClick={() => setIsVisible(true)}
      >
        Show Debug
      </button>
    );
  }

  return (
    <div
      className="fixed bottom-4 right-4 z-50 bg-black/90 border border-gray-600 rounded-lg p-4 w-80 max-h-[70vh] overflow-y-auto"
      style={{ pointerEvents: 'auto' }}
    >
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-white font-bold">Debug Panel</h3>
        <button
          className="text-gray-400 hover:text-white"
          onClick={() => setIsVisible(false)}
        >
          ✕
        </button>
      </div>

      {/* Stats */}
      <div className="mb-4 p-2 bg-gray-800 rounded text-xs text-gray-300">
        <div>Player: ({playerPos.x}, {playerPos.y})</div>
        <div>Enemies: {enemyCount}</div>
        <div>Projectiles: {projectileCount}</div>
        <div>Mouse: {isMouseDown ? 'DOWN' : 'UP'}</div>
      </div>

      {/* Attack Tests */}
      <div className="mb-4">
        <h4 className="text-yellow-400 font-bold text-sm mb-2">Attack Tests</h4>
        <div className="grid grid-cols-2 gap-2">
          <button
            className="bg-red-600 hover:bg-red-500 text-white px-2 py-1 rounded text-xs"
            onClick={testAttack}
          >
            Fire Projectile
          </button>
          <button
            className="bg-orange-600 hover:bg-orange-500 text-white px-2 py-1 rounded text-xs"
            onClick={clearProjectiles}
          >
            Clear Projectiles
          </button>
        </div>
      </div>

      {/* Ability Tests */}
      <div className="mb-4">
        <h4 className="text-blue-400 font-bold text-sm mb-2">Ability Tests (Slots 1-5)</h4>
        <div className="grid grid-cols-5 gap-1 mb-2">
          {[1, 2, 3, 4, 5].map(slot => (
            <button
              key={slot}
              className="bg-blue-600 hover:bg-blue-500 text-white px-1 py-2 rounded text-xs font-bold"
              onClick={() => testAbility(slot)}
            >
              {slot}
            </button>
          ))}
        </div>
        <button
          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white px-2 py-1 rounded text-xs"
          onClick={() => {
            abilitySystem.unlockAllAbilities();
            addLog('All abilities unlocked!');
          }}
        >
          Unlock All Abilities
        </button>
      </div>

      {/* Element Tests */}
      <div className="mb-4">
        <h4 className="text-purple-400 font-bold text-sm mb-2">Set Element</h4>
        <div className="grid grid-cols-3 gap-1">
          {[
            { type: ElementType.NONE, label: 'None', color: 'bg-gray-600' },
            { type: ElementType.FIRE, label: 'Fire', color: 'bg-red-600' },
            { type: ElementType.ICE, label: 'Ice', color: 'bg-blue-600' },
            { type: ElementType.LIGHTNING, label: 'Light', color: 'bg-yellow-600' },
            { type: ElementType.POISON, label: 'Poison', color: 'bg-green-600' },
            { type: ElementType.ARCANE, label: 'Arcane', color: 'bg-purple-600' },
          ].map(({ type, label, color }) => (
            <button
              key={type}
              className={`${color} hover:opacity-80 text-white px-1 py-1 rounded text-xs`}
              onClick={() => setElement(type)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Spawn Enemies */}
      <div className="mb-4">
        <h4 className="text-green-400 font-bold text-sm mb-2">Spawn Enemies</h4>
        <div className="grid grid-cols-3 gap-1 text-xs">
          {[
            { type: EnemyType.GOBLIN, label: 'Goblin', dna: 'GRASS' },
            { type: EnemyType.SPIDER, label: 'Spider', dna: 'POISON' },
            { type: EnemyType.WOLF, label: 'Wolf', dna: 'BEAST' },
            { type: EnemyType.SKELETON, label: 'Skeleton', dna: 'VOID' },
            { type: EnemyType.MANTICORE, label: 'Manticore', dna: 'FIRE' },
            { type: EnemyType.SERPENT, label: 'Serpent', dna: 'WATER' },
            { type: EnemyType.ORC, label: 'Orc', dna: 'BEAST' },
            { type: EnemyType.GOLEM, label: 'Golem', dna: 'EARTH' },
            { type: EnemyType.DARK_MAGE, label: 'Mage', dna: 'ARCANE' },
            { type: EnemyType.CRYSTAL_WALKER, label: 'Crystal', dna: 'CRYSTAL' },
            { type: EnemyType.STORM_BIRD, label: 'Storm', dna: 'WIND' },
            { type: EnemyType.CHIMERA, label: 'Chimera', dna: 'CHAOS' },
          ].map(({ type, label }) => (
            <button
              key={type}
              className="bg-green-700 hover:bg-green-600 text-white px-1 py-1 rounded text-xs"
              onClick={() => spawnEnemy(type)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Wave Control */}
      <div className="mb-4">
        <h4 className="text-cyan-400 font-bold text-sm mb-2">Wave Control</h4>
        <div className="grid grid-cols-4 gap-1">
          {[1, 2, 3, 5].map(wave => (
            <button
              key={wave}
              className="bg-cyan-700 hover:bg-cyan-600 text-white px-1 py-1 rounded text-xs"
              onClick={() => startWave(wave)}
            >
              W{wave}
            </button>
          ))}
        </div>
      </div>

      {/* Player Cheats */}
      <div className="mb-4">
        <h4 className="text-pink-400 font-bold text-sm mb-2">Player Cheats</h4>
        <div className="grid grid-cols-2 gap-1">
          <button
            className="bg-pink-700 hover:bg-pink-600 text-white px-1 py-1 rounded text-xs"
            onClick={healPlayer}
          >
            Heal/Full Mana
          </button>
          <button
            className="bg-pink-700 hover:bg-pink-600 text-white px-1 py-1 rounded text-xs"
            onClick={levelUpPlayer}
          >
            Level Up
          </button>
        </div>
      </div>

      {/* Fast Forward Mode */}
      <div className="mb-4">
        <h4 className="text-pink-400 font-bold text-sm mb-2">🚀 Fast Forward</h4>
        <button
          className="w-full mb-2 px-2 py-2 rounded text-xs font-bold bg-pink-600 hover:bg-pink-500 text-white"
          onClick={unlockAllContent}
        >
          UNLOCK ALL CONTENT
        </button>
        <button
          className="w-full px-2 py-2 rounded text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white"
          onClick={giveAllDNA}
        >
          Give All DNA Types
        </button>
      </div>

      {/* Simulation Lab */}
      <div className="mb-4">
        <h4 className="text-indigo-400 font-bold text-sm mb-2">🧪 Simulation Lab</h4>
        <button
          className="w-full mb-2 px-2 py-2 rounded text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white"
          onClick={() => globalEvents.emit(GameEvent.OPEN_SIMULATION_PANEL, {})}
        >
          Open Simulation Lab
        </button>
        <button
          className="w-full px-2 py-2 rounded text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white"
          onClick={() => globalEvents.emit(GameEvent.OPEN_SIMULATION_DASHBOARD, {})}
        >
          📊 Analytics Dashboard
        </button>
      </div>

      {/* Loot Scaling */}
      <div className="mb-4">
        <h4 className="text-amber-400 font-bold text-sm mb-2">Loot Scaling</h4>
        <button
          className={`w-full mb-2 px-2 py-2 rounded text-xs font-bold transition-colors ${
            lootSystem.isTestingMode() 
              ? 'bg-green-600 hover:bg-green-500 text-white' 
              : 'bg-gray-600 hover:bg-gray-500 text-white'
          }`}
          onClick={toggleTestingMode}
        >
          {lootSystem.isTestingMode() ? '✓ Testing Mode ON' : 'Testing Mode OFF'}
        </button>
        <div className="grid grid-cols-3 gap-1">
          {[1, 5, 10].map(multiplier => (
            <button
              key={multiplier}
              className="bg-amber-700 hover:bg-amber-600 text-white px-1 py-1 rounded text-xs"
              onClick={() => setLootMultiplier(multiplier)}
            >
              {multiplier}x Drops
            </button>
          ))}
        </div>
      </div>

      {/* Enemy Control */}
      <div className="mb-4">
        <button
          className="w-full bg-red-800 hover:bg-red-700 text-white px-2 py-2 rounded text-xs font-bold"
          onClick={killAllEnemies}
        >
          KILL ALL ENEMIES
        </button>
      </div>

      {/* Logs */}
      <div className="mt-4">
        <h4 className="text-gray-400 font-bold text-sm mb-2">Recent Logs</h4>
        <div className="bg-gray-900 rounded p-2 text-xs font-mono h-32 overflow-y-auto">
          {logs.length === 0 && <div className="text-gray-600">No actions yet...</div>}
          {logs.map((log, i) => (
            <div key={i} className="text-gray-300 mb-1">{log}</div>
          ))}
        </div>
      </div>
    </div>
  );
};
