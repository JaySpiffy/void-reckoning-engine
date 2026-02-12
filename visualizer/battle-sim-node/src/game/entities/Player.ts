import type { EntityConfig } from './Entity';
import type { Vector2, PlayerStats, DamageInfo } from '../types';
import { WeaponType, DamageType, GameEvent, ElementType, ELEMENT_CONFIGS, EntityType } from '../types';
import { Vec2 } from '../utils/Vector2';
import { globalEvents } from '../utils/EventEmitter';
import { clamp } from '../utils';
import { logger, LogCategory } from '../managers/LogManager';
import { configManager } from '../managers/ConfigManager';
import { Entity } from './Entity';
import { dnaSystem } from '../systems/DNASystem';
import { COMPLETE_EVOLUTION_TREE } from '../systems/EvolutionTree';

export interface PlayerConfig extends Omit<EntityConfig, 'type'> {
  name?: string;
}

export class Player extends Entity {
  name: string;

  stats: PlayerStats;

  weapon: WeaponType = WeaponType.STAFF;

  // Combat
  attackCooldown: number = 0;
  isAttacking: boolean = false;
  attackAngle: number = 0;
  isInvulnerable: boolean = false;

  // Movement
  facingDirection: Vector2 = { x: 1, y: 0 };
  shape: 'humanoid' | 'quadruped' | 'amorphous' | 'serpentine' | 'winged' = 'humanoid';
  
  // Visual
  private pulsePhase: number = 0;
  private trail: Vector2[] = [];

  constructor(config: PlayerConfig) {
    super({
      ...config,
      type: EntityType.PLAYER,
      radius: 15,
      color: '#3b82f6',
    });

    const playerConfig = configManager.get('player');

    this.stats = {
      maxHealth: playerConfig.base_health,
      health: playerConfig.base_health,
      maxMana: playerConfig.base_mana,
      mana: playerConfig.base_mana,
      speed: playerConfig.base_speed,
      damage: playerConfig.base_damage,
      attackSpeed: playerConfig.base_attack_speed,
      attackRange: playerConfig.base_attack_range,
      level: 1,
      experience: 0,
      experienceToNext: playerConfig.exp_base,
      element: ElementType.NONE,
      elementDuration: 0,
      elementLevel: 0,
      elementExperience: 0,
    };

    this.name = config.name ?? 'Hero';
    this.zIndex = 100;
  }

  update(deltaTime: number): void {
    this.pulsePhase += deltaTime * 3;

    // Apply evolution bonuses if any
    this.updateEvolutionStats();

    // Store trail for serpentine/winged logic
    if (this.age % 0.05 < deltaTime) {
      this.trail.push(Vec2.clone(this.position));
      if (this.trail.length > 10) this.trail.shift();
    }

    // Apply velocity with status effect multipliers
    const speedMult = this.getSpeedMultiplier();
    if (Vec2.magnitudeSquared(this.velocity) > 0) {
       const delta = Vec2.mul(Vec2.mul(this.velocity, speedMult), deltaTime);
       this.position = Vec2.add(this.position, delta);
    }

    // Update attack cooldown
    if (this.attackCooldown > 0) {
      this.attackCooldown -= deltaTime;
    }

    // Update element duration
    if (this.stats.elementDuration > 0) {
      this.stats.elementDuration -= deltaTime;
      if (this.stats.elementDuration <= 0) {
        this.setElement(ElementType.NONE);
      }
    }

    // Regenerate mana slowly
    this.stats.mana = Math.min(this.stats.maxMana, this.stats.mana + deltaTime * 3);
  }

  private updateEvolutionStats(): void {
    const currentFormId = dnaSystem.getCurrentForm();
    if (currentFormId === 'base') {
      this.shape = 'humanoid';
      return;
    }

    const evolution = COMPLETE_EVOLUTION_TREE[currentFormId];
    if (evolution) {
      // Update appearance
      this.color = evolution.appearance.color;
      this.radius = 15 * evolution.appearance.size;
      this.shape = evolution.appearance.shape;
    }
  }

  setMovement(direction: Vector2): void {
    // Normalize and apply speed
    const normalized = Vec2.normalize(direction);
    
    // Apply speed with evolution multiplier
    let speed = this.stats.speed;
    const currentFormId = dnaSystem.getCurrentForm();
    if (currentFormId !== 'base') {
      const evolution = COMPLETE_EVOLUTION_TREE[currentFormId];
      if (evolution) {
        speed *= evolution.bonuses.speedMultiplier;
      }
    }

    this.velocity = Vec2.mul(normalized, speed);

    // Update facing direction if moving
    if (Vec2.magnitudeSquared(normalized) > 0) {
      this.facingDirection = normalized;
    }
  }

