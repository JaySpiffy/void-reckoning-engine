import { GamePhase, EntityType } from '../types';
import { GameEvent } from '../types/events';
import type { GameState, PlayerStats, Resources, Vector2, DNAType } from '../types';
import { Player, Resource, ElementalPickup, createLevelUpEffect, createRandomElementalPickup, damageNumberManager } from '../entities';
import type { Enemy } from '../entities';
import type { EntityManager} from './EntityManager';
import { entityManager } from './EntityManager';
import type { InputSystem} from '../systems/InputSystem';
import { inputSystem } from '../systems/InputSystem';
import type { CombatSystem} from '../systems/CombatSystem';
import { combatSystem } from '../systems/CombatSystem';
import type { WaveSystem} from '../systems/WaveSystem';
import { waveSystem } from '../systems/WaveSystem';
import type { AbilitySystem} from '../systems/AbilitySystem';
import { abilitySystem } from '../systems/AbilitySystem';
import type { AutoplaySystem} from '../systems/AutoplaySystem';
import { autoplaySystem } from '../systems/AutoplaySystem';
import { npcSystem } from '../systems/NPCSystem';
import { dnaSystem } from '../systems/DNASystem';
import { lootSystem } from '../systems/LootSystem';
import type { LootItem } from '../systems/LootSystem';
import { collisionSystem } from '../systems/CollisionSystem';
import { logger, LogCategory } from './LogManager';
import { CollisionSystem } from '../systems/CollisionSystem';
import { globalEvents } from '../utils';
import { configManager } from './ConfigManager';
import { clamp } from '../utils';

export interface GameConfig {
  canvas: HTMLCanvasElement;
  worldWidth?: number;
  worldHeight?: number;
}

export class GameManager {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;

  // Game state
  private phase: GamePhase = GamePhase.MENU;
  private state: GameState = {
    phase: GamePhase.MENU,
    wave: 0,
    score: 0,
    gameTime: 0,
  };

  // Resources
  private resources: Resources = {
    wood: 0,
    stone: 0,
    gold: 0,
    mana: 0,
  };

  // Systems
  private entityManager: EntityManager;
  private inputSystem: InputSystem;
  private combatSystem: CombatSystem;
  private waveSystem: WaveSystem;
  private abilitySystem: AbilitySystem;
  private autoplaySystem: AutoplaySystem;

  // World
  private worldWidth: number;
  private worldHeight: number;

  // Camera
  private camera: Vector2 = { x: 0, y: 0 };

  // Timing
  private lastTime: number = 0;
  private deltaTime: number = 0;
  private animationFrameId: number = 0;

  // Callbacks
  private onStateChange?: (state: GameState) => void;
  private onResourcesChange?: (resources: Resources) => void;
  private onPlayerStatsChange?: (stats: PlayerStats) => void;

  constructor(config: GameConfig) {
    this.canvas = config.canvas;
    this.ctx = config.canvas.getContext('2d')!;

    const worldConfig = configManager.get('world');
    this.worldWidth = config.worldWidth ?? worldConfig.width;
    this.worldHeight = config.worldHeight ?? worldConfig.height;

    // Initialize systems
    this.entityManager = entityManager;
    this.inputSystem = inputSystem;
    this.combatSystem = combatSystem;
    this.waveSystem = waveSystem;
    this.abilitySystem = abilitySystem;
    this.autoplaySystem = autoplaySystem;

    this.abilitySystem.initialize();
    this.setupEventListeners();
    this.inputSystem.initialize(this.canvas);
    this.waveSystem.initialize(this.worldWidth, this.worldHeight);
  }

