import { Building } from '../entities/Building';
import type { Vector2 } from '../types';
import { BuildingType, GameEvent, ResourceType, EntityType } from '../types';
import { globalEvents } from '../utils';
import { entityManager } from '../managers/EntityManager';

export interface BuildingArchetype {
  type: BuildingType;
  maxHealth: number;
  cost: {
    [K in ResourceType]?: number;
  };
  description: string;
  icon: string;
}

export const BUILDING_ARCHETYPES: Record<BuildingType, BuildingArchetype> = {
  [BuildingType.WALL]: {
    type: BuildingType.WALL,
    maxHealth: 200,
    cost: { [ResourceType.WOOD]: 20, [ResourceType.STONE]: 10 },
    description: 'A sturdy barrier to block enemies.',
    icon: '🧱',
  },
  [BuildingType.TOWER]: {
    type: BuildingType.TOWER,
    maxHealth: 100,
    cost: { [ResourceType.STONE]: 30, [ResourceType.GOLD]: 15 },
    description: 'Automatically shoots at nearby enemies.',
    icon: '🏹',
  },
  [BuildingType.HEALING_SHRINE]: {
    type: BuildingType.HEALING_SHRINE,
    maxHealth: 50,
    cost: { [ResourceType.GOLD]: 50, [ResourceType.MANA]: 20 },
    description: 'Slowly heals the player when nearby.',
    icon: '✨',
  },
  [BuildingType.RESOURCE_GENERATOR]: {
    type: BuildingType.RESOURCE_GENERATOR,
    maxHealth: 80,
    cost: { [ResourceType.WOOD]: 40, [ResourceType.STONE]: 40 },
    description: 'Generates random resources over time.',
    icon: '⚒️',
  }
};

export class BuildingSystem {
  private buildings: Building[] = [];

  constructor() {}

  canAfford(type: BuildingType, resources: Record<string, number>): boolean {
    const archetype = BUILDING_ARCHETYPES[type];
    if (!archetype) return false;

    for (const [res, amount] of Object.entries(archetype.cost)) {
      if ((resources[res.toLowerCase()] || 0) < (amount as number)) return false;
    }

    return true;
  }

  placeBuilding(type: BuildingType, position: Vector2, resources: Record<string, number>): Building | null {
    const archetype = BUILDING_ARCHETYPES[type];
    if (!archetype || !this.canAfford(type, resources)) return null;

    // Deduct resources via events
    for (const [res, amount] of Object.entries(archetype.cost)) {
      globalEvents.emit(GameEvent.RESOURCE_COLLECTED, {
        type: res as ResourceType,
        amount: -(amount as number),
      });
    }

    const building = new Building({
      position,
      buildingType: type,
      health: archetype.maxHealth,
      maxHealth: archetype.maxHealth,
      cost: archetype.cost,
    });

    this.buildings.push(building);
    entityManager.addEntity(building);

    globalEvents.emit(GameEvent.ENTITY_CREATED, {
      entityId: building.id,
      type: EntityType.BUILDING,
    });

    return building;
  }

  update(_deltaTime: number): void {
    // Buildings are updated via the main entityManager loop
    // But we can handle system-wide building logic here if needed
    this.buildings = this.buildings.filter(b => b.isActive);
  }

  clear(): void {
    this.buildings = [];
  }
}

export const buildingSystem = new BuildingSystem();
