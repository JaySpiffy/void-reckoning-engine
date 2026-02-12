/**
 * SIMULATION MANAGER - Headless Game Runner
 * 
 * Runs the game without rendering for high-speed simulation.
 * Used for balance testing, AI training, and data collection.
 */

import { GameManager } from '../managers/GameManager';
import { GamePhase } from '../types';
import { smartAutoplaySystem } from './SmartAutoplaySystem';
import { entityManager } from '../managers/EntityManager';
import { combatSystem } from './CombatSystem';
import { waveSystem } from './WaveSystem';
import { npcSystem } from './NPCSystem';
import { abilitySystem } from './AbilitySystem';
import { dnaSystem } from './DNASystem';
import { simulationLogger } from './SimulationLogger';
import { simulationMetrics } from './SimulationMetrics';
import { simulationReplay } from './SimulationReplay';

import { globalEvents } from '../utils';
import type { DNAType } from '../types';
import { GameEvent } from '../types';

export interface SimulationConfig {
  /** How long to run (in seconds of game time) */
  maxDuration: number;
  /** Maximum wave to reach */
  maxWave: number;
  /** Simulation speed multiplier (1 = real-time, 100 = 100x) */
  speed: number;
  /** Whether to use smart AI */
  useSmartAI: boolean;
  /** Starting wave */
  startWave: number;
  /** RNG seed for reproducibility */
  seed?: number;
  /** Whether to record a replay */
  recordReplay?: boolean;
  /** Session ID for grouping simulations */
  sessionId?: string;
}

export interface SimulationResult {
  /** Unique simulation ID */
  id: string;
  /** Configuration used */
  config: SimulationConfig;
  /** How long the simulation ran */
  duration: number;
  /** Waves completed */
  wavesCompleted: number;
  /** Total enemies killed */
  enemiesKilled: number;
  /** Final score */
  score: number;
  /** DNA acquired by type */
  dnaAcquired: Record<DNAType, number>;
  /** Evolution history */
  evolutionHistory: Array<{ wave: number; path: string; name: string }>;
  /** Final player stats */
  finalStats: {
    health: number;
    maxHealth: number;
    damage: number;
    speed: number;
    level: number;
  };
  /** Cause of death (if died) */
  causeOfDeath?: string;
  /** Whether simulation completed successfully */
  success: boolean;
  /** Number of mutations purchased (tracked by AI) */
  mutationsPurchased?: number;
  /** Number of buildings constructed (tracked by AI) */
  buildingsConstructed?: number;
  /** Replay ID if recorded */
  replayId?: string;
  /** Session ID */
  sessionId?: string;
}

const DEFAULT_CONFIG: SimulationConfig = {
  maxDuration: 600, // 10 minutes game time
  maxWave: 20,
  speed: 100, // 100x speed
  useSmartAI: true,
  startWave: 1,
};

export class SimulationManager {
  private gameManager: GameManager | null = null;
  private config: SimulationConfig;
  private isRunning: boolean = false;
  private result: Partial<SimulationResult> = {};

  private gameTime: number = 0;
  private evolutionHistory: Array<{ wave: number; path: string; name: string }> = [];
  private enemiesKilled: number = 0;
  private mutationsPurchased: number = 0;
  private buildingsConstructed: number = 0;
  
  constructor(config: Partial<SimulationConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.setupEventListeners();
  }
  
  private setupEventListeners(): void {
    // Track enemy kills
    globalEvents.on(GameEvent.ENEMY_KILLED, () => {
      this.enemiesKilled++;
    });
    
    // Track evolutions
    globalEvents.on(GameEvent.EVOLUTION_COMPLETE, (data: { to: string; generation: number }) => {
      const wave = waveSystem.getCurrentWave();
      this.evolutionHistory.push({
        wave,
        path: data.to,
        name: data.to,
      });
    });
    
    // Track mutations
    globalEvents.on(GameEvent.MUTATION_APPLIED, () => {
      this.mutationsPurchased++;
    });
    
    // Track buildings
    globalEvents.on(GameEvent.ENTITY_CREATED, (data: { type: string }) => {
      if (data.type === 'building') {
        this.buildingsConstructed++;
      }
    });
  }
  
