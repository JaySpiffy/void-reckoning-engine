/**
 * Interceptor / Deployment Ship
 * Protoss-style small attack drones launched from carriers
 */

import { Entity } from './Entity';
import { DamageType } from '../types';
import { Vec2 } from '../utils/Vector2';
import type { Vector2 } from '../types';
import { Unit } from './Unit';

export interface InterceptorConfig {
    position: Vector2;
    parentId: string;
    team: import('../types/battle').Team;
    color: string;
}

export class Interceptor extends Entity {
    public parentId: string;
    public team: import('../types/battle').Team;
    public targetId: string | null = null;
    public damage: number = 8;
    public attackRange: number = 40;
    public attackCooldown: number = 0.4;
    public attackTimer: number = 0;
    public lifetime: number = 15;
    public maxLifetime: number = 15;
    public orbitAngle: number = Math.random() * Math.PI * 2;
    public orbitRadius: number = 30 + Math.random() * 20;
    public state: 'orbiting' | 'attacking' | 'returning' = 'orbiting';
    public kills: number = 0;

    constructor(config: InterceptorConfig) {
        super({
            position: Vec2.clone(config.position),
            type: 'INTERCEPTOR' as any,
            radius: 4,
            color: config.color
        });

        this.parentId = config.parentId;
        this.team = config.team;
        this.isActive = true;
    }

    // Custom update with extra parameters - called manually from BattleManager
    customUpdate(deltaTime: number, parent: Unit | null, allUnits: Unit[]): void {
        if (!this.isActive) return;

        this.lifetime -= deltaTime;
        if (this.lifetime <= 0) {
            this.isActive = false;
            return;
        }

        this.attackTimer -= deltaTime;
        this.age += deltaTime;

        if (!parent || !parent.isActive) {
            // Parent died - go aggressive
            this.state = 'attacking';
        }

        // Find target
        if (!this.targetId || !this.isValidTarget(this.targetId, allUnits)) {
            this.targetId = this.findBestTarget(allUnits);
        }

        const target = this.targetId ? allUnits.find(u => u.id === this.targetId) : null;

        if (target && target.isActive) {
            const dist = Vec2.distance(this.position, target.position);

            if (dist <= this.attackRange && this.attackTimer <= 0) {
                // Attack!
                this.performAttack(target);
                this.attackTimer = this.attackCooldown;
            }

            if (dist > this.attackRange * 0.8) {
                // Move toward target
                const dir = Vec2.normalize(Vec2.sub(target.position, this.position));
                this.position = Vec2.add(this.position, Vec2.mul(dir, 120 * deltaTime));
                this.state = 'attacking';
            } else {
                // Orbit around target
                this.orbitAngle += 3 * deltaTime;
                const orbitX = target.position.x + Math.cos(this.orbitAngle) * 25;
                const orbitY = target.position.y + Math.sin(this.orbitAngle) * 25;
                this.position = Vec2.lerp(this.position, Vec2.create(orbitX, orbitY), 0.1);
            }
        } else if (parent && parent.isActive) {
            // Orbit around parent
            this.orbitAngle += 2 * deltaTime;
            const targetX = parent.position.x + Math.cos(this.orbitAngle) * this.orbitRadius;
            const targetY = parent.position.y + Math.sin(this.orbitAngle) * this.orbitRadius;
            this.position = Vec2.lerp(this.position, Vec2.create(targetX, targetY), 0.05);
            this.state = 'orbiting';
        }

        // World bounds
        this.clampToWorld();
    }

    private isValidTarget(targetId: string, allUnits: Unit[]): boolean {
        const target = allUnits.find(u => u.id === targetId);
        return target !== undefined && target.isActive && target.team !== this.team;
    }

    private findBestTarget(allUnits: Unit[]): string | null {
        let bestTarget: string | null = null;
        let bestDist = Infinity;

        for (const unit of allUnits) {
            if (!unit.isActive || unit.team === this.team) continue;
            
            const dist = Vec2.distance(this.position, unit.position);
            if (dist < bestDist && dist < 400) {
                bestDist = dist;
                bestTarget = unit.id;
            }
        }

        return bestTarget;
    }

    private performAttack(target: Unit): void {
        target.takeDamage(this.damage, 'PHYSICAL' as any, this.parentId);
        
        if (!target.isActive) {
            this.kills++;
        }
    }

    private clampToWorld(): void {
        const margin = 20;
        this.position.x = Math.max(margin, Math.min(2980, this.position.x));
        this.position.y = Math.max(margin, Math.min(1980, this.position.y));
    }

    render(ctx: CanvasRenderingContext2D): void {
        if (!this.isVisible) return;

        const pulse = Math.sin(this.age * 8) * 1;

        // Glow
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 8 + pulse;

        // Body
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y, this.radius + pulse * 0.3, 0, Math.PI * 2);
        ctx.fill();

        // Core
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y, 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;

        // State indicator
        if (this.state === 'attacking') {
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, this.radius + 3, 0, Math.PI * 2);
            ctx.stroke();
        }
    }

    takeDamage(_amount: number, _type: DamageType, _source?: string): void {
        // Interceptors are fragile - die in one hit
        this.isActive = false;
    }

    // Base update required by Entity - just lifetime management
    update(deltaTime: number): void {
        if (!this.isActive) return;
        this.lifetime -= deltaTime;
        if (this.lifetime <= 0) {
            this.isActive = false;
        }
        this.age += deltaTime;
    }
}
