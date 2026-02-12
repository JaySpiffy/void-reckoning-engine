/**
 * ABILITY SYSTEM - Fixed and Working
 *
 * All abilities 1-5 now work:
 * - Slot 1: Basic Attack (mouse click or key 1)
 * - Slot 2: Dash (key 2)
 * - Slot 3: Primary Ability (key 3)
 * - Slot 4: Secondary Ability (key 4)
 * - Slot 5: Ultimate Ability (key 5)
 */

import type { AbilityState, ElementEvolution } from '../types/abilities';
import { AbilityType, ABILITY_CONFIGS } from '../types/abilities';
import { ElementType, DamageType, GameEvent } from '../types';
import type { Player, Enemy} from '../entities';
import { Projectile, Particle } from '../entities';
import { logger, LogCategory } from '../managers/LogManager';
import { globalEvents } from '../utils';
import { Vec2 } from '../utils/Vector2';
import { combatSystem } from './CombatSystem';
import { entityManager } from '../managers/EntityManager';
import { randomRange } from '../utils';
import { configManager } from '../managers/ConfigManager';

// Projectile configuration for each element
const ELEMENT_PROJECTILE_CONFIGS: Record<ElementType, {
  speed: number;
  radius: number;
  color: string;
  glowColor: string;
  damageMultiplier: number;
  pierce: number;
  dotDamage?: number;
  dotDuration?: number;
  slowPercent?: number;
  slowDuration?: number;
  chainCount?: number;
}> = {
  [ElementType.NONE]: {
    speed: 500,
    radius: 6,
    color: '#60a5fa',
    glowColor: '#3b82f6',
    damageMultiplier: 1,
    pierce: 0,
  },
  [ElementType.FIRE]: {
    speed: 450,
    radius: 8,
    color: '#f97316',
    glowColor: '#ef4444',
    damageMultiplier: 1.5,
    pierce: 2,
    dotDamage: 5,
    dotDuration: 3,
  },
  [ElementType.ICE]: {
    speed: 550,
    radius: 7,
    color: '#60a5fa',
    glowColor: '#3b82f6',
    damageMultiplier: 0.8,
    pierce: 3,
    slowPercent: 0.5,
    slowDuration: 2,
  },
  [ElementType.LIGHTNING]: {
    speed: 700,
    radius: 5,
    color: '#facc15',
    glowColor: '#eab308',
    damageMultiplier: 1.2,
    pierce: 0,
    chainCount: 3,
  },
  [ElementType.POISON]: {
    speed: 400,
    radius: 7,
    color: '#4ade80',
    glowColor: '#22c55e',
    damageMultiplier: 0.6,
    pierce: 1,
    dotDamage: 8,
    dotDuration: 5,
  },
  [ElementType.ARCANE]: {
    speed: 600,
    radius: 9,
    color: '#c084fc',
    glowColor: '#a855f7',
    damageMultiplier: 2,
    pierce: 5,
  },
};

// Ability slots configuration for each element
function getSlotsForElement(element: ElementType, evolutionLevel: number): AbilityType[] {
  // Base slots always available
  const slots: AbilityType[] = [
    AbilityType.BASIC_ATTACK,  // Slot 1
    AbilityType.DASH,          // Slot 2
  ];

  // Element-specific abilities
  const elementAbilities: Record<ElementType, AbilityType[]> = {
    [ElementType.NONE]: [
      AbilityType.BASIC_ATTACK,
      AbilityType.BASIC_ATTACK,
      AbilityType.BASIC_ATTACK,
    ],
    [ElementType.FIRE]: [
      AbilityType.FIREBALL,
      AbilityType.FLAME_WAVE,
      AbilityType.INFERNO,
    ],
    [ElementType.ICE]: [
      AbilityType.ICE_BOLT,
      AbilityType.FROST_NOVA,
      AbilityType.BLIZZARD,
    ],
    [ElementType.LIGHTNING]: [
      AbilityType.LIGHTNING_BOLT,
      AbilityType.CHAIN_LIGHTNING,
      AbilityType.THUNDERSTORM,
    ],
    [ElementType.POISON]: [
      AbilityType.POISON_DART,
      AbilityType.VENOM_POOL,
      AbilityType.PLAGUE,
    ],
    [ElementType.ARCANE]: [
      AbilityType.ARCANE_MISSILE,
      AbilityType.MANA_BURST,
      AbilityType.BLACK_HOLE,
    ],
  };

  const abilities = elementAbilities[element] || elementAbilities[ElementType.NONE];

  // Add abilities based on evolution level
  // Evolution 0: Only basic attack in slots 3-5
  // Evolution 1: Primary ability unlocked
  // Evolution 2: Secondary ability unlocked
  // Evolution 3: Ultimate unlocked

  if (evolutionLevel >= 0) {
    slots.push(abilities[0]); // Slot 3: Primary
  }
  if (evolutionLevel >= 1) {
    slots.push(abilities[1]); // Slot 4: Secondary
  } else {
    slots.push(abilities[0]); // Repeat primary if not evolved
  }
  if (evolutionLevel >= 2) {
    slots.push(abilities[2]); // Slot 5: Ultimate
  } else {
    slots.push(abilities[0]); // Repeat primary if not evolved
  }

  return slots;
}

