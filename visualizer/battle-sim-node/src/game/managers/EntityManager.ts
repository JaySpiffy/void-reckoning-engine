import type { Entity, Player} from '../entities';
import { Enemy, Projectile, Resource, Particle } from '../entities';
import { Building } from '../entities/Building';
import { GameEvent } from '../types';
import type { Vector2 , EntityType, EnemyType, ResourceType } from '../types';
import { globalEvents } from '../utils';
import { Vec2 } from '../utils/Vector2';
import { createResourceDrop } from '../entities';

export class EntityManager {
  private entities: Map<string, Entity> = new Map();
  private entitiesByType: Map<EntityType, Set<string>> = new Map();
  private player: Player | null = null;
  
  // Entity lists for quick access
  private enemies: Enemy[] = [];
  private projectiles: Projectile[] = [];
  private resources: Resource[] = [];
  private particles: Particle[] = [];
  private buildings: Building[] = [];

  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    globalEvents.on(GameEvent.ENEMY_KILLED, (data) => {
      this.spawnResourceDrops(data.position, data.enemyType);
    });
  }

  // Entity creation
  addEntity(entity: Entity): void {
    this.entities.set(entity.id, entity);
    
    // Track by type
    if (!this.entitiesByType.has(entity.type)) {
      this.entitiesByType.set(entity.type, new Set());
    }
    this.entitiesByType.get(entity.type)!.add(entity.id);
    
    // Track in specific lists
    if (entity instanceof Enemy) {
      this.enemies.push(entity);
    } else if (entity instanceof Projectile) {
      this.projectiles.push(entity);
    } else if (entity instanceof Resource) {
      this.resources.push(entity);
    } else if (entity instanceof Particle) {
      this.particles.push(entity);
    } else if (entity instanceof Building) {
      this.buildings.push(entity);
    }
    
    globalEvents.emit(GameEvent.ENTITY_CREATED, {
      entityId: entity.id,
      type: entity.type,
    });
  }

  removeEntity(entity: Entity): void {
    this.entities.delete(entity.id);
    
    // Remove from type tracking
    const typeSet = this.entitiesByType.get(entity.type);
    if (typeSet) {
      typeSet.delete(entity.id);
    }
    
    // Remove from specific lists
    if (entity instanceof Enemy) {
      const index = this.enemies.indexOf(entity);
      if (index > -1) this.enemies.splice(index, 1);
    } else if (entity instanceof Projectile) {
      const index = this.projectiles.indexOf(entity);
      if (index > -1) this.projectiles.splice(index, 1);
    } else if (entity instanceof Resource) {
      const index = this.resources.indexOf(entity);
      if (index > -1) this.resources.splice(index, 1);
    } else if (entity instanceof Particle) {
      const index = this.particles.indexOf(entity);
      if (index > -1) this.particles.splice(index, 1);
    } else if (entity instanceof Building) {
      const index = this.buildings.indexOf(entity);
      if (index > -1) this.buildings.splice(index, 1);
    }
    
    globalEvents.emit(GameEvent.ENTITY_DESTROYED, {
      entityId: entity.id,
      type: entity.type,
    });
  }

  // Player management
  setPlayer(player: Player): void {
    this.player = player;
    this.addEntity(player);
  }

  getPlayer(): Player | null {
    return this.player;
  }

  // Enemy management
  spawnEnemy(type: EnemyType, position: Vector2): Enemy {
    const enemy = new Enemy({
      position: Vec2.clone(position),
      enemyType: type,
    });
    this.addEntity(enemy);
    return enemy;
  }

  // Resource management
  spawnResource(type: ResourceType, position: Vector2, amount: number): Resource {
    const resource = new Resource({
      position: Vec2.clone(position),
      resourceType: type,
      amount,
    });
    this.addEntity(resource);
    return resource;
  }

  private spawnResourceDrops(position: Vector2, enemyType: EnemyType): void {
    const drops = createResourceDrop(position, enemyType);
    
    for (const resource of drops) {
      this.addEntity(resource);
    }
  }

  // Particle management
  spawnParticle(particle: Particle): void {
    this.addEntity(particle);
  }

  spawnParticles(particles: Particle[]): void {
    for (const particle of particles) {
      this.addEntity(particle);
    }
  }

  // Projectile management
  spawnProjectile(projectile: Projectile): void {
    this.addEntity(projectile);
  }

  // Update all entities
  update(deltaTime: number): void {
    // Update all active entities
    for (const entity of this.entities.values()) {
      if (entity.isActive) {
        entity.tick(deltaTime);
      }
    }
    
    // Clean up inactive entities
    this.cleanupInactive();
  }

  private cleanupInactive(): void {
    const toRemove: Entity[] = [];
    
    for (const entity of this.entities.values()) {
      if (!entity.isActive) {
        toRemove.push(entity);
      }
    }
    
    for (const entity of toRemove) {
      this.removeEntity(entity);
    }
  }

  // Getters
  getEntity(id: string): Entity | undefined {
    return this.entities.get(id);
  }

  getAllEntities(): Entity[] {
    return Array.from(this.entities.values());
  }

  getEntitiesByType(type: EntityType): Entity[] {
    const ids = this.entitiesByType.get(type);
    if (!ids) return [];
    
    const entities: Entity[] = [];
    for (const id of ids) {
      const entity = this.entities.get(id);
      if (entity && entity.isActive) {
        entities.push(entity);
      }
    }
    return entities;
  }

  getEnemies(): Enemy[] {
    return this.enemies.filter(e => e.isActive);
  }

  getProjectiles(): Projectile[] {
    return this.projectiles.filter(p => p.isActive);
  }

  getResources(): Resource[] {
    return this.resources.filter(r => r.isActive);
  }

  getParticles(): Particle[] {
    return this.particles.filter(p => p.isActive);
  }

  getBuildings(): Building[] {
    return this.buildings.filter(b => b.isActive);
  }

  // Query methods
  getEntitiesInRadius(center: Vector2, radius: number): Entity[] {
    const result: Entity[] = [];
    const radiusSquared = radius * radius;
    
    for (const entity of this.entities.values()) {
      if (!entity.isActive) continue;
      
      const distanceSquared = Vec2.distanceSquared(center, entity.position);
      if (distanceSquared <= radiusSquared) {
        result.push(entity);
      }
    }
    
    return result;
  }

  getNearestEnemy(position: Vector2, maxDistance: number = Infinity): Enemy | null {
    let nearest: Enemy | null = null;
    let nearestDistance = maxDistance;
    
    for (const enemy of this.enemies) {
      if (!enemy.isActive) continue;
      
      const distance = Vec2.distance(position, enemy.position);
      if (distance < nearestDistance) {
        nearest = enemy;
        nearestDistance = distance;
      }
    }
    
    return nearest;
  }

  // Clear all entities
  clear(): void {
    this.entities.clear();
    this.entitiesByType.clear();
    this.player = null;
    this.enemies = [];
    this.projectiles = [];
    this.resources = [];
    this.particles = [];
    this.buildings = [];
  }

  // Stats
  getEntityCount(): number {
    return this.entities.size;
  }

  getActiveEntityCount(): number {
    let count = 0;
    for (const entity of this.entities.values()) {
      if (entity.isActive) count++;
    }
    return count;
  }
}

export const entityManager = new EntityManager();
