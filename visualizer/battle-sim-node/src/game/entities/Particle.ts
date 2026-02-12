import type { EntityConfig } from './Entity';
import type { Vector2 , DamageType } from '../types';
import { Vec2 } from '../utils/Vector2';
import { EntityType } from '../types';
import { randomRange, randomChoice } from '../utils';
import { Entity } from './Entity';

export interface ParticleConfig extends Omit<EntityConfig, 'type'> {
  velocity: Vector2;
  lifetime: number;
  fadeOut?: boolean;
  shrink?: boolean;
  gravity?: number;
  onComplete?: () => void;
}

export class Particle extends Entity {
  initialRadius: number;
  fadeOut: boolean;
  shrink: boolean;
  gravity: number;
  onComplete?: () => void;

  private initialAlpha: number = 1;

  constructor(config: ParticleConfig) {
    super({
      ...config,
      type: EntityType.PARTICLE,
    });

    this.velocity = Vec2.clone(config.velocity);
    this.maxAge = config.lifetime;
    this.initialRadius = this.radius;
    this.fadeOut = config.fadeOut ?? true;
    this.shrink = config.shrink ?? true;
    this.gravity = config.gravity ?? 0;
    this.onComplete = config.onComplete;

    this.zIndex = 1000;
  }

  update(deltaTime: number): void {
    // Apply gravity
    if (this.gravity !== 0) {
      this.velocity.y += this.gravity * deltaTime;
    }

    // Move
    this.move(deltaTime);

    // Calculate life ratio (0 = just born, 1 = dead)
    const lifeRatio = this.age / (this.maxAge ?? 1);

    // Fade out
    if (this.fadeOut) {
      this.initialAlpha = 1 - lifeRatio;
    }

    // Shrink
    if (this.shrink) {
      this.radius = this.initialRadius * (1 - lifeRatio);
    }

    // Call onComplete when dying
    if (lifeRatio >= 1 && this.onComplete) {
      this.onComplete();
    }
  }

  takeDamage(_amount: number, _type: DamageType, _source: string = 'enemy'): void {
    // Particles don't take damage
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    ctx.save();
    ctx.globalAlpha = this.initialAlpha;

    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, Math.max(0, this.radius), 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();

    ctx.restore();
  }
}

// Particle effect factories
export function createExplosion(
  position: Vector2,
  color: string = '#ef4444',
  count: number = 10,
  spread: number = 100
): Particle[] {
  const particles: Particle[] = [];

  for (let i = 0; i < count; i++) {
    const angle = randomRange(0, Math.PI * 2);
    const speed = randomRange(spread * 0.3, spread);
    const velocity = Vec2.fromAngle(angle, speed);

    particles.push(new Particle({
      position: Vec2.clone(position),
      velocity,
      lifetime: randomRange(0.3, 0.8),
      radius: randomRange(2, 5),
      color,
      fadeOut: true,
      shrink: true,
    }));
  }

  return particles;
}

export function createHitEffect(
  position: Vector2,
  color: string = '#ffffff'
): Particle[] {
  return createExplosion(position, color, 5, 50);
}

export function createLevelUpEffect(position: Vector2): Particle[] {
  const colors = ['#fbbf24', '#f59e0b', '#fcd34d', '#ffffff'];
  const particles: Particle[] = [];

  for (let i = 0; i < 30; i++) {
    const angle = randomRange(0, Math.PI * 2);
    const speed = randomRange(80, 150);
    const velocity = Vec2.fromAngle(angle, speed);

    particles.push(new Particle({
      position: Vec2.clone(position),
      velocity,
      lifetime: randomRange(0.5, 1.2),
      radius: randomRange(3, 6),
      color: randomChoice(colors),
      fadeOut: true,
      shrink: true,
    }));
  }

  return particles;
}

export function createTrailEffect(
  position: Vector2,
  color: string = '#3b82f6',
  count: number = 3
): Particle[] {
  const particles: Particle[] = [];

  for (let i = 0; i < count; i++) {
    const offset = {
      x: randomRange(-5, 5),
      y: randomRange(-5, 5),
    };

    particles.push(new Particle({
      position: Vec2.add(position, offset),
      velocity: { x: 0, y: 0 },
      lifetime: randomRange(0.2, 0.4),
      radius: randomRange(2, 4),
      color,
      fadeOut: true,
      shrink: true,
    }));
  }

  return particles;
}

export function createDamageNumber(
  position: Vector2,
  _damage: number
): Particle {
  const velocity = {
    x: randomRange(-20, 20),
    y: -50 - randomRange(0, 30),
  };

  return new Particle({
    position: Vec2.clone(position),
    velocity,
    lifetime: 0.8,
    radius: 0,
    color: '#ffffff',
    fadeOut: true,
    shrink: false,
    gravity: 100,
  });
}
