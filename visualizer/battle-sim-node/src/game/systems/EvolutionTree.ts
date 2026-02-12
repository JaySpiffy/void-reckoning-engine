/**
 * EVOLUTION TREE - Complete 3-Tier Evolution Paths for All DNA Types
 * 
 * POKEMON-STYLE EVOLUTION SYSTEM:
 * - Stage 0 (Base): Starting forms unlocked at 20 DNA
 * - Stage 1 (Mid): Evolution at 50 DNA + secondary DNA + kills/time
 * - Stage 2 (Final): Ultimate form at 80+ DNA + special conditions
 * 
 * Each DNA type has its own evolution branch with unique abilities,
 * resistances, and visual transformations.
 */

import { DNAType } from '../types/core';
import { type EvolutionPath } from './DNACore';

// ============================================
// HELPER FUNCTIONS FOR EVOLUTION REQUIREMENTS
// ============================================

const baseReqs = (dnaType: DNAType, amount: number = 20) => ({
  minDNA: { [dnaType]: amount } as Partial<Record<DNAType, number>>,
  maxDNA: {},
  minKills: 0,
  minSurvivalTime: 0,
  minGeneration: 0,
});

const stage1Reqs = (
  primaryDNA: DNAType, 
  primaryAmount: number,
  secondaryDNA: DNAType,
  secondaryAmount: number,
  kills: number = 15,
  time: number = 120,
  maxDNA?: Partial<Record<DNAType, number>>
) => ({
  minDNA: { [primaryDNA]: primaryAmount, [secondaryDNA]: secondaryAmount } as Partial<Record<DNAType, number>>,
  maxDNA: maxDNA || {},
  minKills: kills,
  minSurvivalTime: time,
  minGeneration: 1,
});

const stage2Reqs = (
  primaryDNA: DNAType,
  primaryAmount: number,
  secondaryDNA: DNAType,
  secondaryAmount: number,
  kills: number = 40,
  time: number = 300,
  maxDNA?: Partial<Record<DNAType, number>>
) => ({
  minDNA: { [primaryDNA]: primaryAmount, [secondaryDNA]: secondaryAmount } as Partial<Record<DNAType, number>>,
  maxDNA: maxDNA || {},
  minKills: kills,
  minSurvivalTime: time,
  minGeneration: 2,
});

// ============================================
// FIRE BRANCH - 3 STAGES
// ============================================

const FIRE_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'emberling': {
    id: 'emberling',
    name: 'Emberling',
    description: 'A small spark of fire given form. Fast but fragile.',
    requirements: baseReqs(DNAType.FIRE, 20),
    bonuses: {
      healthMultiplier: 0.8,
      damageMultiplier: 1.3,
      speedMultiplier: 1.2,
      specialAbilities: ['fire_dash', 'ember_trail'],
      resistances: { [DNAType.FIRE]: 0.5, [DNAType.ICE]: 0.3 },
      weaknesses: { [DNAType.WATER]: 0.5, [DNAType.EARTH]: 0.3 },
    },
    appearance: {
      color: '#ff6b35',
      shape: 'humanoid',
      size: 0.9,
      particleEffect: 'ember_sparks',
    },
    nextEvolutions: ['flame_serpent', 'magma_core'],
  },

  // STAGE 1: Branch A - Speed/Damage
  'flame_serpent': {
    id: 'flame_serpent',
    name: 'Flame Serpent',
    description: 'A burning wyrm that leaves fire in its wake. High mobility.',
    requirements: stage1Reqs(DNAType.FIRE, 50, DNAType.REPTILE, 15, 20, 150, { [DNAType.WATER]: 20 }),
    bonuses: {
      healthMultiplier: 1.1,
      damageMultiplier: 1.6,
      speedMultiplier: 1.5,
      specialAbilities: ['flame_breath', 'serpentine_dash', 'burning_trail', 'fire_coil'],
      resistances: { [DNAType.FIRE]: 0.7, [DNAType.ICE]: 0.5, [DNAType.GRASS]: 0.4 },
      weaknesses: { [DNAType.WATER]: 0.7, [DNAType.EARTH]: 0.4 },
    },
    appearance: {
      color: '#ff4500',
      shape: 'serpentine',
      size: 1.3,
      particleEffect: 'flame_wisps',
    },
    nextEvolutions: ['inferno_drake'],
  },

  // STAGE 1: Branch B - Tank/Burst
  'magma_core': {
    id: 'magma_core',
    name: 'Magma Core',
    description: 'Living magma with earth armor. Slow but devastating.',
    requirements: stage1Reqs(DNAType.FIRE, 50, DNAType.EARTH, 30, 25, 180, { [DNAType.WIND]: 20 }),
    bonuses: {
      healthMultiplier: 2.2,
      damageMultiplier: 1.9,
      speedMultiplier: 0.6,
      specialAbilities: ['magma_armor', 'eruption', 'heat_aura', 'lava_pool'],
      resistances: { [DNAType.FIRE]: 0.9, [DNAType.EARTH]: 0.6, [DNAType.ICE]: 0.4 },
      weaknesses: { [DNAType.WATER]: 0.8, [DNAType.ICE]: 0.5 },
    },
    appearance: {
      color: '#8b0000',
      shape: 'humanoid',
      size: 1.6,
      particleEffect: 'magma_bubbles',
    },
    nextEvolutions: ['volcano_titan'],
  },

  // STAGE 2: Ultimate Fire Form A
  'inferno_drake': {
    id: 'inferno_drake',
    name: 'Inferno Drake',
    description: 'A dragon of pure flame. Destroys everything in its path.',
    requirements: stage2Reqs(DNAType.FIRE, 80, DNAType.REPTILE, 40, 50, 400),
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 2.5,
      speedMultiplier: 1.6,
      specialAbilities: ['dragon_flight', 'inferno_breath', 'wing_buffet', 'meteor_strike', 'flame_immunity'],
      resistances: { [DNAType.FIRE]: 1.0, [DNAType.ICE]: 0.7, [DNAType.GRASS]: 0.6 },
      weaknesses: { [DNAType.WATER]: 0.5 },
    },
    appearance: {
      color: '#ff0000',
      shape: 'winged',
      size: 2.0,
      particleEffect: 'inferno_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Fire Form B
  'volcano_titan': {
    id: 'volcano_titan',
    name: 'Volcano Titan',
    description: 'A walking volcano. Its steps shake the earth.',
    requirements: stage2Reqs(DNAType.FIRE, 80, DNAType.EARTH, 60, 60, 450),
    bonuses: {
      healthMultiplier: 3.5,
      damageMultiplier: 2.2,
      speedMultiplier: 0.5,
      specialAbilities: ['volcanic_eruption', 'magma_fist', 'earth_shatter', 'lava_tsunami', 'magma_immunity'],
      resistances: { [DNAType.FIRE]: 1.0, [DNAType.EARTH]: 0.8, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.WATER]: 0.6, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#4a0000',
      shape: 'humanoid',
      size: 2.5,
      particleEffect: 'volcano_eruption',
    },
    nextEvolutions: [],
  },
};

// ============================================
// ICE BRANCH - 3 STAGES
// ============================================