export class AbilitySystem {
  private abilities: Map<AbilityType, AbilityState> = new Map();
  private elementEvolutions: Map<ElementType, ElementEvolution> = new Map();
  private currentElement: ElementType = ElementType.NONE;
  private player: Player | null = null;
  private slots: AbilityType[] = getSlotsForElement(ElementType.NONE, 0);
  private dashEndTime: number = 0; // Timer for dash end instead of setTimeout
  private isInitialized: boolean = false;

  constructor() {
    this.setupEventListeners();
  }

  initialize(): void {
    if (this.isInitialized) return;
    
    this.initializeAbilities();
    this.initializeElementEvolutions();
    this.isInitialized = true;
    
    logger.info(LogCategory.SYSTEM, 'AbilitySystem initialized with config');
  }

  private initializeAbilities(): void {
    const abilityConfigValues = configManager.get('abilities');

    for (const config of Object.values(ABILITY_CONFIGS)) {
      const clonedConfig = { ...config };

      // Map TOML config to specific abilities
      // Note: This is an initial implementation, can be generalized later
      if (config.id === AbilityType.DASH) {
        clonedConfig.manaCost = abilityConfigValues.dash_cost;
        clonedConfig.cooldown = abilityConfigValues.dash_cooldown;
      } else if ([AbilityType.FROST_NOVA, AbilityType.FLAME_WAVE, AbilityType.VENOM_POOL, AbilityType.MANA_BURST].includes(config.id)) {
        clonedConfig.manaCost = abilityConfigValues.nova_cost;
        clonedConfig.cooldown = abilityConfigValues.nova_cooldown;
      } else if (config.id === AbilityType.CHAIN_LIGHTNING) {
        clonedConfig.manaCost = abilityConfigValues.chain_lightning_cost;
        clonedConfig.cooldown = abilityConfigValues.chain_lightning_cooldown;
      } else if (config.evolutionLevel === 3) {
        clonedConfig.manaCost = abilityConfigValues.ultimate_cost;
        clonedConfig.cooldown = abilityConfigValues.ultimate_cooldown;
      }

      this.abilities.set(config.id, {
        config: clonedConfig,
        currentCooldown: 0,
        isUnlocked: true,
        killCount: 0,
      });
    }
  }

  private initializeElementEvolutions(): void {
    const elements = [ElementType.NONE, ElementType.FIRE, ElementType.ICE, ElementType.LIGHTNING, ElementType.POISON, ElementType.ARCANE];

    for (const element of elements) {
      this.elementEvolutions.set(element, {
        element,
        level: 0,
        experience: 0,
        experienceToNext: 100,
        killsWithElement: 0,
        unlockedAbilities: [],
      });
    }
  }

  private setupEventListeners(): void {
    globalEvents.on(GameEvent.ENEMY_KILLED, (data) => {
      this.onEnemyKilled(data.experience);
    });
  }

  setPlayer(player: Player): void {
    this.player = player;
  }

  update(deltaTime: number): void {
    // Update cooldowns
    for (const ability of this.abilities.values()) {
      if (ability.currentCooldown > 0) {
        ability.currentCooldown -= deltaTime;
      }
    }

    // Handle dash end (replaces setTimeout race condition)
    if (this.dashEndTime > 0) {
      this.dashEndTime -= deltaTime;
      if (this.dashEndTime <= 0 && this.player) {
        this.player.velocity = { x: 0, y: 0 };
        this.player.isInvulnerable = false;
        this.dashEndTime = 0;
      }
    }
  }

