import { DNAType } from '../types/core';
import { dnaSystem } from './DNASystem';
import { globalEvents } from '../utils';
import { GameEvent } from '../types';
import { logger, LogCategory } from '../managers/LogManager';

export enum MutationType {
  DNA_STABILITY_BOOST = 'dna_stability_boost',
  RESISTANCE_BOOST = 'resistance_boost',
  WEAKNESS_REDUCTION = 'weakness_reduction',
  GENETIC_PURIFICATION = 'genetic_purification', // Reduce other DNA types
  DNA_REROLL = 'dna_reroll',
}

export interface Mutation {
  id: MutationType;
  name: string;
  description: string;
  cost: number; // In mutationPoints
  effect: {
    dnaType?: DNAType; // Which DNA type this mutation affects
    stabilityIncrease?: number;
    resistanceIncrease?: DNAType;
    weaknessReduce?: DNAType;
    purityIncrease?: number;
    randomizeDNA?: boolean;
    // Add more specific effects as needed
  };
}

export const MUTATIONS: Record<MutationType, Mutation> = {
  [MutationType.DNA_STABILITY_BOOST]: {
    id: MutationType.DNA_STABILITY_BOOST,
    name: 'Genetic Stabilizer',
    description: 'Increases the stability of a chosen DNA strand, reducing mutation risk.',
    cost: 5,
    effect: {
      stabilityIncrease: 0.1, // 10% increase
    },
  },
  [MutationType.RESISTANCE_BOOST]: {
    id: MutationType.RESISTANCE_BOOST,
    name: 'Elemental Shielding',
    description: 'Grants increased resistance to a specific elemental damage type.',
    cost: 10,
    effect: {
      resistanceIncrease: DNAType.FIRE, // Example, specific DNA type chosen at purchase
    },
  },
  [MutationType.WEAKNESS_REDUCTION]: {
    id: MutationType.WEAKNESS_REDUCTION,
    name: 'Adaptive Biology',
    description: 'Reduces vulnerability to a specific elemental damage type.',
    cost: 10,
    effect: {
      weaknessReduce: DNAType.ICE, // Example, specific DNA type chosen at purchase
    },
  },
  [MutationType.GENETIC_PURIFICATION]: {
    id: MutationType.GENETIC_PURIFICATION,
    name: 'Purity Infusion',
    description: 'Slightly reduces the value of all non-dominant DNA strands, increasing purity.',
    cost: 15,
    effect: {
      purityIncrease: 0.05, // 5% purity increase
    },
  },
  [MutationType.DNA_REROLL]: {
    id: MutationType.DNA_REROLL,
    name: 'Genetic Reshuffle',
    description: 'Randomly re-distributes your non-dominant DNA points (use with caution!).',
    cost: 20,
    effect: {
      randomizeDNA: true,
    },
  },
};

export class MutationSystem {
  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    globalEvents.on(GameEvent.ENEMY_KILLED, (_data) => {
      // Small chance to gain mutation points on enemy kill
      if (Math.random() < 0.05) { // 5% chance
        dnaSystem.addMutationPoints(1);
      }
    });

    globalEvents.on(GameEvent.EVOLUTION_COMPLETE, () => {
      // Gain mutation points on evolution
      dnaSystem.addMutationPoints(5);
    });
  }

  /**
   * Applies a mutation to the player's genome.
   * @param mutationType The type of mutation to apply.
   * @param targetDnaType Optional: The specific DNAType to target for some mutations.
   * @returns True if mutation was applied successfully, false otherwise.
   */
  applyMutation(mutationType: MutationType, targetDnaType?: DNAType): boolean {
    const mutation = MUTATIONS[mutationType];
    if (!mutation) {
      logger.warn(LogCategory.GAMEPLAY, `MutationSystem: Unknown mutation type ${mutationType}`);
      return false;
    }

    if (dnaSystem.getMutationPoints() < mutation.cost) {
      logger.info(LogCategory.GAMEPLAY, `MutationSystem: Not enough mutation points for ${mutation.name}`);
      return false;
    }

    // Deduct cost
    dnaSystem.deductMutationPoints(mutation.cost);

    // Apply effect
    const genome = dnaSystem.getGenome();

    if (mutation.effect.stabilityIncrease && targetDnaType) {
      const strand = genome.strands.get(targetDnaType);
      if (strand) {
        strand.stability = Math.min(1, strand.stability + mutation.effect.stabilityIncrease);
        logger.info(LogCategory.GAMEPLAY, `Mutation: Increased stability of ${targetDnaType} to ${strand.stability}`);
      }
    } else if (mutation.effect.resistanceIncrease && targetDnaType) {
      // This would require a mechanism to apply permanent resistances to the player
      // For now, let's just log it
      logger.info(LogCategory.GAMEPLAY, `Mutation: Player gained permanent resistance to ${targetDnaType}`);
    } else if (mutation.effect.weaknessReduce && targetDnaType) {
      logger.info(LogCategory.GAMEPLAY, `Mutation: Player reduced weakness to ${targetDnaType}`);
    } else if (mutation.effect.purityIncrease) {
      for (const [type, strand] of genome.strands) {
        if (type !== genome.dominantType && strand.value > 0) {
          strand.value = Math.max(0, strand.value - (strand.value * mutation.effect.purityIncrease));
        }
      }
      dnaSystem.recalculateGenome(); // Recalculate after changes
      logger.info(LogCategory.GAMEPLAY, 'Mutation: Genetic purification applied.');
    } else if (mutation.effect.randomizeDNA) {
      const totalNonDominantDNA = Array.from(genome.strands.values())
        .filter(s => s.type !== genome.dominantType)
        .reduce((sum, s) => sum + s.value, 0);

      const nonDominantTypes = Array.from(genome.strands.keys()).filter(t => t !== genome.dominantType);
      
      // Reset non-dominant DNA
      for (const type of nonDominantTypes) {
        genome.strands.get(type)!.value = 0;
      }

      // Redistribute
      let remainingPoints = totalNonDominantDNA;
      while(remainingPoints > 0) {
        const randomType = nonDominantTypes[Math.floor(Math.random() * nonDominantTypes.length)];
        const strand = genome.strands.get(randomType)!;
        strand.value = Math.min(100, strand.value + 1);
        remainingPoints--;
      }
      dnaSystem.recalculateGenome();
      logger.info(LogCategory.GAMEPLAY, 'Mutation: DNA reshuffled.');
    } else {
      logger.warn(LogCategory.GAMEPLAY, `MutationSystem: Mutation effect not implemented for ${mutationType}`);
      return false;
    }
    
    globalEvents.emit(GameEvent.MUTATION_APPLIED, { mutationType, targetDnaType: targetDnaType ?? 'none' });
    return true;
  }
}

export const mutationSystem = new MutationSystem();
