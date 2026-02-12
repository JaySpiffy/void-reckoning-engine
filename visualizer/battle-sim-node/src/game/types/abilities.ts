// ============================================
// ABILITY SYSTEM
// ============================================

import { ElementType, DamageType } from './core';

export enum AbilityType {
  // Basic abilities (always available)
  BASIC_ATTACK = 'basic_attack',
  DASH = 'dash',
  
  // Fire abilities
  FIREBALL = 'fireball',
  FLAME_WAVE = 'flame_wave',
  INFERNO = 'inferno',
  
  // Ice abilities
  ICE_BOLT = 'ice_bolt',
  FROST_NOVA = 'frost_nova',
  BLIZZARD = 'blizzard',
  
  // Lightning abilities
  LIGHTNING_BOLT = 'lightning_bolt',
  CHAIN_LIGHTNING = 'chain_lightning',
  THUNDERSTORM = 'thunderstorm',
  
  // Poison abilities
  POISON_DART = 'poison_dart',
  VENOM_POOL = 'venom_pool',
  PLAGUE = 'plague',
  
  // Arcane abilities
  ARCANE_MISSILE = 'arcane_missile',
  MANA_BURST = 'mana_burst',
  BLACK_HOLE = 'black_hole',
}

export interface AbilityConfig {
  id: AbilityType;
  name: string;
  description: string;
  icon: string;
  element: ElementType;
  
  // Costs
  manaCost: number;
  healthCost?: number;
  
  // Cooldown
  cooldown: number;
  
  // Damage
  damage: number;
  damageType: DamageType;
  
  // Effects
  dotDamage?: number;
  dotDuration?: number;
  slowPercent?: number;
  slowDuration?: number;
  stunDuration?: number;
  knockback?: number;
  pierceCount?: number;
  chainCount?: number;
  aoeRadius?: number;
  
  // Projectile
  projectileSpeed?: number;
  projectileCount?: number;
  
  // Evolution
  evolutionLevel: number;
  evolvesFrom?: AbilityType;
  evolvesTo?: AbilityType;
  evolutionKillsRequired: number;
}

// Evolution tracking
export interface ElementEvolution {
  element: ElementType;
  level: number;
  experience: number;
  experienceToNext: number;
  killsWithElement: number;
  unlockedAbilities: AbilityType[];
}

// Ability instance (runtime state)
export interface AbilityState {
  config: AbilityConfig;
  currentCooldown: number;
  isUnlocked: boolean;
  killCount: number;
}

// ============================================
// ABILITY DEFINITIONS
// ============================================

