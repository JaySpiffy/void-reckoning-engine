/**
 * LOOT SYSTEM - DNA Extraction and Item Generation
 *
 * INTENTION: When you kill enemies, you extract their DNA. Different enemy types
 * give different DNA. This DNA is what drives your evolution.
 *
 * Loot isn't just "stuff" - it's genetic material that becomes part of you.
 * 
 * TESTING MODE: Set TESTING_MODE = true for extremely high drop rates
 * and guaranteed rare items for testing purposes.
 */

import { DNAType } from '../types/core';
import { EnemyType, GameEvent } from '../types';
import { globalEvents } from '../utils';

// Loot rarity affects DNA amount and bonus items
export enum LootRarity {
  COMMON = 'common',      // Basic DNA
  UNCOMMON = 'uncommon',  // DNA + small bonus
  RARE = 'rare',          // DNA + item + mutation chance
  EPIC = 'epic',          // Lots of DNA + guaranteed item
  LEGENDARY = 'legendary',// Massive DNA + unique item + forced mutation
}

// Loot scaling configuration for balancing
export interface LootScalingConfig {
  /** Multiplier for drop chance (1.0 = normal, 10.0 = 10x more drops) */
  dropRateMultiplier: number;
  /** Multiplier for rarity weights - higher = better rarity more often */
  rarityWeightMultiplier: number;
  /** Minimum rarity tier to drop (0=common, 1=uncommon, etc) */
  minimumRarityTier: number;
  /** Force all drops to be at least this rarity (for testing) */
  forceMinRarity: LootRarity | null;
  /** Multiplier for DNA amounts */
  dnaAmountMultiplier: number;
  /** Multiplier for number of items dropped */
  itemCountMultiplier: number;
}

// Default scaling (normal gameplay)
const NORMAL_SCALING: LootScalingConfig = {
  dropRateMultiplier: 1.0,
  rarityWeightMultiplier: 1.0,
  minimumRarityTier: 0,
  forceMinRarity: null,
  dnaAmountMultiplier: 1.0,
  itemCountMultiplier: 1.0,
};

// Testing mode scaling (EXTREME drops for testing)
const TESTING_SCALING: LootScalingConfig = {
  dropRateMultiplier: 5.0,        // 5x more drops
  rarityWeightMultiplier: 3.0,    // 3x better rarity chances
  minimumRarityTier: 1,           // Minimum uncommon
  forceMinRarity: LootRarity.UNCOMMON,
  dnaAmountMultiplier: 3.0,       // 3x more DNA
  itemCountMultiplier: 2.5,       // 2.5x more items
};

// Loot drop from an enemy
export interface LootDrop {
  dnaType: DNAType;
  dnaAmount: number;
  rarity: LootRarity;
  items: LootItem[];
  mutationChance: number;
}

// Loot items that can be consumed or equipped
export interface LootItem {
  id: string;
  name: string;
  description: string;
  icon: string;
  type: 'consumable' | 'mutation' | 'upgrade';

  // Effects when used
  effects: {
    dnaBonus?: Partial<Record<DNAType, number>>;
    healthRestore?: number;
    manaRestore?: number;
    statBoost?: Partial<Record<string, number>>;
    mutation?: string;
  };

  // Requirements to use
  requirements?: {
    minDNA?: Partial<Record<DNAType, number>>;
    maxDNA?: Partial<Record<DNAType, number>>;
  };
}