  setElement(element: ElementType, duration: number = 0): void {
    this.stats.element = element;
    this.stats.elementDuration = duration;

    // Update color based on element (if not evolved)
    if (dnaSystem.getCurrentForm() === 'base') {
      const config = ELEMENT_CONFIGS[element];
      this.color = config.color;
    }
  }

  getElementDamageType(): DamageType {
    switch (this.stats.element) {
      case ElementType.FIRE: return DamageType.FIRE;
      case ElementType.ICE: return DamageType.ICE;
      case ElementType.LIGHTNING: return DamageType.LIGHTNING;
      case ElementType.POISON: return DamageType.POISON;
      case ElementType.ARCANE: return DamageType.ARCANE;
      default: return DamageType.MAGIC;
    }
  }

  getModifiedDamage(): number {
    let baseDamage = this.stats.damage;
    
    // Evolution multiplier
    const currentFormId = dnaSystem.getCurrentForm();
    if (currentFormId !== 'base') {
      const evolution = COMPLETE_EVOLUTION_TREE[currentFormId];
      if (evolution) {
        baseDamage *= evolution.bonuses.damageMultiplier;
      }
    }

    const elementConfig = ELEMENT_CONFIGS[this.stats.element];
    const damageMultiplier = elementConfig.stats.damage ?? 1;
    return baseDamage * damageMultiplier;
  }

  getProjectileSpeed(): number {
    const baseSpeed = 400;
    const elementConfig = ELEMENT_CONFIGS[this.stats.element];
    const speedMultiplier = elementConfig.stats.speed ?? 1;
    return baseSpeed * speedMultiplier;
  }

  getPierceCount(): number {
    const elementConfig = ELEMENT_CONFIGS[this.stats.element];
    return elementConfig.stats.pierceCount ?? 1;
  }

  attack(targetPosition: Vector2): boolean {
    if (this.attackCooldown > 0) return false;

    this.isAttacking = true;
    this.attackAngle = Vec2.angle(Vec2.sub(targetPosition, this.position));
    this.attackCooldown = 1 / this.stats.attackSpeed;

    // Reset attack animation flag after short delay
    setTimeout(() => {
      this.isAttacking = false;
    }, 100);

    return true;
  }

  canAttack(): boolean {
    return this.attackCooldown <= 0;
  }

  markAttackUsed(): void {
    this.attackCooldown = 1 / this.stats.attackSpeed;
  }

  takeDamage(amount: number, type: DamageType = DamageType.PHYSICAL, source: string = 'enemy'): void {
    // Apply damage reduction based on type could go here
    let actualDamage = Math.max(1, amount);
    
    // Evolution resistances
    const currentFormId = dnaSystem.getCurrentForm();
    if (currentFormId !== 'base') {
      const evolution = COMPLETE_EVOLUTION_TREE[currentFormId];
      if (evolution) {
        // Find if this damage type has resistance in evolution
        // DamageType and DNAType are similar but not same, need mapping or unified enum
        // For now, simple check
        const resistance = (evolution.bonuses.resistances as Record<string, number>)[type] || 0;
        actualDamage *= (1 - resistance);
        
        const weakness = (evolution.bonuses.weaknesses as Record<string, number>)[type] || 0;
        actualDamage *= (1 + weakness);
      }
    }

    this.stats.health = clamp(this.stats.health - actualDamage, 0, this.stats.maxHealth);

    globalEvents.emit(GameEvent.DAMAGE_DEALT, {
      targetId: this.id,
      damage: {
        amount: actualDamage,
        type,
        source,
      } as DamageInfo,
    });

    if (this.stats.health <= 0) {
      this.die();
    }
  }

  heal(amount: number): void {
    this.stats.health = clamp(this.stats.health + amount, 0, this.stats.maxHealth);
  }

  restoreMana(amount: number): void {
    this.stats.mana = clamp(this.stats.mana + amount, 0, this.stats.maxMana);
  }

  gainExperience(amount: number): void {
    this.stats.experience += amount;

    if (this.stats.experience >= this.stats.experienceToNext) {
      this.levelUp();
    }
  }

