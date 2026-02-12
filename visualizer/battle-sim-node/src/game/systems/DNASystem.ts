/**
 * DNA SYSTEM - Core Evolution Mechanics
 *
 * INTENTION: This system tracks the player's genetic makeup across multiple
 * elemental/physical traits. As you consume loot from different sources,
 * your DNA shifts toward those elements, unlocking new evolution paths.
 *
 * DNA is NOT just a currency - it's your character's fundamental nature.
 * High Fire DNA makes you vulnerable to Ice but resistant to Grass.
 * Your appearance, abilities, and available evolutions all derive from DNA.
 */

import { globalEvents } from '../utils';
import { GameEvent, DNAType } from '../types';
import {
  type DNAStrand,
  type Genome,
  type EvolutionPath,
  type BattleRoyaleStats
} from './DNACore';
import { logger, LogCategory } from '../managers/LogManager';

// Import the complete evolution tree from EvolutionTree.ts
import { COMPLETE_EVOLUTION_TREE } from './EvolutionTree';

// Re-export for backward compatibility
export const EVOLUTION_PATHS = COMPLETE_EVOLUTION_TREE;

export class DNASystem {
  private genome: Genome;
  private currentForm: string = 'base';
  private killHistory: Array<{ dna: DNAType; timestamp: number }> = [];
  private lootHistory: Array<{ dna: DNAType; amount: number; timestamp: number }> = [];
  
  // Track which evolution paths have been offered to prevent spam
  private offeredEvolutions: Set<string> = new Set();
  private lastEvolutionCheck: number = 0;
  private readonly EVOLUTION_COOLDOWN = 5000; // 5 seconds between checks

  constructor() {
    this.genome = this.createBaseGenome();
  }

  private createBaseGenome(): Genome {
    const strands = new Map<DNAType, DNAStrand>();

    // Initialize all DNA types at 0
    for (const type of Object.values(DNAType)) {
      strands.set(type, {
        type,
        value: 0,
        stability: 0.8,
        mutations: 0,
      });
    }

    return {
      strands,
      dominantType: DNAType.FIRE,
      purity: 0,
      generation: 0,
      mutationPoints: 0,
    };
  }

  /**
   * Absorb DNA from loot/kills
   * This is the PRIMARY way DNA changes - you become what you consume
   */
  absorbDNA(type: DNAType, amount: number, source: 'loot' | 'kill'): void {
    const strand = this.genome.strands.get(type);
    if (!strand) return;

    // Record for history tracking
    if (source === 'kill') {
      this.killHistory.push({ dna: type, timestamp: Date.now() });
    } else {
      this.lootHistory.push({ dna: type, amount, timestamp: Date.now() });
    }

    // Apply DNA with diminishing returns as you get more pure
    const purityFactor = 1 - (this.genome.purity * 0.5);
    const actualGain = amount * purityFactor;

    strand.value = Math.min(100, strand.value + actualGain);

    // Other DNA types decay slightly (you're becoming MORE of this type)
    for (const [otherType, otherStrand] of this.genome.strands) {
      if (otherType !== type && otherStrand.value > 0) {
        otherStrand.value = Math.max(0, otherStrand.value - (actualGain * 0.1));
      }
    }

    this.recalculateDominantType();
    this.checkForEvolution();
  }

  /**
   * Recalculate which DNA type is dominant
   * This determines your current elemental affinity
   */
  private recalculateDominantType(): void {
    let maxValue = 0;
    let dominant = this.genome.dominantType;
    let totalValue = 0;

    for (const [type, strand] of this.genome.strands) {
      totalValue += strand.value;
      if (strand.value > maxValue) {
        maxValue = strand.value;
        dominant = type;
      }
    }

    this.genome.dominantType = dominant;
    this.genome.purity = maxValue / Math.max(totalValue, 1);
  }

  /**
   * Check if we meet requirements for any evolution
   * Only emits EVOLUTION_AVAILABLE for NEW paths not yet offered
   */
  private checkForEvolution(): void {
    const now = Date.now();
    
    // Throttle evolution checks
    if (now - this.lastEvolutionCheck < this.EVOLUTION_COOLDOWN) {
      return;
    }
    this.lastEvolutionCheck = now;
    
    const availablePaths = this.getAvailableEvolutionPaths();
    
    // Filter out paths that have already been offered
    const newPaths = availablePaths.filter(path => !this.offeredEvolutions.has(path.id));

    if (newPaths.length > 0) {
      // Mark these paths as offered
      newPaths.forEach(path => this.offeredEvolutions.add(path.id));
      
      globalEvents.emit(GameEvent.EVOLUTION_AVAILABLE, {
        paths: newPaths,
        currentDNA: this.getDNABreakdown(),
      });
    }
  }
  