// Enemy loot tables - what each enemy type drops
const ENEMY_LOOT_TABLES: Record<EnemyType, { dna: DNAType; baseAmount: number; rarityWeights: Record<LootRarity, number> }> = {
  // Early game enemies
  [EnemyType.GOBLIN]: {
    dna: DNAType.GRASS,
    baseAmount: 5,
    rarityWeights: {
      [LootRarity.COMMON]: 70,
      [LootRarity.UNCOMMON]: 25,
      [LootRarity.RARE]: 5,
      [LootRarity.EPIC]: 0,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  [EnemyType.SPIDER]: {
    dna: DNAType.POISON,
    baseAmount: 6,
    rarityWeights: {
      [LootRarity.COMMON]: 65,
      [LootRarity.UNCOMMON]: 28,
      [LootRarity.RARE]: 7,
      [LootRarity.EPIC]: 0,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  [EnemyType.WOLF]: {
    dna: DNAType.BEAST,
    baseAmount: 7,
    rarityWeights: {
      [LootRarity.COMMON]: 65,
      [LootRarity.UNCOMMON]: 28,
      [LootRarity.RARE]: 7,
      [LootRarity.EPIC]: 0,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  [EnemyType.SKELETON]: {
    dna: DNAType.VOID,
    baseAmount: 8,
    rarityWeights: {
      [LootRarity.COMMON]: 60,
      [LootRarity.UNCOMMON]: 30,
      [LootRarity.RARE]: 9,
      [LootRarity.EPIC]: 1,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  
  // Mid game enemies
  [EnemyType.MANTICORE]: {
    dna: DNAType.FIRE,
    baseAmount: 14,
    rarityWeights: {
      [LootRarity.COMMON]: 50,
      [LootRarity.UNCOMMON]: 35,
      [LootRarity.RARE]: 13,
      [LootRarity.EPIC]: 2,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  [EnemyType.SERPENT]: {
    dna: DNAType.WATER,
    baseAmount: 13,
    rarityWeights: {
      [LootRarity.COMMON]: 52,
      [LootRarity.UNCOMMON]: 33,
      [LootRarity.RARE]: 13,
      [LootRarity.EPIC]: 2,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  [EnemyType.ORC]: {
    dna: DNAType.BEAST,
    baseAmount: 12,
    rarityWeights: {
      [LootRarity.COMMON]: 50,
      [LootRarity.UNCOMMON]: 35,
      [LootRarity.RARE]: 13,
      [LootRarity.EPIC]: 2,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  [EnemyType.GOLEM]: {
    dna: DNAType.EARTH,
    baseAmount: 16,
    rarityWeights: {
      [LootRarity.COMMON]: 45,
      [LootRarity.UNCOMMON]: 38,
      [LootRarity.RARE]: 15,
      [LootRarity.EPIC]: 2,
      [LootRarity.LEGENDARY]: 0,
    },
  },
  [EnemyType.DARK_MAGE]: {
    dna: DNAType.ARCANE,
    baseAmount: 15,
    rarityWeights: {
      [LootRarity.COMMON]: 40,
      [LootRarity.UNCOMMON]: 35,
      [LootRarity.RARE]: 20,
      [LootRarity.EPIC]: 4,
      [LootRarity.LEGENDARY]: 1,
    },
  },
  
  // Late game enemies
  [EnemyType.CRYSTAL_WALKER]: {
    dna: DNAType.CRYSTAL,
    baseAmount: 20,
    rarityWeights: {
      [LootRarity.COMMON]: 35,
      [LootRarity.UNCOMMON]: 35,
      [LootRarity.RARE]: 22,
      [LootRarity.EPIC]: 7,
      [LootRarity.LEGENDARY]: 1,
    },
  },
  [EnemyType.STORM_BIRD]: {
    dna: DNAType.WIND,
    baseAmount: 18,
    rarityWeights: {
      [LootRarity.COMMON]: 38,
      [LootRarity.UNCOMMON]: 35,
      [LootRarity.RARE]: 20,
      [LootRarity.EPIC]: 6,
      [LootRarity.LEGENDARY]: 1,
    },
  },
  [EnemyType.SLIME_BOSS]: {
    dna: DNAType.SLIME,
    baseAmount: 22,
    rarityWeights: {
      [LootRarity.COMMON]: 30,
      [LootRarity.UNCOMMON]: 35,
      [LootRarity.RARE]: 25,
      [LootRarity.EPIC]: 8,
      [LootRarity.LEGENDARY]: 2,
    },
  },
  [EnemyType.LIGHT_WARDEN]: {
    dna: DNAType.LIGHT,
    baseAmount: 19,
    rarityWeights: {
      [LootRarity.COMMON]: 35,
      [LootRarity.UNCOMMON]: 35,
      [LootRarity.RARE]: 22,
      [LootRarity.EPIC]: 7,
      [LootRarity.LEGENDARY]: 1,
    },
  },
  [EnemyType.CHIMERA]: {
    dna: DNAType.CHAOS,
    baseAmount: 25,
    rarityWeights: {
      [LootRarity.COMMON]: 25,
      [LootRarity.UNCOMMON]: 30,
      [LootRarity.RARE]: 28,
      [LootRarity.EPIC]: 14,
      [LootRarity.LEGENDARY]: 3,
    },
  },
  
  // Boss
  [EnemyType.BOSS]: {
    dna: DNAType.CHAOS,
    baseAmount: 50,
    rarityWeights: {
      [LootRarity.COMMON]: 0,
      [LootRarity.UNCOMMON]: 20,
      [LootRarity.RARE]: 40,
      [LootRarity.EPIC]: 30,
      [LootRarity.LEGENDARY]: 10,
    },
  },
};

// Special loot items that can drop
const LOOT_ITEMS: LootItem[] = [
  // Consumables
  {
    id: 'health_orb',
    name: 'Health Orb',
    description: 'Restore 25 health',
    icon: '❤️',
    type: 'consumable',
    effects: { healthRestore: 25 },
  },
  {
    id: 'mana_crystal',
    name: 'Mana Crystal',
    description: 'Restore 30 mana',
    icon: '💎',
    type: 'consumable',
    effects: { manaRestore: 30 },
  },

  // DNA Boosters
  {
    id: 'fire_essence',
    name: 'Fire Essence',
    description: '+10 Fire DNA. You feel warmer...',
    icon: '🔥',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.FIRE]: 10 } },
  },
  {
    id: 'grass_seed',
    name: 'Grass Seed',
    description: '+10 Grass DNA. Growth begins within...',
    icon: '🌱',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.GRASS]: 10 } },
  },
  {
    id: 'water_drop',
    name: 'Pure Water',
    description: '+10 Water DNA. Fluid as the ocean...',
    icon: '💧',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.WATER]: 10 } },
  },
  {
    id: 'lightning_core',
    name: 'Lightning Core',
    description: '+10 Lightning DNA. Electricity courses through you...',
    icon: '⚡',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.LIGHTNING]: 10 } },
  },
  {
    id: 'earth_shard',
    name: 'Earth Shard',
    description: '+10 Earth DNA. You feel grounded...',
    icon: '🪨',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.EARTH]: 10 } },
  },
  {
    id: 'ice_crystal',
    name: 'Ice Crystal',
    description: '+10 Ice DNA. Cold but controlled...',
    icon: '❄️',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.ICE]: 10 } },
  },
  {
    id: 'poison_gland',
    name: 'Venom Gland',
    description: '+10 Poison DNA. Toxic power flows...',
    icon: '☠️',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.POISON]: 10 } },
  },
  {
    id: 'arcane_dust',
    name: 'Arcane Dust',
    description: '+10 Arcane DNA. Mystical energies swirl...',
    icon: '✨',
    type: 'consumable',
    effects: { dnaBonus: { [DNAType.ARCANE]: 10 } },
  },

  // Mutation items (rare)
  {
    id: 'mutation_serum',
    name: 'Mutation Serum',
    description: 'Force a random mutation. Risky but powerful.',
    icon: '🧪',
    type: 'mutation',
    effects: { mutation: 'random' },
  },
  {
    id: 'stabilizer',
    name: 'DNA Stabilizer',
    description: 'Increase DNA stability, reducing unwanted mutations.',
    icon: '🧬',
    type: 'upgrade',
    effects: { statBoost: { dnaStability: 0.1 } },
  },

  // Legendary items
  {
    id: 'phoenix_feather',
    name: 'Phoenix Feather',
    description: 'Massive Fire DNA boost. Legendary evolution catalyst.',
    icon: '🪶',
    type: 'consumable',
    effects: {
      dnaBonus: { [DNAType.FIRE]: 30 },
      healthRestore: 50,
    },
    requirements: { maxDNA: { [DNAType.WATER]: 30 } },
  },
  {
    id: 'world_tree_bark',
    name: 'World Tree Bark',
    description: 'Massive Grass DNA boost. Nature itself recognizes you.',
    icon: '🌳',
    type: 'consumable',
    effects: {
      dnaBonus: { [DNAType.GRASS]: 30 },
      healthRestore: 50,
    },
    requirements: { maxDNA: { [DNAType.FIRE]: 30 } },
  },
  {
    id: 'dragons_hoard',
    name: "Dragon's Hoard",
    description: 'Random massive DNA boost. The dragon shares its power.',
    icon: '🐉',
    type: 'consumable',
    effects: {
      dnaBonus: { [DNAType.CHAOS]: 25 },
    },
  },
  {
    id: 'primordial_ooze',
    name: 'Primordial Ooze',
    description: 'Pure genetic potential. All DNA types increased.',
    icon: '🦠',
    type: 'consumable',
    effects: {
      dnaBonus: { 
        [DNAType.BEAST]: 10,
        [DNAType.FIRE]: 10,
        [DNAType.WATER]: 10,
        [DNAType.GRASS]: 10,
        [DNAType.VOID]: 10,
      },
      healthRestore: 25,
      manaRestore: 25,
    },
  },
];