  // Use an ability by slot number (1-5)
  useAbilitySlot(slotIndex: number, targetPosition?: { x: number; y: number }): boolean {
    if (slotIndex < 1 || slotIndex > 5) return false;
    const abilityType = this.slots[slotIndex - 1];
    return this.useAbility(abilityType, targetPosition);
  }

  // Use a specific ability
  useAbility(abilityType: AbilityType, targetPosition?: { x: number; y: number }): boolean {
    if (!this.isInitialized) {
      logger.warn(LogCategory.ABILITY, 'AbilitySystem used before initialization');
      return false;
    }
    const ability = this.abilities.get(abilityType);
    if (!ability) return false;
    if (!ability.isUnlocked) return false;
    if (ability.currentCooldown > 0) return false;
    if (!this.player) return false;

    const config = ability.config;

    // Check mana cost
    if (this.player.stats.mana < config.manaCost) return false;

    // Deduct mana
    this.player.stats.mana -= config.manaCost;

    // Set cooldown
    ability.currentCooldown = config.cooldown;

    // Execute ability effect
    const success = this.executeAbility(abilityType, targetPosition);

    if (success) {
      globalEvents.emit(GameEvent.ABILITY_USED, {
        abilityId: config.id,
        slot: this.slots.indexOf(abilityType) + 1,
      });
    }

    return success;
  }

  private executeAbility(abilityType: AbilityType, targetPosition?: { x: number; y: number }): boolean {
    if (!this.player) return false;

    switch (abilityType) {
      case AbilityType.BASIC_ATTACK:
        return this.executeBasicAttack(targetPosition);

      case AbilityType.DASH:
        return this.executeDash();

      case AbilityType.FIREBALL:
      case AbilityType.ICE_BOLT:
      case AbilityType.LIGHTNING_BOLT:
      case AbilityType.POISON_DART:
      case AbilityType.ARCANE_MISSILE:
        if (targetPosition) {
          this.fireProjectile(targetPosition, abilityType);
          return true;
        }
        return false;

      case AbilityType.FLAME_WAVE:
      case AbilityType.FROST_NOVA:
      case AbilityType.VENOM_POOL:
      case AbilityType.MANA_BURST:
        this.executeNova(abilityType);
        return true;

      case AbilityType.CHAIN_LIGHTNING:
        if (targetPosition) {
          this.executeChainLightning(targetPosition);
          return true;
        }
        return false;

      case AbilityType.INFERNO:
      case AbilityType.BLIZZARD:
      case AbilityType.THUNDERSTORM:
      case AbilityType.PLAGUE:
      case AbilityType.BLACK_HOLE:
        if (targetPosition) {
          this.executeUltimate(targetPosition, abilityType);
          return true;
        }
        return false;

      default:
        logger.warn(LogCategory.SYSTEM, `Unknown ability type: ${abilityType}`);
        return false;
    }
  }

  private executeBasicAttack(targetPosition?: { x: number; y: number }): boolean {
    if (!this.player) return false;

    // Use facing direction if no target position
    const target = targetPosition || Vec2.add(this.player.position, this.player.facingDirection);

    const direction = Vec2.normalize(Vec2.sub(target, this.player.position));
    const spawnPos = Vec2.add(this.player.position, Vec2.mul(direction, this.player.radius + 15));

    const config = ELEMENT_PROJECTILE_CONFIGS[this.currentElement];
    const damage = this.player.stats.damage * config.damageMultiplier;

    const projectile = new Projectile({
      position: spawnPos,
      velocity: Vec2.mul(direction, config.speed),
      radius: config.radius,
      color: config.color,
      damage,
      damageType: this.getDamageTypeForElement(this.currentElement),
      pierce: config.pierce,
      dotDamage: config.dotDamage || 0,
      dotDuration: config.dotDuration || 0,
      slowPercent: config.slowPercent || 0,
      slowDuration: config.slowDuration || 0,
      chainCount: config.chainCount || 0,
      element: this.currentElement,
      lifetime: 1.5,
    });

    projectile.glowColor = config.glowColor;
    projectile.glowRadius = config.radius * 2;

    combatSystem.getProjectiles().push(projectile);

    // Muzzle flash effect
    this.spawnMuzzleFlash(spawnPos, config.color);

    return true;
  }