  /**
   * Run a single simulation
   */
  async runSimulation(): Promise<SimulationResult> {
    if (this.isRunning) {
      throw new Error('Simulation already running');
    }
    
    this.isRunning = true;
    this.result = {
      id: this.generateId(),
      config: { ...this.config },
      duration: 0,
      success: false,
    };
    this.gameTime = 0;  // Reset game time
    this.evolutionHistory = [];
    this.enemiesKilled = 0;
    this.mutationsPurchased = 0;
    this.buildingsConstructed = 0;
    
    // Start metrics collection if part of a session
    if (this.config.sessionId) {
      simulationMetrics.startSession(this.config.sessionId);
    }
    
    // Start replay recording if enabled
    let replayId: string | undefined;
    if (this.config.recordReplay) {
      replayId = simulationReplay.startRecording({
        speed: this.config.speed,
        useSmartAI: this.config.useSmartAI,
        maxDuration: this.config.maxDuration,
      });
    }
    
    try {
      // Create a dummy canvas for GameManager
      const canvas = this.createDummyCanvas();
      
      // Initialize game
      this.gameManager = new GameManager({ canvas });
      
      // Enable smart autoplay
      if (this.config.useSmartAI) {
        smartAutoplaySystem.enable();
      }
      
      // Start the game
      this.gameManager.start();
      
      // Jump to starting wave if needed
      if (this.config.startWave > 1) {
        waveSystem.startWave(this.config.startWave);
      }
      
      // Run simulation loop
      await this.runSimulationLoop();
      
      // Collect final results
      const finalResult = this.collectResults();
      
      // Add replay ID and session ID
      finalResult.replayId = replayId;
      finalResult.sessionId = this.config.sessionId;
      
      // Stop replay recording
      if (this.config.recordReplay && replayId) {
        simulationReplay.stopRecording({
          wavesCompleted: finalResult.wavesCompleted,
          score: finalResult.score,
          success: finalResult.success,
          causeOfDeath: finalResult.causeOfDeath,
        });
      }
      
      // Log to session
      if (this.config.sessionId) {
        simulationLogger.logResult(finalResult);
        simulationMetrics.endSession(finalResult);
      }
      
      return finalResult;
      
    } catch (error) {
      console.error('[Simulation] Error:', error);
      return this.collectResults(String(error));
    } finally {
      this.cleanup();
    }
  }
  
  /**
   * Main simulation loop - runs at high speed
   */
  private async runSimulationLoop(): Promise<void> {
    return new Promise((resolve) => {
      let lastTime = performance.now();
      const timeStep = 1 / 60; // Fixed 60 FPS logic
      
      const loop = () => {
        if (!this.isRunning || !this.gameManager) {
          resolve();
          return;
        }
        
        const now = performance.now();
        const realDelta = (now - lastTime) / 1000;
        lastTime = now;
        
        // Scale time by simulation speed
        const gameDelta = realDelta * this.config.speed;
        this.gameTime += gameDelta;
        
        // Check end conditions
        if (this.shouldEndSimulation()) {
          resolve();
          return;
        }
        
        // Run game update multiple times for high speed simulation
        const steps = Math.min(Math.ceil(this.config.speed), 100); // Cap at 100 steps per frame
        for (let i = 0; i < steps; i++) {
          this.updateGame(timeStep);
        }
        
        // Schedule next frame
        requestAnimationFrame(loop);
      };
      
      loop();
    });
  }
  