  private setupEventListeners(): void {
    // Resource collection
    globalEvents.on(GameEvent.RESOURCE_COLLECTED, (data) => {
      this.resources[data.type] += data.amount;
      this.notifyResourcesChange();
    });

    // Element change
    globalEvents.on(GameEvent.ELEMENT_CHANGED, (data) => {
      const player = this.getPlayer();
      if (player) {
        player.setElement(data.element, data.duration);
        this.abilitySystem.setElement(data.element);
        this.notifyPlayerStatsChange();
      }
    });

    // Enemy killed
    globalEvents.on(GameEvent.ENEMY_KILLED, (data) => {
      this.state.score += data.experience;
      const player = this.getPlayer();
      if (player) {
        player.gainExperience(data.experience);
        
        // ABSORB DNA - The core mechanic
        const npcState = npcSystem.getNPCState(data.enemyId);
        const dnaType = npcState?.archetype?.dnaType || dnaSystem.getDominantType();
        dnaSystem.absorbDNA(dnaType, data.experience / 2, 'kill');
        
        // Generate Loot
        const drop = lootSystem.generateLoot(data.enemyType, dnaSystem.getDominantType());
        
        // Emit loot drop event for notifications
        if (drop.items.length > 0 && drop.items[0]) {
          globalEvents.emit(GameEvent.LOOT_ACQUIRED, { item: drop.items[0] });
        }
        
        if (drop.items.length > 0) {
          for (const item of drop.items) {
             // For now, auto-add to inventory or spawn pickup
             lootSystem.addToInventory(item);
          }
        }
      }
      this.notifyPlayerStatsChange();
      this.notifyStateChange();

      // Chance to spawn elemental pickup
      if (Math.random() < 0.2) {
        this.spawnElementalPickup(data.position);
      }
    });

    // Level up
    globalEvents.on(GameEvent.LEVEL_UP, () => {
      const player = this.getPlayer();
      if (player) {
        const particles = createLevelUpEffect(player.position);
        this.entityManager.spawnParticles(particles);
      }
      this.notifyPlayerStatsChange();
    });

    // Wave completed
    globalEvents.on(GameEvent.WAVE_COMPLETED, () => {
      setTimeout(() => {
        if (this.phase === GamePhase.PLAYING) {
          this.waveSystem.startWave(this.state.wave + 1);
          this.state.wave++;
          this.notifyStateChange();
        }
      }, 3000);
    });

    // Game over
    globalEvents.on(GameEvent.GAME_OVER, () => {
      this.gameOver();
    });

    // Item usage
    globalEvents.on(GameEvent.ITEM_USED, (data) => {
      const player = this.getPlayer();
      if (!player) return;

      const item = data.item as LootItem;
      if (item.effects.healthRestore) {
        player.heal(item.effects.healthRestore);
      }
      if (item.effects.manaRestore) {
        player.restoreMana(item.effects.manaRestore);
      }
      if (item.effects.dnaBonus) {
        for (const [dnaType, amount] of Object.entries(item.effects.dnaBonus)) {
          dnaSystem.absorbDNA(dnaType as DNAType, amount as number, 'loot');
        }
      }
      if (item.effects.statBoost) {
        // Apply temporary or permanent stat boosts
        if (item.effects.statBoost.speed) {
          player.stats.speed += item.effects.statBoost.speed as number;
        }
      }
      
      this.notifyPlayerStatsChange();
      this.notifyResourcesChange();
    });
  }

  private spawnElementalPickup(position: Vector2): void {
    const pickup = createRandomElementalPickup(position);
    this.entityManager.addEntity(pickup);
  }

  // Game lifecycle
  start(): void {
    if (this.phase !== GamePhase.MENU && this.phase !== GamePhase.GAME_OVER) return;

    this.reset();
    this.phase = GamePhase.PLAYING;
    this.state.phase = GamePhase.PLAYING;
    this.state.wave = 1;

    // Create player
    const player = new Player({
      position: {
        x: this.worldWidth / 2,
        y: this.worldHeight / 2,
      },
      name: 'Hero',
    });
    this.entityManager.setPlayer(player);
    this.abilitySystem.setPlayer(player);

    // Unlock all abilities for testing
    this.abilitySystem.unlockAllAbilities();

    // Start first wave
    this.waveSystem.startWave(1);

    // Enable Autoplay by default for demonstration
    this.autoplaySystem.enable();

    // Start game loop
    this.lastTime = performance.now();
    this.gameLoop();

    this.notifyStateChange();
    this.notifyPlayerStatsChange();
    this.notifyResourcesChange();
  }

  pause(): void {
    if (this.phase === GamePhase.PLAYING) {
      this.phase = GamePhase.PAUSED;
      this.state.phase = GamePhase.PAUSED;
      this.notifyStateChange();
    }
  }

