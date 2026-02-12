// ============================================
// CORE TYPES - NO DEPENDENCIES
// These are the fundamental types that other modules depend on.
// This file should NEVER import from other files in the game.
// ============================================

// ============================================
// BASIC MATH TYPES
// ============================================

export interface Vector2 {
  x: number;
  y: number;
}

export interface Bounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

// ============================================
// ENTITY TYPE ENUMS - Defined here to avoid circular deps
// ============================================

export enum EntityType {
  PLAYER = 'player',
  ENEMY = 'enemy',
  PROJECTILE = 'projectile',
  RESOURCE = 'resource',
  BUILDING = 'building',
  PARTICLE = 'particle',
  ELEMENTAL_PICKUP = 'elemental_pickup',
}

export enum EnemyType {
  // Early game (Wave 1-3)
  GOBLIN = 'goblin',           // GRASS DNA
  SKELETON = 'skeleton',       // VOID DNA
  SPIDER = 'spider',           // POISON DNA
  WOLF = 'wolf',               // BEAST DNA
  
  // Mid game (Wave 4-8)
  ORC = 'orc',                 // BEAST DNA (tankier)
  DARK_MAGE = 'dark_mage',     // ARCANE DNA
  MANTICORE = 'manticore',     // FIRE DNA
  SERPENT = 'serpent',         // WATER DNA
  GOLEM = 'golem',             // EARTH DNA
  
  // Late game (Wave 9+)
  CRYSTAL_WALKER = 'crystal_walker', // CRYSTAL DNA
  SLIME_BOSS = 'slime_boss',         // SLIME DNA
  CHIMERA = 'chimera',               // CHAOS DNA
  LIGHT_WARDEN = 'light_warden',     // LIGHT DNA
  STORM_BIRD = 'storm_bird',         // WIND DNA
  
  // Bosses
  BOSS = 'boss',
}

export enum ResourceType {
  WOOD = 'wood',
  STONE = 'stone',
  GOLD = 'gold',
  MANA = 'mana',
}

export enum BuildingType {
  WALL = 'wall',
  TOWER = 'tower',
  HEALING_SHRINE = 'healing_shrine',
  RESOURCE_GENERATOR = 'resource_generator',
}

// ============================================
// ELEMENT TYPE - Core to many systems
// ============================================

export enum ElementType {
  NONE = 'none',
  FIRE = 'fire',
  ICE = 'ice',
  LIGHTNING = 'lightning',
  POISON = 'poison',
  ARCANE = 'arcane',
}

// ============================================
// DAMAGE TYPES
// ============================================

export enum DamageType {
  PHYSICAL = 'physical',
  MAGIC = 'magic',
  FIRE = 'fire',
  ICE = 'ice',
  POISON = 'poison',
  LIGHTNING = 'lightning',
  ARCANE = 'arcane',
}

export enum WeaponType {
  SWORD = 'sword',
  BOW = 'bow',
  STAFF = 'staff',
  AXE = 'axe',
  DAGGER = 'dagger',
}

// ============================================
// DNA TYPES - fundamental blocks of evolution
// ============================================

export enum DNAType {
  // Elemental DNA - Determines elemental affinity and resistances
  FIRE = 'fire',
  ICE = 'ice',
  WATER = 'water',
  EARTH = 'earth',      // Rock/metal/stone
  WIND = 'wind',        // Air/speed
  LIGHTNING = 'lightning',
  POISON = 'poison',
  VOID = 'void',        // Dark/arcane
  LIGHT = 'light',      // Holy/radiant
  ARCANE = 'arcane',    // Pure magic
  
  // Physical DNA - Determines body type and physical traits
  GRASS = 'grass',      // Plant/nature life
  FUNGUS = 'fungus',    // Decay/regeneration
  INSECT = 'insect',    // Exoskeleton/swarm
  BEAST = 'beast',      // Fur/fangs/claws
  REPTILE = 'reptile',  // Scales/cold-blooded
  AQUATIC = 'aquatic',  // Gills/fins/amphibious
  PHYSICAL = 'physical', // Raw physical power
  
  // Special DNA - Rare mutations
  CRYSTAL = 'crystal',  // Gem/mineral body
  SLIME = 'slime',      // Amorphous/adaptive
  MECH = 'mech',        // Cybernetic/artificial
  CHAOS = 'chaos',      // Unstable/random mutations
}

// ============================================
// GAME STATE
// ============================================

export enum GamePhase {
  MENU = 'menu',
  PLAYING = 'playing',
  PAUSED = 'paused',
  GAME_OVER = 'game_over',
}

export interface GameState {
  phase: GamePhase;
  wave: number;
  score: number;
  gameTime: number;
}

export interface PlayerStats {
  maxHealth: number;
  health: number;
  maxMana: number;
  mana: number;
  speed: number;
  damage: number;
  attackSpeed: number;
  attackRange: number;
  level: number;
  experience: number;
  experienceToNext: number;
  element: ElementType;
  elementDuration: number;
  elementLevel: number;
  elementExperience: number;
}

export interface Resources {
  wood: number;
  stone: number;
  gold: number;
  mana: number;
  [key: string]: number;
}

// ============================================
// INPUT
// ============================================

export interface InputState {
  keys: Set<string>;
  mousePosition: Vector2;
  mouseDown: boolean;
  mouseJustPressed: boolean;
}


// ============================================
// COMBAT
// ============================================

export interface DamageInfo {
  amount: number;
  type: DamageType;
  source: string;
  knockback?: Vector2;
  isDot?: boolean;
  dotDuration?: number;
}

// ============================================
// ELEMENT CONFIGS - Self-contained
// ============================================

export interface ElementStats {
  damage: number;
  speed: number;
  range: number;
  dotDamage?: number;
  dotDuration?: number;
  slowPercent?: number;
  slowDuration?: number;
  chainCount?: number;
  pierceCount?: number;
}

export interface ElementConfig {
  color: string;
  projectileColor: string;
  stats: Partial<ElementStats>;
  description: string;
}

export const ELEMENT_CONFIGS: Record<ElementType, ElementConfig> = {
  [ElementType.NONE]: {
    color: '#3b82f6',
    projectileColor: '#60a5fa',
    stats: {},
    description: 'Basic attacks',
  },
  [ElementType.FIRE]: {
    color: '#ef4444',
    projectileColor: '#f97316',
    stats: { damage: 1.5, dotDamage: 5, dotDuration: 3, pierceCount: 2 },
    description: 'High damage + burn over time',
  },
  [ElementType.ICE]: {
    color: '#3b82f6',
    projectileColor: '#60a5fa',
    stats: { damage: 0.8, slowPercent: 0.5, slowDuration: 2, pierceCount: 3 },
    description: 'Slows enemies + pierces',
  },
  [ElementType.LIGHTNING]: {
    color: '#eab308',
    projectileColor: '#facc15',
    stats: { damage: 1.2, chainCount: 3, speed: 1.5 },
    description: 'Chains to nearby enemies',
  },
  [ElementType.POISON]: {
    color: '#22c55e',
    projectileColor: '#4ade80',
    stats: { damage: 0.6, dotDamage: 8, dotDuration: 5, pierceCount: 1 },
    description: 'Strong poison damage over time',
  },
  [ElementType.ARCANE]: {
    color: '#a855f7',
    projectileColor: '#c084fc',
    stats: { damage: 2, pierceCount: 5, range: 1.3 },
    description: 'High damage + extreme pierce',
  },
};
