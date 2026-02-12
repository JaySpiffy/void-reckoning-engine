/**
 * NPC SYSTEM - Enemy Types and Behaviors
 *
 * INTENTION: Different enemy types have different behaviors, loot, and DNA.
 * NPCs should feel distinct and require different strategies.
 *
 * As the game progresses, NPCs should evolve too - becoming more dangerous
 * based on how well the player is doing.
 */

import type { Vector2 } from '../types';
import { Enemy } from '../entities/Enemy';
import { EnemyType, GameEvent, DNAType } from '../types';
import { globalEvents } from '../utils';

// NPC Behavior Types - How enemies act
export enum NPCBehavior {
  AGGRESSIVE = 'aggressive',     // Charges directly at player
  RANGED = 'ranged',             // Keeps distance, shoots
  TANK = 'tank',                 // Slow, high health, blocks
  SWARMER = 'swarmer',           // Fast, weak, attacks in groups
  CASTER = 'caster',             // Uses abilities, teleports
  AMBUSHER = 'ambusher',         // Hides, attacks when close
  BOSS = 'boss',                 // Complex patterns, phases
}

// NPC Stats Template
export interface NPCStats {
  health: number;
  damage: number;
  speed: number;
  attackRange: number;
  attackCooldown: number;
  armor: number;

  // Behavior-specific
  detectionRange: number;
  fleeThreshold: number;  // Health % to flee at
}

// NPC Archetype - Base template for enemy types
export interface NPCArchetype {
  type: EnemyType;
  behavior: NPCBehavior;
  stats: NPCStats;
  dnaType: DNAType;

  // Visual
  color: string;
  size: number;
  particles: string;

  // Abilities
  abilities: string[];

  // Scaling
  levelScaling: {
    healthPerWave: number;
    damagePerWave: number;
    speedPerWave: number;
  };
}

