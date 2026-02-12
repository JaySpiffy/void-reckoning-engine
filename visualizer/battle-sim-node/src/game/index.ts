// ============================================
// DARWIN'S ISLAND REHELIXED - Main Game Export
// ============================================

export * from './types';
export * from './utils';
export * from './entities';
export * from './managers';

// Systems - export individually to avoid conflicts
export { DNASystem, dnaSystem, EVOLUTION_PATHS } from './systems/DNASystem';
export * from './systems/DNACore';
export * from './systems/LootSystem';
export * from './systems/NPCSystem';

export { createGame } from './managers';
export * from './managers/GameManager';
