import type { EntityConfig } from './Entity';
import type { Vector2 } from '../types';
import { EnemyType, DamageType, GameEvent, EntityType } from '../types';
import { Vec2 } from '../utils/Vector2';
import { globalEvents } from '../utils/EventEmitter';
import { clamp, randomRange } from '../utils';
import { Entity } from './Entity';

export interface EnemyConfig extends Omit<EntityConfig, 'type'> {
  enemyType: EnemyType;
}

interface EnemyStats {
  health: number;
  maxHealth: number;
  speed: number;
  damage: number;
  attackRange: number;
  attackCooldown: number;
  experienceValue: number;
}

const ENEMY_STAT_CONFIGS: Record<EnemyType, Partial<EnemyStats>> = {
  // Original enemies
  [EnemyType.GOBLIN]: {
    maxHealth: 30,
    speed: 120,
    damage: 8,
    attackRange: 25,
    attackCooldown: 1,
    experienceValue: 10,
  },
  [EnemyType.SKELETON]: {
    maxHealth: 40,
    speed: 80,
    damage: 12,
    attackRange: 30,
    attackCooldown: 1.2,
    experienceValue: 15,
  },
  [EnemyType.ORC]: {
    maxHealth: 80,
    speed: 60,
    damage: 20,
    attackRange: 35,
    attackCooldown: 1.5,
    experienceValue: 30,
  },
  [EnemyType.DARK_MAGE]: {
    maxHealth: 50,
    speed: 70,
    damage: 25,
    attackRange: 200,
    attackCooldown: 2,
    experienceValue: 40,
  },
  [EnemyType.BOSS]: {
    maxHealth: 500,
    speed: 40,
    damage: 50,
    attackRange: 50,
    attackCooldown: 2,
    experienceValue: 200,
  },
  
  // New enemies - Early game
  [EnemyType.SPIDER]: {
    maxHealth: 25,
    speed: 100,
    damage: 10,
    attackRange: 20,
    attackCooldown: 0.8,
    experienceValue: 12,
  },
  [EnemyType.WOLF]: {
    maxHealth: 35,
    speed: 140,
    damage: 12,
    attackRange: 25,
    attackCooldown: 0.9,
    experienceValue: 14,
  },
  
  // New enemies - Mid game
  [EnemyType.MANTICORE]: {
    maxHealth: 70,
    speed: 90,
    damage: 22,
    attackRange: 35,
    attackCooldown: 1.1,
    experienceValue: 35,
  },
  [EnemyType.SERPENT]: {
    maxHealth: 55,
    speed: 95,
    damage: 18,
    attackRange: 30,
    attackCooldown: 1.0,
    experienceValue: 28,
  },
  [EnemyType.GOLEM]: {
    maxHealth: 120,
    speed: 50,
    damage: 15,
    attackRange: 40,
    attackCooldown: 1.5,
    experienceValue: 45,
  },
  
  // New enemies - Late game
  [EnemyType.CRYSTAL_WALKER]: {
    maxHealth: 90,
    speed: 65,
    damage: 28,
    attackRange: 200,
    attackCooldown: 1.8,
    experienceValue: 50,
  },
  [EnemyType.STORM_BIRD]: {
    maxHealth: 70,
    speed: 130,
    damage: 25,
    attackRange: 180,
    attackCooldown: 1.2,
    experienceValue: 42,
  },
  [EnemyType.SLIME_BOSS]: {
    maxHealth: 200,
    speed: 55,
    damage: 20,
    attackRange: 45,
    attackCooldown: 1.3,
    experienceValue: 80,
  },
  [EnemyType.LIGHT_WARDEN]: {
    maxHealth: 85,
    speed: 75,
    damage: 30,
    attackRange: 220,
    attackCooldown: 1.5,
    experienceValue: 48,
  },
  [EnemyType.CHIMERA]: {
    maxHealth: 150,
    speed: 85,
    damage: 35,
    attackRange: 40,
    attackCooldown: 1.0,
    experienceValue: 75,
  },
};

const ENEMY_COLORS: Record<EnemyType, string> = {
  // Original
  [EnemyType.GOBLIN]: '#22c55e',
  [EnemyType.SKELETON]: '#e5e7eb',
  [EnemyType.ORC]: '#166534',
  [EnemyType.DARK_MAGE]: '#7c3aed',
  [EnemyType.BOSS]: '#dc2626',
  // New - Early game
  [EnemyType.SPIDER]: '#84cc16',
  [EnemyType.WOLF]: '#9ca3af',
  // New - Mid game
  [EnemyType.MANTICORE]: '#ef4444',
  [EnemyType.SERPENT]: '#3b82f6',
  [EnemyType.GOLEM]: '#92400e',
  // New - Late game
  [EnemyType.CRYSTAL_WALKER]: '#a855f7',
  [EnemyType.STORM_BIRD]: '#22d3ee',
  [EnemyType.SLIME_BOSS]: '#ec4899',
  [EnemyType.LIGHT_WARDEN]: '#fef3c7',
  [EnemyType.CHIMERA]: '#7c3aed',
};

export class Enemy extends Entity {
  enemyType: EnemyType;
  stats: EnemyStats;

  private attackCooldownTimer: number = 0;
  private wanderTarget: Vector2 | null = null;
  private wanderTimer: number = 0;
  private isWandering: boolean = false;

  // Visual
  private idleOffset: number = randomRange(0, Math.PI * 2);
  private hitFlash: number = 0;