// NPC Archetype Definitions
export const NPC_ARCHETYPES: Record<EnemyType, NPCArchetype> = {
  [EnemyType.GOBLIN]: {
    type: EnemyType.GOBLIN,
    behavior: NPCBehavior.SWARMER,
    stats: {
      health: 30,
      damage: 8,
      speed: 120,
      attackRange: 25,
      attackCooldown: 1,
      armor: 0,
      detectionRange: 400,
      fleeThreshold: 0.3,
    },
    dnaType: DNAType.GRASS,
    color: '#22c55e',
    size: 12,
    particles: 'none',
    abilities: ['quick_attack'],
    levelScaling: {
      healthPerWave: 5,
      damagePerWave: 1,
      speedPerWave: 2,
    },
  },

  [EnemyType.SKELETON]: {
    type: EnemyType.SKELETON,
    behavior: NPCBehavior.AGGRESSIVE,
    stats: {
      health: 40,
      damage: 12,
      speed: 80,
      attackRange: 30,
      attackCooldown: 1.2,
      armor: 2,
      detectionRange: 450,
      fleeThreshold: 0, // Never flees
    },
    dnaType: DNAType.VOID,
    color: '#e5e7eb',
    size: 14,
    particles: 'bone_dust',
    abilities: ['relentless', 'undead_resilience'],
    levelScaling: {
      healthPerWave: 6,
      damagePerWave: 2,
      speedPerWave: 1,
    },
  },

  [EnemyType.ORC]: {
    type: EnemyType.ORC,
    behavior: NPCBehavior.TANK,
    stats: {
      health: 80,
      damage: 20,
      speed: 60,
      attackRange: 35,
      attackCooldown: 1.5,
      armor: 5,
      detectionRange: 350,
      fleeThreshold: 0.2,
    },
    dnaType: DNAType.BEAST,
    color: '#166534',
    size: 18,
    particles: 'none',
    abilities: ['heavy_slam', 'enrage'],
    levelScaling: {
      healthPerWave: 12,
      damagePerWave: 3,
      speedPerWave: 0,
    },
  },

  [EnemyType.DARK_MAGE]: {
    type: EnemyType.DARK_MAGE,
    behavior: NPCBehavior.CASTER,
    stats: {
      health: 50,
      damage: 25,
      speed: 70,
      attackRange: 250,
      attackCooldown: 2,
      armor: 0,
      detectionRange: 500,
      fleeThreshold: 0.4,
    },
    dnaType: DNAType.ARCANE,
    color: '#7c3aed',
    size: 14,
    particles: 'dark_sparks',
    abilities: ['shadow_bolt', 'teleport', 'summon_skeleton'],
    levelScaling: {
      healthPerWave: 4,
      damagePerWave: 4,
      speedPerWave: 1,
    },
  },

  [EnemyType.BOSS]: {
    type: EnemyType.BOSS,
    behavior: NPCBehavior.BOSS,
    stats: {
      health: 500,
      damage: 50,
      speed: 40,
      attackRange: 50,
      attackCooldown: 2,
      armor: 10,
      detectionRange: 600,
      fleeThreshold: 0,
    },
    dnaType: DNAType.CHAOS,
    color: '#dc2626',
    size: 30,
    particles: 'boss_aura',
    abilities: ['phase_shift', 'minion_spawn', 'aoe_slam', 'rage_mode'],
    levelScaling: {
      healthPerWave: 100,
      damagePerWave: 10,
      speedPerWave: 1,
    },
  },

  // NEW ENEMY TYPES - More DNA variety
  
  // Spider - POISON DNA (Early game)
  [EnemyType.SPIDER]: {
    type: EnemyType.SPIDER,
    behavior: NPCBehavior.AMBUSHER,
    stats: {
      health: 25,
      damage: 10,
      speed: 100,
      attackRange: 20,
      attackCooldown: 0.8,
      armor: 0,
      detectionRange: 350,
      fleeThreshold: 0.2,
    },
    dnaType: DNAType.POISON,
    color: '#84cc16',
    size: 10,
    particles: 'web_trails',
    abilities: ['venom_bite', 'web_shot', 'burrow'],
    levelScaling: {
      healthPerWave: 4,
      damagePerWave: 1.5,
      speedPerWave: 2,
    },
  },

  // Wolf - BEAST DNA (Early game, faster)
  [EnemyType.WOLF]: {
    type: EnemyType.WOLF,
    behavior: NPCBehavior.AGGRESSIVE,
    stats: {
      health: 35,
      damage: 12,
      speed: 140,
      attackRange: 25,
      attackCooldown: 0.9,
      armor: 1,
      detectionRange: 450,
      fleeThreshold: 0.25,
    },
    dnaType: DNAType.BEAST,
    color: '#9ca3af',
    size: 13,
    particles: 'fur_trails',
    abilities: ['pack_hunt', 'dash_bite', 'howl'],
    levelScaling: {
      healthPerWave: 5,
      damagePerWave: 2,
      speedPerWave: 3,
    },
  },

  // Manticore - FIRE DNA (Mid game)
  [EnemyType.MANTICORE]: {
    type: EnemyType.MANTICORE,
    behavior: NPCBehavior.AGGRESSIVE,
    stats: {
      health: 70,
      damage: 22,
      speed: 90,
      attackRange: 35,
      attackCooldown: 1.1,
      armor: 3,
      detectionRange: 480,
      fleeThreshold: 0.3,
    },
    dnaType: DNAType.FIRE,
    color: '#ef4444',
    size: 16,
    particles: 'fire_mane',
    abilities: ['fire_breath', 'tail_spike', 'pounce'],
    levelScaling: {
      healthPerWave: 10,
      damagePerWave: 3,
      speedPerWave: 1,
    },
  },

  // Serpent - WATER DNA (Mid game)
  [EnemyType.SERPENT]: {
    type: EnemyType.SERPENT,
    behavior: NPCBehavior.AGGRESSIVE,
    stats: {
      health: 55,
      damage: 18,
      speed: 95,
      attackRange: 30,
      attackCooldown: 1.0,
      armor: 2,
      detectionRange: 420,
      fleeThreshold: 0.15,
    },
    dnaType: DNAType.WATER,
    color: '#3b82f6',
    size: 15,
    particles: 'water_trails',
    abilities: ['constrict', 'water_spit', 'slither'],
    levelScaling: {
      healthPerWave: 7,
      damagePerWave: 2.5,
      speedPerWave: 2,
    },
  },

  // Golem - EARTH DNA (Mid game tank)
  [EnemyType.GOLEM]: {
    type: EnemyType.GOLEM,
    behavior: NPCBehavior.TANK,
    stats: {
      health: 120,
      damage: 15,
      speed: 50,
      attackRange: 40,
      attackCooldown: 1.5,
      armor: 8,
      detectionRange: 380,
      fleeThreshold: 0,
    },
    dnaType: DNAType.EARTH,
    color: '#92400e',
    size: 20,
    particles: 'dust_trails',
    abilities: ['ground_slam', 'rock_throw', 'harden'],
    levelScaling: {
      healthPerWave: 15,
      damagePerWave: 2,
      speedPerWave: 0,
    },
  },

  // Crystal Walker - CRYSTAL DNA (Late game)
  [EnemyType.CRYSTAL_WALKER]: {
    type: EnemyType.CRYSTAL_WALKER,
    behavior: NPCBehavior.CASTER,
    stats: {
      health: 90,
      damage: 28,
      speed: 65,
      attackRange: 200,
      attackCooldown: 1.8,
      armor: 5,
      detectionRange: 500,
      fleeThreshold: 0.35,
    },
    dnaType: DNAType.CRYSTAL,
    color: '#a855f7',
    size: 14,
    particles: 'crystal_shards',
    abilities: ['prism_beam', 'crystal_shield', 'reflect'],
    levelScaling: {
      healthPerWave: 8,
      damagePerWave: 4,
      speedPerWave: 1,
    },
  },

  // Slime Boss - SLIME DNA (Late game)
  [EnemyType.SLIME_BOSS]: {
    type: EnemyType.SLIME_BOSS,
    behavior: NPCBehavior.TANK,
    stats: {
      health: 200,
      damage: 20,
      speed: 55,
      attackRange: 45,
      attackCooldown: 1.3,
      armor: 2,
      detectionRange: 400,
      fleeThreshold: 0,
    },
    dnaType: DNAType.SLIME,
    color: '#ec4899',
    size: 22,
    particles: 'slime_drip',
    abilities: ['split', 'slime_trail', 'absorb', 'acid_pool'],
    levelScaling: {
      healthPerWave: 20,
      damagePerWave: 2,
      speedPerWave: 1,
    },
  },

  // Chimera - CHAOS DNA (Late game)
  [EnemyType.CHIMERA]: {
    type: EnemyType.CHIMERA,
    behavior: NPCBehavior.AGGRESSIVE,
    stats: {
      health: 150,
      damage: 35,
      speed: 85,
      attackRange: 40,
      attackCooldown: 1.0,
      armor: 4,
      detectionRange: 520,
      fleeThreshold: 0.2,
    },
    dnaType: DNAType.CHAOS,
    color: '#7c3aed',
    size: 18,
    particles: 'chaos_mutation',
    abilities: ['random_breath', 'mutation', 'chaos_claw', 'unpredictable'],
    levelScaling: {
      healthPerWave: 12,
      damagePerWave: 3.5,
      speedPerWave: 2,
    },
  },

  // Light Warden - LIGHT DNA (Late game)
  [EnemyType.LIGHT_WARDEN]: {
    type: EnemyType.LIGHT_WARDEN,
    behavior: NPCBehavior.CASTER,
    stats: {
      health: 85,
      damage: 30,
      speed: 75,
      attackRange: 220,
      attackCooldown: 1.5,
      armor: 3,
      detectionRange: 550,
      fleeThreshold: 0.3,
    },
    dnaType: DNAType.LIGHT,
    color: '#fef3c7',
    size: 15,
    particles: 'light_rays',
    abilities: ['holy_bolt', 'blinding_light', 'heal_ally', 'smite'],
    levelScaling: {
      healthPerWave: 6,
      damagePerWave: 3,
      speedPerWave: 1,
    },
  },

  // Storm Bird - WIND DNA (Late game)
  [EnemyType.STORM_BIRD]: {
    type: EnemyType.STORM_BIRD,
    behavior: NPCBehavior.RANGED,
    stats: {
      health: 70,
      damage: 25,
      speed: 130,
      attackRange: 180,
      attackCooldown: 1.2,
      armor: 1,
      detectionRange: 480,
      fleeThreshold: 0.4,
    },
    dnaType: DNAType.WIND,
    color: '#22d3ee',
    size: 13,
    particles: 'wind_feathers',
    abilities: ['dive_attack', 'wind_gust', 'feather_storm', 'sky_dodge'],
    levelScaling: {
      healthPerWave: 5,
      damagePerWave: 2.5,
      speedPerWave: 3,
    },
  },
};