export class LootSystem {
  private inventory: LootItem[] = [];
  private scaling: LootScalingConfig = { ...NORMAL_SCALING };

  /**
   * Set testing mode for extreme drop rates
   */
  setTestingMode(enabled: boolean): void {
    this.scaling = enabled ? { ...TESTING_SCALING } : { ...NORMAL_SCALING };
    // Testing mode logging removed for production
  }

  /**
   * Check if testing mode is active
   */
  isTestingMode(): boolean {
    return this.scaling.dropRateMultiplier > 1.0;
  }

  /**
   * Get current scaling configuration
   */
  getScaling(): LootScalingConfig {
    return { ...this.scaling };
  }

  /**
   * Set custom scaling configuration
   */
  setScaling(config: Partial<LootScalingConfig>): void {
    this.scaling = { ...this.scaling, ...config };
  }

  /**
   * Generate loot when an enemy dies
   * This is the main entry point for loot generation
   */
  generateLoot(enemyType: EnemyType, killerDNA: DNAType): LootDrop {
    const table = ENEMY_LOOT_TABLES[enemyType];
    if (!table) {
      return this.generateDefaultLoot();
    }

    // Determine rarity with scaling applied
    const rarity = this.rollRarity(table.rarityWeights);

    // Calculate DNA amount based on rarity and scaling
    const dnaMultiplier = this.getRarityMultiplier(rarity) * this.scaling.dnaAmountMultiplier;
    const dnaAmount = table.baseAmount * dnaMultiplier;

    // Generate items based on rarity with scaling
    const items = this.generateItems(rarity, killerDNA);

    // Calculate mutation chance
    const mutationChance = this.getMutationChance(rarity);

    return {
      dnaType: table.dna,
      dnaAmount,
      rarity,
      items,
      mutationChance,
    };
  }