  /**
   * Update game state one step
   */
  private updateGame(deltaTime: number): void {
    if (!this.gameManager) return;
    
    // Get current state
    const player = entityManager.getPlayer();
    const enemies = entityManager.getEnemies();
    const phase = this.gameManager.getPhase();
    
    if (phase !== GamePhase.PLAYING || !player) return;
    
    // Update smart autoplay
    if (this.config.useSmartAI) {
      smartAutoplaySystem.update(deltaTime, player, enemies);
      
      // Apply AI inputs
      const moveVector = smartAutoplaySystem.getMovementVector();
      player.setMovement(moveVector);
      
      const targetPos = smartAutoplaySystem.getTargetPosition();
      
      // Handle attacks
      if (smartAutoplaySystem.shouldAttack()) {
        // Trigger basic attack
      }
      
      // Handle abilities
      const abilitySlot = smartAutoplaySystem.getAbilitySlotToUse();
      if (abilitySlot > 0) {
        abilitySystem.useAbilitySlot(abilitySlot, targetPos);
      }
    }
    
    // Update all systems
    combatSystem.update(deltaTime, player, enemies);
    waveSystem.update(deltaTime, player.position);
    npcSystem.update(deltaTime, player.position);
    abilitySystem.update(deltaTime);
    
    // Update entities
    entityManager.update(deltaTime);
    
    // Record metrics snapshot
    if (this.config.sessionId) {
      const genome = dnaSystem.getGenome();
      const dnaDistribution = {} as Record<DNAType, number>;
      for (const [type, strand] of genome.strands) {
        dnaDistribution[type] = strand.value;
      }
      
      simulationMetrics.recordSnapshot({
        timestamp: Date.now(),
        gameTime: this.gameTime,
        wave: waveSystem.getCurrentWave(),
        playerHealth: player.stats.health,
        playerPosition: { x: player.position.x, y: player.position.y },
        enemyCount: enemies.length,
        dnaDistribution,
        activeAbilities: [],
      });
    }
    
    // Record replay frame
    if (this.config.recordReplay && this.config.sessionId) {
      const genome = dnaSystem.getGenome();
      const dnaDistribution = {} as Record<DNAType, number>;
      for (const [type, strand] of genome.strands) {
        dnaDistribution[type] = strand.value;
      }
      
      simulationReplay.recordFrame(this.gameTime, {
        wave: waveSystem.getCurrentWave(),
        player: {
          position: { x: player.position.x, y: player.position.y },
          health: player.stats.health,
          maxHealth: player.stats.maxHealth,
          mana: player.stats.mana,
          level: player.stats.level,
          dna: dnaDistribution,
          dominantType: genome.dominantType,
          purity: genome.purity,
        },
        enemies: enemies.map(e => ({
          id: e.id,
          type: e.type,
          position: { x: e.position.x, y: e.position.y },
          health: e.stats.health,
        })),
        buildings: entityManager.getBuildings().map(b => ({
          id: b.id,
          type: b.type,
          position: { x: b.position.x, y: b.position.y },
          health: b.health,
        })),
        resources: { wood: 0, stone: 0, gold: 0, mana: 0 }, // TODO: Get from game state
        mutations: this.mutationsPurchased,
        evolutionPaths: this.evolutionHistory.map(e => e.path),
        aiDecisions: [],
      });
    }
  }
  
  /**
   * Check if simulation should end
   */
  private shouldEndSimulation(): boolean {
    if (!this.gameManager) return true;
    
    const phase = this.gameManager.getPhase();
    const currentWave = waveSystem.getCurrentWave();
    
    // End if game over
    if (phase === GamePhase.GAME_OVER) {
      return true;
    }
    
    // End if max duration reached
    if (this.gameTime >= this.config.maxDuration) {
      return true;
    }
    
    // End if max wave reached
    if (currentWave >= this.config.maxWave) {
      return true;
    }
    
    return false;
  }
  
  /**
   * Collect final simulation results
   */
  private collectResults(causeOfDeath?: string): SimulationResult {
    const player = entityManager.getPlayer();
    const genome = dnaSystem.getGenome();
    
    // Build DNA acquired record
    const dnaAcquired: Record<DNAType, number> = {} as Record<DNAType, number>;
    for (const [type, strand] of genome.strands) {
      dnaAcquired[type] = strand.value;
    }
    
    return {
      id: this.result.id || this.generateId(),
      config: this.result.config || this.config,
      duration: this.gameTime,
      wavesCompleted: waveSystem.getCurrentWave(),
      enemiesKilled: this.enemiesKilled,
      mutationsPurchased: this.mutationsPurchased,
      buildingsConstructed: this.buildingsConstructed,
      score: 0, // TODO: Get from game state
      dnaAcquired,
      evolutionHistory: this.evolutionHistory,
      finalStats: player ? {
        health: player.stats.health,
        maxHealth: player.stats.maxHealth,
        damage: player.stats.damage,
        speed: player.stats.speed,
        level: player.stats.level,
      } : {
        health: 0,
        maxHealth: 0,
        damage: 0,
        speed: 0,
        level: 0,
      },
      causeOfDeath,
      success: !causeOfDeath,
    };
  }
  
  /**
   * Cleanup after simulation
   */
  private cleanup(): void {
    this.isRunning = false;
    smartAutoplaySystem.disable();
    
    if (this.gameManager) {
      this.gameManager.destroy();
      this.gameManager = null;
    }
    
    // Clear entities
    entityManager.clear();
    combatSystem.clear();
    waveSystem.clear();
    npcSystem.clear();
  }
  
  /**
   * Create a dummy canvas for headless operation
   */
  private createDummyCanvas(): HTMLCanvasElement {
    // In browser, create a small off-screen canvas
    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 600;
    return canvas;
  }
  
  /**
   * Generate unique simulation ID
   */
  private generateId(): string {
    return `sim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Check if simulation is running
   */
  getRunningState(): boolean {
    return this.isRunning;
  }
  
  /**
   * Stop current simulation
   */
  stop(): void {
    this.isRunning = false;
  }
}

export const simulationManager = new SimulationManager();
