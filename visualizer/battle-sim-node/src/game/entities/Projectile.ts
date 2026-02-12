import type { EntityConfig } from './Entity';
import type { Vector2 } from '../types';
import { DamageType, EntityType, ElementType, ELEMENT_CONFIGS } from '../types';
import { Vec2 } from '../utils/Vector2';
import { Entity } from './Entity';

export interface ProjectileConfig extends Omit<EntityConfig, 'type'> {
  velocity: Vector2;
  damage: number;
  damageType: DamageType;
  lifetime: number;
  pierce?: number;
  element?: ElementType;
  chainCount?: number;
  dotDamage?: number;
  dotDuration?: number;
  slowPercent?: number;
  slowDuration?: number;
  onHit?: (target: Entity) => void;
  glowColor?: string;
  glowRadius?: number;
}

export class Projectile extends Entity {
  damage: number;
  damageType: DamageType;
  pierce: number;
  element: ElementType;
  chainCount: number;
  dotDamage: number;
  dotDuration: number;
  slowPercent: number;
  slowDuration: number;
  onHit?: (target: Entity) => void;
  hasChained: Set<string> = new Set();
  glowColor?: string;
  glowRadius: number = 0;
  
  private trail: Vector2[] = [];
  private maxTrailLength: number = 10;

  constructor(config: ProjectileConfig) {
    super({
      ...config,
      type: EntityType.PROJECTILE,
      radius: 6,
    });
    
    this.velocity = Vec2.clone(config.velocity);
    this.damage = config.damage;
    this.damageType = config.damageType;
    this.maxAge = config.lifetime;
    this.pierce = config.pierce ?? 1;
    this.element = config.element ?? ElementType.NONE;
    this.chainCount = config.chainCount ?? 0;
    this.dotDamage = config.dotDamage ?? 0;
    this.dotDuration = config.dotDuration ?? 0;
    this.slowPercent = config.slowPercent ?? 0;
    this.slowDuration = config.slowDuration ?? 0;
    this.onHit = config.onHit;
    this.glowColor = config.glowColor;
    this.glowRadius = config.glowRadius ?? 0;
    
    this.zIndex = 60;
  }

  update(deltaTime: number): void {
    // Store trail
    this.trail.push(Vec2.clone(this.position));
    if (this.trail.length > this.maxTrailLength) {
      this.trail.shift();
    }
    
    // Move
    this.move(deltaTime);
  }

  takeDamage(_amount: number, _type: DamageType, _source: string = 'enemy'): void {
    // Projectiles don't take damage
  }

  hit(target: Entity): boolean {
    if (this.pierce <= 0) return false;
    
    this.pierce--;
    this.hasChained.add(target.id);
    
    if (this.onHit) {
      this.onHit(target);
    }
    
    if (this.pierce <= 0) {
      this.destroy();
      return true;
    }
    
    return false;
  }

  canChainTo(targetId: string): boolean {
    return this.chainCount > 0 && !this.hasChained.has(targetId);
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    // Draw trail
    if (this.trail.length > 1) {
      ctx.beginPath();
      ctx.moveTo(this.trail[0].x, this.trail[0].y);
      
      for (let i = 1; i < this.trail.length; i++) {
        ctx.lineTo(this.trail[i].x, this.trail[i].y);
      }
      
      ctx.lineTo(this.position.x, this.position.y);
      
      const gradient = ctx.createLinearGradient(
        this.trail[0].x, this.trail[0].y,
        this.position.x, this.position.y
      );
      gradient.addColorStop(0, 'rgba(255, 255, 255, 0)');
      gradient.addColorStop(0.5, this.color + '80');
      gradient.addColorStop(1, this.color);
      
      ctx.strokeStyle = gradient;
      ctx.lineWidth = this.radius * 1.5;
      ctx.lineCap = 'round';
      ctx.stroke();
    }

    // Draw projectile core
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    
    // Draw element glow
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, this.radius * 2, 0, Math.PI * 2);
    ctx.fillStyle = this.color + '60';
    ctx.fill();
    
    // Draw outer glow based on element
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, this.radius * 3, 0, Math.PI * 2);
    ctx.fillStyle = this.color + '30';
    ctx.fill();
  }
}

// Factory functions for different projectile types
export function createElementalProjectile(
  position: Vector2,
  direction: Vector2,
  baseDamage: number,
  element: ElementType
): Projectile {
  const config = ELEMENT_CONFIGS[element];
  const damage = baseDamage * (config.stats.damage ?? 1);
  const speed = 400 * (config.stats.speed ?? 1);
  
  let damageType = DamageType.MAGIC;
  switch (element) {
    case ElementType.FIRE: damageType = DamageType.FIRE; break;
    case ElementType.ICE: damageType = DamageType.ICE; break;
    case ElementType.LIGHTNING: damageType = DamageType.LIGHTNING; break;
    case ElementType.POISON: damageType = DamageType.POISON; break;
    case ElementType.ARCANE: damageType = DamageType.ARCANE; break;
  }
  
  return new Projectile({
    position,
    velocity: Vec2.mul(direction, speed),
    damage,
    damageType,
    lifetime: 3,
    color: config.projectileColor,
    pierce: config.stats.pierceCount ?? 1,
    element,
    chainCount: config.stats.chainCount ?? 0,
    dotDamage: config.stats.dotDamage ?? 0,
    dotDuration: config.stats.dotDuration ?? 0,
    slowPercent: config.stats.slowPercent ?? 0,
    slowDuration: config.stats.slowDuration ?? 0,
  });
}

export function createArrow(
  position: Vector2,
  direction: Vector2,
  speed: number,
  damage: number
): Projectile {
  return new Projectile({
    position,
    velocity: Vec2.mul(direction, speed),
    damage,
    damageType: DamageType.PHYSICAL,
    lifetime: 2,
    color: '#d4a574',
    pierce: 1,
  });
}

export function createMagicBolt(
  position: Vector2,
  direction: Vector2,
  speed: number,
  damage: number,
  element: 'fire' | 'ice' | 'arcane' = 'arcane'
): Projectile {
  const colors = {
    fire: '#ef4444',
    ice: '#3b82f6',
    arcane: '#a855f7',
  };
  
  const damageTypes = {
    fire: DamageType.FIRE,
    ice: DamageType.ICE,
    arcane: DamageType.MAGIC,
  };
  
  return new Projectile({
    position,
    velocity: Vec2.mul(direction, speed),
    damage,
    damageType: damageTypes[element],
    lifetime: 3,
    color: colors[element],
    pierce: 2,
  });
}

export function createFireball(
  position: Vector2,
  direction: Vector2,
  speed: number,
  damage: number
): Projectile {
  return new Projectile({
    position,
    velocity: Vec2.mul(direction, speed),
    damage,
    damageType: DamageType.FIRE,
    lifetime: 2.5,
    color: '#f97316',
    radius: 10,
    pierce: 5,
  });
}