  /**
   * Roll for loot rarity based on weights
   * Applies rarity weight multiplier for better drops
   */
  private rollRarity(weights: Record<LootRarity, number>): LootRarity {
    // Apply scaling to rarity weights
    const scaledWeights: Record<LootRarity, number> = { ...weights };
    
    // Boost higher rarities based on multiplier
    if (this.scaling.rarityWeightMultiplier > 1.0) {
      scaledWeights[LootRarity.UNCOMMON] *= this.scaling.rarityWeightMultiplier;
      scaledWeights[LootRarity.RARE] *= this.scaling.rarityWeightMultiplier * 1.5;
      scaledWeights[LootRarity.EPIC] *= this.scaling.rarityWeightMultiplier * 2.0;
      scaledWeights[LootRarity.LEGENDARY] *= this.scaling.rarityWeightMultiplier * 3.0;
    }

    // Force minimum rarity if set
    if (this.scaling.forceMinRarity) {
      const minRarity = this.scaling.forceMinRarity;
      const rarityOrder = [LootRarity.COMMON, LootRarity.UNCOMMON, LootRarity.RARE, LootRarity.EPIC, LootRarity.LEGENDARY];
      const minIndex = rarityOrder.indexOf(minRarity);
      
      // Zero out weights below minimum
      for (let i = 0; i < minIndex; i++) {
        scaledWeights[rarityOrder[i]] = 0;
      }
    }

    const total = Object.values(scaledWeights).reduce((a, b) => a + b, 0);
    let roll = Math.random() * total;

    for (const [rarity, weight] of Object.entries(scaledWeights)) {
      roll -= weight;
      if (roll <= 0) return rarity as LootRarity;
    }

    return LootRarity.COMMON;
  }