  levelUp(): void {
    this.stats.level++;
    this.stats.experience -= this.stats.experienceToNext;
    this.stats.experienceToNext = Math.floor(this.stats.experienceToNext * 1.4);

    // Significant stat increases that impact gameplay
    const level = this.stats.level;

    // Health: +15 per level (scales with level)
    this.stats.maxHealth += 15 + Math.floor(level * 2);
    this.stats.health = this.stats.maxHealth;

    // Mana: +10 per level
    this.stats.maxMana += 10 + Math.floor(level * 1.5);
    this.stats.mana = this.stats.maxMana;

    // Damage: +5 per level (compounds with element multipliers)
    this.stats.damage += 5 + Math.floor(level * 0.5);

    // Attack Speed: Small increase every few levels
    if (level % 3 === 0) {
      this.stats.attackSpeed = Math.min(10, this.stats.attackSpeed + 0.2);
    }

    // Movement Speed: Small increase every few levels
    if (level % 5 === 0) {
      this.stats.speed = Math.min(400, this.stats.speed + 10);
    }

    // Attack Range: Increase every few levels
    if (level % 4 === 0) {
      this.stats.attackRange = Math.min(400, this.stats.attackRange + 15);
    }

    logger.info(LogCategory.GAMEPLAY, `Level up! Now level ${level}`);
    logger.info(LogCategory.GAMEPLAY, `Stats: HP ${this.stats.maxHealth}, MP ${this.stats.maxMana}, DMG ${this.stats.damage}, SPD ${this.stats.speed.toFixed(0)}, ASPD ${this.stats.attackSpeed.toFixed(1)}`);

    globalEvents.emit(GameEvent.LEVEL_UP, { level: this.stats.level });
  }

  die(): void {
    globalEvents.emit(GameEvent.GAME_OVER, {
      score: 0,
      wave: 0,
      survived: 0,
    });
  }

  isAlive(): boolean {
    return this.stats.health > 0;
  }

  render(ctx: CanvasRenderingContext2D): void {
    if (!this.isVisible) return;

    // Draw weapon range indicator when attacking
    if (this.isAttacking) {
      ctx.save();
      ctx.translate(this.position.x, this.position.y);
      ctx.rotate(this.attackAngle);

      const range = this.stats.attackRange;
      ctx.beginPath();
      ctx.arc(0, 0, range, -Math.PI / 6, Math.PI / 6);
      ctx.fillStyle = this.color + '40';
      ctx.fill();

      ctx.restore();
    }

    const pulse = Math.sin(this.pulsePhase) * 2;

    // Elemental aura
    if (this.stats.element !== ElementType.NONE) {
      const auraGradient = ctx.createRadialGradient(
        this.position.x, this.position.y, 0,
        this.position.x, this.position.y, this.radius + 15 + pulse
      );
      auraGradient.addColorStop(0, this.color + '40');
      auraGradient.addColorStop(1, this.color + '00');

      ctx.beginPath();
      ctx.arc(this.position.x, this.position.y, this.radius + 15 + pulse, 0, Math.PI * 2);
      ctx.fillStyle = auraGradient;
      ctx.fill();
    }

    ctx.save();
    
    // Draw based on shape
    switch (this.shape) {
      case 'serpentine':
        this.drawSerpentine(ctx);
        break;
      case 'winged':
        this.drawWinged(ctx, pulse);
        break;
      case 'quadruped':
        this.drawQuadruped(ctx, pulse);
        break;
      case 'amorphous':
        this.drawAmorphous(ctx, pulse);
        break;
      default: // humanoid/circle
        this.drawHumanoid(ctx, pulse);
    }

    ctx.restore();

    // Draw health bar and element indicator
    this.renderHealthBar(ctx);
    if (this.stats.element !== ElementType.NONE) {
      this.renderElementIndicator(ctx);
    }
  }

  private drawHumanoid(ctx: CanvasRenderingContext2D, pulse: number): void {
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, this.radius + pulse, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Core
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, this.radius * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    // Direction indicator
    const dirEnd = Vec2.add(this.position, Vec2.mul(this.facingDirection, this.radius + 10));
    ctx.beginPath();
    ctx.moveTo(this.position.x, this.position.y);
    ctx.lineTo(dirEnd.x, dirEnd.y);
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 3;
    ctx.stroke();
  }

