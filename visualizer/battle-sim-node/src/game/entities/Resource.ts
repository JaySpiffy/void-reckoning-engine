import type { EntityConfig } from './Entity';
import type { DamageType } from '../types';
import { ResourceType, GameEvent, EntityType } from '../types';
import { Vec2 } from '../utils/Vector2';
import { globalEvents } from '../utils/EventEmitter';
import { randomRange } from '../utils';
import { Entity } from './Entity';

export interface ResourceConfig extends Omit<EntityConfig, 'type'> {
  resourceType: ResourceType;
  amount: number;
  autoCollect?: boolean;
}

const RESOURCE_COLORS: Record<ResourceType, string> = {
  [ResourceType.WOOD]: '#92400e',
  [ResourceType.STONE]: '#6b7280',
  [ResourceType.GOLD]: '#eab308',
  [ResourceType.MANA]: '#3b82f6',
};

const RESOURCE_RADIUS: Record<ResourceType, number> = {
  [ResourceType.WOOD]: 8,
  [ResourceType.STONE]: 10,
  [ResourceType.GOLD]: 6,
  [ResourceType.MANA]: 7,
};

export class Resource extends Entity {
  resourceType: ResourceType;
  amount: number;
  autoCollect: boolean;

  private bobPhase: number = randomRange(0, Math.PI * 2);
  private magnetTarget: { x: number; y: number } | null = null;
  private magnetSpeed: number = 0;

  constructor(config: ResourceConfig) {
    super({
      ...config,
      position: config.position, // Explicitly pass position
      type: EntityType.RESOURCE,
      radius: RESOURCE_RADIUS[config.resourceType],
      color: RESOURCE_COLORS[config.resourceType],
    });

    this.resourceType = config.resourceType;
    this.amount = config.amount;
    this.autoCollect = config.autoCollect ?? false;

    this.zIndex = 20;
  }

  update(deltaTime: number): void {
    this.bobPhase += deltaTime * 4;

    // Magnet behavior
    if (this.magnetTarget) {
      const direction = Vec2.normalize(Vec2.sub(this.magnetTarget, this.position));
      this.velocity = Vec2.mul(direction, this.magnetSpeed);
      this.move(deltaTime);

      // Increase magnet speed over time
      this.magnetSpeed = Math.min(this.magnetSpeed + deltaTime * 500, 400);
    }
  }

  attractTo(target: { x: number; y: number }): void {
    this.magnetTarget = target;
    this.magnetSpeed = 100;
  }

  collect(): void {
    globalEvents.emit(GameEvent.RESOURCE_COLLECTED, {
      type: this.resourceType,
      amount: this.amount,
    });

    this.destroy();
  }

  takeDamage(_amount: number, _type: DamageType, _source: string = 'enemy'): void {
    // Resources don't take damage
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    const bobOffset = Math.sin(this.bobPhase) * 3;
    const x = this.position.x;
    const y = this.position.y + bobOffset;

    // Draw glow for mana and gold
    if (this.resourceType === ResourceType.MANA || this.resourceType === ResourceType.GOLD) {
      ctx.beginPath();
      ctx.arc(x, y, this.radius * 2, 0, Math.PI * 2);
      ctx.fillStyle = this.color + '30';
      ctx.fill();
    }

    // Draw resource body
    ctx.beginPath();
    ctx.arc(x, y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();

    // Draw inner highlight
    ctx.beginPath();
    ctx.arc(x - this.radius * 0.3, y - this.radius * 0.3, this.radius * 0.3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.fill();

    // Border
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Draw amount for larger stacks
    if (this.amount > 1) {
      ctx.fillStyle = '#ffffff';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(this.amount.toString(), x, y);
    }
  }
}

// Factory functions
export function createResourceDrop(
  position: { x: number; y: number },
  enemyType: string
): Resource[] {
  const resources: Resource[] = [];

  // Determine drops based on enemy type
  const drops: { type: ResourceType; min: number; max: number; chance: number }[] = [
    { type: ResourceType.GOLD, min: 1, max: 5, chance: 0.8 },
    { type: ResourceType.WOOD, min: 0, max: 2, chance: 0.3 },
    { type: ResourceType.STONE, min: 0, max: 1, chance: 0.2 },
  ];

  // Add mana drops for higher level enemies
  if (enemyType === 'dark_mage' || enemyType === 'boss') {
    drops.push({ type: ResourceType.MANA, min: 1, max: 3, chance: 0.5 });
  }

  for (const drop of drops) {
    if (Math.random() < drop.chance) {
      const amount = Math.floor(randomRange(drop.min, drop.max + 1));
      if (amount > 0) {
        // Spread resources around slightly
        const offsetX = randomRange(-15, 15);
        const offsetY = randomRange(-15, 15);

        resources.push(new Resource({
          position: {
            x: position.x + offsetX,
            y: position.y + offsetY,
          },
          resourceType: drop.type,
          amount,
        }));
      }
    }
  }

  return resources;
}