  private executeDash(): boolean {
    if (!this.player) return false;

    const dashSpeed = 600;
    const dashDuration = 0.2;

    // Dash in facing direction
    this.player.velocity = Vec2.mul(this.player.facingDirection, dashSpeed);
    this.player.isInvulnerable = true;

    // Create dash trail effect
    this.createDashTrail();

    // Set timer for dash end (handled in update() instead of setTimeout)
    this.dashEndTime = dashDuration;

    return true;
  }

  private fireProjectile(targetPosition: { x: number; y: number }, abilityType: AbilityType): void {
    if (!this.player) return;

    const direction = Vec2.normalize(Vec2.sub(targetPosition, this.player.position));
    const spawnPos = Vec2.add(this.player.position, Vec2.mul(direction, this.player.radius + 15));

    const elementConfig = ELEMENT_PROJECTILE_CONFIGS[this.currentElement];
    const abilityConfig = ABILITY_CONFIGS[abilityType];

    const damage = this.player.stats.damage * abilityConfig.damage;

    const projectile = new Projectile({
      position: spawnPos,
      velocity: Vec2.mul(direction, elementConfig.speed * 1.1),
      radius: elementConfig.radius * 1.3,
      color: elementConfig.color,
      damage,
      damageType: abilityConfig.damageType,
      pierce: abilityConfig.pierceCount || elementConfig.pierce,
      dotDamage: abilityConfig.dotDamage || elementConfig.dotDamage || 0,
      dotDuration: abilityConfig.dotDuration || elementConfig.dotDuration || 0,
      slowPercent: abilityConfig.slowPercent || elementConfig.slowPercent || 0,
      slowDuration: abilityConfig.slowDuration || elementConfig.slowDuration || 0,
      chainCount: abilityConfig.chainCount || elementConfig.chainCount || 0,
      element: this.currentElement,
      lifetime: 2,
    });

    projectile.glowColor = elementConfig.glowColor;
    projectile.glowRadius = elementConfig.radius * 3;

    combatSystem.getProjectiles().push(projectile);

    // Enhanced muzzle flash
    this.spawnMuzzleFlash(spawnPos, elementConfig.color, 12);
  }

  private executeNova(abilityType: AbilityType): void {
    if (!this.player) return;

    const abilityConfig = ABILITY_CONFIGS[abilityType];
    const elementConfig = ELEMENT_PROJECTILE_CONFIGS[this.currentElement];

    const projectileCount = 12;
    const damage = this.player.stats.damage * abilityConfig.damage;

    for (let i = 0; i < projectileCount; i++) {
      const angle = (i / projectileCount) * Math.PI * 2;
      const direction = {
        x: Math.cos(angle),
        y: Math.sin(angle),
      };

      const spawnPos = Vec2.add(this.player.position, Vec2.mul(direction, this.player.radius + 10));

      const projectile = new Projectile({
        position: spawnPos,
        velocity: Vec2.mul(direction, elementConfig.speed * 0.7),
        radius: elementConfig.radius * 1.2,
        color: elementConfig.color,
        damage,
        damageType: abilityConfig.damageType,
        pierce: 999, // Nova pierces everything
        dotDamage: abilityConfig.dotDamage || elementConfig.dotDamage || 0,
        dotDuration: abilityConfig.dotDuration || elementConfig.dotDuration || 0,
        slowPercent: abilityConfig.slowPercent ? Math.min(0.8, abilityConfig.slowPercent * 1.5) : 0,
        slowDuration: abilityConfig.slowDuration ? abilityConfig.slowDuration * 1.5 : 0,
        chainCount: 0,
        element: this.currentElement,
        lifetime: 0.8,
      });

      projectile.glowColor = elementConfig.glowColor;
      projectile.glowRadius = elementConfig.radius * 3;

      combatSystem.getProjectiles().push(projectile);
    }

    // Big explosion effect
    combatSystem.spawnExplosion(this.player.position, elementConfig.color, 20);
  }

