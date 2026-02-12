import { EnemyType, GameEvent } from '../types';
import type { Vector2 } from '../types';
import type { Enemy } from '../entities';
import { globalEvents } from '../utils/EventEmitter';
import { randomRange, randomChoice } from '../utils';
import { configManager } from '../managers/ConfigManager';
import { npcSystem } from './NPCSystem';

export interface WaveConfig {
  wave: number;
  enemyCount: number;
  enemyTypes: EnemyType[];
  spawnInterval: number;
  spawnRadius: number;
}

interface SpawnPoint {
  x: number;
  y: number;
}

export class WaveSystem {
  private currentWave: number = 0;
  private isWaveActive: boolean = false;
  private enemiesSpawned: number = 0;
  private enemiesKilled: number = 0;
  private spawnTimer: number = 0;
  private spawnInterval: number = 1;
  private waveConfig: WaveConfig | null = null;

  private spawnPoints: SpawnPoint[] = [];
  private worldBounds: { width: number; height: number } = { width: 2000, height: 2000 };

  private enemyQueue: EnemyType[] = [];
  private activeEnemies: Enemy[] = [];

  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    globalEvents.on(GameEvent.ENEMY_KILLED, () => {
      this.enemiesKilled++;
      this.checkWaveComplete();
    });
  }

  initialize(worldWidth: number, worldHeight: number): void {
    this.worldBounds = { width: worldWidth, height: worldHeight };
    this.generateSpawnPoints();
    npcSystem.setWave(1);
  }

  private generateSpawnPoints(): void {
    // Generate spawn points around the edges of the world
    const margin = 100;
    const points: SpawnPoint[] = [];

    // Top and bottom edges
    for (let x = margin; x < this.worldBounds.width - margin; x += 200) {
      points.push({ x, y: margin });
      points.push({ x, y: this.worldBounds.height - margin });
    }

    // Left and right edges
    for (let y = margin; y < this.worldBounds.height - margin; y += 200) {
      points.push({ x: margin, y });
      points.push({ x: this.worldBounds.width - margin, y });
    }

    this.spawnPoints = points;
  }

  startWave(waveNumber: number): WaveConfig {
    this.currentWave = waveNumber;
    this.isWaveActive = true;
    this.enemiesSpawned = 0;
    this.enemiesKilled = 0;
    npcSystem.setWave(waveNumber);

    // Generate wave configuration
    this.waveConfig = this.generateWaveConfig(waveNumber);
    this.spawnInterval = this.waveConfig.spawnInterval;

    // Build enemy queue
    this.enemyQueue = this.buildEnemyQueue(this.waveConfig);

    globalEvents.emit(GameEvent.WAVE_STARTED, {
      wave: waveNumber,
      enemyCount: this.waveConfig.enemyCount,
    });

    return this.waveConfig;
  }

  private generateWaveConfig(wave: number): WaveConfig {
    const wavesConfig = configManager.get('waves');
    const worldConfig = configManager.get('world');

    // Scale difficulty with wave number
    const enemyCount = wavesConfig.base_enemy_count + Math.floor(wave * wavesConfig.count_increase_per_wave);

    // Determine available enemy types based on wave - MORE VARIETY EARLY
    const availableTypes: EnemyType[] = [EnemyType.GOBLIN];

    // Wave 1+ additions (early variety)
    if (wave >= 1) {
      availableTypes.push(EnemyType.SPIDER);  // POISON
      availableTypes.push(EnemyType.WOLF);    // BEAST
    }
    
    // Wave 2+ additions
    if (wave >= 2) {
      availableTypes.push(EnemyType.SKELETON); // VOID
    }
    
    // Wave 3+ additions (mid game starts earlier)
    if (wave >= 3) {
      availableTypes.push(EnemyType.MANTICORE); // FIRE
      availableTypes.push(EnemyType.SERPENT);   // WATER
    }
    
    // Wave 4+ additions
    if (wave >= 4) {
      availableTypes.push(EnemyType.ORC);       // BEAST (tank)
      availableTypes.push(EnemyType.GOLEM);     // EARTH
    }
    
    // Wave 5+ additions
    if (wave >= 5) {
      availableTypes.push(EnemyType.DARK_MAGE); // ARCANE
    }
    
    // Wave 7+ additions (late game)
    if (wave >= 7) {
      availableTypes.push(EnemyType.CRYSTAL_WALKER); // CRYSTAL
      availableTypes.push(EnemyType.STORM_BIRD);     // WIND
    }
    
    // Wave 9+ additions
    if (wave >= 9) {
      availableTypes.push(EnemyType.SLIME_BOSS);   // SLIME
      availableTypes.push(EnemyType.LIGHT_WARDEN); // LIGHT
      availableTypes.push(EnemyType.CHIMERA);      // CHAOS
    }
    
    // Boss waves
    if (wave >= 10 && wave % 5 === 0) availableTypes.push(EnemyType.BOSS);

    // Spawn interval decreases slightly with waves (faster spawning)
    const spawnInterval = Math.max(
      wavesConfig.min_spawn_interval,
      wavesConfig.base_spawn_interval - wave * wavesConfig.interval_decrease_per_wave
    );

    return {
      wave,
      enemyCount,
      enemyTypes: availableTypes,
      spawnInterval,
      spawnRadius: worldConfig.spawn_max_distance, // Distance from player to spawn
    };
  }

  private buildEnemyQueue(config: WaveConfig): EnemyType[] {
    const queue: EnemyType[] = [];

    // Wave 1: Only goblins
    // Later waves: Mix of enemy types with increasing variety
    for (let i = 0; i < config.enemyCount; i++) {
      // Higher chance for tougher enemies in later waves
      const roll = Math.random();
      let selectedType = config.enemyTypes[0];

      if (config.enemyTypes.length > 1) {
        if (roll < 0.5) {
          selectedType = config.enemyTypes[0]; // Common
        } else if (roll < 0.8 && config.enemyTypes.length > 1) {
          selectedType = config.enemyTypes[1]; // Uncommon
        } else if (roll < 0.95 && config.enemyTypes.length > 2) {
          selectedType = config.enemyTypes[2]; // Rare
        } else if (config.enemyTypes.length > 3) {
          selectedType = config.enemyTypes[3]; // Very rare
        }
      }

      queue.push(selectedType);
    }

    // Shuffle the queue
    for (let i = queue.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [queue[i], queue[j]] = [queue[j], queue[i]];
    }

    return queue;
  }

  update(deltaTime: number, playerPosition: Vector2): Enemy[] {
    const newEnemies: Enemy[] = [];

    if (!this.isWaveActive || this.enemyQueue.length === 0) {
      return newEnemies;
    }

    this.spawnTimer += deltaTime;

    if (this.spawnTimer >= this.spawnInterval) {
      this.spawnTimer = 0;

      const enemyType = this.enemyQueue.shift();
      if (enemyType) {
        const spawnPos = this.getSpawnPosition(playerPosition);
        const enemy = npcSystem.spawnNPC(enemyType, spawnPos);

        this.activeEnemies.push(enemy);
        this.enemiesSpawned++;
        newEnemies.push(enemy);
      }
    }

    return newEnemies;
  }

  private getSpawnPosition(playerPosition: Vector2): Vector2 {
    const worldConfig = configManager.get('world');
    // Find spawn points that are far enough from player
    const minDistance = worldConfig.spawn_min_distance;
    const maxDistance = worldConfig.spawn_max_distance;

    const validPoints = this.spawnPoints.filter(point => {
      const dx = point.x - playerPosition.x;
      const dy = point.y - playerPosition.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      return distance >= minDistance && distance <= maxDistance;
    });

    if (validPoints.length > 0) {
      const point = randomChoice(validPoints);
      return {
        x: point.x + randomRange(-50, 50),
        y: point.y + randomRange(-50, 50),
      };
    }

    // Fallback: random position around player
    const angle = randomRange(0, Math.PI * 2);
    const distance = randomRange(minDistance, maxDistance);
    return {
      x: playerPosition.x + Math.cos(angle) * distance,
      y: playerPosition.y + Math.sin(angle) * distance,
    };
  }

  private checkWaveComplete(): void {
    if (!this.isWaveActive) return;

    const totalEnemies = this.waveConfig?.enemyCount ?? 0;

    if (this.enemiesKilled >= totalEnemies && this.enemyQueue.length === 0) {
      this.completeWave();
    }
  }

  private completeWave(): void {
    this.isWaveActive = false;

    globalEvents.emit(GameEvent.WAVE_COMPLETED, {
      wave: this.currentWave,
    });
  }

  // Getters
  getCurrentWave(): number {
    return this.currentWave;
  }

  isActive(): boolean {
    return this.isWaveActive;
  }

  getEnemiesRemaining(): number {
    return (this.waveConfig?.enemyCount ?? 0) - this.enemiesKilled;
  }

  getSpawnProgress(): number {
    if (!this.waveConfig) return 0;
    return this.enemiesSpawned / this.waveConfig.enemyCount;
  }

  getKillProgress(): number {
    if (!this.waveConfig) return 0;
    return this.enemiesKilled / this.waveConfig.enemyCount;
  }

  getActiveEnemies(): Enemy[] {
    return this.activeEnemies.filter(e => e.isActive);
  }

  removeEnemy(enemy: Enemy): void {
    const index = this.activeEnemies.indexOf(enemy);
    if (index > -1) {
      this.activeEnemies.splice(index, 1);
    }
  }

  clear(): void {
    this.isWaveActive = false;
    this.enemyQueue = [];
    this.activeEnemies = [];
    this.currentWave = 0;
  }
}

export const waveSystem = new WaveSystem();