  resume(): void {
    if (this.phase === GamePhase.PAUSED) {
      this.phase = GamePhase.PLAYING;
      this.state.phase = GamePhase.PLAYING;
      this.lastTime = performance.now();
      this.gameLoop();
      this.notifyStateChange();
    }
  }

  gameOver(): void {
    this.phase = GamePhase.GAME_OVER;
    this.state.phase = GamePhase.GAME_OVER;
    cancelAnimationFrame(this.animationFrameId);
    this.notifyStateChange();
  }

  reset(): void {
    this.phase = GamePhase.MENU;
    this.state = {
      phase: GamePhase.MENU,
      wave: 0,
      score: 0,
      gameTime: 0,
    };
    this.resources = {
      wood: 0,
      stone: 0,
      gold: 0,
      mana: 0,
    };
    this.camera = { x: 0, y: 0 };
    this.entityManager.clear();
    this.combatSystem.clear();
    this.waveSystem.clear();
    npcSystem.clear();
    damageNumberManager.clear();
    // Reset DNA system evolution tracking
    dnaSystem.resetOfferedEvolutions();
    // Reset ability system
    // abilitySystem is singleton, would need reset method
  }

  // Main game loop
  private gameLoop = (): void => {
    if (this.phase !== GamePhase.PLAYING) return;

    const currentTime = performance.now();
    this.deltaTime = Math.min((currentTime - this.lastTime) / 1000, 0.1);
    this.lastTime = currentTime;

    this.update(this.deltaTime);
    this.render();

    this.animationFrameId = requestAnimationFrame(this.gameLoop);
  };

  private update(deltaTime: number): void {
    this.state.gameTime += deltaTime;

    // Update input
    this.inputSystem.update();

    // Check for pause key
    if (this.inputSystem.isKeyJustPressed('escape') || this.inputSystem.isKeyJustPressed('p')) {
      this.pause();
      return;
    }

    // Toggle autoplay with F9
    if (this.inputSystem.isKeyJustPressed('f9')) {
      this.autoplaySystem.toggle();
    }

    // Get player
    const player = this.getPlayer();
    if (!player || !player.isAlive()) return;

    // Update autoplay AI
    const enemies = this.entityManager.getEnemies();
    this.autoplaySystem.update(deltaTime, player, enemies, {
      width: this.worldWidth,
      height: this.worldHeight,
    });

    // Update ability system
    this.abilitySystem.update(deltaTime);

    // Handle player input (or autoplay)
    this.handlePlayerInput(player);

    // Update wave system
    const newEnemies = this.waveSystem.update(deltaTime, player.position);
    for (const enemy of newEnemies) {
      this.entityManager.addEntity(enemy);
    }

    // Update entities
    this.entityManager.update(deltaTime);

    // Update combat (reuse enemies from autoplay update)
    this.combatSystem.update(deltaTime, player, enemies);

    // Update damage numbers
    damageNumberManager.update(deltaTime);

    // Update NPC AI via NPCSystem
    npcSystem.update(deltaTime, player.position);

    // Check collisions via CollisionSystem
    this.checkCollisions(player);

    // Update camera
    this.updateCamera(player.position);

    // Notify stat changes
    if (Math.floor(this.state.gameTime * 10) % 10 === 0) {
      this.notifyPlayerStatsChange();
    }
  }