// NPC AI State
export interface NPCState {
  enemy: Enemy;
  archetype: NPCArchetype;

  // AI state
  targetPosition: Vector2 | null;
  isFleeing: boolean;
  abilityCooldowns: Map<string, number>;

  // Boss-specific
  phase: number;
  phaseHealthThresholds: number[];
}

export class NPCSystem {
  private activeNPCs: Map<string, NPCState> = new Map();
  private waveNumber: number = 1;

  /**
   * Spawn an NPC with proper scaling for current wave
   */
  spawnNPC(type: EnemyType, position: Vector2): Enemy {
    const archetype = NPC_ARCHETYPES[type];
    if (!archetype) {
      throw new Error(`Unknown NPC type: ${type}`);
    }

    // Scale stats based on wave
    const scaledStats = this.scaleStats(archetype.stats, archetype.levelScaling);

    // Create enemy
    const enemy = new Enemy({
      position,
      enemyType: type,
    });

    // Apply scaled stats
    enemy.stats.maxHealth = scaledStats.health;
    enemy.stats.health = scaledStats.health;
    enemy.stats.damage = scaledStats.damage;
    enemy.stats.speed = scaledStats.speed;
    enemy.stats.attackRange = scaledStats.attackRange;
    enemy.stats.attackCooldown = scaledStats.attackCooldown;

    // Track NPC state
    const npcState: NPCState = {
      enemy,
      archetype,
      targetPosition: null,
      isFleeing: false,
      abilityCooldowns: new Map(),
      phase: 1,
      phaseHealthThresholds: type === EnemyType.BOSS ? [0.75, 0.5, 0.25] : [],
    };

    this.activeNPCs.set(enemy.id, npcState);

    // Emit spawn event
    globalEvents.emit(GameEvent.NPC_SPAWNED, {
      id: enemy.id,
      type,
      position,
    });

    return enemy;
  }

