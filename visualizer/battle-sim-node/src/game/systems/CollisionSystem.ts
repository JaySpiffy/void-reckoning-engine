import type { Vector2 } from '../types';
import type { Entity } from '../entities';
import { Vec2 } from '../utils/Vector2';

interface CollisionPair {
  entityA: Entity;
  entityB: Entity;
}

interface SpatialHashCell {
  entities: Set<Entity>;
}

export class CollisionSystem {
  private cellSize: number = 100;
  private spatialHash: Map<string, SpatialHashCell> = new Map();
  private entityCells: Map<string, Set<string>> = new Map();

  update(entities: Entity[]): CollisionPair[] {
    this.clearSpatialHash();
    
    // Insert entities into spatial hash
    for (const entity of entities) {
      if (!entity.isActive) continue;
      this.insertEntity(entity);
    }
    
    // Find collisions
    return this.findCollisions();
  }

  private clearSpatialHash(): void {
    this.spatialHash.clear();
    this.entityCells.clear();
  }

  private getCellsForEntity(entity: Entity): string[] {
    const bounds = entity.getBounds();
    const minCellX = Math.floor(bounds.x / this.cellSize);
    const maxCellX = Math.floor((bounds.x + bounds.width) / this.cellSize);
    const minCellY = Math.floor(bounds.y / this.cellSize);
    const maxCellY = Math.floor((bounds.y + bounds.height) / this.cellSize);

    const cells: string[] = [];
    for (let x = minCellX; x <= maxCellX; x++) {
      for (let y = minCellY; y <= maxCellY; y++) {
        cells.push(`${x},${y}`);
      }
    }
    return cells;
  }

  private insertEntity(entity: Entity): void {
    const cells = this.getCellsForEntity(entity);
    this.entityCells.set(entity.id, new Set(cells));

    for (const cellKey of cells) {
      if (!this.spatialHash.has(cellKey)) {
        this.spatialHash.set(cellKey, { entities: new Set() });
      }
      this.spatialHash.get(cellKey)!.entities.add(entity);
    }
  }

  private findCollisions(): CollisionPair[] {
    const collisions: CollisionPair[] = [];
    const checkedPairs = new Set<string>();

    for (const [entityId, cellKeys] of this.entityCells) {
      const entity = this.getEntityById(entityId);
      if (!entity) continue;

      const nearbyEntities = this.getNearbyEntities(entityId, cellKeys);

      for (const other of nearbyEntities) {
        if (entity === other) continue;
        
        const pairId = this.getPairId(entity.id, other.id);
        if (checkedPairs.has(pairId)) continue;
        checkedPairs.add(pairId);

        if (entity.intersects(other)) {
          collisions.push({ entityA: entity, entityB: other });
        }
      }
    }

    return collisions;
  }

  private getNearbyEntities(entityId: string, cellKeys: Set<string>): Entity[] {
    const nearby = new Set<Entity>();
    
    for (const cellKey of cellKeys) {
      const cell = this.spatialHash.get(cellKey);
      if (cell) {
        for (const entity of cell.entities) {
          if (entity.id !== entityId) {
            nearby.add(entity);
          }
        }
      }
    }
    
    return Array.from(nearby);
  }

  private getEntityById(id: string): Entity | null {
    // This is a bit hacky - we store entities in cells but need to retrieve by ID
    // In practice, we'd want a separate entity map
    for (const cell of this.spatialHash.values()) {
      for (const entity of cell.entities) {
        if (entity.id === id) return entity;
      }
    }
    return null;
  }

  private getPairId(id1: string, id2: string): string {
    return id1 < id2 ? `${id1}-${id2}` : `${id2}-${id1}`;
  }

  // Static collision resolution helpers
  static resolveCircleCollision(
    posA: Vector2,
    radiusA: number,
    posB: Vector2,
    radiusB: number
  ): { position: Vector2; normal: Vector2; penetration: number } | null {
    const distance = Vec2.distance(posA, posB);
    const minDistance = radiusA + radiusB;

    if (distance >= minDistance) return null;

    const normal = Vec2.normalize(Vec2.sub(posB, posA));
    const penetration = minDistance - distance;
    const position = Vec2.add(posA, Vec2.mul(normal, penetration));

    return { position, normal, penetration };
  }

  static pointInCircle(point: Vector2, center: Vector2, radius: number): boolean {
    return Vec2.distanceSquared(point, center) <= radius * radius;
  }

  static lineCircleIntersection(
    lineStart: Vector2,
    lineEnd: Vector2,
    circleCenter: Vector2,
    radius: number
  ): boolean {
    const d = Vec2.sub(lineEnd, lineStart);
    const f = Vec2.sub(lineStart, circleCenter);
    
    const a = Vec2.dot(d, d);
    const b = 2 * Vec2.dot(f, d);
    const c = Vec2.dot(f, f) - radius * radius;
    
    const discriminant = b * b - 4 * a * c;
    
    if (discriminant < 0) return false;
    
    const discriminantSqrt = Math.sqrt(discriminant);
    const t1 = (-b - discriminantSqrt) / (2 * a);
    const t2 = (-b + discriminantSqrt) / (2 * a);
    
    return (t1 >= 0 && t1 <= 1) || (t2 >= 0 && t2 <= 1);
  }
}

export const collisionSystem = new CollisionSystem();
