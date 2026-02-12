import type { EntityType, EnemyType, ResourceType, ElementType, DamageInfo, Vector2 } from './core';
import type { EvolutionPath } from '../systems/DNACore';
import type { LootItem } from '../systems/LootSystem';
import type { BindableAction } from '../systems/KeybindingSystem';

// ============================================
// EVENTS
// ============================================

export enum GameEvent {
  ENTITY_CREATED = 'entity_created',
  ENTITY_DESTROYED = 'entity_destroyed',
  DAMAGE_DEALT = 'damage_dealt',
  ENEMY_KILLED = 'enemy_killed',
  RESOURCE_COLLECTED = 'resource_collected',
  ELEMENT_CHANGED = 'element_changed',
  ELEMENT_LEVELED_UP = 'element_leveled_up',
  ABILITY_USED = 'ability_used',
  ABILITY_UNLOCKED = 'ability_unlocked',
  WAVE_STARTED = 'wave_started',
  WAVE_COMPLETED = 'wave_completed',
  GAME_OVER = 'game_over',
  LEVEL_UP = 'level_up',
  EVOLUTION_AVAILABLE = 'evolution_available',
  EVOLUTION_COMPLETE = 'evolution_complete',
  KEYBINDING_PRESSED = 'keybinding_pressed',
  LOOT_ACQUIRED = 'loot_acquired',
  ITEM_USED = 'item_used',
  NPC_SPAWNED = 'npc_spawned',
  NPC_ABILITY_CAST = 'npc_ability_cast',
  BOSS_PHASE_CHANGE = 'boss_phase_change',
  TOGGLE_DEBUG_PANEL = 'toggle_debug_panel',
  MUTATION_APPLIED = 'mutation_applied',
  OPEN_SIMULATION_PANEL = 'open_simulation_panel',
  OPEN_SIMULATION_DASHBOARD = 'open_simulation_dashboard',
  // Add more events here
}

export type GameEventData = {
  entity_created: { entityId: string; type: EntityType };
  entity_destroyed: { entityId: string; type: EntityType };
  damage_dealt: { targetId: string; damage: DamageInfo };
  enemy_killed: { enemyId: string; enemyType: EnemyType; position: Vector2; experience: number };
  resource_collected: { type: ResourceType; amount: number };
  element_changed: { element: ElementType; duration: number };
  element_leveled_up: { element: ElementType; level: number };
  ability_used: { abilityId: string; slot: number };
  ability_unlocked: { abilityId: string };
  wave_started: { wave: number; enemyCount: number };
  wave_completed: { wave: number };
  game_over: { score: number; wave: number; survived: number };
  level_up: { level: number };
  evolution_available: { paths: EvolutionPath[]; currentDNA: Record<string, number> };
  evolution_complete: { from: string; to: string; generation: number; bonuses: unknown };
  keybinding_pressed: { action: BindableAction; pressed: boolean };
  loot_acquired: { item: LootItem };
  item_used: { item: LootItem };
  npc_spawned: { id: string; type: EnemyType; position: Vector2 };
  npc_ability_cast: { npcId: string; ability: string; targetPosition: Vector2 };
  boss_phase_change: { npcId: string; newPhase: number };
  toggle_debug_panel: Record<string, never>;
  open_simulation_panel: Record<string, never>;
  open_simulation_dashboard: Record<string, never>;
  mutation_applied: { mutationType: string; targetDnaType: string };
};

export type EventCallback<T extends keyof GameEventData> = (data: GameEventData[T]) => void;