  private drawSerpentine(ctx: CanvasRenderingContext2D): void {
    // Draw trail segments
    for (let i = 0; i < this.trail.length; i++) {
      const pos = this.trail[i];
      const r = this.radius * (0.4 + (i / this.trail.length) * 0.6);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, r, 0, Math.PI * 2);
      ctx.fillStyle = this.color + '80';
      ctx.fill();
    }

    // Head
    ctx.beginPath();
    ctx.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Eyes
    const eyeAngle = Math.atan2(this.facingDirection.y, this.facingDirection.x);
    for (const side of [-1, 1]) {
       const x = this.position.x + Math.cos(eyeAngle + 0.5 * side) * (this.radius * 0.6);
       const y = this.position.y + Math.sin(eyeAngle + 0.5 * side) * (this.radius * 0.6);
       ctx.beginPath();
       ctx.arc(x, y, 3, 0, Math.PI * 2);
       ctx.fillStyle = '#ffffff';
       ctx.fill();
    }
  }

  private drawWinged(ctx: CanvasRenderingContext2D, _pulse: number): void {
    const angle = Math.atan2(this.facingDirection.y, this.facingDirection.x);
    const wingFlap = Math.sin(this.age * 10) * 0.5;

    ctx.save();
    ctx.translate(this.position.x, this.position.y);
    ctx.rotate(angle);

    // Wings
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(-this.radius * 2, -this.radius * (2 + wingFlap), -this.radius * 3, 0);
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(-this.radius * 2, this.radius * (2 + wingFlap), -this.radius * 3, 0);
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 4;
    ctx.stroke();

    // Body
    ctx.beginPath();
    ctx.ellipse(0, 0, this.radius * 1.2, this.radius * 0.8, 0, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.stroke();

    ctx.restore();
  }

  private drawQuadruped(ctx: CanvasRenderingContext2D, _pulse: number): void {
    const angle = Math.atan2(this.facingDirection.y, this.facingDirection.x);
    ctx.save();
    ctx.translate(this.position.x, this.position.y);
    ctx.rotate(angle);

    // Legs (simple rects)
    ctx.fillStyle = this.color;
    const legOffset = Math.sin(this.age * 8) * 5;
    ctx.fillRect(-this.radius, -this.radius - 2 + legOffset, 6, 6);
    ctx.fillRect(this.radius - 6, -this.radius - 2 - legOffset, 6, 6);
    ctx.fillRect(-this.radius, this.radius - 4 - legOffset, 6, 6);
    ctx.fillRect(this.radius - 6, this.radius - 4 + legOffset, 6, 6);

    // Body
    ctx.beginPath();
    ctx.roundRect(-this.radius * 1.2, -this.radius * 0.8, this.radius * 2.4, this.radius * 1.6, 5);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.stroke();

    ctx.restore();
  }

  private drawAmorphous(ctx: CanvasRenderingContext2D, pulse: number): void {
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const r = this.radius + Math.sin(this.age * 4 + i) * 5 + pulse;
      const x = this.position.x + Math.cos(a) * r;
      const y = this.position.y + Math.sin(a) * r;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff40';
    ctx.stroke();
  }

  private renderHealthBar(ctx: CanvasRenderingContext2D): void {
    const barWidth = 50;
    const barHeight = 6;
    const x = this.position.x - barWidth / 2;
    const y = this.position.y - this.radius - 20;

    // Background
    ctx.fillStyle = '#374151';
    ctx.fillRect(x, y, barWidth, barHeight);

    // Health
    const healthPercent = this.stats.health / this.stats.maxHealth;
    ctx.fillStyle = healthPercent > 0.5 ? '#22c55e' : healthPercent > 0.25 ? '#eab308' : '#ef4444';
    ctx.fillRect(x, y, barWidth * healthPercent, barHeight);

    // Border
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, barWidth, barHeight);
  }

  private renderElementIndicator(ctx: CanvasRenderingContext2D): void {
    const x = this.position.x;
    const y = this.position.y - this.radius - 30;

    // Element icon background
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Duration bar
    const barWidth = 40;
    const durationPercent = this.stats.elementDuration / 15;

    ctx.fillStyle = '#374151';
    ctx.fillRect(x - barWidth / 2, y + 12, barWidth, 4);

    ctx.fillStyle = this.color;
    ctx.fillRect(x - barWidth / 2, y + 12, barWidth * durationPercent, 4);
  }
}