  private executeChainLightning(targetPosition: { x: number; y: number }): void {
    if (!this.player) return;

    const enemies = entityManager.getEnemies();
    if (enemies.length === 0) return;

    // Find nearest enemy to target position
    let targetEnemy: Enemy | null = null;
    let nearestDistance = Infinity;

    for (const enemy of enemies) {
      if (!enemy.isActive) continue;
      const distance = Vec2.distance(targetPosition, enemy.position);
      if (distance < nearestDistance) {
        nearestDistance = distance;
        targetEnemy = enemy;
      }
    }

    if (!targetEnemy) return;

    const damage = this.player.stats.damage * ABILITY_CONFIGS[AbilityType.CHAIN_LIGHTNING].damage;
    const chainCount = ABILITY_CONFIGS[AbilityType.CHAIN_LIGHTNING].chainCount || 5;
    const chainedEnemies = new Set<string>();

    let currentEnemy = targetEnemy;
    let remainingChains = chainCount;

    while (currentEnemy && remainingChains > 0) {
      // Apply damage
      currentEnemy.takeDamage(damage * (1 - (chainCount - remainingChains) * 0.15), DamageType.LIGHTNING);

      // Visual effect
      combatSystem.spawnExplosion(currentEnemy.position, '#facc15', 8);

      chainedEnemies.add(currentEnemy.id);
      remainingChains--;

      // Find next target
      let nextEnemy: Enemy | null = null;
      let nextDistance = Infinity;

      for (const enemy of enemies) {
        if (!enemy.isActive || chainedEnemies.has(enemy.id)) continue;
        const distance = Vec2.distance(currentEnemy.position, enemy.position);
        if (distance < nextDistance && distance < 200) {
          nextDistance = distance;
          nextEnemy = enemy;
        }
      }

      if (!nextEnemy) break;
      currentEnemy = nextEnemy;
    }
  }

  private executeUltimate(targetPosition: { x: number; y: number }, abilityType: AbilityType): void {
    if (!this.player) return;

    const abilityConfig = ABILITY_CONFIGS[abilityType];
    const elementConfig = ELEMENT_PROJECTILE_CONFIGS[this.currentElement];

    const count = abilityConfig.projectileCount || 16;
    const damage = this.player.stats.damage * abilityConfig.damage;

    // Fire projectiles in all directions from target position
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      const direction = {
        x: Math.cos(angle),
        y: Math.sin(angle),
      };

      const spawnPos = {
        x: targetPosition.x + direction.x * 30,
        y: targetPosition.y + direction.y * 30,
      };

      const projectile = new Projectile({
        position: spawnPos,
        velocity: Vec2.mul(direction, elementConfig.speed * 0.9),
        radius: elementConfig.radius * 1.5,
        color: elementConfig.color,
        damage,
        damageType: abilityConfig.damageType,
        pierce: 999,
        dotDamage: abilityConfig.dotDamage ? abilityConfig.dotDamage * 2 : 0,
        dotDuration: abilityConfig.dotDuration ? abilityConfig.dotDuration * 2 : 0,
        slowPercent: abilityConfig.slowPercent,
        slowDuration: abilityConfig.slowDuration,
        chainCount: this.currentElement === ElementType.LIGHTNING ? 3 : 0,
        element: this.currentElement,
        lifetime: 2,
      });

      projectile.glowColor = elementConfig.glowColor;
      projectile.glowRadius = elementConfig.radius * 4;

      combatSystem.getProjectiles().push(projectile);
    }