const ICE_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'frost_mote': {
    id: 'frost_mote',
    name: 'Frost Mote',
    description: 'A floating crystal of ice. Fragile but freezing.',
    requirements: baseReqs(DNAType.ICE, 20),
    bonuses: {
      healthMultiplier: 0.75,
      damageMultiplier: 1.2,
      speedMultiplier: 1.0,
      specialAbilities: ['frost_bolt', 'chilling_aura'],
      resistances: { [DNAType.ICE]: 0.6, [DNAType.WATER]: 0.3 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.LIGHTNING]: 0.3 },
    },
    appearance: {
      color: '#a5f3fc',
      shape: 'amorphous',
      size: 0.8,
      particleEffect: 'frost_sparkles',
    },
    nextEvolutions: ['frost_wraith', 'glacier_golem'],
  },

  // STAGE 1: Branch A - Control/Debuff
  'frost_wraith': {
    id: 'frost_wraith',
    name: 'Frost Wraith',
    description: 'An ethereal being of pure cold. Freezes enemies solid.',
    requirements: stage1Reqs(DNAType.ICE, 50, DNAType.VOID, 15, 18, 140),
    bonuses: {
      healthMultiplier: 0.9,
      damageMultiplier: 1.4,
      speedMultiplier: 1.3,
      specialAbilities: ['freeze_ray', 'ice_prison', 'ethereal_chill', 'blizzard_step'],
      resistances: { [DNAType.ICE]: 0.8, [DNAType.VOID]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.7, [DNAType.LIGHT]: 0.4 },
    },
    appearance: {
      color: '#cffafe',
      shape: 'amorphous',
      size: 1.1,
      particleEffect: 'freezing_mist',
    },
    nextEvolutions: ['absolute_zero'],
  },

  // STAGE 1: Branch B - Tank
  'glacier_golem': {
    id: 'glacier_golem',
    name: 'Glacier Golem',
    description: 'A massive construct of ancient ice. Nearly unbreakable.',
    requirements: stage1Reqs(DNAType.ICE, 50, DNAType.EARTH, 25, 22, 160),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 1.3,
      speedMultiplier: 0.5,
      specialAbilities: ['ice_armor', 'glacier_slam', 'frozen_ground', 'ice_barrier'],
      resistances: { [DNAType.ICE]: 0.9, [DNAType.EARTH]: 0.5, [DNAType.PHYSICAL]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.8, [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#0891b2',
      shape: 'humanoid',
      size: 1.8,
      particleEffect: 'glacier_cracks',
    },
    nextEvolutions: ['frost_colossus'],
  },

  // STAGE 2: Ultimate Ice Form A
  'absolute_zero': {
    id: 'absolute_zero',
    name: 'Absolute Zero',
    description: 'The embodiment of perfect cold. Stops molecular motion.',
    requirements: stage2Reqs(DNAType.ICE, 85, DNAType.VOID, 35, 45, 380),
    bonuses: {
      healthMultiplier: 1.2,
      damageMultiplier: 2.8,
      speedMultiplier: 1.4,
      specialAbilities: ['time_freeze', 'zero_point', 'molecular_stop', 'eternal_winter', 'phase_shift'],
      resistances: { [DNAType.ICE]: 1.0, [DNAType.VOID]: 0.6 },
      weaknesses: { [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#ecfeff',
      shape: 'amorphous',
      size: 1.5,
      particleEffect: 'absolute_zero_fog',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Ice Form B
  'frost_colossus': {
    id: 'frost_colossus',
    name: 'Frost Colossus',
    description: 'A mountain of living ice. Nothing can melt it.',
    requirements: stage2Reqs(DNAType.ICE, 85, DNAType.EARTH, 55, 55, 420),
    bonuses: {
      healthMultiplier: 4.0,
      damageMultiplier: 2.0,
      speedMultiplier: 0.4,
      specialAbilities: ['avalanche', 'ice_age', 'frozen_fortress', 'glacier_charge', 'permafrost'],
      resistances: { [DNAType.ICE]: 1.0, [DNAType.EARTH]: 0.7, [DNAType.PHYSICAL]: 0.6 },
      weaknesses: { [DNAType.FIRE]: 0.5 },
    },
    appearance: {
      color: '#164e63',
      shape: 'humanoid',
      size: 2.8,
      particleEffect: 'blizzard_surround',
    },
    nextEvolutions: [],
  },
};

// ============================================
// WATER BRANCH - 3 STAGES
// ============================================

const WATER_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'tadpole': {
    id: 'tadpole',
    name: 'Tadpole',
    description: 'An aquatic larval form. Fast in water, slow on land.',
    requirements: baseReqs(DNAType.WATER, 20),
    bonuses: {
      healthMultiplier: 0.85,
      damageMultiplier: 0.9,
      speedMultiplier: 1.3,
      specialAbilities: ['aquatic_dash', 'water_bolt', 'hydration'],
      resistances: { [DNAType.WATER]: 0.7, [DNAType.FIRE]: 0.4 },
      weaknesses: { [DNAType.LIGHTNING]: 0.6, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#3b82f6',
      shape: 'serpentine',
      size: 0.8,
      particleEffect: 'water_droplets',
    },
    nextEvolutions: ['riptide_serpent', 'coral_guardian'],
  },

  // STAGE 1: Branch A - Speed/Mobility
  'riptide_serpent': {
    id: 'riptide_serpent',
    name: 'Riptide Serpent',
    description: 'A serpent that commands currents. Drags enemies underwater.',
    requirements: stage1Reqs(DNAType.WATER, 50, DNAType.AQUATIC, 20, 20, 150),
    bonuses: {
      healthMultiplier: 1.1,
      damageMultiplier: 1.3,
      speedMultiplier: 1.6,
      specialAbilities: ['riptide', 'water_vortex', 'drowning_grasp', 'tidal_dash'],
      resistances: { [DNAType.WATER]: 0.8, [DNAType.FIRE]: 0.5 },
      weaknesses: { [DNAType.LIGHTNING]: 0.7, [DNAType.ICE]: 0.5 },
    },
    appearance: {
      color: '#0ea5e9',
      shape: 'serpentine',
      size: 1.4,
      particleEffect: 'water_currents',
    },
    nextEvolutions: ['leviathan'],
  },

  // STAGE 1: Branch B - Defense/Sustain
  'coral_guardian': {
    id: 'coral_guardian',
    name: 'Coral Guardian',
    description: 'A living reef. Regenerates and protects allies.',
    requirements: stage1Reqs(DNAType.WATER, 50, DNAType.EARTH, 25, 18, 140),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 1.0,
      speedMultiplier: 0.7,
      specialAbilities: ['coral_armor', 'regeneration_aura', 'healing_wave', 'barrier_reef'],
      resistances: { [DNAType.WATER]: 0.9, [DNAType.EARTH]: 0.4 },
      weaknesses: { [DNAType.POISON]: 0.5, [DNAType.LIGHTNING]: 0.5 },
    },
    appearance: {
      color: '#f97316',
      shape: 'humanoid',
      size: 1.5,
      particleEffect: 'coral_particles',
    },
    nextEvolutions: ['abyssal_titan'],
  },

  // STAGE 2: Ultimate Water Form A
  'leviathan': {
    id: 'leviathan',
    name: 'Leviathan',
    description: 'The ancient sea monster. Commands all waters.',
    requirements: stage2Reqs(DNAType.WATER, 80, DNAType.AQUATIC, 50, 50, 400),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 2.2,
      speedMultiplier: 1.5,
      specialAbilities: ['tsunami', 'maelstrom', 'depth_charge', 'abyssal_swallow', 'tidal_wave'],
      resistances: { [DNAType.WATER]: 1.0, [DNAType.FIRE]: 0.7 },
      weaknesses: { [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#1e3a8a',
      shape: 'serpentine',
      size: 2.5,
      particleEffect: 'leviathan_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Water Form B
  'abyssal_titan': {
    id: 'abyssal_titan',
    name: 'Abyssal Titan',
    description: 'Lord of the deepest oceans. Pressure itself obeys.',
    requirements: stage2Reqs(DNAType.WATER, 80, DNAType.EARTH, 60, 55, 450),
    bonuses: {
      healthMultiplier: 3.5,
      damageMultiplier: 1.8,
      speedMultiplier: 0.6,
      specialAbilities: ['crushing_depth', 'pressure_wave', 'abyssal_armor', 'hydro_cannon', 'deep_regen'],
      resistances: { [DNAType.WATER]: 1.0, [DNAType.EARTH]: 0.6, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.LIGHTNING]: 0.5 },
    },
    appearance: {
      color: '#0c4a6e',
      shape: 'humanoid',
      size: 2.2,
      particleEffect: 'abyssal_pressure',
    },
    nextEvolutions: [],
  },
};

// ============================================
// EARTH BRANCH - 3 STAGES
// ============================================

const EARTH_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'pebble_sprite': {
    id: 'pebble_sprite',
    name: 'Pebble Sprite',
    description: 'A small earth spirit. Tough for its size.',
    requirements: baseReqs(DNAType.EARTH, 20),
    bonuses: {
      healthMultiplier: 1.2,
      damageMultiplier: 0.9,
      speedMultiplier: 0.8,
      specialAbilities: ['rock_throw', 'stone_skin'],
      resistances: { [DNAType.EARTH]: 0.5, [DNAType.FIRE]: 0.3 },
      weaknesses: { [DNAType.WATER]: 0.4, [DNAType.WIND]: 0.3 },
    },
    appearance: {
      color: '#92400e',
      shape: 'humanoid',
      size: 0.85,
      particleEffect: 'dust_clouds',
    },
    nextEvolutions: ['stone_golem', 'crystal_warden'],
  },

  // STAGE 1: Branch A - Pure Tank
  'stone_golem': {
    id: 'stone_golem',
    name: 'Stone Golem',
    description: 'A construct of solid rock. Immovable object.',
    requirements: stage1Reqs(DNAType.EARTH, 55, DNAType.CRYSTAL, 15, 20, 160),
    bonuses: {
      healthMultiplier: 2.8,
      damageMultiplier: 1.2,
      speedMultiplier: 0.5,
      specialAbilities: ['stone_fist', 'earth_shake', 'rock_armor', 'seismic_slam'],
      resistances: { [DNAType.EARTH]: 0.8, [DNAType.PHYSICAL]: 0.6, [DNAType.FIRE]: 0.4 },
      weaknesses: { [DNAType.WATER]: 0.5, [DNAType.WIND]: 0.4 },
    },
    appearance: {
      color: '#57534e',
      shape: 'humanoid',
      size: 1.7,
      particleEffect: 'stone_fragments',
    },
    nextEvolutions: ['mountain_king'],
  },

  // STAGE 1: Branch B - Crystal/Offense
  'crystal_warden': {
    id: 'crystal_warden',
    name: 'Crystal Warden',
    description: 'Sharp crystals grow from its body. Reflects damage.',
    requirements: stage1Reqs(DNAType.EARTH, 50, DNAType.CRYSTAL, 30, 18, 150),
    bonuses: {
      healthMultiplier: 1.6,
      damageMultiplier: 1.5,
      speedMultiplier: 0.8,
      specialAbilities: ['crystal_spikes', 'prism_beam', 'reflect_shield', 'shard_storm'],
      resistances: { [DNAType.EARTH]: 0.7, [DNAType.CRYSTAL]: 0.6, [DNAType.LIGHT]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.4, [DNAType.SLIME]: 0.3 },
    },
    appearance: {
      color: '#a855f7',
      shape: 'humanoid',
      size: 1.4,
      particleEffect: 'crystal_shimmer',
    },
    nextEvolutions: ['diamond_overlord'],
  },

  // STAGE 2: Ultimate Earth Form A
  'mountain_king': {
    id: 'mountain_king',
    name: 'Mountain King',
    description: 'A walking mountain. The earth itself obeys.',
    requirements: stage2Reqs(DNAType.EARTH, 85, DNAType.CRYSTAL, 40, 55, 450),
    bonuses: {
      healthMultiplier: 4.5,
      damageMultiplier: 2.0,
      speedMultiplier: 0.4,
      specialAbilities: ['mountain_drop', 'continental_drift', 'earthquake', 'stone_prison', 'lithify'],
      resistances: { [DNAType.EARTH]: 1.0, [DNAType.PHYSICAL]: 0.7, [DNAType.FIRE]: 0.5 },
      weaknesses: { [DNAType.WIND]: 0.4 },
    },
    appearance: {
      color: '#451a03',
      shape: 'humanoid',
      size: 3.0,
      particleEffect: 'mountain_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Earth Form B
  'diamond_overlord': {
    id: 'diamond_overlord',
    name: 'Diamond Overlord',
    description: 'Body of pure diamond. Unbreakable and brilliant.',
    requirements: stage2Reqs(DNAType.EARTH, 80, DNAType.CRYSTAL, 70, 50, 420),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 2.5,
      speedMultiplier: 0.9,
      specialAbilities: ['diamond_edge', 'prism_cannon', 'reflect_all', 'crystal_fortress', 'brilliant_burst'],
      resistances: { [DNAType.EARTH]: 0.9, [DNAType.CRYSTAL]: 1.0, [DNAType.PHYSICAL]: 0.8 },
      weaknesses: { [DNAType.CHAOS]: 0.4 },
    },
    appearance: {
      color: '#e0e7ff',
      shape: 'humanoid',
      size: 1.8,
      particleEffect: 'diamond_sparkle',
    },
    nextEvolutions: [],
  },
};

// ============================================
// WIND BRANCH - 3 STAGES
// ============================================

const WIND_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'zephyr': {
    id: 'zephyr',
    name: 'Zephyr',
    description: 'A gentle breeze given form. Fast but weak.',
    requirements: baseReqs(DNAType.WIND, 20),
    bonuses: {
      healthMultiplier: 0.7,
      damageMultiplier: 1.0,
      speedMultiplier: 1.4,
      specialAbilities: ['gust', 'wind_dash'],
      resistances: { [DNAType.WIND]: 0.5, [DNAType.EARTH]: 0.3 },
      weaknesses: { [DNAType.ICE]: 0.4, [DNAType.LIGHTNING]: 0.3 },
    },
    appearance: {
      color: '#a5f3fc',
      shape: 'amorphous',
      size: 0.9,
      particleEffect: 'wind_trails',
    },
    nextEvolutions: ['storm_harpy', 'tempest_knight'],
  },

  // STAGE 1: Branch A - Mobility/Hit&Run
  'storm_harpy': {
    id: 'storm_harpy',
    name: 'Storm Harpy',
    description: 'A winged predator of the skies. Strikes from above.',
    requirements: stage1Reqs(DNAType.WIND, 50, DNAType.BEAST, 15, 20, 140),
    bonuses: {
      healthMultiplier: 0.9,
      damageMultiplier: 1.4,
      speedMultiplier: 1.7,
      specialAbilities: ['dive_bomb', 'wind_slice', 'feather_storm', 'sky_dance'],
      resistances: { [DNAType.WIND]: 0.8, [DNAType.EARTH]: 0.5 },
      weaknesses: { [DNAType.ICE]: 0.5, [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#22d3ee',
      shape: 'winged',
      size: 1.2,
      particleEffect: 'storm_feathers',
    },
    nextEvolutions: ['hurricane_queen'],
  },

  // STAGE 1: Branch B - Control/AoE
  'tempest_knight': {
    id: 'tempest_knight',
    name: 'Tempest Knight',
    description: 'A warrior wrapped in storm clouds. Controls the battlefield.',
    requirements: stage1Reqs(DNAType.WIND, 50, DNAType.LIGHTNING, 20, 22, 160),
    bonuses: {
      healthMultiplier: 1.4,
      damageMultiplier: 1.3,
      speedMultiplier: 1.3,
      specialAbilities: ['tempest_armor', 'cyclone', 'thunder_blade', 'wind_wall'],
      resistances: { [DNAType.WIND]: 0.8, [DNAType.LIGHTNING]: 0.5 },
      weaknesses: { [DNAType.EARTH]: 0.4, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#0e7490',
      shape: 'humanoid',
      size: 1.4,
      particleEffect: 'tempest_clouds',
    },
    nextEvolutions: ['storm_god'],
  },

  // STAGE 2: Ultimate Wind Form A
  'hurricane_queen': {
    id: 'hurricane_queen',
    name: 'Hurricane Queen',
    description: 'The eye of the storm. Nothing can catch her.',
    requirements: stage2Reqs(DNAType.WIND, 80, DNAType.BEAST, 40, 50, 380),
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 2.2,
      speedMultiplier: 2.0,
      specialAbilities: ['hurricane', 'eye_of_storm', 'sonic_boom', 'tornado_dance', 'wind_mastery'],
      resistances: { [DNAType.WIND]: 1.0, [DNAType.EARTH]: 0.7 },
      weaknesses: { [DNAType.ICE]: 0.3 },
    },
    appearance: {
      color: '#06b6d4',
      shape: 'winged',
      size: 1.6,
      particleEffect: 'hurricane_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Wind Form B
  'storm_god': {
    id: 'storm_god',
    name: 'Storm God',
    description: 'Master of thunder and wind. The sky is their domain.',
    requirements: stage2Reqs(DNAType.WIND, 80, DNAType.LIGHTNING, 55, 55, 420),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 2.0,
      speedMultiplier: 1.5,
      specialAbilities: ['divine_thunder', 'storm_summon', 'lightning_strike', 'cloud_walk', 'judgment_bolt'],
      resistances: { [DNAType.WIND]: 1.0, [DNAType.LIGHTNING]: 0.8 },
      weaknesses: { [DNAType.EARTH]: 0.4 },
    },
    appearance: {
      color: '#fbbf24',
      shape: 'winged',
      size: 2.0,
      particleEffect: 'divine_storm',
    },
    nextEvolutions: [],
  },
};

// ============================================
// LIGHTNING BRANCH - 3 STAGES
// ============================================

const LIGHTNING_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'spark': {
    id: 'spark',
    name: 'Spark',
    description: 'A tiny electrical discharge. Fast but fragile.',
    requirements: baseReqs(DNAType.LIGHTNING, 20),
    bonuses: {
      healthMultiplier: 0.7,
      damageMultiplier: 1.2,
      speedMultiplier: 1.5,
      specialAbilities: ['zap', 'static_field'],
      resistances: { [DNAType.LIGHTNING]: 0.6, [DNAType.WIND]: 0.3 },
      weaknesses: { [DNAType.EARTH]: 0.5, [DNAType.WATER]: 0.4 },
    },
    appearance: {
      color: '#fef08a',
      shape: 'amorphous',
      size: 0.75,
      particleEffect: 'electric_sparks',
    },
    nextEvolutions: ['thunder_wolf', 'storm_wraith'],
  },

  // STAGE 1: Branch A - Beast/Speed
  'thunder_wolf': {
    id: 'thunder_wolf',
    name: 'Thunder Wolf',
    description: 'A lightning-fast predator. Strikes before enemies react.',
    requirements: stage1Reqs(DNAType.LIGHTNING, 50, DNAType.BEAST, 20, 22, 150),
    bonuses: {
      healthMultiplier: 1.1,
      damageMultiplier: 1.5,
      speedMultiplier: 1.8,
      specialAbilities: ['lightning_fang', 'thunder_dash', 'pack_howl', 'static_cling'],
      resistances: { [DNAType.LIGHTNING]: 0.8, [DNAType.BEAST]: 0.4 },
      weaknesses: { [DNAType.EARTH]: 0.6, [DNAType.WATER]: 0.4 },
    },
    appearance: {
      color: '#facc15',
      shape: 'quadruped',
      size: 1.3,
      particleEffect: 'thunder_crackle',
    },
    nextEvolutions: ['raiju'],
  },

  // STAGE 1: Branch B - Wraith/Chain
  'storm_wraith': {
    id: 'storm_wraith',
    name: 'Storm Wraith',
    description: 'An ethereal being of pure electricity. Chains through enemies.',
    requirements: stage1Reqs(DNAType.LIGHTNING, 50, DNAType.VOID, 15, 20, 160),
    bonuses: {
      healthMultiplier: 0.85,
      damageMultiplier: 1.6,
      speedMultiplier: 1.5,
      specialAbilities: ['chain_lightning', 'storm_form', 'static_discharge', 'thunder_clap'],
      resistances: { [DNAType.LIGHTNING]: 0.9, [DNAType.VOID]: 0.4 },
      weaknesses: { [DNAType.EARTH]: 0.7, [DNAType.ICE]: 0.3 },
    },
    appearance: {
      color: '#fef9c3',
      shape: 'amorphous',
      size: 1.1,
      particleEffect: 'storm_lightning',
    },
    nextEvolutions: ['thunder_god'],
  },

  // STAGE 2: Ultimate Lightning Form A
  'raiju': {
    id: 'raiju',
    name: 'Raiju',
    description: 'The thunder beast. Lightning itself given beast form.',
    requirements: stage2Reqs(DNAType.LIGHTNING, 85, DNAType.BEAST, 45, 55, 400),
    bonuses: {
      healthMultiplier: 1.5,
      damageMultiplier: 2.5,
      speedMultiplier: 2.0,
      specialAbilities: ['thunder_charge', 'lightning_spear', 'storm_howl', 'electrocute', 'speed_of_light'],
      resistances: { [DNAType.LIGHTNING]: 1.0, [DNAType.WIND]: 0.6 },
      weaknesses: { [DNAType.EARTH]: 0.4 },
    },
    appearance: {
      color: '#fbbf24',
      shape: 'quadruped',
      size: 1.8,
      particleEffect: 'raiju_thunder',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Lightning Form B
  'thunder_god': {
    id: 'thunder_god',
    name: 'Thunder God',
    description: 'Divine authority over all lightning. Judgment incarnate.',
    requirements: stage2Reqs(DNAType.LIGHTNING, 85, DNAType.VOID, 40, 60, 450),
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 2.8,
      speedMultiplier: 1.6,
      specialAbilities: ['divine_judgment', 'thunderstorm', 'lightning_form', 'smite', 'wrath_of_heaven'],
      resistances: { [DNAType.LIGHTNING]: 1.0, [DNAType.VOID]: 0.6 },
      weaknesses: { [DNAType.EARTH]: 0.3 },
    },
    appearance: {
      color: '#ffffff',
      shape: 'humanoid',
      size: 2.0,
      particleEffect: 'divine_lightning',
    },
    nextEvolutions: [],
  },
};

// ============================================
// POISON BRANCH - 3 STAGES
// ============================================

const POISON_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'venom_slime': {
    id: 'venom_slime',
    name: 'Venom Slime',
    description: 'A toxic blob. Weak but applies poison to everything.',
    requirements: baseReqs(DNAType.POISON, 20),
    bonuses: {
      healthMultiplier: 0.9,
      damageMultiplier: 0.85,
      speedMultiplier: 0.8,
      specialAbilities: ['poison_touch', 'toxic_sludge'],
      resistances: { [DNAType.POISON]: 0.6, [DNAType.FUNGUS]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.LIGHT]: 0.4 },
    },
    appearance: {
      color: '#84cc16',
      shape: 'amorphous',
      size: 0.85,
      particleEffect: 'toxic_bubbles',
    },
    nextEvolutions: ['viper', 'plague_rat'],
  },

  // STAGE 1: Branch A - Reptile/Venom
  'viper': {
    id: 'viper',
    name: 'Viper',
    description: 'A venomous serpent. One bite is fatal.',
    requirements: stage1Reqs(DNAType.POISON, 50, DNAType.REPTILE, 20, 20, 150),
    bonuses: {
      healthMultiplier: 1.0,
      damageMultiplier: 1.4,
      speedMultiplier: 1.2,
      specialAbilities: ['venom_fang', 'constrict', 'shed_skin', 'paralytic_bite'],
      resistances: { [DNAType.POISON]: 0.8, [DNAType.REPTILE]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#65a30d',
      shape: 'serpentine',
      size: 1.2,
      particleEffect: 'venom_drip',
    },
    nextEvolutions: ['basilisk'],
  },

  // STAGE 1: Branch B - Swarm/Plague
  'plague_rat': {
    id: 'plague_rat',
    name: 'Plague Rat',
    description: 'A disease carrier. Spreads infection everywhere.',
    requirements: stage1Reqs(DNAType.POISON, 50, DNAType.BEAST, 15, 18, 140),
    bonuses: {
      healthMultiplier: 1.1,
      damageMultiplier: 1.1,
      speedMultiplier: 1.1,
      specialAbilities: ['plague_bite', 'disease_cloud', 'swarm_call', 'infectious_wound'],
      resistances: { [DNAType.POISON]: 0.8, [DNAType.FUNGUS]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.LIGHT]: 0.5 },
    },
    appearance: {
      color: '#3f6212',
      shape: 'quadruped',
      size: 1.0,
      particleEffect: 'plague_miasma',
    },
    nextEvolutions: ['plague_lord'],
  },

  // STAGE 2: Ultimate Poison Form A
  'basilisk': {
    id: 'basilisk',
    name: 'Basilisk',
    description: 'The king of serpents. Its gaze petrifies.',
    requirements: stage2Reqs(DNAType.POISON, 80, DNAType.REPTILE, 50, 50, 400),
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 2.3,
      speedMultiplier: 1.1,
      specialAbilities: ['petrify', 'death_gaze', 'venom_storm', 'serpent_coil', 'toxic_aura'],
      resistances: { [DNAType.POISON]: 1.0, [DNAType.REPTILE]: 0.7, [DNAType.EARTH]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#14532d',
      shape: 'serpentine',
      size: 2.0,
      particleEffect: 'basilisk_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Poison Form B
  'plague_lord': {
    id: 'plague_lord',
    name: 'Plague Lord',
    description: 'Master of disease. Entire kingdoms fall to its touch.',
    requirements: stage2Reqs(DNAType.POISON, 85, DNAType.FUNGUS, 40, 55, 420),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 1.8,
      speedMultiplier: 0.9,
      specialAbilities: ['plague_wave', 'undead_legion', 'pandemic', 'rot_field', 'disease_mastery'],
      resistances: { [DNAType.POISON]: 1.0, [DNAType.FUNGUS]: 0.8, [DNAType.PHYSICAL]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.LIGHT]: 0.4 },
    },
    appearance: {
      color: '#1a2e05',
      shape: 'humanoid',
      size: 1.8,
      particleEffect: 'plague_lord_aura',
    },
    nextEvolutions: [],
  },
};

// ============================================
// VOID BRANCH - 3 STAGES
// ============================================

const VOID_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'shadow_mote': {
    id: 'shadow_mote',
    name: 'Shadow Mote',
    description: 'A fragment of darkness. Weak but hard to see.',
    requirements: baseReqs(DNAType.VOID, 20),
    bonuses: {
      healthMultiplier: 0.8,
      damageMultiplier: 1.1,
      speedMultiplier: 1.1,
      specialAbilities: ['shadow_step', 'darkness'],
      resistances: { [DNAType.VOID]: 0.5, [DNAType.LIGHT]: 0.3 },
      weaknesses: { [DNAType.LIGHT]: 0.6, [DNAType.FIRE]: 0.3 },
    },
    appearance: {
      color: '#1e1b4b',
      shape: 'amorphous',
      size: 0.85,
      particleEffect: 'shadow_wisps',
    },
    nextEvolutions: ['shadow_assassin', 'void_horror'],
  },

  // STAGE 1: Branch A - Assassin
  'shadow_assassin': {
    id: 'shadow_assassin',
    name: 'Shadow Assassin',
    description: 'A killer from the darkness. Strikes unseen.',
    requirements: stage1Reqs(DNAType.VOID, 50, DNAType.BEAST, 15, 25, 160),
    bonuses: {
      healthMultiplier: 0.95,
      damageMultiplier: 1.8,
      speedMultiplier: 1.4,
      specialAbilities: ['backstab', 'shadow_clone', 'vanish', 'assassinate'],
      resistances: { [DNAType.VOID]: 0.7, [DNAType.LIGHT]: 0.4 },
      weaknesses: { [DNAType.LIGHT]: 0.7, [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#0f0f23',
      shape: 'humanoid',
      size: 1.1,
      particleEffect: 'shadow_blades',
    },
    nextEvolutions: ['night_king'],
  },

  // STAGE 1: Branch B - Horror/Tank
  'void_horror': {
    id: 'void_horror',
    name: 'Void Horror',
    description: 'A creature from beyond reality. Maddening to behold.',
    requirements: stage1Reqs(DNAType.VOID, 55, DNAType.CHAOS, 15, 22, 180),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 1.3,
      speedMultiplier: 0.8,
      specialAbilities: ['madness_aura', 'void_tentacles', 'reality_tear', 'consume_sanity'],
      resistances: { [DNAType.VOID]: 0.9, [DNAType.CHAOS]: 0.5 },
      weaknesses: { [DNAType.LIGHT]: 0.8, [DNAType.ARCANE]: 0.4 },
    },
    appearance: {
      color: '#000000',
      shape: 'amorphous',
      size: 1.6,
      particleEffect: 'void_eyes',
    },
    nextEvolutions: ['eldritch_abomination'],
  },

  // STAGE 2: Ultimate Void Form A
  'night_king': {
    id: 'night_king',
    name: 'Night King',
    description: 'Ruler of shadows. Darkness itself obeys.',
    requirements: stage2Reqs(DNAType.VOID, 80, DNAType.BEAST, 40, 60, 420),
    bonuses: {
      healthMultiplier: 1.4,
      damageMultiplier: 2.5,
      speedMultiplier: 1.5,
      specialAbilities: ['shadow_realm', 'nightfall', 'shadow_army', 'death_mark', 'eternal_night'],
      resistances: { [DNAType.VOID]: 1.0, [DNAType.LIGHT]: 0.5 },
      weaknesses: { [DNAType.LIGHT]: 0.5 },
    },
    appearance: {
      color: '#020617',
      shape: 'humanoid',
      size: 1.7,
      particleEffect: 'night_king_crown',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Void Form B
  'eldritch_abomination': {
    id: 'eldritch_abomination',
    name: 'Eldritch Abomination',
    description: 'Beyond comprehension. Reality warps around it.',
    requirements: stage2Reqs(DNAType.VOID, 85, DNAType.CHAOS, 50, 55, 480),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 2.0,
      speedMultiplier: 0.7,
      specialAbilities: ['reality_break', 'void_portal', 'insanity_wave', 'dimensional_shift', 'cosmic_horror'],
      resistances: { [DNAType.VOID]: 1.0, [DNAType.CHAOS]: 0.8, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.LIGHT]: 0.6 },
    },
    appearance: {
      color: '#1a0a2e',
      shape: 'amorphous',
      size: 2.5,
      particleEffect: 'eldritch_tentacles',
    },
    nextEvolutions: [],
  },
};

// ============================================
// LIGHT BRANCH - 3 STAGES
// ============================================

const LIGHT_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'luminous_mote': {
    id: 'luminous_mote',
    name: 'Luminous Mote',
    description: 'A spark of holy light. Weak but radiant.',
    requirements: baseReqs(DNAType.LIGHT, 20),
    bonuses: {
      healthMultiplier: 0.85,
      damageMultiplier: 1.15,
      speedMultiplier: 1.1,
      specialAbilities: ['holy_bolt', 'radiance'],
      resistances: { [DNAType.LIGHT]: 0.6, [DNAType.VOID]: 0.4 },
      weaknesses: { [DNAType.VOID]: 0.4, [DNAType.POISON]: 0.3 },
    },
    appearance: {
      color: '#fef3c7',
      shape: 'amorphous',
      size: 0.85,
      particleEffect: 'holy_sparkles',
    },
    nextEvolutions: ['paladin', 'seraph'],
  },

  // STAGE 1: Branch A - Warrior/Tank
  'paladin': {
    id: 'paladin',
    name: 'Paladin',
    description: 'A holy warrior. Protects allies and smites evil.',
    requirements: stage1Reqs(DNAType.LIGHT, 50, DNAType.EARTH, 20, 20, 160),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 1.3,
      speedMultiplier: 0.9,
      specialAbilities: ['holy_smite', 'divine_shield', 'blessing', 'consecration'],
      resistances: { [DNAType.LIGHT]: 0.8, [DNAType.VOID]: 0.5, [DNAType.EARTH]: 0.4 },
      weaknesses: { [DNAType.VOID]: 0.5, [DNAType.CHAOS]: 0.3 },
    },
    appearance: {
      color: '#fbbf24',
      shape: 'humanoid',
      size: 1.5,
      particleEffect: 'holy_aura',
    },
    nextEvolutions: ['divine_champion'],
  },

  // STAGE 1: Branch B - Angel/Support
  'seraph': {
    id: 'seraph',
    name: 'Seraph',
    description: 'A celestial being. Heals and purifies.',
    requirements: stage1Reqs(DNAType.LIGHT, 50, DNAType.WIND, 20, 18, 150),
    bonuses: {
      healthMultiplier: 1.2,
      damageMultiplier: 1.2,
      speedMultiplier: 1.3,
      specialAbilities: ['healing_light', 'purify', 'angelic_flight', 'resurrection'],
      resistances: { [DNAType.LIGHT]: 0.8, [DNAType.WIND]: 0.4 },
      weaknesses: { [DNAType.VOID]: 0.5, [DNAType.POISON]: 0.4 },
    },
    appearance: {
      color: '#fffbeb',
      shape: 'winged',
      size: 1.3,
      particleEffect: 'angelic_wings',
    },
    nextEvolutions: ['archangel'],
  },

  // STAGE 2: Ultimate Light Form A
  'divine_champion': {
    id: 'divine_champion',
    name: 'Divine Champion',
    description: 'The chosen of the gods. Unstoppable force of justice.',
    requirements: stage2Reqs(DNAType.LIGHT, 80, DNAType.EARTH, 50, 55, 450),
    bonuses: {
      healthMultiplier: 3.0,
      damageMultiplier: 2.0,
      speedMultiplier: 1.0,
      specialAbilities: ['divine_judgment', 'holy_wrath', 'godly_shield', 'smite_evil', 'avatar_of_light'],
      resistances: { [DNAType.LIGHT]: 1.0, [DNAType.VOID]: 0.7, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.CHAOS]: 0.4 },
    },
    appearance: {
      color: '#f59e0b',
      shape: 'humanoid',
      size: 2.0,
      particleEffect: 'divine_champion_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Light Form B
  'archangel': {
    id: 'archangel',
    name: 'Archangel',
    description: 'A messenger of the divine. Brings salvation or doom.',
    requirements: stage2Reqs(DNAType.LIGHT, 80, DNAType.WIND, 50, 50, 420),
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 1.8,
      speedMultiplier: 1.5,
      specialAbilities: ['mass_resurrection', 'divine_intervention', 'trumpet_of_doom', 'heavenly_host', 'ascension'],
      resistances: { [DNAType.LIGHT]: 1.0, [DNAType.WIND]: 0.6 },
      weaknesses: { [DNAType.VOID]: 0.4 },
    },
    appearance: {
      color: '#ffffff',
      shape: 'winged',
      size: 2.2,
      particleEffect: 'archangel_glory',
    },
    nextEvolutions: [],
  },
};

// ============================================
// GRASS BRANCH - 3 STAGES
// ============================================

const GRASS_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'sproutling': {
    id: 'sproutling',
    name: 'Sproutling',
    description: 'A young plant creature. Weak but regenerates quickly.',
    requirements: baseReqs(DNAType.GRASS, 20),
    bonuses: {
      healthMultiplier: 0.9,
      damageMultiplier: 0.8,
      speedMultiplier: 0.9,
      specialAbilities: ['regrowth', 'thorn_shot', 'photosynthesis'],
      resistances: { [DNAType.GRASS]: 0.5, [DNAType.EARTH]: 0.3 },
      weaknesses: { [DNAType.FIRE]: 0.7, [DNAType.POISON]: 0.4 },
    },
    appearance: {
      color: '#4ade80',
      shape: 'humanoid',
      size: 0.85,
      particleEffect: 'falling_leaves',
    },
    nextEvolutions: ['vine_lasher', 'treant_sapling'],
  },

  // STAGE 1: Branch A - Offense/Control
  'vine_lasher': {
    id: 'vine_lasher',
    name: 'Vine Lasher',
    description: 'Whip-like vines extend from its body. High range damage.',
    requirements: stage1Reqs(DNAType.GRASS, 50, DNAType.BEAST, 15, 18, 140, { [DNAType.FIRE]: 25 }),
    bonuses: {
      healthMultiplier: 1.1,
      damageMultiplier: 1.4,
      speedMultiplier: 1.1,
      specialAbilities: ['vine_whip', 'entangle', 'thorn_armor', 'strangle'],
      resistances: { [DNAType.GRASS]: 0.7, [DNAType.EARTH]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.8, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#16a34a',
      shape: 'humanoid',
      size: 1.2,
      particleEffect: 'vine_growth',
    },
    nextEvolutions: ['jungle_tyrant'],
  },

  // STAGE 1: Branch B - Tank/Sustain
  'treant_sapling': {
    id: 'treant_sapling',
    name: 'Treant Sapling',
    description: 'A young tree spirit. Tough and regenerating.',
    requirements: stage1Reqs(DNAType.GRASS, 50, DNAType.EARTH, 30, 20, 160),
    bonuses: {
      healthMultiplier: 2.2,
      damageMultiplier: 1.0,
      speedMultiplier: 0.6,
      specialAbilities: ['bark_skin', 'root_grasp', 'nature_heal', 'forest_aura'],
      resistances: { [DNAType.GRASS]: 0.8, [DNAType.EARTH]: 0.6 },
      weaknesses: { [DNAType.FIRE]: 0.8, [DNAType.ICE]: 0.5 },
    },
    appearance: {
      color: '#5d4a37',
      shape: 'humanoid',
      size: 1.6,
      particleEffect: 'tree_rustle',
    },
    nextEvolutions: ['world_tree'],
  },

  // STAGE 2: Ultimate Grass Form A
  'jungle_tyrant': {
    id: 'jungle_tyrant',
    name: 'Jungle Tyrant',
    description: 'The apex predator of the plant kingdom. All flora obeys.',
    requirements: stage2Reqs(DNAType.GRASS, 80, DNAType.BEAST, 45, 50, 400),
    bonuses: {
      healthMultiplier: 1.6,
      damageMultiplier: 2.2,
      speedMultiplier: 1.2,
      specialAbilities: ['jungle_overgrowth', 'predator_vines', 'spore_cloud', 'nature_wrath', 'regeneration'],
      resistances: { [DNAType.GRASS]: 1.0, [DNAType.EARTH]: 0.6, [DNAType.POISON]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.5 },
    },
    appearance: {
      color: '#15803d',
      shape: 'humanoid',
      size: 1.8,
      particleEffect: 'jungle_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Grass Form B
  'world_tree': {
    id: 'world_tree',
    name: 'World Tree',
    description: 'An ancient tree of legend. Life itself flows through it.',
    requirements: stage2Reqs(DNAType.GRASS, 85, DNAType.EARTH, 60, 55, 450),
    bonuses: {
      healthMultiplier: 4.0,
      damageMultiplier: 1.5,
      speedMultiplier: 0.4,
      specialAbilities: ['world_root', 'life_bloom', 'nature_blessing', 'forest_sanctuary', 'eternal_growth'],
      resistances: { [DNAType.GRASS]: 1.0, [DNAType.EARTH]: 0.8, [DNAType.LIGHT]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.6 },
    },
    appearance: {
      color: '#3f2e18',
      shape: 'humanoid',
      size: 2.8,
      particleEffect: 'world_tree_aura',
    },
    nextEvolutions: [],
  },
};

// ============================================
// FUNGUS BRANCH - 3 STAGES
// ============================================

const FUNGUS_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'sporeling': {
    id: 'sporeling',
    name: 'Sporeling',
    description: 'A small mushroom creature. Spreads spores everywhere.',
    requirements: baseReqs(DNAType.FUNGUS, 20),
    bonuses: {
      healthMultiplier: 0.95,
      damageMultiplier: 0.85,
      speedMultiplier: 0.85,
      specialAbilities: ['spore_cloud', 'regenerate'],
      resistances: { [DNAType.FUNGUS]: 0.5, [DNAType.POISON]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.LIGHT]: 0.4 },
    },
    appearance: {
      color: '#c084fc',
      shape: 'humanoid',
      size: 0.8,
      particleEffect: 'spore_puff',
    },
    nextEvolutions: ['myconid', 'decay_spreader'],
  },

  // STAGE 1: Branch A - Controller
  'myconid': {
    id: 'myconid',
    name: 'Myconid',
    description: 'A fungal humanoid. Controls minds with spores.',
    requirements: stage1Reqs(DNAType.FUNGUS, 50, DNAType.VOID, 15, 18, 150),
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 1.1,
      speedMultiplier: 0.9,
      specialAbilities: ['mind_spores', 'fungal_growth', 'spore_burst', 'hive_mind'],
      resistances: { [DNAType.FUNGUS]: 0.8, [DNAType.VOID]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.7, [DNAType.LIGHT]: 0.5 },
    },
    appearance: {
      color: '#a855f7',
      shape: 'humanoid',
      size: 1.3,
      particleEffect: 'mind_spores',
    },
    nextEvolutions: ['fungal_overmind'],
  },

  // STAGE 1: Branch B - Decay
  'decay_spreader': {
    id: 'decay_spreader',
    name: 'Decay Spreader',
    description: 'Accelerates rot and decay. Nothing lasts near it.',
    requirements: stage1Reqs(DNAType.FUNGUS, 50, DNAType.POISON, 25, 20, 160),
    bonuses: {
      healthMultiplier: 1.4,
      damageMultiplier: 1.2,
      speedMultiplier: 0.8,
      specialAbilities: ['decay_aura', 'rot_touch', 'decomposition', 'plague_spores'],
      resistances: { [DNAType.FUNGUS]: 0.9, [DNAType.POISON]: 0.6 },
      weaknesses: { [DNAType.FIRE]: 0.8, [DNAType.LIGHT]: 0.5 },
    },
    appearance: {
      color: '#3f6212',
      shape: 'amorphous',
      size: 1.4,
      particleEffect: 'decay_miasma',
    },
    nextEvolutions: ['rot_god'],
  },

  // STAGE 2: Ultimate Fungus Form A
  'fungal_overmind': {
    id: 'fungal_overmind',
    name: 'Fungal Overmind',
    description: 'A collective consciousness. Controls an army of spores.',
    requirements: stage2Reqs(DNAType.FUNGUS, 80, DNAType.VOID, 40, 50, 420),
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 1.8,
      speedMultiplier: 0.9,
      specialAbilities: ['mind_control', 'spore_army', 'collective_consciousness', 'fungal_network', 'dominate'],
      resistances: { [DNAType.FUNGUS]: 1.0, [DNAType.VOID]: 0.6, [DNAType.POISON]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.5 },
    },
    appearance: {
      color: '#7c3aed',
      shape: 'amorphous',
      size: 1.8,
      particleEffect: 'overmind_spores',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Fungus Form B
  'rot_god': {
    id: 'rot_god',
    name: 'Rot God',
    description: 'Entropy given form. All things return to it.',
    requirements: stage2Reqs(DNAType.FUNGUS, 85, DNAType.POISON, 50, 55, 450),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 2.0,
      speedMultiplier: 0.6,
      specialAbilities: ['entropy_field', 'age_touch', 'decrepify', 'rot_wave', 'return_to_dust'],
      resistances: { [DNAType.FUNGUS]: 1.0, [DNAType.POISON]: 0.8, [DNAType.PHYSICAL]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.LIGHT]: 0.4 },
    },
    appearance: {
      color: '#1a2e05',
      shape: 'amorphous',
      size: 2.2,
      particleEffect: 'rot_god_aura',
    },
    nextEvolutions: [],
  },
};

// ============================================
// INSECT BRANCH - 3 STAGES
// ============================================

const INSECT_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'larva': {
    id: 'larva',
    name: 'Larva',
    description: 'A small insect larva. Weak but will transform.',
    requirements: baseReqs(DNAType.INSECT, 20),
    bonuses: {
      healthMultiplier: 0.8,
      damageMultiplier: 0.9,
      speedMultiplier: 0.9,
      specialAbilities: ['burrow', 'silk_shot'],
      resistances: { [DNAType.INSECT]: 0.5, [DNAType.GRASS]: 0.3 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.POISON]: 0.4 },
    },
    appearance: {
      color: '#bef264',
      shape: 'serpentine',
      size: 0.75,
      particleEffect: 'larva_squirm',
    },
    nextEvolutions: ['mantis', 'beetle'],
  },

  // STAGE 1: Branch A - Speed/Damage
  'mantis': {
    id: 'mantis',
    name: 'Mantis',
    description: 'A deadly predator. Strikes with blinding speed.',
    requirements: stage1Reqs(DNAType.INSECT, 50, DNAType.BEAST, 15, 22, 150),
    bonuses: {
      healthMultiplier: 1.0,
      damageMultiplier: 1.6,
      speedMultiplier: 1.5,
      specialAbilities: ['scythe_strike', 'praying_mantis', 'ambush', 'blinding_speed'],
      resistances: { [DNAType.INSECT]: 0.7, [DNAType.GRASS]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.WIND]: 0.4 },
    },
    appearance: {
      color: '#65a30d',
      shape: 'humanoid',
      size: 1.2,
      particleEffect: 'mantis_blur',
    },
    nextEvolutions: ['praying_destroyer'],
  },

  // STAGE 1: Branch B - Tank/Defense
  'beetle': {
    id: 'beetle',
    name: 'Beetle',
    description: 'Heavily armored insect. Nearly impenetrable shell.',
    requirements: stage1Reqs(DNAType.INSECT, 50, DNAType.EARTH, 25, 20, 160),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 1.1,
      speedMultiplier: 0.7,
      specialAbilities: ['shell_armor', 'horn_charge', 'burrow_attack', 'rolling_defense'],
      resistances: { [DNAType.INSECT]: 0.8, [DNAType.EARTH]: 0.5, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#1e293b',
      shape: 'quadruped',
      size: 1.5,
      particleEffect: 'beetle_shine',
    },
    nextEvolutions: ['titan_beetle'],
  },

  // STAGE 2: Ultimate Insect Form A
  'praying_destroyer': {
    id: 'praying_destroyer',
    name: 'Praying Destroyer',
    description: 'The ultimate predator. Nothing escapes its blades.',
    requirements: stage2Reqs(DNAType.INSECT, 80, DNAType.BEAST, 45, 55, 400),
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 2.8,
      speedMultiplier: 1.8,
      specialAbilities: ['death_scythe', 'predator_instinct', 'assassinate', 'blade_dance', 'hunters_mark'],
      resistances: { [DNAType.INSECT]: 1.0, [DNAType.GRASS]: 0.7, [DNAType.BEAST]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#3f6212',
      shape: 'humanoid',
      size: 1.6,
      particleEffect: 'destroyer_blur',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Insect Form B
  'titan_beetle': {
    id: 'titan_beetle',
    name: 'Titan Beetle',
    description: 'An insect of impossible size. Its shell is diamond-hard.',
    requirements: stage2Reqs(DNAType.INSECT, 80, DNAType.EARTH, 60, 50, 450),
    bonuses: {
      healthMultiplier: 3.5,
      damageMultiplier: 1.8,
      speedMultiplier: 0.6,
      specialAbilities: ['diamond_shell', 'earthquake_charge', 'impenetrable', 'beetle_cannon', 'colossal_slam'],
      resistances: { [DNAType.INSECT]: 1.0, [DNAType.EARTH]: 0.8, [DNAType.PHYSICAL]: 0.7 },
      weaknesses: { [DNAType.FIRE]: 0.5 },
    },
    appearance: {
      color: '#0f172a',
      shape: 'quadruped',
      size: 2.5,
      particleEffect: 'titan_shimmer',
    },
    nextEvolutions: [],
  },
};

// ============================================
// BEAST BRANCH - 3 STAGES
// ============================================

const BEAST_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'cub': {
    id: 'cub',
    name: 'Cub',
    description: 'A young beast. Small but fierce.',
    requirements: baseReqs(DNAType.BEAST, 20),
    bonuses: {
      healthMultiplier: 1.0,
      damageMultiplier: 1.1,
      speedMultiplier: 1.1,
      specialAbilities: ['claw', 'growl'],
      resistances: { [DNAType.BEAST]: 0.5, [DNAType.GRASS]: 0.3 },
      weaknesses: { [DNAType.FIRE]: 0.4, [DNAType.POISON]: 0.3 },
    },
    appearance: {
      color: '#92400e',
      shape: 'quadruped',
      size: 0.9,
      particleEffect: 'beast_breath',
    },
    nextEvolutions: ['dire_wolf', 'werebear'],
  },

  // STAGE 1: Branch A - Speed/Pack
  'dire_wolf': {
    id: 'dire_wolf',
    name: 'Dire Wolf',
    description: 'A massive wolf. Hunts in packs, strikes as one.',
    requirements: stage1Reqs(DNAType.BEAST, 50, DNAType.WIND, 15, 22, 150),
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 1.4,
      speedMultiplier: 1.4,
      specialAbilities: ['pack_howl', 'rend', 'alpha_strike', 'blood_frenzy'],
      resistances: { [DNAType.BEAST]: 0.7, [DNAType.WIND]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.POISON]: 0.4 },
    },
    appearance: {
      color: '#475569',
      shape: 'quadruped',
      size: 1.4,
      particleEffect: 'wolf_howl',
    },
    nextEvolutions: ['alpha_predator'],
  },

  // STAGE 1: Branch B - Tank/Burst
  'werebear': {
    id: 'werebear',
    name: 'Werebear',
    description: 'A bear of immense strength. Unstoppable force.',
    requirements: stage1Reqs(DNAType.BEAST, 50, DNAType.EARTH, 25, 25, 170),
    bonuses: {
      healthMultiplier: 2.3,
      damageMultiplier: 1.5,
      speedMultiplier: 0.7,
      specialAbilities: ['maul', 'bear_hug', 'ground_slam', 'berserk'],
      resistances: { [DNAType.BEAST]: 0.8, [DNAType.EARTH]: 0.5, [DNAType.PHYSICAL]: 0.4 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#78350f',
      shape: 'quadruped',
      size: 1.7,
      particleEffect: 'bear_roar',
    },
    nextEvolutions: ['ursa_major'],
  },

  // STAGE 2: Ultimate Beast Form A
  'alpha_predator': {
    id: 'alpha_predator',
    name: 'Alpha Predator',
    description: 'The apex of hunters. All beasts bow to it.',
    requirements: stage2Reqs(DNAType.BEAST, 80, DNAType.WIND, 40, 60, 420),
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 2.3,
      speedMultiplier: 1.6,
      specialAbilities: ['alpha_roar', 'predatory_instinct', 'kill_command', 'pack_leader', 'blood_scent'],
      resistances: { [DNAType.BEAST]: 1.0, [DNAType.WIND]: 0.6, [DNAType.GRASS]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#1e293b',
      shape: 'quadruped',
      size: 1.9,
      particleEffect: 'alpha_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Beast Form B
  'ursa_major': {
    id: 'ursa_major',
    name: 'Ursa Major',
    description: 'The great bear. Mountains shake at its step.',
    requirements: stage2Reqs(DNAType.BEAST, 85, DNAType.EARTH, 60, 55, 450),
    bonuses: {
      healthMultiplier: 4.0,
      damageMultiplier: 2.2,
      speedMultiplier: 0.6,
      specialAbilities: ['earth_shatter', 'star_fall', 'cosmic_roar', 'bear_swipe', 'mountain_crush'],
      resistances: { [DNAType.BEAST]: 1.0, [DNAType.EARTH]: 0.8, [DNAType.PHYSICAL]: 0.6 },
      weaknesses: { [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#451a03',
      shape: 'quadruped',
      size: 2.8,
      particleEffect: 'ursa_stars',
    },
    nextEvolutions: [],
  },
};

// ============================================
// REPTILE BRANCH - 3 STAGES
// ============================================

const REPTILE_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'hatchling': {
    id: 'hatchling',
    name: 'Hatchling',
    description: 'A newly hatched reptile. Small but growing.',
    requirements: baseReqs(DNAType.REPTILE, 20),
    bonuses: {
      healthMultiplier: 0.9,
      damageMultiplier: 1.0,
      speedMultiplier: 1.0,
      specialAbilities: ['bite', 'scale_armor'],
      resistances: { [DNAType.REPTILE]: 0.5, [DNAType.EARTH]: 0.3 },
      weaknesses: { [DNAType.ICE]: 0.5, [DNAType.FIRE]: 0.3 },
    },
    appearance: {
      color: '#84cc16',
      shape: 'serpentine',
      size: 0.85,
      particleEffect: 'hatchling_crawl',
    },
    nextEvolutions: ['cobra', 'crocodile'],
  },

  // STAGE 1: Branch A - Venom
  'cobra': {
    id: 'cobra',
    name: 'Cobra',
    description: 'A venomous serpent. Its strike is deadly.',
    requirements: stage1Reqs(DNAType.REPTILE, 50, DNAType.POISON, 20, 20, 150),
    bonuses: {
      healthMultiplier: 1.0,
      damageMultiplier: 1.4,
      speedMultiplier: 1.2,
      specialAbilities: ['venom_spit', 'hood_flare', 'constrict', 'neurotoxin'],
      resistances: { [DNAType.REPTILE]: 0.7, [DNAType.POISON]: 0.5 },
      weaknesses: { [DNAType.ICE]: 0.6, [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#65a30d',
      shape: 'serpentine',
      size: 1.3,
      particleEffect: 'cobra_hood',
    },
    nextEvolutions: ['king_cobra'],
  },

  // STAGE 1: Branch B - Tank
  'crocodile': {
    id: 'crocodile',
    name: 'Crocodile',
    description: 'An ancient predator. Armor and death roll.',
    requirements: stage1Reqs(DNAType.REPTILE, 50, DNAType.WATER, 20, 22, 160),
    bonuses: {
      healthMultiplier: 2.2,
      damageMultiplier: 1.3,
      speedMultiplier: 0.7,
      specialAbilities: ['death_roll', 'ambush', 'scale_plate', 'river_lurk'],
      resistances: { [DNAType.REPTILE]: 0.8, [DNAType.WATER]: 0.5, [DNAType.PHYSICAL]: 0.4 },
      weaknesses: { [DNAType.ICE]: 0.5, [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#3f6212',
      shape: 'quadruped',
      size: 1.6,
      particleEffect: 'crocodile_chomp',
    },
    nextEvolutions: ['tyrant_lizard'],
  },

  // STAGE 2: Ultimate Reptile Form A
  'king_cobra': {
    id: 'king_cobra',
    name: 'King Cobra',
    description: 'The king of serpents. Its venom kills gods.',
    requirements: stage2Reqs(DNAType.REPTILE, 80, DNAType.POISON, 50, 50, 400),
    bonuses: {
      healthMultiplier: 1.5,
      damageMultiplier: 2.4,
      speedMultiplier: 1.3,
      specialAbilities: ['god_venom', 'royal_hood', 'serpent_command', 'venom_storm', 'divine_toxin'],
      resistances: { [DNAType.REPTILE]: 1.0, [DNAType.POISON]: 0.8 },
      weaknesses: { [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#14532d',
      shape: 'serpentine',
      size: 2.0,
      particleEffect: 'king_crown',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Reptile Form B
  'tyrant_lizard': {
    id: 'tyrant_lizard',
    name: 'Tyrant Lizard',
    description: 'The T-Rex reborn. Absolute apex predator.',
    requirements: stage2Reqs(DNAType.REPTILE, 85, DNAType.WATER, 50, 55, 450),
    bonuses: {
      healthMultiplier: 3.5,
      damageMultiplier: 2.3,
      speedMultiplier: 0.7,
      specialAbilities: ['tyrant_roar', 'extinction_bite', 'earth_stomp', 'apex_hunter', 'prehistoric_terror'],
      resistances: { [DNAType.REPTILE]: 1.0, [DNAType.WATER]: 0.7, [DNAType.PHYSICAL]: 0.6 },
      weaknesses: { [DNAType.ICE]: 0.5 },
    },
    appearance: {
      color: '#3f2e18',
      shape: 'quadruped',
      size: 2.5,
      particleEffect: 'tyrant_aura',
    },
    nextEvolutions: [],
  },
};

// ============================================
// AQUATIC BRANCH - 3 STAGES
// ============================================

const AQUATIC_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'minnow': {
    id: 'minnow',
    name: 'Minnow',
    description: 'A small fish. Quick but vulnerable.',
    requirements: baseReqs(DNAType.AQUATIC, 20),
    bonuses: {
      healthMultiplier: 0.8,
      damageMultiplier: 0.9,
      speedMultiplier: 1.3,
      specialAbilities: ['swift_swim', 'schooling'],
      resistances: { [DNAType.AQUATIC]: 0.5, [DNAType.WATER]: 0.4 },
      weaknesses: { [DNAType.LIGHTNING]: 0.5, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#60a5fa',
      shape: 'serpentine',
      size: 0.75,
      particleEffect: 'fish_swim',
    },
    nextEvolutions: ['shark', 'kraken_spawn'],
  },

  // STAGE 1: Branch A - Predator
  'shark': {
    id: 'shark',
    name: 'Shark',
    description: 'An apex ocean predator. Smells blood from miles.',
    requirements: stage1Reqs(DNAType.AQUATIC, 50, DNAType.BEAST, 20, 25, 160),
    bonuses: {
      healthMultiplier: 1.5,
      damageMultiplier: 1.6,
      speedMultiplier: 1.4,
      specialAbilities: ['blood_frenzy', 'shark_bite', 'charge', 'scent_blood'],
      resistances: { [DNAType.AQUATIC]: 0.8, [DNAType.BEAST]: 0.5 },
      weaknesses: { [DNAType.LIGHTNING]: 0.6, [DNAType.POISON]: 0.4 },
    },
    appearance: {
      color: '#64748b',
      shape: 'serpentine',
      size: 1.5,
      particleEffect: 'shark_fin',
    },
    nextEvolutions: ['megalodon'],
  },

  // STAGE 1: Branch B - Tentacles
  'kraken_spawn': {
    id: 'kraken_spawn',
    name: 'Kraken Spawn',
    description: 'A young kraken. Tentacles and terror.',
    requirements: stage1Reqs(DNAType.AQUATIC, 50, DNAType.VOID, 15, 22, 170),
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 1.3,
      speedMultiplier: 0.9,
      specialAbilities: ['tentacle_grab', 'ink_cloud', 'crush', 'deep_pull'],
      resistances: { [DNAType.AQUATIC]: 0.8, [DNAType.VOID]: 0.4 },
      weaknesses: { [DNAType.LIGHTNING]: 0.5, [DNAType.FIRE]: 0.4 },
    },
    appearance: {
      color: '#1e1b4b',
      shape: 'amorphous',
      size: 1.4,
      particleEffect: 'ink_cloud',
    },
    nextEvolutions: ['kraken'],
  },

  // STAGE 2: Ultimate Aquatic Form A
  'megalodon': {
    id: 'megalodon',
    name: 'Megalodon',
    description: 'The ancient shark. Its jaws could swallow ships.',
    requirements: stage2Reqs(DNAType.AQUATIC, 80, DNAType.BEAST, 50, 60, 450),
    bonuses: {
      healthMultiplier: 2.8,
      damageMultiplier: 2.5,
      speedMultiplier: 1.3,
      specialAbilities: ['mega_bite', 'ancient_frenzy', 'ship_destroyer', 'blood_tsunami', 'ocean_terror'],
      resistances: { [DNAType.AQUATIC]: 1.0, [DNAType.BEAST]: 0.7, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#334155',
      shape: 'serpentine',
      size: 2.5,
      particleEffect: 'megalodon_jaws',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Aquatic Form B
  'kraken': {
    id: 'kraken',
    name: 'Kraken',
    description: 'The sea monster of legend. Ships fear its name.',
    requirements: stage2Reqs(DNAType.AQUATIC, 85, DNAType.VOID, 45, 55, 480),
    bonuses: {
      healthMultiplier: 3.0,
      damageMultiplier: 2.2,
      speedMultiplier: 0.8,
      specialAbilities: ['tentacle_maelstrom', 'ship_grab', 'abyssal_gaze', 'kraken_release', 'ocean_doom'],
      resistances: { [DNAType.AQUATIC]: 1.0, [DNAType.VOID]: 0.6, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.LIGHTNING]: 0.5 },
    },
    appearance: {
      color: '#0f0f23',
      shape: 'amorphous',
      size: 2.8,
      particleEffect: 'kraken_tentacles',
    },
    nextEvolutions: [],
  },
};

// ============================================
// CRYSTAL BRANCH - 3 STAGES
// ============================================

const CRYSTAL_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'gemling': {
    id: 'gemling',
    name: 'Gemling',
    description: 'A small living gem. Fragile but reflective.',
    requirements: baseReqs(DNAType.CRYSTAL, 20),
    bonuses: {
      healthMultiplier: 1.0,
      damageMultiplier: 1.1,
      speedMultiplier: 0.9,
      specialAbilities: ['crystal_shard', 'reflect'],
      resistances: { [DNAType.CRYSTAL]: 0.5, [DNAType.LIGHT]: 0.3 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.SLIME]: 0.4 },
    },
    appearance: {
      color: '#e0e7ff',
      shape: 'humanoid',
      size: 0.8,
      particleEffect: 'gem_shimmer',
    },
    nextEvolutions: ['prism_warrior', 'diamond_golem'],
  },

  // STAGE 1: Branch A - Offense
  'prism_warrior': {
    id: 'prism_warrior',
    name: 'Prism Warrior',
    description: 'Fights with light and crystal. Refracts damage.',
    requirements: stage1Reqs(DNAType.CRYSTAL, 50, DNAType.LIGHT, 20, 20, 150),
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 1.5,
      speedMultiplier: 1.1,
      specialAbilities: ['prism_beam', 'light_blade', 'refract', 'rainbow_burst'],
      resistances: { [DNAType.CRYSTAL]: 0.7, [DNAType.LIGHT]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.VOID]: 0.4 },
    },
    appearance: {
      color: '#c7d2fe',
      shape: 'humanoid',
      size: 1.3,
      particleEffect: 'prism_rainbow',
    },
    nextEvolutions: ['spectrum_lord'],
  },

  // STAGE 1: Branch B - Defense
  'diamond_golem': {
    id: 'diamond_golem',
    name: 'Diamond Golem',
    description: 'Made of pure diamond. Nearly indestructible.',
    requirements: stage1Reqs(DNAType.CRYSTAL, 55, DNAType.EARTH, 25, 22, 170),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 1.2,
      speedMultiplier: 0.6,
      specialAbilities: ['diamond_skin', 'crystal_fist', 'impenetrable', 'shatter'],
      resistances: { [DNAType.CRYSTAL]: 0.9, [DNAType.EARTH]: 0.5, [DNAType.PHYSICAL]: 0.7 },
      weaknesses: { [DNAType.FIRE]: 0.4, [DNAType.CHAOS]: 0.4 },
    },
    appearance: {
      color: '#eef2ff',
      shape: 'humanoid',
      size: 1.7,
      particleEffect: 'diamond_sparkle',
    },
    nextEvolutions: ['crystal_titan'],
  },

  // STAGE 2: Ultimate Crystal Form A
  'spectrum_lord': {
    id: 'spectrum_lord',
    name: 'Spectrum Lord',
    description: 'Master of light and crystal. Colors are weapons.',
    requirements: stage2Reqs(DNAType.CRYSTAL, 80, DNAType.LIGHT, 50, 50, 420),
    bonuses: {
      healthMultiplier: 1.6,
      damageMultiplier: 2.4,
      speedMultiplier: 1.2,
      specialAbilities: ['spectrum_blast', 'prism_prison', 'light_mastery', 'color_beam', 'rainbow_nova'],
      resistances: { [DNAType.CRYSTAL]: 1.0, [DNAType.LIGHT]: 0.8 },
      weaknesses: { [DNAType.VOID]: 0.4 },
    },
    appearance: {
      color: '#ffffff',
      shape: 'humanoid',
      size: 1.7,
      particleEffect: 'spectrum_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Crystal Form B
  'crystal_titan': {
    id: 'crystal_titan',
    name: 'Crystal Titan',
    description: 'A mountain of living crystal. Unbreakable.',
    requirements: stage2Reqs(DNAType.CRYSTAL, 85, DNAType.EARTH, 60, 55, 450),
    bonuses: {
      healthMultiplier: 3.5,
      damageMultiplier: 2.0,
      speedMultiplier: 0.5,
      specialAbilities: ['crystal_fortress', 'diamond_storm', 'impenetrable_aura', 'shatter_world', 'crystal_mastery'],
      resistances: { [DNAType.CRYSTAL]: 1.0, [DNAType.EARTH]: 0.7, [DNAType.PHYSICAL]: 0.8 },
      weaknesses: { [DNAType.CHAOS]: 0.4 },
    },
    appearance: {
      color: '#f8fafc',
      shape: 'humanoid',
      size: 2.5,
      particleEffect: 'titan_crystal',
    },
    nextEvolutions: [],
  },
};

// ============================================
// SLIME BRANCH - 3 STAGES
// ============================================

const SLIME_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'slime_drop': {
    id: 'slime_drop',
    name: 'Slime Drop',
    description: 'A small blob of slime. Adorable but weak.',
    requirements: baseReqs(DNAType.SLIME, 20),
    bonuses: {
      healthMultiplier: 0.85,
      damageMultiplier: 0.8,
      speedMultiplier: 0.9,
      specialAbilities: ['ooze', 'absorb'],
      resistances: { [DNAType.SLIME]: 0.5, [DNAType.PHYSICAL]: 0.3 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.ICE]: 0.4 },
    },
    appearance: {
      color: '#22d3ee',
      shape: 'amorphous',
      size: 0.8,
      particleEffect: 'slime_jiggle',
    },
    nextEvolutions: ['gelatinous_cube', 'acid_ooze'],
  },

  // STAGE 1: Branch A - Cube/Trapper
  'gelatinous_cube': {
    id: 'gelatinous_cube',
    name: 'Gelatinous Cube',
    description: 'A transparent cube. Absorbs everything it touches.',
    requirements: stage1Reqs(DNAType.SLIME, 50, DNAType.WATER, 20, 18, 150),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 1.0,
      speedMultiplier: 0.6,
      specialAbilities: ['engulf', 'digest', 'transparent', 'absorb_item'],
      resistances: { [DNAType.SLIME]: 0.8, [DNAType.WATER]: 0.5, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.7, [DNAType.ICE]: 0.5 },
    },
    appearance: {
      color: '#a5f3fc',
      shape: 'humanoid',
      size: 1.5,
      particleEffect: 'cube_transparent',
    },
    nextEvolutions: ['primordial_ooze'],
  },

  // STAGE 1: Branch B - Acid/Offense
  'acid_ooze': {
    id: 'acid_ooze',
    name: 'Acid Ooze',
    description: 'Highly corrosive slime. Melts through armor.',
    requirements: stage1Reqs(DNAType.SLIME, 50, DNAType.POISON, 25, 20, 160),
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 1.4,
      speedMultiplier: 0.9,
      specialAbilities: ['acid_splash', 'corrode', 'melt_armor', 'acid_pool'],
      resistances: { [DNAType.SLIME]: 0.8, [DNAType.POISON]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.6, [DNAType.WATER]: 0.4 },
    },
    appearance: {
      color: '#84cc16',
      shape: 'amorphous',
      size: 1.2,
      particleEffect: 'acid_bubbles',
    },
    nextEvolutions: ['world_eater'],
  },

  // STAGE 2: Ultimate Slime Form A
  'primordial_ooze': {
    id: 'primordial_ooze',
    name: 'Primordial Ooze',
    description: 'The first slime. Contains the essence of all life.',
    requirements: stage2Reqs(DNAType.SLIME, 80, DNAType.WATER, 50, 50, 420),
    bonuses: {
      healthMultiplier: 3.0,
      damageMultiplier: 1.5,
      speedMultiplier: 0.7,
      specialAbilities: ['primordial_soup', 'evolutionary_adapt', 'absorb_all', 'life_seed', 'creation_ooze'],
      resistances: { [DNAType.SLIME]: 1.0, [DNAType.WATER]: 0.8, [DNAType.PHYSICAL]: 0.6 },
      weaknesses: { [DNAType.FIRE]: 0.5 },
    },
    appearance: {
      color: '#0891b2',
      shape: 'amorphous',
      size: 2.0,
      particleEffect: 'primordial_glow',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Slime Form B
  'world_eater': {
    id: 'world_eater',
    name: 'World Eater',
    description: 'A slime that consumes everything. Nothing escapes.',
    requirements: stage2Reqs(DNAType.SLIME, 85, DNAType.POISON, 55, 55, 450),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 2.3,
      speedMultiplier: 0.8,
      specialAbilities: ['devour', 'digest_world', 'acid_tsunami', 'consume_all', 'apocalypse_slime'],
      resistances: { [DNAType.SLIME]: 1.0, [DNAType.POISON]: 0.8, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.FIRE]: 0.6 },
    },
    appearance: {
      color: '#3f6212',
      shape: 'amorphous',
      size: 2.2,
      particleEffect: 'world_eater_glow',
    },
    nextEvolutions: [],
  },
};

// ============================================
// MECH BRANCH - 3 STAGES
// ============================================

const MECH_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'scrap_bot': {
    id: 'scrap_bot',
    name: 'Scrap Bot',
    description: 'Made of junk and hope. Fragile but upgradeable.',
    requirements: baseReqs(DNAType.MECH, 20),
    bonuses: {
      healthMultiplier: 1.1,
      damageMultiplier: 1.0,
      speedMultiplier: 0.9,
      specialAbilities: ['repair', 'scrap_shot'],
      resistances: { [DNAType.MECH]: 0.5, [DNAType.POISON]: 0.4, [DNAType.FIRE]: 0.3 },
      weaknesses: { [DNAType.LIGHTNING]: 0.5, [DNAType.WATER]: 0.4 },
    },
    appearance: {
      color: '#64748b',
      shape: 'humanoid',
      size: 0.9,
      particleEffect: 'scrap_sparks',
    },
    nextEvolutions: ['combat_droid', 'tank_walker'],
  },

  // STAGE 1: Branch A - Combat
  'combat_droid': {
    id: 'combat_droid',
    name: 'Combat Droid',
    description: 'A military-grade robot. Efficient and deadly.',
    requirements: stage1Reqs(DNAType.MECH, 50, DNAType.FIRE, 15, 22, 160),
    bonuses: {
      healthMultiplier: 1.5,
      damageMultiplier: 1.5,
      speedMultiplier: 1.1,
      specialAbilities: ['laser_blast', 'targeting_system', 'rapid_fire', 'overload'],
      resistances: { [DNAType.MECH]: 0.7, [DNAType.FIRE]: 0.5 },
      weaknesses: { [DNAType.LIGHTNING]: 0.6, [DNAType.WATER]: 0.5 },
    },
    appearance: {
      color: '#94a3b8',
      shape: 'humanoid',
      size: 1.4,
      particleEffect: 'droid_laser',
    },
    nextEvolutions: ['annihilator'],
  },

  // STAGE 1: Branch B - Tank
  'tank_walker': {
    id: 'tank_walker',
    name: 'Tank Walker',
    description: 'Heavy armor and big guns. Slow but devastating.',
    requirements: stage1Reqs(DNAType.MECH, 50, DNAType.EARTH, 25, 25, 180),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 1.4,
      speedMultiplier: 0.5,
      specialAbilities: ['cannon_fire', 'armor_plate', 'siege_mode', 'barrage'],
      resistances: { [DNAType.MECH]: 0.8, [DNAType.EARTH]: 0.5, [DNAType.PHYSICAL]: 0.6 },
      weaknesses: { [DNAType.LIGHTNING]: 0.5, [DNAType.WATER]: 0.4 },
    },
    appearance: {
      color: '#334155',
      shape: 'humanoid',
      size: 1.8,
      particleEffect: 'tank_treads',
    },
    nextEvolutions: ['mech_god'],
  },

  // STAGE 2: Ultimate Mech Form A
  'annihilator': {
    id: 'annihilator',
    name: 'Annihilator',
    description: 'A killing machine. Nothing survives its gaze.',
    requirements: stage2Reqs(DNAType.MECH, 80, DNAType.FIRE, 45, 60, 450),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 2.5,
      speedMultiplier: 1.2,
      specialAbilities: ['death_ray', 'annihilation_beam', 'perfect_target', 'omega_blast', 'extermination'],
      resistances: { [DNAType.MECH]: 1.0, [DNAType.FIRE]: 0.7 },
      weaknesses: { [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#ef4444',
      shape: 'humanoid',
      size: 1.8,
      particleEffect: 'annihilator_glow',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Mech Form B
  'mech_god': {
    id: 'mech_god',
    name: 'Mech God',
    description: 'The ultimate machine. Technology given divinity.',
    requirements: stage2Reqs(DNAType.MECH, 85, DNAType.EARTH, 60, 55, 480),
    bonuses: {
      healthMultiplier: 3.5,
      damageMultiplier: 2.2,
      speedMultiplier: 0.7,
      specialAbilities: ['god_cannon', 'divine_armor', 'sky_beam', 'mech_legion', 'technological_apotheosis'],
      resistances: { [DNAType.MECH]: 1.0, [DNAType.EARTH]: 0.8, [DNAType.PHYSICAL]: 0.7 },
      weaknesses: { [DNAType.LIGHTNING]: 0.5 },
    },
    appearance: {
      color: '#fbbf24',
      shape: 'humanoid',
      size: 2.5,
      particleEffect: 'mech_god_aura',
    },
    nextEvolutions: [],
  },
};

// ============================================
// CHAOS BRANCH - 3 STAGES
// ============================================

const CHAOS_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'chaos_mote': {
    id: 'chaos_mote',
    name: 'Chaos Mote',
    description: 'A fragment of pure chaos. Unpredictable.',
    requirements: baseReqs(DNAType.CHAOS, 20),
    bonuses: {
      healthMultiplier: 0.9,
      damageMultiplier: 1.2,
      speedMultiplier: 1.1,
      specialAbilities: ['random_blast', 'chaos_shift'],
      resistances: { [DNAType.CHAOS]: 0.6 },
      weaknesses: { [DNAType.LIGHT]: 0.5, [DNAType.ARCANE]: 0.4 },
    },
    appearance: {
      color: '#d946ef',
      shape: 'amorphous',
      size: 0.85,
      particleEffect: 'chaos_swirl',
    },
    nextEvolutions: ['chaos_warrior', 'reality_breaker'],
  },

  // STAGE 1: Branch A - Warrior
  'chaos_warrior': {
    id: 'chaos_warrior',
    name: 'Chaos Warrior',
    description: 'A fighter wielding chaos. Every strike is different.',
    requirements: stage1Reqs(DNAType.CHAOS, 50, DNAType.BEAST, 20, 25, 170),
    bonuses: {
      healthMultiplier: 1.4,
      damageMultiplier: 1.6,
      speedMultiplier: 1.2,
      specialAbilities: ['chaos_blade', 'random_buff', 'unpredictable', 'chaos_armor'],
      resistances: { [DNAType.CHAOS]: 0.8, [DNAType.BEAST]: 0.4 },
      weaknesses: { [DNAType.LIGHT]: 0.6, [DNAType.ARCANE]: 0.5 },
    },
    appearance: {
      color: '#c026d3',
      shape: 'humanoid',
      size: 1.4,
      particleEffect: 'chaos_weapons',
    },
    nextEvolutions: ['chaos_lord'],
  },

  // STAGE 1: Branch B - Reality Warper
  'reality_breaker': {
    id: 'reality_breaker',
    name: 'Reality Breaker',
    description: 'Twists reality itself. Nothing is certain near it.',
    requirements: stage1Reqs(DNAType.CHAOS, 50, DNAType.VOID, 20, 22, 180),
    bonuses: {
      healthMultiplier: 1.5,
      damageMultiplier: 1.4,
      speedMultiplier: 1.0,
      specialAbilities: ['reality_twist', 'probability_shift', 'chaos_field', 'random_teleport'],
      resistances: { [DNAType.CHAOS]: 0.9, [DNAType.VOID]: 0.5 },
      weaknesses: { [DNAType.LIGHT]: 0.7, [DNAType.ARCANE]: 0.5 },
    },
    appearance: {
      color: '#86198f',
      shape: 'amorphous',
      size: 1.5,
      particleEffect: 'reality_cracks',
    },
    nextEvolutions: ['chaos_god'],
  },

  // STAGE 2: Ultimate Chaos Form A
  'chaos_lord': {
    id: 'chaos_lord',
    name: 'Chaos Lord',
    description: 'Master of chaotic combat. Unpredictable and deadly.',
    requirements: stage2Reqs(DNAType.CHAOS, 80, DNAType.BEAST, 50, 60, 450),
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 2.5,
      speedMultiplier: 1.3,
      specialAbilities: ['chaos_storm', 'random_ultimate', 'chaos_form', 'entropy_blade', 'master_of_chaos'],
      resistances: { [DNAType.CHAOS]: 1.0, [DNAType.BEAST]: 0.6 },
      weaknesses: { [DNAType.LIGHT]: 0.5 },
    },
    appearance: {
      color: '#701a75',
      shape: 'humanoid',
      size: 1.9,
      particleEffect: 'chaos_lord_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Chaos Form B
  'chaos_god': {
    id: 'chaos_god',
    name: 'Chaos God',
    description: 'A deity of pure chaos. Reality is its plaything.',
    requirements: stage2Reqs(DNAType.CHAOS, 85, DNAType.VOID, 55, 55, 500),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 2.3,
      speedMultiplier: 1.1,
      specialAbilities: ['reality_rewrite', 'chaos_wave', 'probability_collapse', 'existence_erasure', 'primordial_chaos'],
      resistances: { [DNAType.CHAOS]: 1.0, [DNAType.VOID]: 0.7, [DNAType.PHYSICAL]: 0.5 },
      weaknesses: { [DNAType.LIGHT]: 0.4 },
    },
    appearance: {
      color: '#4a044e',
      shape: 'amorphous',
      size: 2.5,
      particleEffect: 'chaos_god_form',
    },
    nextEvolutions: [],
  },
};

// ============================================
// PHYSICAL BRANCH - 3 STAGES
// Pure physical power evolution path
// ============================================

const PHYSICAL_EVOLUTIONS: Record<string, EvolutionPath> = {
  // STAGE 0: Base Form
  'training_dummy': {
    id: 'training_dummy',
    name: 'Training Dummy',
    description: 'A basic construct learning to fight. Resilient but unremarkable.',
    requirements: baseReqs(DNAType.PHYSICAL, 20),
    bonuses: {
      healthMultiplier: 1.1,
      damageMultiplier: 1.0,
      speedMultiplier: 0.9,
      specialAbilities: ['basic_punch', 'toughness'],
      resistances: { [DNAType.PHYSICAL]: 0.4 },
      weaknesses: { [DNAType.ARCANE]: 0.3, [DNAType.VOID]: 0.3 },
    },
    appearance: {
      color: '#9ca3af',
      shape: 'humanoid',
      size: 1.0,
      particleEffect: 'dust_puffs',
    },
    nextEvolutions: ['brawler', 'juggernaut'],
  },

  // STAGE 1: Branch A - Speed/Damage (Brawler)
  'brawler': {
    id: 'brawler',
    name: 'Brawler',
    description: 'A skilled fighter. Fast punches and relentless assault.',
    requirements: stage1Reqs(DNAType.PHYSICAL, 50, DNAType.BEAST, 15, 20, 150),
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 1.5,
      speedMultiplier: 1.3,
      specialAbilities: ['combo_strike', 'flurry', 'counter_attack', 'adrenaline_rush'],
      resistances: { [DNAType.PHYSICAL]: 0.6, [DNAType.BEAST]: 0.3 },
      weaknesses: { [DNAType.ARCANE]: 0.4, [DNAType.VOID]: 0.3 },
    },
    appearance: {
      color: '#d97706',
      shape: 'humanoid',
      size: 1.2,
      particleEffect: 'impact_sparks',
    },
    nextEvolutions: ['martial_master'],
  },

  // STAGE 1: Branch B - Tank (Juggernaut)
  'juggernaut': {
    id: 'juggernaut',
    name: 'Juggernaut',
    description: 'An unstoppable force. Pure resilience and raw power.',
    requirements: stage1Reqs(DNAType.PHYSICAL, 55, DNAType.EARTH, 25, 22, 170),
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 1.3,
      speedMultiplier: 0.6,
      specialAbilities: ['unstoppable', 'crushing_blow', 'iron_skin', 'ground_slam'],
      resistances: { [DNAType.PHYSICAL]: 0.8, [DNAType.EARTH]: 0.5 },
      weaknesses: { [DNAType.ARCANE]: 0.5, [DNAType.LIGHTNING]: 0.4 },
    },
    appearance: {
      color: '#4b5563',
      shape: 'humanoid',
      size: 1.7,
      particleEffect: 'heavy_footsteps',
    },
    nextEvolutions: ['titan'],
  },

  // STAGE 2: Ultimate Physical Form A
  'martial_master': {
    id: 'martial_master',
    name: 'Martial Master',
    description: 'Perfection of physical combat. Every strike is lethal.',
    requirements: stage2Reqs(DNAType.PHYSICAL, 80, DNAType.BEAST, 45, 50, 400),
    bonuses: {
      healthMultiplier: 1.6,
      damageMultiplier: 2.5,
      speedMultiplier: 1.5,
      specialAbilities: ['one_inch_punch', 'thousand_hands', 'perfect_form', 'chi_strike', 'afterimage'],
      resistances: { [DNAType.PHYSICAL]: 0.9, [DNAType.BEAST]: 0.6 },
      weaknesses: { [DNAType.ARCANE]: 0.3 },
    },
    appearance: {
      color: '#f59e0b',
      shape: 'humanoid',
      size: 1.5,
      particleEffect: 'chi_aura',
    },
    nextEvolutions: [],
  },

  // STAGE 2: Ultimate Physical Form B
  'titan': {
    id: 'titan',
    name: 'Titan',
    description: 'A being of pure physical might. Mountains tremble before it.',
    requirements: stage2Reqs(DNAType.PHYSICAL, 85, DNAType.EARTH, 60, 55, 450),
    bonuses: {
      healthMultiplier: 4.0,
      damageMultiplier: 2.2,
      speedMultiplier: 0.5,
      specialAbilities: ['world_breaker', 'titan_slam', 'immovable_object', 'colossal_strength', 'earthquake_punch'],
      resistances: { [DNAType.PHYSICAL]: 1.0, [DNAType.EARTH]: 0.8 },
      weaknesses: { [DNAType.ARCANE]: 0.4 },
    },
    appearance: {
      color: '#1f2937',
      shape: 'humanoid',
      size: 2.8,
      particleEffect: 'titan_aura',
    },
    nextEvolutions: [],
  },
};

// ============================================
// HYBRID EVOLUTIONS - Special combinations
// ============================================

const HYBRID_EVOLUTIONS: Record<string, EvolutionPath> = {
  // Fire + Water = Steam
  'steam_wraith': {
    id: 'steam_wraith',
    name: 'Steam Wraith',
    description: 'Fire and Water in balance. Ethereal and hard to hit.',
    requirements: {
      minDNA: { [DNAType.FIRE]: 35, [DNAType.WATER]: 35 },
      maxDNA: {},
      minKills: 25,
      minSurvivalTime: 200,
      minGeneration: 1,
      specialConditions: ['fire_water_balance'],
    },
    bonuses: {
      healthMultiplier: 0.9,
      damageMultiplier: 1.4,
      speedMultiplier: 1.5,
      specialAbilities: ['steam_cloud', 'condensation_burst', 'ethereal_form'],
      resistances: { [DNAType.FIRE]: 0.5, [DNAType.WATER]: 0.5, [DNAType.EARTH]: 0.3 },
      weaknesses: { [DNAType.WIND]: 0.5, [DNAType.VOID]: 0.4 },
    },
    appearance: {
      color: '#e5e7eb',
      shape: 'amorphous',
      size: 1.0,
      particleEffect: 'steam_clouds',
    },
    nextEvolutions: ['cloud_titan', 'storm_spirit'],
  },

  'cloud_titan': {
    id: 'cloud_titan',
    name: 'Cloud Titan',
    description: 'A being of living vapor. Controls weather.',
    requirements: {
      minDNA: { [DNAType.FIRE]: 50, [DNAType.WATER]: 50, [DNAType.WIND]: 30 },
      maxDNA: {},
      minKills: 50,
      minSurvivalTime: 400,
      minGeneration: 2,
    },
    bonuses: {
      healthMultiplier: 1.8,
      damageMultiplier: 1.8,
      speedMultiplier: 1.4,
      specialAbilities: ['weather_control', 'acid_rain', 'thunder_cloud', 'mist_form'],
      resistances: { [DNAType.FIRE]: 0.6, [DNAType.WATER]: 0.6, [DNAType.WIND]: 0.5 },
      weaknesses: { [DNAType.ICE]: 0.5 },
    },
    appearance: {
      color: '#94a3b8',
      shape: 'amorphous',
      size: 2.0,
      particleEffect: 'cloud_aura',
    },
    nextEvolutions: [],
  },

  'storm_spirit': {
    id: 'storm_spirit',
    name: 'Storm Spirit',
    description: 'Lightning given consciousness. Pure energy.',
    requirements: {
      minDNA: { [DNAType.FIRE]: 50, [DNAType.WATER]: 50, [DNAType.LIGHTNING]: 40 },
      maxDNA: {},
      minKills: 55,
      minSurvivalTime: 420,
      minGeneration: 2,
    },
    bonuses: {
      healthMultiplier: 1.2,
      damageMultiplier: 2.2,
      speedMultiplier: 1.8,
      specialAbilities: ['storm_form', 'lightning_dash', 'thunder_strike', 'energy_being'],
      resistances: { [DNAType.FIRE]: 0.5, [DNAType.WATER]: 0.5, [DNAType.LIGHTNING]: 0.8 },
      weaknesses: { [DNAType.EARTH]: 0.4 },
    },
    appearance: {
      color: '#fbbf24',
      shape: 'amorphous',
      size: 1.5,
      particleEffect: 'storm_spirit_form',
    },
    nextEvolutions: [],
  },

  // Poison + Fungus = Plague
  'plague_bearer': {
    id: 'plague_bearer',
    name: 'Plague Bearer',
    description: 'Poison and Fungus combined. Spreads decay everywhere.',
    requirements: {
      minDNA: { [DNAType.POISON]: 40, [DNAType.FUNGUS]: 30 },
      maxDNA: { [DNAType.LIGHT]: 10 },
      minKills: 30,
      minSurvivalTime: 240,
      minGeneration: 1,
    },
    bonuses: {
      healthMultiplier: 1.3,
      damageMultiplier: 1.2,
      speedMultiplier: 0.9,
      specialAbilities: ['plague_cloud', 'spore_burst', 'necrotic_touch', 'undead_legion'],
      resistances: { [DNAType.POISON]: 0.9, [DNAType.FUNGUS]: 0.8 },
      weaknesses: { [DNAType.FIRE]: 0.7, [DNAType.LIGHT]: 0.6 },
    },
    appearance: {
      color: '#65a30d',
      shape: 'humanoid',
      size: 1.2,
      particleEffect: 'toxic_spores',
    },
    nextEvolutions: ['apocalypse_herald', 'rot_god'],
  },

  'apocalypse_herald': {
    id: 'apocalypse_herald',
    name: 'Apocalypse Herald',
    description: 'Bringer of the end times. Disease follows.',
    requirements: {
      minDNA: { [DNAType.POISON]: 60, [DNAType.FUNGUS]: 50, [DNAType.VOID]: 30 },
      maxDNA: { [DNAType.LIGHT]: 5 },
      minKills: 70,
      minSurvivalTime: 500,
      minGeneration: 2,
    },
    bonuses: {
      healthMultiplier: 2.0,
      damageMultiplier: 1.8,
      speedMultiplier: 0.8,
      specialAbilities: ['apocalypse_rider', 'four_horseman', 'end_times', 'doomsday_clock'],
      resistances: { [DNAType.POISON]: 1.0, [DNAType.FUNGUS]: 0.9, [DNAType.VOID]: 0.6 },
      weaknesses: { [DNAType.FIRE]: 0.5, [DNAType.LIGHT]: 0.5 },
    },
    appearance: {
      color: '#1a2e05',
      shape: 'humanoid',
      size: 2.0,
      particleEffect: 'apocalypse_aura',
    },
    nextEvolutions: [],
  },

  // ULTIMATE FORM - All Elements Balanced
  'elemental_avatar': {
    id: 'elemental_avatar',
    name: 'Elemental Avatar',
    description: 'Master of all elements. The perfect balance.',
    requirements: {
      minDNA: { 
        [DNAType.FIRE]: 25, 
        [DNAType.WATER]: 25, 
        [DNAType.EARTH]: 25, 
        [DNAType.WIND]: 25,
        [DNAType.ICE]: 15,
        [DNAType.LIGHTNING]: 15,
      },
      maxDNA: {},
      minKills: 100,
      minSurvivalTime: 600,
      minGeneration: 3,
    },
    bonuses: {
      healthMultiplier: 2.5,
      damageMultiplier: 2.0,
      speedMultiplier: 1.5,
      specialAbilities: ['elemental_fury', 'prismatic_barrage', 'avatar_form', 'reality_bend'],
      resistances: { 
        [DNAType.FIRE]: 0.5, 
        [DNAType.WATER]: 0.5, 
        [DNAType.EARTH]: 0.5, 
        [DNAType.WIND]: 0.5,
        [DNAType.ICE]: 0.4,
        [DNAType.LIGHTNING]: 0.4,
      },
      weaknesses: {},
    },
    appearance: {
      color: '#ffffff',
      shape: 'humanoid',
      size: 2.0,
      particleEffect: 'prismatic_aura',
    },
    nextEvolutions: [],
  },
};

// ============================================
// COMPLETE EVOLUTION TREE EXPORT
// ============================================

export const COMPLETE_EVOLUTION_TREE: Record<string, EvolutionPath> = {
  ...FIRE_EVOLUTIONS,
  ...ICE_EVOLUTIONS,
  ...WATER_EVOLUTIONS,
  ...EARTH_EVOLUTIONS,
  ...WIND_EVOLUTIONS,
  ...LIGHTNING_EVOLUTIONS,
  ...POISON_EVOLUTIONS,
  ...VOID_EVOLUTIONS,
  ...LIGHT_EVOLUTIONS,
  ...GRASS_EVOLUTIONS,
  ...FUNGUS_EVOLUTIONS,
  ...INSECT_EVOLUTIONS,
  ...BEAST_EVOLUTIONS,
  ...REPTILE_EVOLUTIONS,
  ...AQUATIC_EVOLUTIONS,
  ...CRYSTAL_EVOLUTIONS,
  ...SLIME_EVOLUTIONS,
  ...MECH_EVOLUTIONS,
  ...CHAOS_EVOLUTIONS,
  ...PHYSICAL_EVOLUTIONS,
  ...HYBRID_EVOLUTIONS,
};

// Get evolution paths for a specific DNA type
export function getEvolutionsForDNAType(dnaType: DNAType): EvolutionPath[] {
  return Object.values(COMPLETE_EVOLUTION_TREE).filter(path => {
    const minDNA = path.requirements.minDNA;
    return dnaType in minDNA && Object.keys(minDNA).length <= 2; // Single or dual-type evolutions
  });
}

// Get base forms (generation 0) for all DNA types
export function getBaseForms(): EvolutionPath[] {
  return Object.values(COMPLETE_EVOLUTION_TREE).filter(path => 
    path.requirements.minGeneration === 0
  );
}

// Get ultimate forms (generation 2+)
export function getUltimateForms(): EvolutionPath[] {
  return Object.values(COMPLETE_EVOLUTION_TREE).filter(path => 
    path.requirements.minGeneration >= 2
  );
}

// Get hybrid evolutions
export function getHybridEvolutions(): EvolutionPath[] {
  return Object.values(COMPLETE_EVOLUTION_TREE).filter(path => {
    const minDNA = path.requirements.minDNA;
    return Object.keys(minDNA).length >= 2 && !path.requirements.specialConditions?.includes('fire_water_balance');
  });
}
