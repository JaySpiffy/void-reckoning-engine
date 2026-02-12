/**
 * Projectile Entity for Ranged Combat
 * Lasers, bullets, missiles, etc.
 */

import { Entity } from './Entity';
import { DamageType } from '../types';
import { Vec2 } from '../utils/Vector2';
import type { Vector2 } from '../types';

export interface ProjectileConfig {
    position: Vector2;
    velocity: Vector2;
    damage: number;
    sourceId: string;
    targetId: string;
    color: string;
    type: 'laser' | 'bullet' | 'missile' | 'plasma';
    lifetime?: number;
}

export class BattleProjectile extends Entity {
    public velocity: Vector2;
    public damage: number;
    public sourceId: string;
    public targetId: string;
    public lifetime: number;
    public maxLifetime: number;
    public projectileType: string;
    public trail: Vector2[] = [];
    public hasHit: boolean = false;

    constructor(config: ProjectileConfig) {
        super({
            position: Vec2.clone(config.position),
            type: 'PROJECTILE' as any,
            radius: config.type === 'missile' ? 4 : 2,
            color: config.color
        });

        this.velocity = Vec2.clone(config.velocity);
        this.damage = config.damage;
        this.sourceId = config.sourceId;
        this.targetId = config.targetId;
        this.maxLifetime = config.lifetime || 2.0;
        this.lifetime = this.maxLifetime;
        this.projectileType = config.type;
        this.isActive = true;
    }

    update(deltaTime: number): void {
        if (!this.isActive || this.hasHit) return;

        // Store trail position
        this.trail.push(Vec2.clone(this.position));
        if (this.trail.length > 10) {
            this.trail.shift();
        }

        // Move
        this.position = Vec2.add(this.position, Vec2.mul(this.velocity, deltaTime));
        
        // Update lifetime
        this.lifetime -= deltaTime;
        if (this.lifetime <= 0) {
            this.isActive = false;
        }

        this.age += deltaTime;
    }

    render(ctx: CanvasRenderingContext2D): void {
        if (!this.isVisible || this.hasHit) return;

        const lifePercent = this.lifetime / this.maxLifetime;
        const alpha = Math.max(0.3, lifePercent);

        // Draw trail
        if (this.trail.length > 1) {
            ctx.beginPath();
            ctx.moveTo(this.trail[0].x, this.trail[0].y);
            for (let i = 1; i < this.trail.length; i++) {
                ctx.lineTo(this.trail[i].x, this.trail[i].y);
            }
            ctx.lineTo(this.position.x, this.position.y);
            
            ctx.strokeStyle = this.color + Math.floor(alpha * 100).toString(16).padStart(2, '0');
            ctx.lineWidth = this.projectileType === 'missile' ? 3 : 2;
            ctx.stroke();
        }

        // Draw projectile head
        ctx.save();
        
        if (this.projectileType === 'laser') {
            // Laser beam effect
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 10;
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, 3, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.strokeStyle = this.color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, 5, 0, Math.PI * 2);
            ctx.stroke();
        } else if (this.projectileType === 'missile') {
            // Missile with glow
            ctx.shadowColor = '#f97316';
            ctx.shadowBlur = 15;
            ctx.fillStyle = '#fbbf24';
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, 4, 0, Math.PI * 2);
            ctx.fill();
        } else if (this.projectileType === 'plasma') {
            // Plasma ball
            ctx.shadowColor = '#a855f7';
            ctx.shadowBlur = 12;
            ctx.fillStyle = '#e879f9';
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, 5, 0, Math.PI * 2);
            ctx.fill();
        } else {
            // Standard bullet
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 5;
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, 2, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.restore();
    }

    // Check if projectile hit a target
    checkCollision(targetPos: Vector2, targetRadius: number): boolean {
        if (this.hasHit) return false;
        
        const dist = Vec2.distance(this.position, targetPos);
        if (dist <= targetRadius + this.radius) {
            this.hasHit = true;
            this.isActive = false;
            return true;
        }
        return false;
    }

    // Required by Entity base class
    takeDamage(_amount: number, _type: DamageType, _source?: string): void {
        // Projectiles don't take damage
    }
}

// Particle effect for hits/explosions
export class HitEffect {
    public position: Vector2;
    public color: string;
    public size: number;
    public lifetime: number;
    public maxLifetime: number;
    public particles: Array<{ x: number; y: number; vx: number; vy: number; size: number }> = [];
    public isActive: boolean = true;

    constructor(position: Vector2, color: string, size: number = 20) {
        this.position = Vec2.clone(position);
        this.color = color;
        this.size = size;
        this.maxLifetime = 0.5;
        this.lifetime = this.maxLifetime;

        // Create particles
        const particleCount = Math.floor(size / 2);
        for (let i = 0; i < particleCount; i++) {
            const angle = (Math.PI * 2 * i) / particleCount;
            const speed = Math.random() * 50 + 20;
            this.particles.push({
                x: position.x,
                y: position.y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                size: Math.random() * 3 + 1
            });
        }
    }

    update(deltaTime: number): void {
        this.lifetime -= deltaTime;
        
        // Update particles
        for (const p of this.particles) {
            p.x += p.vx * deltaTime;
            p.y += p.vy * deltaTime;
            p.vx *= 0.95; // Drag
            p.vy *= 0.95;
        }

        if (this.lifetime <= 0) {
            this.isActive = false;
        }
    }

    render(ctx: CanvasRenderingContext2D): void {
        if (!this.isActive) return;

        const alpha = this.lifetime / this.maxLifetime;
        
        ctx.save();
        ctx.globalAlpha = alpha;

        // Draw particles
        for (const p of this.particles) {
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * alpha, 0, Math.PI * 2);
            ctx.fill();
        }

        // Center flash
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y, this.size * alpha * 0.5, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
    }
}