  constructor(config: EnemyConfig) {
    const enemyConfig = ENEMY_STAT_CONFIGS[config.enemyType];

    super({
      ...config,
      type: EntityType.ENEMY,
      radius: config.enemyType === EnemyType.BOSS ? 30 : config.enemyType === EnemyType.ORC ? 18 : 12,
      color: ENEMY_COLORS[config.enemyType],
    });

    this.enemyType = config.enemyType;
    this.stats = {
      health: enemyConfig.maxHealth!,
      maxHealth: enemyConfig.maxHealth!,
      speed: enemyConfig.speed!,
      damage: enemyConfig.damage!,
      attackRange: enemyConfig.attackRange!,
      attackCooldown: enemyConfig.attackCooldown!,
      experienceValue: enemyConfig.experienceValue!,
    };

    this.zIndex = 50;
  }

  update(deltaTime: number): void {
    // Update hit flash
    if (this.hitFlash > 0) {
      this.hitFlash -= deltaTime * 5;
    }

    // Update attack cooldown
    if (this.attackCooldownTimer > 0) {
      this.attackCooldownTimer -= deltaTime;
    }

    // Apply velocity with status effect multipliers
    const speedMult = this.getSpeedMultiplier();
    if (Vec2.magnitudeSquared(this.velocity) > 0) {
       const delta = Vec2.mul(Vec2.mul(this.velocity, speedMult), deltaTime);
       this.position = Vec2.add(this.position, delta);
    }

    // Update wander timer
    if (this.isWandering) {
      this.wanderTimer -= deltaTime;
      if (this.wanderTimer <= 0) {
        this.isWandering = false;
        this.wanderTarget = null;
      }
    }
  }

  chase(target: Vector2): void {
    this.isWandering = false;

    const direction = Vec2.normalize(Vec2.sub(target, this.position));
    this.velocity = Vec2.mul(direction, this.stats.speed);
  }

  wander(bounds: { minX: number; maxX: number; minY: number; maxY: number }): void {
    if (!this.isWandering || this.wanderTarget === null) {
      // Pick new wander target
      this.wanderTarget = {
        x: randomRange(bounds.minX, bounds.maxX),
        y: randomRange(bounds.minY, bounds.maxY),
      };
      this.isWandering = true;
      this.wanderTimer = randomRange(2, 5);
    }

    const direction = Vec2.normalize(Vec2.sub(this.wanderTarget, this.position));
    this.velocity = Vec2.mul(direction, this.stats.speed * 0.5);

    // If close to wander target, pick new one
    if (Vec2.distance(this.position, this.wanderTarget) < 10) {
      this.wanderTarget = null;
    }
  }

  stop(): void {
    this.velocity = Vec2.zero();
  }

  canAttack(): boolean {
    return this.attackCooldownTimer <= 0;
  }

  attack(): number {
    if (!this.canAttack()) return 0;

    this.attackCooldownTimer = this.stats.attackCooldown;
    return this.stats.damage;
  }

  takeDamage(amount: number, type: DamageType = DamageType.PHYSICAL, source: string = 'player'): void {
    this.stats.health = clamp(this.stats.health - amount, 0, this.stats.maxHealth);
    this.hitFlash = 1;

    globalEvents.emit(GameEvent.DAMAGE_DEALT, {
      targetId: this.id,
      damage: {
        amount,
        type,
        source,
      },
    });

    if (this.stats.health <= 0) {
      this.die();
    }
  }

  die(): void {
    globalEvents.emit(GameEvent.ENEMY_KILLED, {
      enemyId: this.id,
      enemyType: this.enemyType,
      position: Vec2.clone(this.position),
      experience: this.stats.experienceValue,
    });

    this.destroy();
  }

  isInAttackRange(target: Vector2): boolean {
    return Vec2.distance(this.position, target) <= this.stats.attackRange;
  }

  isAlive(): boolean {
    return this.stats.health > 0;
  }

  getHealthPercent(): number {
    return this.stats.health / this.stats.maxHealth;
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    // Apply hit flash
    const baseColor = this.color;
    if (this.hitFlash > 0) {
      this.color = '#ffffff';
    }

    // Idle animation
    const idleBob = Math.sin(this.age * 3 + this.idleOffset) * 2;

    // Draw enemy body
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y + idleBob, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();

    // Inner detail based on type
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y + idleBob, this.radius * 0.6, 0, Math.PI * 2);
    ctx.fillStyle = this.getInnerColor();
    ctx.fill();

    // Border
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Health bar for non-goblin enemies or damaged enemies
    if (this.enemyType !== EnemyType.GOBLIN || this.stats.health < this.stats.maxHealth) {
      this.renderHealthBar(ctx, idleBob);
    }

    // Restore color
    this.color = baseColor;
  }

  private getInnerColor(): string {
    switch (this.enemyType) {
      case EnemyType.GOBLIN:
        return '#16a34a';
      case EnemyType.SKELETON:
        return '#9ca3af';
      case EnemyType.ORC:
        return '#14532d';
      case EnemyType.DARK_MAGE:
        return '#5b21b6';
      case EnemyType.BOSS:
        return '#991b1b';
      default:
        return '#ffffff';
    }
  }

  private renderHealthBar(ctx: CanvasRenderingContext2D, yOffset: number): void {
    const barWidth = 30;
    const barHeight = 4;
    const x = this.position.x - barWidth / 2;
    const y = this.position.y - this.radius - 10 + yOffset;

    // Background
    ctx.fillStyle = '#374151';
    ctx.fillRect(x, y, barWidth, barHeight);

    // Health
    const healthPercent = this.getHealthPercent();
    ctx.fillStyle = healthPercent > 0.5 ? '#ef4444' : '#fbbf24';
    ctx.fillRect(x, y, barWidth * healthPercent, barHeight);

    // Border
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, barWidth, barHeight);
  }
}
