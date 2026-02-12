/**
 * DNA CORE - No Dependencies
 * 
 * This file contains the fundamental DNA types and interfaces.
 * It MUST NOT import from any other file to avoid circular dependencies.
 */

import type { DNAType } from '../types';

// DNA Strand - A single genetic marker with value and stability
export interface DNAStrand {
  type: DNAType;
  value: number;        // 0-100, how dominant this trait is
  stability: number;    // 0-1, chance this mutates on evolution
  mutations: number;    // How many times this has mutated
}

// Genome - Complete genetic profile of an entity
export interface Genome {
  strands: Map<DNAType, DNAStrand>;
  dominantType: DNAType;  // Current primary element
  purity: number;         // 0-1, how pure the dominant type is
  generation: number;     // How many evolutions deep
  mutationPoints: number; // Points to spend on mutations
}

// Evolution Path - A possible transformation based on DNA
export interface EvolutionPath {
  id: string;
  name: string;
  description: string;
  
  // Requirements to unlock this path
  requirements: {
    minDNA: Partial<Record<DNAType, number>>;
    maxDNA: Partial<Record<DNAType, number>>;
    minKills: number;
    minSurvivalTime: number;
    minGeneration: number;
    specialConditions?: string[];
  };
  
  // What this evolution grants
  bonuses: {
    healthMultiplier: number;
    damageMultiplier: number;
    speedMultiplier: number;
    specialAbilities: string[];
    resistances: Partial<Record<DNAType, number>>;
    weaknesses: Partial<Record<DNAType, number>>;
  };
  
  // Visual transformation
  appearance: {
    color: string;
    shape: 'humanoid' | 'quadruped' | 'amorphous' | 'serpentine' | 'winged';
    size: number;
    particleEffect: string;
  };
  
  // Next possible evolutions from this form
  nextEvolutions: string[];
}

// Battle Royale Stats - Performance metrics that affect evolution
export interface BattleRoyaleStats {
  totalKills: number;
  recentKills: number;      // Kills in last 60 seconds (momentum)
  survivalTimeSeconds: number;
  dominantDNA: DNAType;
  purity: number;
  generation: number;
  mutationPoints: number;
}
