/**
 * COMBAT SYSTEM - Professional Overhaul
 *
 * This system handles all combat interactions including:
 * - Player projectiles (fired on mouse hold)
 * - Enemy projectiles
 * - Collision detection
 * - Damage application with visual feedback
 * - DOT effects, chain lightning, AoE
 */

import type { Player} from '../entities';
import { Projectile, Enemy, Particle, damageNumberManager } from '../entities';
import type { Vector2 } from '../types';
import { DamageType, ElementType, GameEvent } from '../types';
import { Vec2 } from '../utils/Vector2';
import { randomRange } from '../utils';
import { globalEvents } from '../utils/EventEmitter';
import { StatusEffectType } from '../entities/Entity';
import { entityManager } from '../managers/EntityManager';

export interface CombatResult {
  hit: boolean;
  damage: number;
  killed: boolean;
  particles: Particle[];
}

export class CombatSystem {
  private projectiles: Projectile[] = [];
  private particles: Particle[] = [];

  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    globalEvents.on(GameEvent.NPC_ABILITY_CAST, (data) => {
      const { npcId, ability, targetPosition } = data;
      // Find the enemy
      const entity = entityManager.getEntity(npcId);
      if (!entity || !(entity instanceof Enemy)) return;
      const enemy = entity;

      if (ability === 'shadow_bolt' || ability === 'quick_attack') {
        this.fireEnemyProjectile(enemy, targetPosition, 'magic');
      } else if (ability === 'teleport') {
        // Handle teleport effect
        this.spawnExplosion(enemy.position, '#a855f7', 10);
        const angle = Math.random() * Math.PI * 2;
        const dist = 150;
        enemy.position.x += Math.cos(angle) * dist;
        enemy.position.y += Math.sin(angle) * dist;
        this.spawnExplosion(enemy.position, '#a855f7', 10);
      }
    });
  }

  // New method for enemies to fire projectiles
  fireEnemyProjectile(source: Enemy, targetPosition: Vector2, type: 'arrow' | 'magic' | 'fireball'): void {
    const direction = Vec2.normalize(Vec2.sub(targetPosition, source.position));
    let projectile: Projectile;
    
    // Example logic based on type
    if (type === 'arrow') {
      projectile = new Projectile({
        position: source.position,
        velocity: Vec2.mul(direction, 300),
        damage: source.stats.damage,
        damageType: DamageType.PHYSICAL,
        lifetime: 3,
        color: '#d4a574',
      });
    } else if (type === 'fireball') {
       projectile = new Projectile({
        position: source.position,
        velocity: Vec2.mul(direction, 250),
        damage: source.stats.damage * 1.5,
        damageType: DamageType.FIRE,
        lifetime: 2.5,
        radius: 10,
        color: '#f97316',
        pierce: 2,
        dotDamage: 5,
        dotDuration: 3,
      });
    }
    else { // Default to magic
      projectile = new Projectile({
        position: source.position,
        velocity: Vec2.mul(direction, 200),
        damage: source.stats.damage * 0.8,
        damageType: DamageType.MAGIC,
        lifetime: 4,
        color: '#a855f7',
      });
    }
    this.projectiles.push(projectile);
    return; // Add explicit return here
  }

  // New method for player attacks
  playerAttack(player: Player, targetPosition: Vector2): void {
    const direction = Vec2.normalize(Vec2.sub(targetPosition, player.position));
    
    const projectile = new Projectile({
      position: player.position,
      velocity: Vec2.mul(direction, 400),
      damage: player.stats.damage,
      damageType: DamageType.PHYSICAL, // Default for now, can be element-based
      lifetime: 2,
      color: '#ffffff',
    });
    this.projectiles.push(projectile);
  }

  update(deltaTime: number, player: Player, enemies: Enemy[]): void {
    // Update projectiles
    this.updateProjectiles(deltaTime, enemies, player);

    // Update particles
    this.updateParticles(deltaTime);
  }

  private updateProjectiles(deltaTime: number, enemies: Enemy[], player: Player): void {
    for (const projectile of this.projectiles) {
      if (!projectile.isActive) continue;

      projectile.tick(deltaTime);

      // Check collision with player (Hostile projectiles)
      if (projectile.isActive && player.isActive && projectile.intersects(player)) {
         // Basic heuristic for hostile projectiles: if color is red or damage type is magic/poison
         const isHostile = projectile.damageType === DamageType.MAGIC || 
                          projectile.damageType === DamageType.POISON || 
                          projectile.color === '#ef4444';
         
         if (isHostile) {
            player.takeDamage(projectile.damage, projectile.damageType);
            projectile.hit(player);
            this.particles.push(...this.createHitEffect(player.position, '#ff0000'));
            continue;
         }
      }

      // Check collisions with enemies (Friendly projectiles)
      for (const enemy of enemies) {
        if (!enemy.isActive) continue;
        if (projectile.hasChained.has(enemy.id)) continue;

        if (projectile.intersects(enemy)) {
          const result = this.applyDamage(enemy, projectile.damage, projectile.damageType);

          if (result.hit) {
            const destroyed = projectile.hit(enemy);
            this.particles.push(...result.particles);

            // Apply Status Effects using the new base Entity system
            if (projectile.dotDamage > 0 && projectile.dotDuration > 0) {
              enemy.applyStatusEffect({
                type: projectile.damageType === DamageType.FIRE ? StatusEffectType.BURN : StatusEffectType.POISON,
                duration: projectile.dotDuration,
                damagePerSecond: projectile.dotDamage,
              });
            }

            // Apply slow effect
            if (projectile.slowPercent > 0 && projectile.slowDuration > 0) {
              enemy.applyStatusEffect({
                type: StatusEffectType.SLOW,
                duration: projectile.slowDuration,
                speedMultiplier: 1 - projectile.slowPercent,
              });
            }

            // Chain lightning
            if (projectile.chainCount > 0 && projectile.element === ElementType.LIGHTNING) {
              this.chainLightning(projectile, enemy, enemies, player);
            }

            if (destroyed) break;
          }
        }
      }
    }

    // Remove inactive projectiles
    this.projectiles = this.projectiles.filter(p => p.isActive);
  }

  private updateParticles(deltaTime: number): void {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const particle = this.particles[i];
      particle.tick(deltaTime);
      if (!particle.isActive) {
        this.particles.splice(i, 1);
      }
    }
  }

  private applyDamage(target: Enemy | Player, damage: number, type: DamageType): CombatResult {
    target.takeDamage(damage, type);

    // Spawn damage number if it's an enemy
    if (target instanceof Enemy) {
      damageNumberManager.spawn(target.position, damage, type, false);
    }

    const particles = this.createHitEffect(target.position, '#ffffff');

    return {
      hit: true,
      damage,
      killed: !target.isActive,
      particles,
    };
  }

  private chainLightning(projectile: Projectile, hitEnemy: Enemy, allEnemies: Enemy[], _player: Player): void {
    if (projectile.chainCount <= 0) return;

    // Find nearest enemy that hasn't been chained to
    let nearestEnemy: Enemy | null = null;
    let nearestDistance = Infinity;

    for (const enemy of allEnemies) {
      if (!enemy.isActive || enemy === hitEnemy) continue;
      if (projectile.hasChained.has(enemy.id)) continue;

      const distance = Vec2.distance(hitEnemy.position, enemy.position);
      if (distance < nearestDistance && distance < 200) {
        nearestDistance = distance;
        nearestEnemy = enemy;
      }
    }

    if (nearestEnemy) {
      // Create chain visual
      this.createChainVisual(hitEnemy.position, nearestEnemy.position, projectile.color);

      // Apply damage to chained enemy
      const chainDamage = projectile.damage * 0.7;
      const result = this.applyDamage(nearestEnemy, chainDamage, projectile.damageType);
      this.particles.push(...result.particles);

      // Mark as chained
      projectile.hasChained.add(nearestEnemy.id);
      projectile.chainCount--;

      // Continue chaining
      if (projectile.chainCount > 0) {
        this.chainLightning(projectile, nearestEnemy, allEnemies, _player);
      }
    }
  }

  private createChainVisual(from: Vector2, to: Vector2, color: string): void {
    // Add some particles along the chain path
    for (let i = 0; i < 5; i++) {
      const t = i / 4;
      const pos = Vec2.lerp(from, to, t);
      pos.x += (Math.random() - 0.5) * 10;
      pos.y += (Math.random() - 0.5) * 10;

      // Create simple particle
      const particle = new Particle({
        position: pos,
        velocity: { x: 0, y: 0 },
        lifetime: 0.3,
        radius: 3,
        color,
        fadeOut: true,
        shrink: true,
      });
      this.particles.push(particle);
    }
  }

  private createHitEffect(position: Vector2, color: string): Particle[] {
    const particles: Particle[] = [];
    const count = 5;

    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      const speed = randomRange(50, 150);

      particles.push(new Particle({
        position: { ...position },
        velocity: {
          x: Math.cos(angle) * speed,
          y: Math.sin(angle) * speed,
        },
        lifetime: randomRange(0.2, 0.4),
        radius: randomRange(2, 4),
        color,
        fadeOut: true,
        shrink: true,
      }));
    }

    return particles;
  }

  // Particle effects
  spawnParticles(particles: Particle[]): void {
    this.particles.push(...particles);
  }

  spawnExplosion(position: Vector2, color: string = '#ef4444', count: number = 10): void {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = randomRange(100, 300);

      this.particles.push(new Particle({
        position: { ...position },
        velocity: {
          x: Math.cos(angle) * speed,
          y: Math.sin(angle) * speed,
        },
        lifetime: randomRange(0.3, 0.6),
        radius: randomRange(3, 6),
        color,
        fadeOut: true,
        shrink: true,
      }));
    }
  }

  // Getters for rendering
  getProjectiles(): Projectile[] {
    return this.projectiles;
  }

  getParticles(): Particle[] {
    return this.particles;
  }

  clear(): void {
    this.projectiles = [];
    this.particles = [];
  }
}

export const combatSystem = new CombatSystem();