export const ABILITY_CONFIGS: Record<AbilityType, AbilityConfig> = {
  // BASIC ABILITIES
  [AbilityType.BASIC_ATTACK]: {
    id: AbilityType.BASIC_ATTACK,
    name: 'Elemental Bolt',
    description: 'Fire a bolt of your current element',
    icon: '⚡',
    element: ElementType.NONE,
    manaCost: 0,
    cooldown: 0.3,
    damage: 20,
    damageType: DamageType.MAGIC,
    projectileSpeed: 500,
    evolutionLevel: 0,
    evolutionKillsRequired: 0,
  },
  
  [AbilityType.DASH]: {
    id: AbilityType.DASH,
    name: 'Elemental Dash',
    description: 'Dash in movement direction, leaving elemental trail',
    icon: '💨',
    element: ElementType.NONE,
    manaCost: 15,
    cooldown: 4,
    damage: 10,
    damageType: DamageType.MAGIC,
    aoeRadius: 50,
    evolutionLevel: 0,
    evolutionKillsRequired: 0,
  },
  
  // FIRE ABILITIES - Level 1
  [AbilityType.FIREBALL]: {
    id: AbilityType.FIREBALL,
    name: 'Fireball',
    description: 'Launch a fireball that explodes on impact',
    icon: '🔥',
    element: ElementType.FIRE,
    manaCost: 20,
    cooldown: 3,
    damage: 40,
    damageType: DamageType.FIRE,
    dotDamage: 8,
    dotDuration: 4,
    aoeRadius: 80,
    projectileSpeed: 400,
    evolutionLevel: 1,
    evolutionKillsRequired: 10,
    evolvesTo: AbilityType.FLAME_WAVE,
  },
  
  // FIRE ABILITIES - Level 2
  [AbilityType.FLAME_WAVE]: {
    id: AbilityType.FLAME_WAVE,
    name: 'Flame Wave',
    description: 'Unleash a wave of fire in all directions',
    icon: '🌊',
    element: ElementType.FIRE,
    manaCost: 35,
    cooldown: 6,
    damage: 60,
    damageType: DamageType.FIRE,
    dotDamage: 12,
    dotDuration: 5,
    aoeRadius: 150,
    projectileCount: 8,
    evolutionLevel: 2,
    evolvesFrom: AbilityType.FIREBALL,
    evolutionKillsRequired: 25,
    evolvesTo: AbilityType.INFERNO,
  },
  
  // FIRE ABILITIES - Level 3
  [AbilityType.INFERNO]: {
    id: AbilityType.INFERNO,
    name: 'Inferno',
    description: 'Rain fire from the sky, burning everything',
    icon: '☀️',
    element: ElementType.FIRE,
    manaCost: 60,
    cooldown: 12,
    damage: 100,
    damageType: DamageType.FIRE,
    dotDamage: 20,
    dotDuration: 8,
    aoeRadius: 300,
    projectileCount: 20,
    evolutionLevel: 3,
    evolvesFrom: AbilityType.FLAME_WAVE,
    evolutionKillsRequired: 50,
  },
  
  // ICE ABILITIES - Level 1
  [AbilityType.ICE_BOLT]: {
    id: AbilityType.ICE_BOLT,
    name: 'Ice Bolt',
    description: 'Fire a freezing bolt that slows enemies',
    icon: '❄️',
    element: ElementType.ICE,
    manaCost: 18,
    cooldown: 2.5,
    damage: 25,
    damageType: DamageType.ICE,
    slowPercent: 0.4,
    slowDuration: 3,
    pierceCount: 3,
    projectileSpeed: 450,
    evolutionLevel: 1,
    evolutionKillsRequired: 10,
    evolvesTo: AbilityType.FROST_NOVA,
  },
  
  // ICE ABILITIES - Level 2
  [AbilityType.FROST_NOVA]: {
    id: AbilityType.FROST_NOVA,
    name: 'Frost Nova',
    description: 'Freeze all nearby enemies',
    icon: '💎',
    element: ElementType.ICE,
    manaCost: 40,
    cooldown: 8,
    damage: 50,
    damageType: DamageType.ICE,
    slowPercent: 0.7,
    slowDuration: 5,
    stunDuration: 1,
    aoeRadius: 200,
    evolutionLevel: 2,
    evolvesFrom: AbilityType.ICE_BOLT,
    evolutionKillsRequired: 25,
    evolvesTo: AbilityType.BLIZZARD,
  },
  
  // ICE ABILITIES - Level 3
  [AbilityType.BLIZZARD]: {
    id: AbilityType.BLIZZARD,
    name: 'Blizzard',
    description: 'Create a massive blizzard that freezes everything',
    icon: '🌨️',
    element: ElementType.ICE,
    manaCost: 70,
    cooldown: 15,
    damage: 80,
    damageType: DamageType.ICE,
    slowPercent: 0.9,
    slowDuration: 8,
    stunDuration: 2,
    aoeRadius: 400,
    evolutionLevel: 3,
    evolvesFrom: AbilityType.FROST_NOVA,
    evolutionKillsRequired: 50,
  },
  
  // LIGHTNING ABILITIES - Level 1
  [AbilityType.LIGHTNING_BOLT]: {
    id: AbilityType.LIGHTNING_BOLT,
    name: 'Lightning Bolt',
    description: 'Fire a lightning bolt that chains to enemies',
    icon: '⚡',
    element: ElementType.LIGHTNING,
    manaCost: 22,
    cooldown: 2,
    damage: 30,
    damageType: DamageType.LIGHTNING,
    chainCount: 3,
    projectileSpeed: 600,
    evolutionLevel: 1,
    evolutionKillsRequired: 10,
    evolvesTo: AbilityType.CHAIN_LIGHTNING,
  },
  
  // LIGHTNING ABILITIES - Level 2
  [AbilityType.CHAIN_LIGHTNING]: {
    id: AbilityType.CHAIN_LIGHTNING,
    name: 'Chain Lightning',
    description: 'Lightning that chains through all nearby enemies',
    icon: '🔌',
    element: ElementType.LIGHTNING,
    manaCost: 40,
    cooldown: 5,
    damage: 50,
    damageType: DamageType.LIGHTNING,
    chainCount: 8,
    aoeRadius: 250,
    evolutionLevel: 2,
    evolvesFrom: AbilityType.LIGHTNING_BOLT,
    evolutionKillsRequired: 25,
    evolvesTo: AbilityType.THUNDERSTORM,
  },
  
  // LIGHTNING ABILITIES - Level 3
  [AbilityType.THUNDERSTORM]: {
    id: AbilityType.THUNDERSTORM,
    name: 'Thunderstorm',
    description: 'Call down devastating lightning strikes',
    icon: '⛈️',
    element: ElementType.LIGHTNING,
    manaCost: 65,
    cooldown: 12,
    damage: 90,
    damageType: DamageType.LIGHTNING,
    chainCount: 15,
    aoeRadius: 500,
    projectileCount: 10,
    evolutionLevel: 3,
    evolvesFrom: AbilityType.CHAIN_LIGHTNING,
    evolutionKillsRequired: 50,
  },
  
  // POISON ABILITIES - Level 1
  [AbilityType.POISON_DART]: {
    id: AbilityType.POISON_DART,
    name: 'Poison Dart',
    description: 'Fire a poison dart that deals damage over time',
    icon: '🎯',
    element: ElementType.POISON,
    manaCost: 15,
    cooldown: 2,
    damage: 15,
    damageType: DamageType.POISON,
    dotDamage: 12,
    dotDuration: 6,
    projectileSpeed: 500,
    evolutionLevel: 1,
    evolutionKillsRequired: 10,
    evolvesTo: AbilityType.VENOM_POOL,
  },
  
  // POISON ABILITIES - Level 2
  [AbilityType.VENOM_POOL]: {
    id: AbilityType.VENOM_POOL,
    name: 'Venom Pool',
    description: 'Create a pool of venom that damages enemies',
    icon: '💧',
    element: ElementType.POISON,
    manaCost: 35,
    cooldown: 7,
    damage: 30,
    damageType: DamageType.POISON,
    dotDamage: 20,
    dotDuration: 8,
    aoeRadius: 180,
    slowPercent: 0.3,
    slowDuration: 4,
    evolutionLevel: 2,
    evolvesFrom: AbilityType.POISON_DART,
    evolutionKillsRequired: 25,
    evolvesTo: AbilityType.PLAGUE,
  },
  
  // POISON ABILITIES - Level 3
  [AbilityType.PLAGUE]: {
    id: AbilityType.PLAGUE,
    name: 'Plague',
    description: 'Spread a deadly plague to all enemies',
    icon: '☠️',
    element: ElementType.POISON,
    manaCost: 60,
    cooldown: 14,
    damage: 50,
    damageType: DamageType.POISON,
    dotDamage: 35,
    dotDuration: 12,
    aoeRadius: 450,
    chainCount: 20,
    evolutionLevel: 3,
    evolvesFrom: AbilityType.VENOM_POOL,
    evolutionKillsRequired: 50,
  },
  
  // ARCANE ABILITIES - Level 1
  [AbilityType.ARCANE_MISSILE]: {
    id: AbilityType.ARCANE_MISSILE,
    name: 'Arcane Missile',
    description: 'Fire a piercing arcane missile',
    icon: '🔮',
    element: ElementType.ARCANE,
    manaCost: 25,
    cooldown: 2.5,
    damage: 45,
    damageType: DamageType.ARCANE,
    pierceCount: 5,
    projectileSpeed: 550,
    evolutionLevel: 1,
    evolutionKillsRequired: 10,
    evolvesTo: AbilityType.MANA_BURST,
  },
  
  // ARCANE ABILITIES - Level 2
  [AbilityType.MANA_BURST]: {
    id: AbilityType.MANA_BURST,
    name: 'Mana Burst',
    description: 'Release a burst of pure mana energy',
    icon: '💥',
    element: ElementType.ARCANE,
    manaCost: 45,
    cooldown: 6,
    damage: 75,
    damageType: DamageType.ARCANE,
    pierceCount: 10,
    aoeRadius: 150,
    knockback: 100,
    evolutionLevel: 2,
    evolvesFrom: AbilityType.ARCANE_MISSILE,
    evolutionKillsRequired: 25,
    evolvesTo: AbilityType.BLACK_HOLE,
  },
  
  // ARCANE ABILITIES - Level 3
  [AbilityType.BLACK_HOLE]: {
    id: AbilityType.BLACK_HOLE,
    name: 'Black Hole',
    description: 'Create a black hole that pulls in and destroys enemies',
    icon: '🕳️',
    element: ElementType.ARCANE,
    manaCost: 80,
    cooldown: 18,
    damage: 150,
    damageType: DamageType.ARCANE,
    aoeRadius: 350,
    knockback: -200, // Pull instead of push
    evolutionLevel: 3,
    evolvesFrom: AbilityType.MANA_BURST,
    evolutionKillsRequired: 50,
  },
};