    // Massive explosion
    combatSystem.spawnExplosion(targetPosition, elementConfig.color, 40);
  }

  private createDashTrail(): void {
    if (!this.player) return;

    for (let i = 0; i < 5; i++) {
      setTimeout(() => {
        if (this.player) {
          combatSystem.spawnExplosion(this.player.position, this.player.color, 5);
        }
      }, i * 40);
    }
  }

  private spawnMuzzleFlash(position: { x: number; y: number }, color: string, count: number = 8): void {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = randomRange(50, 150);

      const particle = new Particle({
        position: { ...position },
        velocity: {
          x: Math.cos(angle) * speed,
          y: Math.sin(angle) * speed,
        },
        lifetime: randomRange(0.2, 0.4),
        radius: randomRange(2, 5),
        color,
        fadeOut: true,
        shrink: true,
      });

      combatSystem.getParticles().push(particle);
    }
  }

  private getDamageTypeForElement(element: ElementType): DamageType {
    switch (element) {
      case ElementType.FIRE: return DamageType.FIRE;
      case ElementType.ICE: return DamageType.ICE;
      case ElementType.LIGHTNING: return DamageType.LIGHTNING;
      case ElementType.POISON: return DamageType.POISON;
      case ElementType.ARCANE: return DamageType.ARCANE;
      default: return DamageType.PHYSICAL;
    }
  }

  private onEnemyKilled(experience: number): void {
    if (this.currentElement === ElementType.NONE) return;

    const evolution = this.elementEvolutions.get(this.currentElement);
    if (!evolution) return;

    evolution.experience += experience;
    evolution.killsWithElement++;

    // Check for level up
    if (evolution.experience >= evolution.experienceToNext) {
      this.levelUpElement(evolution);
    }

    // Check for ability unlocks
    this.checkAbilityUnlocks(evolution);
  }

  private levelUpElement(evolution: ElementEvolution): void {
    evolution.level++;
    evolution.experience -= evolution.experienceToNext;
    evolution.experienceToNext = Math.floor(evolution.experienceToNext * 1.5);

    globalEvents.emit(GameEvent.ELEMENT_LEVELED_UP, {
      element: evolution.element,
      level: evolution.level,
    });

    // Update slots with new abilities
    this.updateSlots();
  }

  private checkAbilityUnlocks(evolution: ElementEvolution): void {
    for (const ability of this.abilities.values()) {
      if (ability.config.element !== evolution.element) continue;
      if (ability.isUnlocked) continue;

      // Check if prerequisite is met
      if (ability.config.evolvesFrom) {
        const parentAbility = this.abilities.get(ability.config.evolvesFrom);
        if (!parentAbility?.isUnlocked) continue;
        if (parentAbility.killCount < ability.config.evolutionKillsRequired) continue;
      }

      // Unlock ability
      ability.isUnlocked = true;
      evolution.unlockedAbilities.push(ability.config.id);

      globalEvents.emit(GameEvent.ABILITY_UNLOCKED, {
        abilityId: ability.config.id,
      });
    }

    this.updateSlots();
  }

  private updateSlots(): void {
    const evolution = this.elementEvolutions.get(this.currentElement);
    const evolutionLevel = evolution?.level || 0;

    this.slots = getSlotsForElement(this.currentElement, evolutionLevel);
  }

  setElement(element: ElementType): void {
    this.currentElement = element;
    this.updateSlots();
  }

  // Getters
  getAbilityState(abilityType: AbilityType): AbilityState | undefined {
    return this.abilities.get(abilityType);
  }

  getSlotAbility(slotIndex: number): AbilityState | undefined {
    if (slotIndex < 1 || slotIndex > 5) return undefined;
    return this.abilities.get(this.slots[slotIndex - 1]);
  }

  getSlots(): AbilityType[] {
    return [...this.slots];
  }

  getElementEvolution(element: ElementType): ElementEvolution | undefined {
    return this.elementEvolutions.get(element);
  }

  getCurrentElement(): ElementType {
    return this.currentElement;
  }

  getCooldownPercent(abilityType: AbilityType): number {
    const ability = this.abilities.get(abilityType);
    if (!ability) return 0;
    if (ability.currentCooldown <= 0) return 0;
    return ability.currentCooldown / ability.config.cooldown;
  }

  isAbilityReady(abilityType: AbilityType): boolean {
    const ability = this.abilities.get(abilityType);
    if (!ability) return false;
    if (!ability.isUnlocked) return false;
    return ability.currentCooldown <= 0;
  }

  canAffordAbility(abilityType: AbilityType): boolean {
    const ability = this.abilities.get(abilityType);
    if (!ability) return false;
    if (!this.player) return false;
    return this.player.stats.mana >= ability.config.manaCost;
  }

  // Unlock all abilities (for testing)
  unlockAllAbilities(): void {
    for (const ability of this.abilities.values()) {
      ability.isUnlocked = true;
    }
  }

  // Lock all abilities except basic ones
  lockAllAbilities(): void {
    for (const ability of this.abilities.values()) {
      if (ability.config.evolutionLevel > 0) {
        ability.isUnlocked = false;
      }
    }
  }
}

export const abilitySystem = new AbilitySystem();