  /**
   * Scale NPC stats based on current wave
   */
  private scaleStats(baseStats: NPCStats, scaling: NPCArchetype['levelScaling']): NPCStats {
    return {
      ...baseStats,
      health: baseStats.health + (scaling.healthPerWave * this.waveNumber),
      damage: baseStats.damage + (scaling.damagePerWave * this.waveNumber),
      speed: baseStats.speed + (scaling.speedPerWave * this.waveNumber),
    };
  }

  /**
   * Update all NPC AI
   */
  update(deltaTime: number, playerPosition: Vector2): void {
    for (const [id, npc] of this.activeNPCs) {
      if (!npc.enemy.isActive) {
        this.activeNPCs.delete(id);
        continue;
      }

      // Update ability cooldowns
      for (const [ability, cooldown] of npc.abilityCooldowns) {
        if (cooldown > 0) {
          npc.abilityCooldowns.set(ability, cooldown - deltaTime);
        }
      }

      // Run behavior AI
      this.updateBehavior(npc, deltaTime, playerPosition);

      // Check boss phase transitions
      if (npc.archetype.type === EnemyType.BOSS) {
        this.checkBossPhase(npc);
      }
    }
  }

  /**
   * Update NPC behavior based on archetype
   */
  private updateBehavior(npc: NPCState, deltaTime: number, playerPosition: Vector2): void {
    const behavior = npc.archetype.behavior;
    const distanceToPlayer = npc.enemy.distanceTo({ position: playerPosition });
    const healthPercent = npc.enemy.stats.health / npc.enemy.stats.maxHealth;

    // Check flee threshold
    if (healthPercent < npc.archetype.stats.fleeThreshold && !npc.isFleeing) {
      npc.isFleeing = true;
    }

    switch (behavior) {
      case NPCBehavior.AGGRESSIVE:
        this.behaviorAggressive(npc, playerPosition, distanceToPlayer);
        break;

      case NPCBehavior.RANGED:
        this.behaviorRanged(npc, playerPosition, distanceToPlayer);
        break;

      case NPCBehavior.TANK:
        this.behaviorTank(npc, playerPosition, distanceToPlayer);
        break;

      case NPCBehavior.SWARMER:
        this.behaviorSwarmer(npc, playerPosition, distanceToPlayer);
        break;

      case NPCBehavior.CASTER:
        this.behaviorCaster(npc, playerPosition, distanceToPlayer, deltaTime);
        break;

      case NPCBehavior.AMBUSHER:
        this.behaviorAmbusher(npc, playerPosition, distanceToPlayer);
        break;

      case NPCBehavior.BOSS:
        this.behaviorBoss(npc, playerPosition, distanceToPlayer, deltaTime);
        break;
    }
  }