// Get abilities for an element at a specific evolution level
export function getAbilitiesForElement(element: ElementType, level: number): AbilityType[] {
  const abilities: AbilityType[] = [];
  
  for (const config of Object.values(ABILITY_CONFIGS)) {
    if (config.element === element && config.evolutionLevel <= level) {
      abilities.push(config.id);
    }
  }
  
  return abilities;
}

// Get ability slot assignments (1-5 keys)
export function getAbilitySlots(element: ElementType, evolutionLevel: number): AbilityType[] {
  const slots: AbilityType[] = [
    AbilityType.BASIC_ATTACK, // Always slot 1
    AbilityType.DASH,         // Always slot 2
  ];
  
  // Add element-specific abilities based on evolution level
  const elementAbilities = getAbilitiesForElement(element, evolutionLevel)
    .filter(a => a !== AbilityType.BASIC_ATTACK && a !== AbilityType.DASH)
    .sort((a, b) => ABILITY_CONFIGS[a].evolutionLevel - ABILITY_CONFIGS[b].evolutionLevel);
  
  // Fill slots 3-5 with highest unlocked abilities
  for (let i = elementAbilities.length - 1; i >= 0 && slots.length < 5; i--) {
    const ability = elementAbilities[i];
    if (!slots.includes(ability)) {
      slots.push(ability);
    }
  }
  
  // Pad with empty slots
  while (slots.length < 5) {
    slots.push(AbilityType.BASIC_ATTACK);
  }
  
  return slots.slice(0, 5);
}