  private handlePlayerInput(player: Player): void {
    // Check if autoplay is controlling
    if (this.autoplaySystem.isEnabled()) {
      // Use autoplay movement
      const autoMove = this.autoplaySystem.getMovementVector();
      player.setMovement(autoMove);

      // Use autoplay targeting
      const autoTarget = this.autoplaySystem.getTargetPosition();
      this.lastMousePosition = this.worldToScreen(autoTarget);

      // Autoplay attacks
      if (this.autoplaySystem.shouldAttack()) {
        this.abilitySystem.useAbilitySlot(1, autoTarget);
      }

      // Autoplay ability usage
      const abilitySlot = this.autoplaySystem.getAbilitySlotToUse();
      if (abilitySlot > 0) {
        this.abilitySystem.useAbilitySlot(abilitySlot, autoTarget);
      }

      return;
    }

    // Manual input below
    const moveInput = this.inputSystem.getMovementVector();

    // DEBUG: Always log once per second


    player.setMovement(moveInput);

    // Track mouse position for ability targeting
    const mousePos = this.inputSystem.getMousePosition();
    this.lastMousePosition = { ...mousePos };
    const worldPos = this.screenToWorld(mousePos);

    // Mouse attack (basic attack) - SHMUP style continuous fire
    if (this.inputSystem.isMouseDown() || this.inputSystem.isMouseJustPressed()) {
      // Trigger ability slot 1
      const success = this.abilitySystem.useAbilitySlot(1, worldPos);
      logger.debug(LogCategory.ABILITY, `Slot 1 (Mouse): ${success ? 'FIRED' : 'FAILED'}`);
    }

    // Ability keybinds 2-5 using keybinding system
    const keyBindings = [
      { slot: 2, keys: ['2', 'space'] },
      { slot: 3, keys: ['3', 'q'] },
      { slot: 4, keys: ['4', 'e'] },
      { slot: 5, keys: ['5', 'r'] },
    ];

    for (const binding of keyBindings) {
      for (const key of binding.keys) {
        if (this.inputSystem.isKeyJustPressed(key)) {
          const success = this.abilitySystem.useAbilitySlot(binding.slot, worldPos);
          logger.debug(LogCategory.ABILITY, `Slot ${binding.slot} (Key: ${key}): ${success ? 'FIRED' : 'FAILED'}`);
          break; // Only trigger once per slot per frame
        }
      }
    }
  }

  private checkCollisions(player: Player): void {
    // Use CollisionSystem for all entities
    const allEntities = this.entityManager.getAllEntities();
    const collisions = collisionSystem.update(allEntities);

    for (const collision of collisions) {
      const { entityA, entityB } = collision;

      // Handle Player vs Resource/Pickup (Legacy logic)
      if (entityA.type === EntityType.PLAYER || entityB.type === EntityType.PLAYER) {
        const other = entityA.type === EntityType.PLAYER ? entityB : entityA;
        
        if (other instanceof Resource) {
           other.collect();
        } else if (other instanceof ElementalPickup) {
           other.collect();
        }
      }

      // Basic Resolution for Enemies (Stop stacking with velocity dampening)
      if (entityA.type === EntityType.ENEMY && entityB.type === EntityType.ENEMY) {
        const enemyA = entityA as Enemy;
        const enemyB = entityB as Enemy;
        
        const res = CollisionSystem.resolveCircleCollision(
          enemyA.position, enemyA.radius,
          enemyB.position, enemyB.radius
        );
        
        if (res) {
          // Push them apart positionally with extra buffer to prevent immediate re-collision
          const separationBuffer = 2; // Extra pixels of separation
          const pushDistance = res.penetration * 0.5 + separationBuffer;
          
          enemyA.position.x -= res.normal.x * pushDistance;
          enemyA.position.y -= res.normal.y * pushDistance;
          enemyB.position.x += res.normal.x * pushDistance;
          enemyB.position.y += res.normal.y * pushDistance;
          
          // Dampen velocity toward each other to prevent vibration
          // Project velocity onto collision normal and reduce the component pushing them together
          const relativeVel = {
            x: enemyA.velocity.x - enemyB.velocity.x,
            y: enemyA.velocity.y - enemyB.velocity.y
          };
          const velAlongNormal = relativeVel.x * res.normal.x + relativeVel.y * res.normal.y;
          
          // Only dampen if moving toward each other
          if (velAlongNormal < 0) {
            const damping = 0.5; // Reduce velocity component by 50%
            const impulse = velAlongNormal * damping;
            
            enemyA.velocity.x -= impulse * res.normal.x;
            enemyA.velocity.y -= impulse * res.normal.y;
            enemyB.velocity.x += impulse * res.normal.x;
            enemyB.velocity.y += impulse * res.normal.y;
          }
        }
      }
    }

    // Magnetic attraction for close resources/pickups
    const resources = this.entityManager.getResources();
    for (const resource of resources) {
      if (player.distanceTo(resource) < 100 && resource.isActive) {
        resource.attractTo(player.position);
      }
    }

    const pickups = this.entityManager.getEntitiesByType(EntityType.ELEMENTAL_PICKUP) as ElementalPickup[];
    for (const pickup of pickups) {
       if (player.distanceTo(pickup) < 120 && pickup.isActive) {
        pickup.attractTo(player.position);
      }
    }
  }