  // Behavior implementations
  private behaviorAggressive(npc: NPCState, playerPosition: Vector2, distance: number): void {
    if (distance > npc.archetype.stats.attackRange) {
      npc.enemy.chase(playerPosition);
    } else {
      npc.enemy.stop();
    }
  }

  private behaviorRanged(npc: NPCState, playerPosition: Vector2, distance: number): void {
    const idealRange = npc.archetype.stats.attackRange * 0.7;

    if (distance > idealRange + 50) {
      npc.enemy.chase(playerPosition);
    } else if (distance < idealRange - 50) {
      // Back away
      const direction = npc.enemy.directionTo({ position: playerPosition });
      npc.enemy.velocity = {
        x: -direction.x * npc.archetype.stats.speed * 0.5,
        y: -direction.y * npc.archetype.stats.speed * 0.5,
      };
    } else {
      npc.enemy.stop();
    }
  }

  private behaviorTank(npc: NPCState, playerPosition: Vector2, distance: number): void {
    // Tanks are slow but relentless
    if (distance > npc.archetype.stats.attackRange) {
      npc.enemy.chase(playerPosition);
    } else {
      npc.enemy.stop();
    }
  }

  private behaviorSwarmer(npc: NPCState, playerPosition: Vector2, distance: number): void {
    if (npc.isFleeing) {
      // Flee when low health
      const direction = npc.enemy.directionTo({ position: playerPosition });
      npc.enemy.velocity = {
        x: -direction.x * npc.archetype.stats.speed * 1.5,
        y: -direction.y * npc.archetype.stats.speed * 1.5,
      };
    } else if (distance > npc.archetype.stats.attackRange) {
      npc.enemy.chase(playerPosition);
    } else {
      npc.enemy.stop();
    }
  }