  /**
   * Reset offered evolutions (called when player evolves or on game reset)
   */
  resetOfferedEvolutions(): void {
    this.offeredEvolutions.clear();
    this.lastEvolutionCheck = 0;
  }

  /**
   * Get all evolution paths currently available
   */
  getAvailableEvolutionPaths(): EvolutionPath[] {
    const available: EvolutionPath[] = [];
    const dna = this.getDNABreakdown();
    const stats = this.getBattleRoyaleStats();

    for (const path of Object.values(EVOLUTION_PATHS)) {
      if (this.meetsRequirements(path, dna, stats)) {
        available.push(path);
      }
    }

    return available;
  }

  /**
   * Check if requirements are met for an evolution path
   */
  private meetsRequirements(
    path: EvolutionPath,
    dna: Record<DNAType, number>,
    stats: BattleRoyaleStats
  ): boolean {
    const req = path.requirements;

    // Check minimum DNA requirements
    for (const [type, minValue] of Object.entries(req.minDNA)) {
      if ((dna[type as DNAType] || 0) < minValue) return false;
    }

    // Check maximum DNA requirements
    for (const [type, maxValue] of Object.entries(req.maxDNA)) {
      if ((dna[type as DNAType] || 0) > maxValue) return false;
    }

    // Check kill count
    if (stats.totalKills < req.minKills) return false;

    // Check survival time
    if (stats.survivalTimeSeconds < req.minSurvivalTime) return false;

    // Check generation
    if (this.genome.generation < req.minGeneration) return false;

    return true;
  }

  /**
   * Evolve into a new form
   */
  evolve(pathId: string): boolean {
    const path = EVOLUTION_PATHS[pathId];
    if (!path) return false;

    const dna = this.getDNABreakdown();
    const stats = this.getBattleRoyaleStats();

    if (!this.meetsRequirements(path, dna, stats)) return false;

    const previousForm = this.currentForm;
    this.currentForm = pathId;
    this.genome.generation++;
    
    // Reset offered evolutions after evolving so new tier evolutions can be offered
    this.resetOfferedEvolutions();

    // Emit evolution event
    globalEvents.emit(GameEvent.EVOLUTION_COMPLETE, {
      from: previousForm,
      to: pathId,
      generation: this.genome.generation,
      bonuses: path.bonuses,
    });

    return true;
  }

  /**
   * Get current DNA breakdown as percentages
   */
  getDNABreakdown(): Record<DNAType, number> {
    const breakdown: Partial<Record<DNAType, number>> = {};

    for (const [type, strand] of this.genome.strands) {
      breakdown[type] = strand.value;
    }

    return breakdown as Record<DNAType, number>;
  }

  /**
   * Get battle royale performance stats
   * These affect what evolutions are available
   */
  getBattleRoyaleStats(): BattleRoyaleStats {
    const now = Date.now();
    const recentKills = this.killHistory.filter(k => now - k.timestamp < 60000);

    return {
      totalKills: this.killHistory.length,
      recentKills: recentKills.length,
      survivalTimeSeconds: this.lootHistory.length > 0
        ? (now - this.lootHistory[0].timestamp) / 1000
        : 0,
      dominantDNA: this.genome.dominantType,
      purity: this.genome.purity,
      generation: this.genome.generation,
      mutationPoints: this.genome.mutationPoints,
    };
  }

  // Getters
  getGenome(): Genome {
    return this.genome;
  }

  getCurrentForm(): string {
    return this.currentForm;
  }

  getDominantType(): DNAType {
    return this.genome.dominantType;
  }

  getPurity(): number {
    return this.genome.purity;
  }

  getMutationPoints(): number {
    return this.genome.mutationPoints;
  }

  addMutationPoints(amount: number): void {
    this.genome.mutationPoints += amount;
    logger.info(LogCategory.GAMEPLAY, `DNA System: Gained ${amount} mutation points. Total: ${this.genome.mutationPoints}`);
    // Potentially emit an event
  }

  deductMutationPoints(amount: number): boolean {
    if (this.genome.mutationPoints < amount) {
      logger.warn(LogCategory.GAMEPLAY, `DNA System: Not enough mutation points to deduct ${amount}. Has: ${this.genome.mutationPoints}`);
      return false;
    }
    this.genome.mutationPoints -= amount;
    logger.info(LogCategory.GAMEPLAY, `DNA System: Deducted ${amount} mutation points. Total: ${this.genome.mutationPoints}`);
    return true;
  }

  /**
   * Recalculate the dominant DNA type and purity
   * This is called after external modifications to DNA values (e.g., from mutations)
   */
  recalculateGenome(): void {
    this.recalculateDominantType();
  }
}

export const dnaSystem = new DNASystem();