  private updateCamera(targetPosition: Vector2): void {
    const targetX = targetPosition.x - this.canvas.width / 2;
    const targetY = targetPosition.y - this.canvas.height / 2;

    const maxX = this.worldWidth - this.canvas.width;
    const maxY = this.worldHeight - this.canvas.height;

    this.camera.x = clamp(targetX, 0, Math.max(0, maxX));
    this.camera.y = clamp(targetY, 0, Math.max(0, maxY));
  }

  private render(): void {
    this.ctx.fillStyle = '#1a1a2e';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    this.ctx.save();
    this.ctx.translate(-this.camera.x, -this.camera.y);

    this.renderWorldBackground();

    const entities = this.entityManager.getAllEntities()
      .filter(e => e.isActive && e.isVisible)
      .sort((a, b) => a.zIndex - b.zIndex);

    for (const entity of entities) {
      entity.render(this.ctx);
    }

    for (const projectile of this.combatSystem.getProjectiles()) {
      projectile.render(this.ctx);
    }

    for (const particle of this.combatSystem.getParticles()) {
      particle.render(this.ctx);
    }

    // Render damage numbers (in world space)
    damageNumberManager.render(this.ctx);

    this.ctx.restore();
  }

  private renderWorldBackground(): void {
    const gridSize = 100;
    const startX = Math.floor(this.camera.x / gridSize) * gridSize;
    const startY = Math.floor(this.camera.y / gridSize) * gridSize;
    const endX = startX + this.canvas.width + gridSize;
    const endY = startY + this.canvas.height + gridSize;

    this.ctx.strokeStyle = '#2d2d44';
    this.ctx.lineWidth = 1;

    for (let x = startX; x < endX; x += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.worldHeight);
      this.ctx.stroke();
    }

    for (let y = startY; y < endY; y += gridSize) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.worldWidth, y);
      this.ctx.stroke();
    }

    this.ctx.strokeStyle = '#ef4444';
    this.ctx.lineWidth = 4;
    this.ctx.strokeRect(0, 0, this.worldWidth, this.worldHeight);
  }

  // Track last mouse position for ability targeting
  private lastMousePosition: Vector2 = { x: 0, y: 0 };

  getLastMousePosition(): Vector2 {
    return { ...this.lastMousePosition };
  }

  screenToWorld(screenPos: Vector2): Vector2 {
    return {
      x: screenPos.x + this.camera.x,
      y: screenPos.y + this.camera.y,
    };
  }

  worldToScreen(worldPos: Vector2): Vector2 {
    return {
      x: worldPos.x - this.camera.x,
      y: worldPos.y - this.camera.y,
    };
  }

  private notifyStateChange(): void {
    if (this.onStateChange) {
      this.onStateChange({ ...this.state });
    }
  }

  private notifyResourcesChange(): void {
    if (this.onResourcesChange) {
      this.onResourcesChange({ ...this.resources });
    }
  }

  private notifyPlayerStatsChange(): void {
    if (this.onPlayerStatsChange) {
      const player = this.getPlayer();
      if (player) {
        const evolution = this.abilitySystem.getElementEvolution(player.stats.element);
        const stats: PlayerStats = {
          ...player.stats,
          elementLevel: evolution?.level || 0,
          elementExperience: evolution?.experience || 0,
        };
        this.onPlayerStatsChange(stats);
      }
    }
  }

  onGameStateChange(callback: (state: GameState) => void): void {
    this.onStateChange = callback;
  }

  onResourcesUpdate(callback: (resources: Resources) => void): void {
    this.onResourcesChange = callback;
  }

  onPlayerStatsUpdate(callback: (stats: PlayerStats) => void): void {
    this.onPlayerStatsChange = callback;
  }

  getPlayer(): Player | null {
    return this.entityManager.getPlayer();
  }

  getState(): GameState {
    return { ...this.state };
  }

  getResources(): Resources {
    return { ...this.resources };
  }

  getPhase(): GamePhase {
    return this.phase;
  }

  destroy(): void {
    cancelAnimationFrame(this.animationFrameId);
    this.inputSystem.cleanup();
    this.entityManager.clear();
  }
}
