import type { Vector2 } from '../types';
import { Vec2 } from '../utils/Vector2';
import { randomRange } from '../utils';

/**
 * DamageNumber - Floating text that shows damage dealt
 * This is a visual effect, not a true Entity, to avoid entity system overhead
 */
export class DamageNumber {
  position: Vector2;
  velocity: Vector2;
  damage: number;
  isCrit: boolean;
  lifetime: number;
  maxLifetime: number;
  isActive: boolean = true;
  
  // Color based on damage type
  color: string;

  constructor(
    position: Vector2,
    damage: number,
    damageType: string = 'physical',
    isCrit: boolean = false
  ) {
    this.position = Vec2.clone(position);
    this.velocity = {
      x: randomRange(-30, 30),
      y: -80 - randomRange(0, 40), // Float upward
    };
    this.damage = damage;
    this.isCrit = isCrit;
    this.maxLifetime = isCrit ? 1.2 : 0.8;
    this.lifetime = this.maxLifetime;
    
    // Set color based on damage type
    const colors: Record<string, string> = {
      physical: '#ffffff',
      fire: '#f97316',
      ice: '#60a5fa',
      lightning: '#facc15',
      poison: '#22c55e',
      arcane: '#c084fc',
      magic: '#a855f7',
    };
    this.color = colors[damageType] || colors.physical;
  }

  update(deltaTime: number): void {
    // Move
    this.position.x += this.velocity.x * deltaTime;
    this.position.y += this.velocity.y * deltaTime;
    
    // Slow down horizontal movement
    this.velocity.x *= 0.95;
    
    // Update lifetime
    this.lifetime -= deltaTime;
    if (this.lifetime <= 0) {
      this.isActive = false;
    }
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isActive) return;
    
    const lifeRatio = this.lifetime / this.maxLifetime;
    const alpha = Math.min(1, lifeRatio * 2); // Fade out at end
    
    ctx.save();
    ctx.globalAlpha = alpha;
    
    // Crit damage is larger and has outline
    const fontSize = this.isCrit ? 24 : 16;
    ctx.font = `bold ${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const text = Math.floor(this.damage).toString();
    const x = this.position.x;
    const y = this.position.y;
    
    // Draw outline for crits
    if (this.isCrit) {
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 3;
      ctx.strokeText(text, x, y);
    }
    
    // Draw text
    ctx.fillStyle = this.color;
    ctx.fillText(text, x, y);
    
    // Crit indicator
    if (this.isCrit) {
      ctx.font = 'bold 12px sans-serif';
      ctx.fillStyle = '#ef4444';
      ctx.fillText('CRIT!', x, y - fontSize * 0.8);
    }
    
    ctx.restore();
  }
}

// Manager for all damage numbers
export class DamageNumberManager {
  private damageNumbers: DamageNumber[] = [];

  spawn(position: Vector2, damage: number, damageType: string = 'physical', isCrit: boolean = false): void {
    this.damageNumbers.push(new DamageNumber(position, damage, damageType, isCrit));
  }

  update(deltaTime: number): void {
    for (const dn of this.damageNumbers) {
      dn.update(deltaTime);
    }
    this.damageNumbers = this.damageNumbers.filter(dn => dn.isActive);
  }

  render(ctx: CanvasRenderingContext2D): void {
    for (const dn of this.damageNumbers) {
      dn.render(ctx);
    }
  }

  clear(): void {
    this.damageNumbers = [];
  }
}

export const damageNumberManager = new DamageNumberManager();