  private behaviorCaster(npc: NPCState, playerPosition: Vector2, distance: number, _deltaTime: number): void {
    const detectionRange = npc.archetype.stats.detectionRange;

    if (distance > detectionRange) {
      // Wander when player far away
      npc.enemy.wander({
        minX: 0,
        maxX: 2000,
        minY: 0,
        maxY: 2000,
      });
    } else if (distance < 100 && npc.abilityCooldowns.get('teleport')! <= 0) {
      // Teleport away if too close
      this.castAbility(npc, 'teleport', playerPosition);
    } else if (distance > npc.archetype.stats.attackRange) {
      npc.enemy.chase(playerPosition);
    } else {
      npc.enemy.stop();
      // Cast spells
      if (npc.abilityCooldowns.get('shadow_bolt')! <= 0) {
        this.castAbility(npc, 'shadow_bolt', playerPosition);
      }
    }
  }

  private behaviorAmbusher(npc: NPCState, playerPosition: Vector2, distance: number): void {
    const detectionRange = npc.archetype.stats.detectionRange;

    if (distance > detectionRange) {
      // Hide/wait
      npc.enemy.stop();
    } else if (distance < 100) {
      // Ambush attack - sudden burst of speed
      npc.enemy.velocity = {
        x: npc.enemy.directionTo({ position: playerPosition }).x * npc.archetype.stats.speed * 2,
        y: npc.enemy.directionTo({ position: playerPosition }).y * npc.archetype.stats.speed * 2,
      };
    } else {
      npc.enemy.chase(playerPosition);
    }
  }

  private behaviorBoss(npc: NPCState, playerPosition: Vector2, distance: number, _deltaTime: number): void {
    // Bosses have complex patterns based on phase
    const phase = npc.phase;

    switch (phase) {
      case 1: // Normal phase
        if (distance > npc.archetype.stats.attackRange) {
          npc.enemy.chase(playerPosition);
        } else {
          npc.enemy.stop();
        }
        break;

      case 2: // Summon phase
        if (npc.abilityCooldowns.get('minion_spawn')! <= 0) {
          this.castAbility(npc, 'minion_spawn', playerPosition);
        }
        npc.enemy.chase(playerPosition);
        break;

      case 3: // Rage phase
        npc.enemy.chase(playerPosition);
        npc.enemy.stats.speed *= 1.5; // Speed boost
        break;

      case 4: // Desperate phase
        if (npc.abilityCooldowns.get('aoe_slam')! <= 0) {
          this.castAbility(npc, 'aoe_slam', playerPosition);
        }
        break;
    }
  }

  /**
   * Cast an NPC ability
   */
  private castAbility(npc: NPCState, ability: string, targetPosition: Vector2): void {
    // Set cooldown
    npc.abilityCooldowns.set(ability, 5); // 5 second cooldown default

    // Emit ability cast event
    globalEvents.emit(GameEvent.NPC_ABILITY_CAST, {
      npcId: npc.enemy.id,
      ability,
      targetPosition,
    });
  }

  /**
   * Check and handle boss phase transitions
   */
  private checkBossPhase(npc: NPCState): void {
    const healthPercent = npc.enemy.stats.health / npc.enemy.stats.maxHealth;

    for (let i = 0; i < npc.phaseHealthThresholds.length; i++) {
      if (healthPercent <= npc.phaseHealthThresholds[i] && npc.phase === i + 1) {
        npc.phase = i + 2;

        globalEvents.emit(GameEvent.BOSS_PHASE_CHANGE, {
          npcId: npc.enemy.id,
          newPhase: npc.phase,
        });
      }
    }
  }

  /**
   * Set current wave for scaling
   */
  setWave(wave: number): void {
    this.waveNumber = wave;
  }

  /**
   * Get state for a specific NPC
   */
  getNPCState(id: string): NPCState | undefined {
    return this.activeNPCs.get(id);
  }

  /**
   * Get active NPC count
   */
  getActiveCount(): number {
    return this.activeNPCs.size;
  }

  /**
   * Clear all NPCs
   */
  clear(): void {
    this.activeNPCs.clear();
  }
}

export const npcSystem = new NPCSystem();
