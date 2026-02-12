import { logger, LogCategory } from '../managers/LogManager';
import type { Vector2 } from '../types';
import type { Player } from '../entities/Player';
import type { Enemy } from '../entities/Enemy';
import { Vec2 } from '../utils/Vector2';

/**
 * AUTOPLAY SYSTEM - AI-controlled player for testing
 *
 * This system takes control of the player character and plays the game
 * automatically for testing purposes. It will:
 * - Move toward enemies when safe, retreat when low health
 * - Use abilities and attacks automatically
 * - Dodge incoming threats
 * - Collect pickups
 *
 * Toggle with: AutoplaySystem.toggle() or press 'F9' in game
 */

export interface AutoplayConfig {
    /** Distance to maintain from enemies (default: 150) */
    preferredCombatRange: number;
    /** Health percentage below which to retreat (default: 0.3) */
    retreatHealthThreshold: number;
    /** Enable random movement when no enemies nearby (default: true) */
    idleWander: boolean;
    /** Attack rate multiplier (default: 1.0) */
    aggressiveness: number;
    /** Use abilities automatically (default: true) */
    useAbilities: boolean;
}

const DEFAULT_CONFIG: AutoplayConfig = {
    preferredCombatRange: 150,
    retreatHealthThreshold: 0.3,
    idleWander: true,
    aggressiveness: 1.0,
    useAbilities: true,
};

export class AutoplaySystem {
    private enabled: boolean = false;
    private config: AutoplayConfig;

    // State tracking
    private wanderTarget: Vector2 | null = null;
    private wanderTimer: number = 0;
    private lastAbilityTime: number = 0;
    private currentAbilitySlot: number = 1;

    // Output state (what the system "wants" to do)
    private movementVector: Vector2 = { x: 0, y: 0 };
    private targetPosition: Vector2 = { x: 0, y: 0 };
    private wantsToAttack: boolean = false;
    private abilitySlotToUse: number = 0;

    constructor(config: Partial<AutoplayConfig> = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
    }

    toggle(): boolean {
        this.enabled = !this.enabled;
        logger.info(LogCategory.AUTOPLAY, `${this.enabled ? 'ENABLED' : 'DISABLED'}`);
        return this.enabled;
    }

    enable(): void {
        this.enabled = true;
        logger.info(LogCategory.AUTOPLAY, 'ENABLED');
    }

    disable(): void {
        this.enabled = false;
        logger.info(LogCategory.AUTOPLAY, 'DISABLED');
    }

    isEnabled(): boolean {
        return this.enabled;
    }

    setConfig(config: Partial<AutoplayConfig>): void {
        this.config = { ...this.config, ...config };
    }

    /**
     * Main update - calculates what the AI wants to do this frame
     */
    update(
        deltaTime: number,
        player: Player | null,
        enemies: Enemy[],
        worldBounds: { width: number; height: number }
    ): void {
        if (!this.enabled || !player) {
            this.movementVector = { x: 0, y: 0 };
            this.wantsToAttack = false;
            this.abilitySlotToUse = 0;
            return;
        }

        // Reset frame state
        this.wantsToAttack = false;
        this.abilitySlotToUse = 0;

        // Get active enemies
        const activeEnemies = enemies.filter(e => e.isActive);

        // Calculate decision-making
        const healthPercent = player.stats.health / player.stats.maxHealth;
        const shouldRetreat = healthPercent < this.config.retreatHealthThreshold;

        // Find nearest enemy
        const nearestEnemy = this.findNearestEnemy(player.position, activeEnemies);

        if (nearestEnemy) {
            const distanceToEnemy = Vec2.distance(player.position, nearestEnemy.position);

            // Decide movement strategy
            if (shouldRetreat && distanceToEnemy < 200) {
                // Run away from danger!
                this.movementVector = this.calculateRetreatVector(player.position, activeEnemies, worldBounds);
            } else if (distanceToEnemy > this.config.preferredCombatRange + 50) {
                // Move toward enemy if too far
                this.movementVector = this.calculateApproachVector(player.position, nearestEnemy.position);
            } else if (distanceToEnemy < this.config.preferredCombatRange - 30) {
                // Back up if too close (kiting)
                this.movementVector = this.calculateKiteVector(player.position, nearestEnemy.position);
            } else {
                // In the sweet spot - strafe
                this.movementVector = this.calculateStrafeVector(player.position, nearestEnemy.position, deltaTime);
            }

            // Set target for attacks
            this.targetPosition = { ...nearestEnemy.position };
            this.wantsToAttack = true;

            // Cycle through abilities
            if (this.config.useAbilities) {
                this.lastAbilityTime += deltaTime;
                if (this.lastAbilityTime > 0.3 / this.config.aggressiveness) {
                    this.lastAbilityTime = 0;
                    this.currentAbilitySlot++;
                    if (this.currentAbilitySlot > 5) this.currentAbilitySlot = 1;
                    this.abilitySlotToUse = this.currentAbilitySlot;
                }
            }
        } else if (this.config.idleWander) {
            // No enemies - wander randomly
            this.movementVector = this.calculateWanderVector(player.position, worldBounds, deltaTime);
            this.targetPosition = this.wanderTarget || player.position;
        } else {
            // Stay still
            this.movementVector = { x: 0, y: 0 };
        }

        // Log occasionally
        if (Math.random() < 0.01) {
            logger.debug(LogCategory.AUTOPLAY, `Movement: (${this.movementVector.x.toFixed(1)}, ${this.movementVector.y.toFixed(1)}) | Enemies: ${activeEnemies.length} | Health: ${(healthPercent * 100).toFixed(0)}%`);
        }
    }

