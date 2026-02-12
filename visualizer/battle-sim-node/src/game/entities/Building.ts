import { Entity } from './Entity';
import type { EntityConfig } from './Entity';
import type { DamageType} from '../types';
import { BuildingType, EntityType } from '../types';
import type { Enemy } from './Enemy';
import { combatSystem } from '../systems/CombatSystem';

import { Vec2 } from '../utils/Vector2';
import { entityManager } from '../managers/EntityManager';

export interface BuildingConfig extends Omit<EntityConfig, 'type'> {
  buildingType: BuildingType;
  health: number;
  maxHealth: number;
  cost: {
    wood?: number;
    stone?: number;
    gold?: number;
  };
}

export class Building extends Entity {
  buildingType: BuildingType;
  health: number;
  maxHealth: number;
  
  private attackTimer: number = 0;
  private attackCooldown: number = 1.0;

  constructor(config: BuildingConfig) {
    super({
      ...config,
      type: EntityType.BUILDING,
      radius: config.buildingType === BuildingType.WALL ? 20 : 25,
      color: config.buildingType === BuildingType.WALL ? '#78350f' : '#94a3b8',
    });

    this.buildingType = config.buildingType;
    this.health = config.health;
    this.maxHealth = config.maxHealth;
    this.zIndex = 40;
  }

  update(deltaTime: number): void {
    if (this.buildingType === BuildingType.TOWER) {
      this.updateTower(deltaTime);
    }
  }

  private updateTower(deltaTime: number): void {
    this.attackTimer += deltaTime;
    if (this.attackTimer >= this.attackCooldown) {
      this.attackTimer = 0;
      this.fireAtNearestEnemy();
    }
  }

  private fireAtNearestEnemy(): void {
    const enemies = entityManager.getEnemies();
    let nearest: Enemy | null = null;
    let minDist = 300; // Tower range

    for (const enemy of enemies) {
      if (!enemy.isActive) continue;
      const dist = Vec2.distance(this.position, enemy.position);
      if (dist < minDist) {
        minDist = dist;
        nearest = enemy;
      }
    }

    if (nearest) {
      combatSystem.fireEnemyProjectile(this as unknown as Enemy, nearest.position, 'arrow');
    }
  }

  takeDamage(amount: number, _type: DamageType, _source: string = 'enemy'): void {
    this.health -= amount;
    if (this.health <= 0) {
      this.destroy();
    }
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    ctx.save();
    
    if (this.buildingType === BuildingType.WALL) {
      // Draw a brick-like rectangle for walls
      ctx.fillStyle = this.color;
      ctx.fillRect(this.position.x - this.radius, this.position.y - this.radius, this.radius * 2, this.radius * 2);
      ctx.strokeStyle = '#451a03';
      ctx.lineWidth = 2;
      ctx.strokeRect(this.position.x - this.radius, this.position.y - this.radius, this.radius * 2, this.radius * 2);
    } else {
      // Draw a tower
      ctx.fillStyle = '#475569';
      ctx.beginPath();
      ctx.moveTo(this.position.x - this.radius, this.position.y + this.radius);
      ctx.lineTo(this.position.x + this.radius, this.position.y + this.radius);
      ctx.lineTo(this.position.x + this.radius * 0.6, this.position.y - this.radius);
      ctx.lineTo(this.position.x - this.radius * 0.6, this.position.y - this.radius);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      
      // Top part
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(this.position.x - this.radius * 0.8, this.position.y - this.radius - 10, this.radius * 1.6, 10);
    }

    // Health bar
    const healthPercent = this.health / this.maxHealth;
    ctx.fillStyle = '#374151';
    ctx.fillRect(this.position.x - 15, this.position.y - this.radius - 20, 30, 4);
    ctx.fillStyle = healthPercent > 0.5 ? '#22c55e' : '#ef4444';
    ctx.fillRect(this.position.x - 15, this.position.y - this.radius - 20, 30 * healthPercent, 4);

    ctx.restore();
  }
}
