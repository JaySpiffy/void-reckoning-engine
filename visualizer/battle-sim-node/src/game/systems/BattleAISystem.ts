/**
 * Battle AI System - Fixed for proper ranged behavior
 */

import { Unit } from '../entities/Unit';
import { BattleManager } from '../managers/BattleManager';
import { Vec2 } from '../utils/Vector2';
import { SIMULATION_CONFIG } from '../data/SimulationConfig';

export class BattleAISystem {
    private battle: BattleManager;
    private frameCount: number = 0;

    constructor(battle: BattleManager) {
        this.battle = battle;
    }

    update(deltaTime: number): void {
        if (this.battle.phase !== 'BATTLE') return;

        this.frameCount++;
        
        const units = Array.from(this.battle.units.values());
        
        for (const unit of units) {
            if (!unit.isActive) continue;
            this.updateUnit(unit, deltaTime, units);
        }
    }

    private updateUnit(unit: Unit, _deltaTime: number, allUnits: Unit[]): void {
        // Morale effects
        if (unit.morale < 20) {
            unit.unitSpeed *= 0.5;
            if (Math.random() < 0.02) {
                unit.morale += 5;
            }
        }

        // Find target
        if (!unit.targetId || !this.isValidTarget(unit.targetId, unit)) {
            unit.targetId = this.findBestTarget(unit, allUnits);
        }

        const target = unit.targetId ? this.battle.getUnit(unit.targetId) : null;

        if (target && target.isActive) {
            const distance = unit.distanceToUnit(target);
            const attackRange = unit.attackRange;
            
            // RANGED UNITS: Stay at optimal distance
            if (unit.isRanged) {
                const optimalRange = attackRange * 0.7; // Sweet spot for ranged
                const tooClose = attackRange * 0.3; // Too close to target
                
                if (distance <= attackRange && unit.canAttack()) {
                    // Fire!
                    this.performRangedAttack(unit, target);
                }
                
                // Movement logic for ranged
                if (distance < tooClose) {
                    // WAY too close - back up fast
                    const backDir = Vec2.normalize(Vec2.sub(unit.position, target.position));
                    unit.velocity = Vec2.mul(backDir, unit.speed * 0.8);
                } else if (distance < optimalRange * 0.6) {
                    // A bit too close - back up slowly
                    const backDir = Vec2.normalize(Vec2.sub(unit.position, target.position));
                    unit.velocity = Vec2.mul(backDir, unit.speed * 0.4);
                } else if (distance > attackRange) {
                    // Too far - move closer
                    const dir = Vec2.normalize(Vec2.sub(target.position, unit.position));
                    unit.velocity = Vec2.mul(dir, unit.speed * 0.6);
                } else {
                    // In optimal zone - stop and shoot
                    unit.velocity = Vec2.zero();
                }
            } 
            // MELEE UNITS: Charge in
            else {
                if (distance <= attackRange && unit.canAttack()) {
                    this.performMeleeAttack(unit, target);
                }
                
                if (distance > attackRange) {
                    // Charge!
                    const dir = Vec2.normalize(Vec2.sub(target.position, unit.position));
                    unit.velocity = Vec2.mul(dir, unit.speed);
                } else {
                    unit.velocity = Vec2.zero();
                }
            }
        } else {
            // No target - advance toward enemy center
            const enemyCenter = this.getEnemyCenter(unit.team);
            if (enemyCenter) {
                const dir = Vec2.normalize(Vec2.sub(enemyCenter, unit.position));
                // Ranged moves slower when advancing
                const speedMod = unit.isRanged ? 0.4 : 0.6;
                unit.velocity = Vec2.mul(dir, unit.speed * speedMod);
            }
        }

        // Separation to prevent stacking
        this.applySeparation(unit, allUnits);
        this.clampToWorld(unit);
    }

    private isValidTarget(targetId: string, attacker: Unit): boolean {
        const target = this.battle.getUnit(targetId);
        return target !== undefined && target.isActive && target.team !== attacker.team;
    }

    private findBestTarget(unit: Unit, allUnits: Unit[]): string | null {
        let bestTarget: string | null = null;
        let bestScore = -Infinity;
        
        // Ranged units look further
        const searchRange = unit.isRanged 
            ? Math.max(2000, unit.attackRange * 2.5)
            : Math.max(800, unit.attackRange * 2);

        for (const other of allUnits) {
            if (!other.isActive || other.team === unit.team) continue;

            const dist = unit.distanceToUnit(other);
            if (dist > searchRange) continue;

            let score = 0;
            
            if (unit.isRanged) {
                // Ranged: prefer targets at optimal distance
                const optimal = unit.attackRange * 0.6;
                const distFromOptimal = Math.abs(dist - optimal);
                score = 100 - distFromOptimal * 0.1;
                
                // Bonus for wounded
                score += (1 - other.healthPercent) * 50;
                
                // Big bonus for already in range
                if (dist <= unit.attackRange) score += 100;
            } else {
                // Melee: prefer closest
                score = (searchRange - dist);
                score += (1 - other.healthPercent) * 30;
            }

            if (score > bestScore) {
                bestScore = score;
                bestTarget = other.id;
            }
        }

        return bestTarget;
    }

    private getEnemyCenter(team: import('../types/battle').Team): { x: number; y: number } | null {
        const enemies = this.battle.getEnemies(team);
        if (enemies.length === 0) return null;

        let totalX = 0, totalY = 0;
        for (const enemy of enemies) {
            totalX += enemy.position.x;
            totalY += enemy.position.y;
        }

        return {
            x: totalX / enemies.length,
            y: totalY / enemies.length
        };
    }

    private performRangedAttack(attacker: Unit, target: Unit): void {
        let damage = attacker.damage;
        
        if (attacker.morale < 50) damage *= 0.8;
        if (attacker.age < 3) damage *= 1.2;
        
        this.battle.spawnProjectile({
            source: attacker,
            target: target,
            damage: damage
        });
        
        attacker.resetAttackTimer();
    }

    private performMeleeAttack(attacker: Unit, target: Unit): void {
        // Melee attacks are faster but do less per hit
        let damage = attacker.damage * 0.8;
        
        if (attacker.morale < 50) damage *= 0.8;
        if (attacker.age < 5 && attacker.kills === 0) {
            damage *= 1.3; // Charge bonus
        }
        
        this.battle.spawnMeleeEffect(attacker, target, damage);
        attacker.resetAttackTimer();
    }

    private applySeparation(unit: Unit, allUnits: Unit[]): void {
        const minDistance = unit.radius * 3.0;
        let pushX = 0, pushY = 0;
        let pushCount = 0;

        for (const other of allUnits) {
            if (other.id === unit.id || !other.isActive) continue;

            const dist = unit.distanceToUnit(other);
            if (dist < minDistance && dist > 0.01) {
                const overlap = minDistance - dist;
                const pushDir = Vec2.normalize(Vec2.sub(unit.position, other.position));
                
                const pushStrength = overlap * 3.0;
                pushX += pushDir.x * pushStrength;
                pushY += pushDir.y * pushStrength;
                pushCount++;
            }
        }

        if (pushCount > 0) {
            unit.position.x += pushX;
            unit.position.y += pushY;
        }
    }

    private clampToWorld(unit: Unit): void {
        const margin = unit.radius + 20;
        unit.position.x = Math.max(margin, Math.min(SIMULATION_CONFIG.worldWidth - margin, unit.position.x));
        unit.position.y = Math.max(margin, Math.min(SIMULATION_CONFIG.worldHeight - margin, unit.position.y));
    }
}