    // === Output Methods (called by GameManager) ===

    getMovementVector(): Vector2 {
        return { ...this.movementVector };
    }

    getTargetPosition(): Vector2 {
        return { ...this.targetPosition };
    }

    shouldAttack(): boolean {
        return this.wantsToAttack;
    }

    getAbilitySlotToUse(): number {
        const slot = this.abilitySlotToUse;
        this.abilitySlotToUse = 0; // Consume
        return slot;
    }

    // === Helper Methods ===

    private findNearestEnemy(playerPos: Vector2, enemies: Enemy[]): Enemy | null {
        let nearest: Enemy | null = null;
        let nearestDist = Infinity;

        for (const enemy of enemies) {
            const dist = Vec2.distance(playerPos, enemy.position);
            if (dist < nearestDist) {
                nearestDist = dist;
                nearest = enemy;
            }
        }

        return nearest;
    }

    private calculateApproachVector(from: Vector2, to: Vector2): Vector2 {
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        if (length === 0) return { x: 0, y: 0 };
        return { x: dx / length, y: dy / length };
    }

    private calculateKiteVector(playerPos: Vector2, enemyPos: Vector2): Vector2 {
        // Move away from enemy
        const dx = playerPos.x - enemyPos.x;
        const dy = playerPos.y - enemyPos.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        if (length === 0) return { x: 1, y: 0 };
        return { x: dx / length, y: dy / length };
    }

    private calculateStrafeVector(playerPos: Vector2, enemyPos: Vector2, _deltaTime: number): Vector2 {
        // Circle around the enemy
        const dx = enemyPos.x - playerPos.x;
        const dy = enemyPos.y - playerPos.y;
        // Perpendicular direction (strafe)
        const strafeFactor = Math.sin(Date.now() / 500) > 0 ? 1 : -1;
        return { x: -dy * strafeFactor * 0.7, y: dx * strafeFactor * 0.7 };
    }

    private calculateRetreatVector(playerPos: Vector2, enemies: Enemy[], bounds: { width: number; height: number }): Vector2 {
        // Calculate average enemy direction and run opposite
        let totalDx = 0;
        let totalDy = 0;
        let count = 0;

        for (const enemy of enemies) {
            const dist = Vec2.distance(playerPos, enemy.position);
            if (dist < 300) {
                const weight = 1 / (dist + 1);
                totalDx += (enemy.position.x - playerPos.x) * weight;
                totalDy += (enemy.position.y - playerPos.y) * weight;
                count++;
            }
        }

        if (count === 0) return { x: 0, y: 0 };

        // Invert direction (run away)
        let retreatX = -totalDx;
        let retreatY = -totalDy;
        const length = Math.sqrt(retreatX * retreatX + retreatY * retreatY);
        if (length > 0) {
            retreatX /= length;
            retreatY /= length;
        }

        // Avoid world edges
        const margin = 100;
        if (playerPos.x < margin && retreatX < 0) retreatX = Math.abs(retreatX);
        if (playerPos.x > bounds.width - margin && retreatX > 0) retreatX = -Math.abs(retreatX);
        if (playerPos.y < margin && retreatY < 0) retreatY = Math.abs(retreatY);
        if (playerPos.y > bounds.height - margin && retreatY > 0) retreatY = -Math.abs(retreatY);

        return { x: retreatX, y: retreatY };
    }

    private calculateWanderVector(playerPos: Vector2, bounds: { width: number; height: number }, deltaTime: number): Vector2 {
        this.wanderTimer -= deltaTime;

        // Pick new wander target every few seconds
        if (this.wanderTimer <= 0 || !this.wanderTarget) {
            this.wanderTimer = 2 + Math.random() * 3;
            this.wanderTarget = {
                x: 200 + Math.random() * (bounds.width - 400),
                y: 200 + Math.random() * (bounds.height - 400),
            };
        }

        const distToTarget = Vec2.distance(playerPos, this.wanderTarget);
        if (distToTarget < 30) {
            this.wanderTimer = 0; // Pick new target
            return { x: 0, y: 0 };
        }

        return this.calculateApproachVector(playerPos, this.wanderTarget);
    }
}

export const autoplaySystem = new AutoplaySystem();
