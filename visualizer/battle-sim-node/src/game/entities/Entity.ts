import { DamageType } from '../types';
import type { Vector2, Bounds , EntityType} from '../types';
import { generateId } from '../utils';
import { Vec2 } from '../utils/Vector2';

export interface EntityConfig {
  position: Vector2;
  radius?: number;
  color?: string;
  type: EntityType;
}

export enum StatusEffectType {
  BURN = 'burn',
  SLOW = 'slow',
  POISON = 'poison',
  STUN = 'stun',
  FREEZE = 'freeze',
}

export interface StatusEffect {
  type: StatusEffectType;
  duration: number;
  timer: number;
  damagePerSecond?: number;
  speedMultiplier?: number;
  stacks?: number;
}

export abstract class Entity {
  readonly id: string;
  readonly type: EntityType;

  position: Vector2;
  velocity: Vector2;
  radius: number;
  color: string;

  isActive: boolean = true;
  isVisible: boolean = true;
  zIndex: number = 0;

  // Lifecycle
  age: number = 0;
  maxAge?: number;

  // Status Effects
  statusEffects: StatusEffect[] = [];

  constructor(config: EntityConfig) {
    this.id = generateId(config.type);
    this.type = config.type;
    this.position = Vec2.clone(config.position);
    this.velocity = Vec2.zero();
    this.radius = config.radius ?? 10;
    this.color = config.color ?? '#ffffff';
  }

  abstract update(deltaTime: number): void;

  // This should be implemented by entities that can take damage
  abstract takeDamage(amount: number, type: DamageType, source?: string): void;

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.stroke();

    this.renderStatusEffects(ctx);
  }

  protected renderStatusEffects(ctx: CanvasRenderingContext2D): void {
    if (this.statusEffects.length === 0) return;

    this.statusEffects.forEach((effect, index) => {
      const angle = (index / this.statusEffects.length) * Math.PI * 2 + this.age * 2;
      const x = this.position.x + Math.cos(angle) * (this.radius + 5);
      const y = this.position.y + Math.sin(angle) * (this.radius + 5);

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = this.getStatusEffectColor(effect.type);
      ctx.fill();
    });
  }

  private getStatusEffectColor(type: StatusEffectType): string {
    switch (type) {
      case StatusEffectType.BURN: return '#f97316';
      case StatusEffectType.SLOW: return '#3b82f6';
      case StatusEffectType.POISON: return '#22c55e';
      case StatusEffectType.FREEZE: return '#06b6d4';
      default: return '#ffffff';
    }
  }

  // Called every frame
  tick(deltaTime: number): void {
    if (!this.isActive) return;

    this.age += deltaTime;

    if (this.maxAge !== undefined && this.age >= this.maxAge) {
      this.destroy();
      return;
    }

    this.updateStatusEffects(deltaTime);
    this.update(deltaTime);
  }

  protected updateStatusEffects(deltaTime: number): void {
    for (let i = this.statusEffects.length - 1; i >= 0; i--) {
      const effect = this.statusEffects[i];
      effect.duration -= deltaTime;
      effect.timer += deltaTime;

      // Apply DoT
      if (effect.damagePerSecond && effect.timer >= 1.0) {
        effect.timer -= 1.0;
        this.takeDamage(effect.damagePerSecond, this.getDamageTypeForEffect(effect.type), 'status_effect');
      }

      if (effect.duration <= 0) {
        this.statusEffects.splice(i, 1);
      }
    }
  }

  private getDamageTypeForEffect(type: StatusEffectType): DamageType {
    switch (type) {
      case StatusEffectType.BURN: return DamageType.FIRE;
      case StatusEffectType.POISON: return DamageType.POISON;
      default: return DamageType.MAGIC;
    }
  }

  applyStatusEffect(effect: Omit<StatusEffect, 'timer'>): void {
    const existing = this.statusEffects.find(e => e.type === effect.type);
    if (existing) {
      existing.duration = Math.max(existing.duration, effect.duration);
      if (effect.stacks) existing.stacks = (existing.stacks || 0) + effect.stacks;
    } else {
      this.statusEffects.push({ ...effect, timer: 0 });
    }
  }

  getSpeedMultiplier(): number {
    let multiplier = 1.0;
    for (const effect of this.statusEffects) {
      if (effect.speedMultiplier) {
        multiplier *= effect.speedMultiplier;
      }
    }
    return multiplier;
  }

  // Movement
  move(deltaTime: number): void {
    if (Vec2.magnitudeSquared(this.velocity) > 0) {
      const delta = Vec2.mul(this.velocity, deltaTime);
      this.position = Vec2.add(this.position, delta);
    }
  }

  // Collision
  getBounds(): Bounds {
    return {
      x: this.position.x - this.radius,
      y: this.position.y - this.radius,
      width: this.radius * 2,
      height: this.radius * 2,
    };
  }

  intersects(other: Entity): boolean {
    const distance = Vec2.distance(this.position, other.position);
    return distance < (this.radius + other.radius);
  }

  containsPoint(point: Vector2): boolean {
    const distance = Vec2.distance(this.position, point);
    return distance <= this.radius;
  }

  // Lifecycle
  destroy(): void {
    this.isActive = false;
  }

  // Distance to another entity or position
  distanceTo(other: { position: Vector2 }): number {
    return Vec2.distance(this.position, other.position);
  }

  // Direction to another entity or position
  directionTo(other: { position: Vector2 }): Vector2 {
    return Vec2.normalize(Vec2.sub(other.position, this.position));
  }

  // Angle to another entity or position
  angleTo(other: { position: Vector2 }): number {
    return Vec2.angle(Vec2.sub(other.position, this.position));
  }
}