  /**
   * Get DNA amount multiplier for rarity
   */
  private getRarityMultiplier(rarity: LootRarity): number {
    switch (rarity) {
      case LootRarity.COMMON: return 1;
      case LootRarity.UNCOMMON: return 1.5;
      case LootRarity.RARE: return 2.5;
      case LootRarity.EPIC: return 5;
      case LootRarity.LEGENDARY: return 10;
    }
  }

  /**
   * Get mutation chance for rarity
   */
  private getMutationChance(rarity: LootRarity): number {
    switch (rarity) {
      case LootRarity.COMMON: return 0;
      case LootRarity.UNCOMMON: return 0.05;
      case LootRarity.RARE: return 0.15;
      case LootRarity.EPIC: return 0.3;
      case LootRarity.LEGENDARY: return 0.5;
    }
  }

  /**
   * Generate items for the loot drop
   * Applies item count multiplier for more drops
   */
  private generateItems(rarity: LootRarity, killerDNA: DNAType): LootItem[] {
    const items: LootItem[] = [];

    // Determine number of items based on rarity
    let itemCount = 0;
    switch (rarity) {
      case LootRarity.COMMON: itemCount = Math.random() < 0.3 ? 1 : 0; break;
      case LootRarity.UNCOMMON: itemCount = 1; break;
      case LootRarity.RARE: itemCount = Math.random() < 0.5 ? 2 : 1; break;
      case LootRarity.EPIC: itemCount = 2; break;
      case LootRarity.LEGENDARY: itemCount = 3; break;
    }

    // Apply item count multiplier (for testing mode)
    itemCount = Math.floor(itemCount * this.scaling.itemCountMultiplier);
    itemCount = Math.max(0, Math.min(itemCount, 5)); // Cap at 5 items max

    // Select items based on killer's DNA (you find what you resonate with)
    const availableItems = LOOT_ITEMS.filter(item => {
      // Check requirements
      if (item.requirements?.minDNA) {
        // Would need to pass player DNA here
        return true; // Simplified for now
      }
      return true;
    });

    // Prioritize items matching killer's DNA
    const dnaItems = availableItems.filter(item => {
      const dnaBonus = item.effects.dnaBonus;
      if (!dnaBonus) return false;
      return Object.keys(dnaBonus).some(key => key === killerDNA);
    });

    const otherItems = availableItems.filter(item => !dnaItems.includes(item));

    // Fill item slots
    for (let i = 0; i < itemCount; i++) {
      // 70% chance for DNA-matching item, 30% for random
      const pool = Math.random() < 0.7 && dnaItems.length > 0 ? dnaItems : otherItems;
      const item = pool[Math.floor(Math.random() * pool.length)];
      if (item) items.push(item);
    }

    return items;
  }

  /**
   * Generate default loot for unknown enemy types
   */
  private generateDefaultLoot(): LootDrop {
    return {
      dnaType: DNAType.CHAOS,
      dnaAmount: 3 * this.scaling.dnaAmountMultiplier,
      rarity: this.scaling.forceMinRarity || LootRarity.COMMON,
      items: [],
      mutationChance: 0,
    };
  }

  /**
   * Add item to inventory
   */
  addToInventory(item: LootItem): void {
    this.inventory.push(item);
    globalEvents.emit(GameEvent.LOOT_ACQUIRED, { item });
  }

  /**
   * Use an item from inventory
   */
  useItem(itemId: string): boolean {
    const index = this.inventory.findIndex(item => item.id === itemId);
    if (index === -1) return false;

    const item = this.inventory[index];

    // Emit event with full item data so GameManager can apply effects
    globalEvents.emit(GameEvent.ITEM_USED, { item });

    // Remove from inventory
    this.inventory.splice(index, 1);

    return true;
  }

  /**
   * Get current inventory
   */
  getInventory(): LootItem[] {
    return [...this.inventory];
  }

  /**
   * Clear inventory (for testing/reset)
   */
  clearInventory(): void {
    this.inventory = [];
  }
}

export const lootSystem = new LootSystem();
