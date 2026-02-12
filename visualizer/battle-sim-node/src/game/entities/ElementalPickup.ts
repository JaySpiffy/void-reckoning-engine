import type { EntityConfig } from './Entity';
import type { DamageType } from '../types';
import { ElementType, EntityType, GameEvent } from '../types';
import { Vec2 } from '../utils/Vector2';
import { globalEvents } from '../utils/EventEmitter';
import { randomRange } from '../utils';
import { Entity } from './Entity';

export interface ElementalPickupConfig extends Omit<EntityConfig, 'type'> {
  elementType: ElementType;
  duration: number;
}

const ELEMENT_COLORS: Record<ElementType, string> = {
  [ElementType.NONE]: '#9ca3af',
  [ElementType.FIRE]: '#ef4444',
  [ElementType.ICE]: '#3b82f6',
  [ElementType.LIGHTNING]: '#eab308',
  [ElementType.POISON]: '#22c55e',
  [ElementType.ARCANE]: '#a855f7',
};

const ELEMENT_NAMES: Record<ElementType, string> = {
  [ElementType.NONE]: 'None',
  [ElementType.FIRE]: 'Fire',
  [ElementType.ICE]: 'Ice',
  [ElementType.LIGHTNING]: 'Lightning',
  [ElementType.POISON]: 'Poison',
  [ElementType.ARCANE]: 'Arcane',
};

export class ElementalPickup extends Entity {
  elementType: ElementType;
  duration: number;
  
  private bobPhase: number = randomRange(0, Math.PI * 2);
  private pulsePhase: number = 0;
  private magnetTarget: { x: number; y: number } | null = null;
  private magnetSpeed: number = 0;

  constructor(config: ElementalPickupConfig) {
    super({
      ...config,
      type: EntityType.ELEMENTAL_PICKUP,
      radius: 15,
      color: ELEMENT_COLORS[config.elementType],
    });
    
    this.elementType = config.elementType;
    this.duration = config.duration;
    this.zIndex = 25;
  }

  update(deltaTime: number): void {
    this.bobPhase += deltaTime * 4;
    this.pulsePhase += deltaTime * 5;
    
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
    globalEvents.emit(GameEvent.ELEMENT_CHANGED, {
      element: this.elementType,
      duration: this.duration,
    });
    
    this.destroy();
  }

  takeDamage(_amount: number, _type: DamageType, _source: string = 'enemy'): void {
    // Pickups don't take damage
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    const bobOffset = Math.sin(this.bobPhase) * 5;
    const pulseScale = 1 + Math.sin(this.pulsePhase) * 0.15;
    const x = this.position.x;
    const y = this.position.y + bobOffset;
    const radius = this.radius * pulseScale;

    // Outer glow
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius * 2);
    gradient.addColorStop(0, this.color + '80');
    gradient.addColorStop(0.5, this.color + '40');
    gradient.addColorStop(1, this.color + '00');
    
    ctx.beginPath();
    ctx.arc(x, y, radius * 2, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Main body
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();

    // Inner core
    ctx.beginPath();
    ctx.arc(x, y, radius * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    // Element symbol/icon
    ctx.fillStyle = this.color;
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const symbol = this.getElementSymbol();
    ctx.fillText(symbol, x, y);

    // Border
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Label
    ctx.fillStyle = '#ffffff';
    ctx.font = '10px sans-serif';
    ctx.fillText(ELEMENT_NAMES[this.elementType], x, y + radius + 12);
  }

  private getElementSymbol(): string {
    switch (this.elementType) {
      case ElementType.FIRE: return '🔥';
      case ElementType.ICE: return '❄️';
      case ElementType.LIGHTNING: return '⚡';
      case ElementType.POISON: return '☠️';
      case ElementType.ARCANE: return '✨';
      default: return '?';
    }
  }
}

// Factory function to create random elemental pickup
export function createRandomElementalPickup(position: { x: number; y: number }): ElementalPickup {
  const elements = [ElementType.FIRE, ElementType.ICE, ElementType.LIGHTNING, ElementType.POISON, ElementType.ARCANE];
  const randomElement = elements[Math.floor(Math.random() * elements.length)];
  
  return new ElementalPickup({
    position: { ...position },
    elementType: randomElement,
    duration: 15, // 15 seconds of elemental power
  });
}
