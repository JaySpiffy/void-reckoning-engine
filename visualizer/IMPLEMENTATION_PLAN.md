# Node Battle Simulator - Implementation Plan

> **Source Engine**: `C:\Users\Mike\Documents\DarwinsIslandReHelixedWeb`  
> **Target**: Working 50v50 battle demo in Node/TypeScript  
> **Estimated Time**: 2-3 days  
> **Output**: Web-deployable battle visualizer

---

## Overview

This plan adapts the existing **Darwin's Island** Node survival game into a **50v50 battle simulator**. We strip survival mechanics (DNA, evolution, loot, building) and add team-based combat with spectator controls.

The Node version is more mature and has better performance optimization (spatial hash), so this will be the fastest path to a working demo.

---

## Phase 1: Project Setup (20 minutes)

### 1.1 Create New Project
```bash
# Copy the Node engine to our draft folder
cp -r "/mnt/c/Users/Mike/Documents/DarwinsIslandReHelixedWeb" .
mv DarwinsIslandReHelixedWeb battle-sim-node
cd battle-sim-node
```

### 1.2 Clean Dependencies
```bash
# Install dependencies
npm install

# Verify it builds
npm run build
```

### 1.3 Clean Up Unnecessary Files
```bash
# Remove things we don't need for battle sim
rm -rf src/systems/DNASystem.ts
rm -rf src/systems/MutationSystem.ts
rm -rf src/systems/BuildingSystem.ts
rm -rf src/systems/LootSystem.ts
rm -rf src/systems/EvolutionTree.ts
```

---

## Phase 2: Type Definitions (30 minutes)

### 2.1 Create Battle Types
**File**: `src/types/battle.ts` (NEW)

```typescript
export enum Team {
    BLUE = 'BLUE',
    RED = 'RED'
}

export interface TeamConfig {
    color: string;
    name: string;
}

export const TEAM_CONFIG: Record<Team, TeamConfig> = {
    [Team.BLUE]: {
        color: '#3b82f6', // Bright blue
        name: 'Blue Team'
    },
    [Team.RED]: {
        color: '#ef4444', // Bright red
        name: 'Red Team'
    }
};

export interface BattleConfig {
    blueCount: number;
    redCount: number;
    worldWidth: number;
    worldHeight: number;
    spawnMargin: number;
}

export const DEFAULT_BATTLE_CONFIG: BattleConfig = {
    blueCount: 50,
    redCount: 50,
    worldWidth: 3000,
    worldHeight: 2000,
    spawnMargin: 200
};

export interface BattleStats {
    blueAlive: number;
    redAlive: number;
    blueKills: number;
    redKills: number;
    battleTime: number;
}

export enum BattlePhase {
    SETUP = 'SETUP',
    BATTLE = 'BATTLE',
    FINISHED = 'FINISHED'
}
```

### 2.2 Create Unit Types
**File**: `src/types/unitTypes.ts` (NEW)

```typescript
export enum UnitClass {
    GRUNT = 'GRUNT',       // Basic melee
    ARCHER = 'ARCHER',     // Ranged
    TANK = 'TANK',         // Heavy, slow, high HP
    MAGE = 'MAGE'          // AOE spells
}

export interface UnitStats {
    maxHealth: number;
    speed: number;
    damage: number;
    attackRange: number;
    attackCooldown: number;
    radius: number;
}

export const UNIT_STAT_CONFIG: Record<UnitClass, UnitStats> = {
    [UnitClass.GRUNT]: {
        maxHealth: 100,
        speed: 80,
        damage: 15,
        attackRange: 25,
        attackCooldown: 0.8,
        radius: 12
    },
    [UnitClass.ARCHER]: {
        maxHealth: 60,
        speed: 90,
        damage: 12,
        attackRange: 250,
        attackCooldown: 1.2,
        radius: 10
    },
    [UnitClass.TANK]: {
        maxHealth: 250,
        speed: 50,
        damage: 20,
        attackRange: 30,
        attackCooldown: 1.5,
        radius: 18
    },
    [UnitClass.MAGE]: {
        maxHealth: 70,
        speed: 75,
        damage: 25,
        attackRange: 180,
        attackCooldown: 2.0,
        radius: 11
    }
};

export const UNIT_COLORS: Record<UnitClass, string> = {
    [UnitClass.GRUNT]: '#666666',
    [UnitClass.ARCHER]: '#0ea5e9',
    [UnitClass.TANK]: '#64748b',
    [UnitClass.MAGE]: '#a855f7'
};
```

---

## Phase 3: Unit Entity (1 hour)

### 3.1 Create Generic Unit Entity
**File**: `src/game/entities/Unit.ts` (NEW)

```typescript
import { Entity, EntityType } from './Entity';
import { Vector2 } from '../utils/Vector2';
import { Team } from '../types/battle';
import { UnitClass, UnitStats, UNIT_STAT_CONFIG } from '../types/unitTypes';
import { TEAM_CONFIG } from '../types/battle';

export class Unit extends Entity {
    public team: Team;
    public unitClass: UnitClass;
    public health: number;
    public maxHealth: number;
    public targetId: string | null = null;
    public attackTimer: number = 0;
    public kills: number = 0;
    
    private stats: UnitStats;

    constructor(
        id: string,
        position: Vector2,
        team: Team,
        unitClass: UnitClass
    ) {
        super(id, EntityType.ENEMY); // Reuse ENEMY type for simplicity
        
        this.team = team;
        this.unitClass = unitClass;
        this.stats = UNIT_STAT_CONFIG[unitClass];
        
        this.position = position;
        this.velocity = new Vector2(0, 0);
        this.maxHealth = this.stats.maxHealth;
        this.health = this.maxHealth;
        this.radius = this.stats.radius;
        this.color = TEAM_CONFIG[team].color;
        this.isActive = true;
        this.isVisible = true;
    }

    get speed(): number {
        return this.stats.speed;
    }

    get damage(): number {
        return this.stats.damage;
    }

    get attackRange(): number {
        return this.stats.attackRange;
    }

    get attackCooldown(): number {
        return this.stats.attackCooldown;
    }

    takeDamage(amount: number): void {
        this.health -= amount;
        if (this.health <= 0) {
            this.health = 0;
            this.isActive = false;
        }
    }

    heal(amount: number): void {
        this.health = Math.min(this.health + amount, this.maxHealth);
    }

    canAttack(): boolean {
        return this.attackTimer <= 0;
    }

    resetAttackTimer(): void {
        this.attackTimer = this.attackCooldown;
    }

    update(deltaTime: number): void {
        if (!this.isActive) return;
        
        // Decrement attack cooldown
        if (this.attackTimer > 0) {
            this.attackTimer -= deltaTime;
        }
        
        // Apply velocity
        this.position = this.position.add(this.velocity.multiply(deltaTime));
        
        // Reset velocity (calculated each frame by AI)
        this.velocity = new Vector2(0, 0);
        
        // Update age
        this.age += deltaTime;
    }

    render(ctx: CanvasRenderingContext2D): void {
        if (!this.isVisible) return;

        // Draw health bar
        this.renderHealthBar(ctx);
        
        // Draw unit body
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
        
        // Draw outline
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw class indicator
        ctx.beginPath();
        ctx.arc(this.position.x, this.position.y, this.radius * 0.4, 0, Math.PI * 2);
        ctx.fillStyle = this.getClassColor();
        ctx.fill();
    }

    private renderHealthBar(ctx: CanvasRenderingContext2D): void {
        const barWidth = this.radius * 2;
        const barHeight = 4;
        const barX = this.position.x - this.radius;
        const barY = this.position.y - this.radius - 8;
        
        // Background
        ctx.fillStyle = '#333';
        ctx.fillRect(barX, barY, barWidth, barHeight);
        
        // Health
        const healthPct = this.health / this.maxHealth;
        const healthColor = healthPct > 0.6 ? '#22c55e' : healthPct > 0.3 ? '#eab308' : '#ef4444';
        ctx.fillStyle = healthColor;
        ctx.fillRect(barX, barY, barWidth * healthPct, barHeight);
    }

    private getClassColor(): string {
        switch (this.unitClass) {
            case UnitClass.GRUNT: return '#666';
            case UnitClass.ARCHER: return '#0ea5e9';
            case UnitClass.TANK: return '#64748b';
            case UnitClass.MAGE: return '#a855f7';
        }
    }
}
```

---

## Phase 4: Battle Manager (1.5 hours)

### 4.1 Create Battle Manager
**File**: `src/game/managers/BattleManager.ts` (NEW)

```typescript
import { Unit } from '../entities/Unit';
import { Vector2 } from '../utils/Vector2';
import { 
    Team, 
    BattleConfig, 
    DEFAULT_BATTLE_CONFIG, 
    BattleStats, 
    BattlePhase 
} from '../types/battle';
import { UnitClass } from '../types/unitTypes';

export class BattleManager {
    public units: Map<string, Unit> = new Map();
    public config: BattleConfig;
    public phase: BattlePhase = BattlePhase.SETUP;
    public battleTime: number = 0;
    public winner: Team | null = null;
    public blueKills: number = 0;
    public redKills: number = 0;
    
    private nextEntityId: number = 1;

    constructor(config: Partial<BattleConfig> = {}) {
        this.config = { ...DEFAULT_BATTLE_CONFIG, ...config };
        this.spawnInitialUnits();
    }

    private generateId(): string {
        return `unit_${this.nextEntityId++}`;
    }

    private spawnInitialUnits(): void {
        // Spawn Blue team on the left
        this.spawnTeam(Team.BLUE, this.config.blueCount);
        
        // Spawn Red team on the right
        this.spawnTeam(Team.RED, this.config.redCount);
    }

    private spawnTeam(team: Team, count: number): void {
        const startX = team === Team.BLUE 
            ? this.config.spawnMargin 
            : this.config.worldWidth - this.config.spawnMargin;
        
        const classes = [UnitClass.GRUNT, UnitClass.ARCHER, UnitClass.TANK, UnitClass.MAGE];
        
        for (let i = 0; i < count; i++) {
            const row = Math.floor(i / 5);
            const col = i % 5;
            
            const x = startX + (col * 30);
            const y = (this.config.worldHeight / 2) + (row * 30) - (count / 5 * 15);
            
            const unitClass = classes[i % classes.length];
            const id = this.generateId();
            
            const unit = new Unit(
                id,
                new Vector2(x, y),
                team,
                unitClass
            );
            
            this.units.set(id, unit);
        }
    }

    startBattle(): void {
        if (this.phase === BattlePhase.SETUP) {
            this.phase = BattlePhase.BATTLE;
        }
    }

    update(deltaTime: number): void {
        if (this.phase !== BattlePhase.BATTLE) return;
        
        this.battleTime += deltaTime;
        
        // Update all units
        for (const unit of this.units.values()) {
            if (unit.isActive) {
                unit.update(deltaTime);
            }
        }
        
        // Check victory conditions
        this.checkVictory();
    }

    private checkVictory(): void {
        const blueAlive = this.getAliveCount(Team.BLUE);
        const redAlive = this.getAliveCount(Team.RED);
        
        if (blueAlive === 0) {
            this.phase = BattlePhase.FINISHED;
            this.winner = Team.RED;
        } else if (redAlive === 0) {
            this.phase = BattlePhase.FINISHED;
            this.winner = Team.BLUE;
        }
    }

    getAliveCount(team: Team): number {
        let count = 0;
        for (const unit of this.units.values()) {
            if (unit.team === team && unit.isActive) {
                count++;
            }
        }
        return count;
    }

    getStats(): BattleStats {
        return {
            blueAlive: this.getAliveCount(Team.BLUE),
            redAlive: this.getAliveCount(Team.RED),
            blueKills: this.blueKills,
            redKills: this.redKills,
            battleTime: this.battleTime
        };
    }

    recordKill(killerTeam: Team): void {
        if (killerTeam === Team.BLUE) {
            this.blueKills++;
        } else {
            this.redKills++;
        }
    }

    reset(): void {
        this.units.clear();
        this.nextEntityId = 1;
        this.phase = BattlePhase.SETUP;
        this.battleTime = 0;
        this.winner = null;
        this.blueKills = 0;
        this.redKills = 0;
        this.spawnInitialUnits();
    }

    getAllActiveUnits(): Unit[] {
        return Array.from(this.units.values()).filter(u => u.isActive);
    }

    getUnit(id: string): Unit | undefined {
        return this.units.get(id);
    }
}
```

---

## Phase 5: Battle AI System (1.5 hours)

### 5.1 Create Battle AI System
**File**: `src/game/systems/BattleAISystem.ts` (NEW)

```typescript
import { Unit } from '../entities/Unit';
import { BattleManager } from '../managers/BattleManager';
import { Vector2 } from '../utils/Vector2';

export class BattleAISystem {
    private battle: BattleManager;

    constructor(battle: BattleManager) {
        this.battle = battle;
    }

    update(deltaTime: number): void {
        if (this.battle.phase !== 'BATTLE') return;

        for (const unit of this.battle.units.values()) {
            if (!unit.isActive) continue;

            this.updateUnit(unit, deltaTime);
        }
    }

    private updateUnit(unit: Unit, deltaTime: number): void {
        // Find target if none
        if (!unit.targetId || !this.isTargetValid(unit.targetId, unit)) {
            unit.targetId = this.findNearestEnemy(unit);
        }

        const target = unit.targetId ? this.battle.getUnit(unit.targetId) : null;

        if (target && target.isActive) {
            const distance = unit.position.distance(target.position);

            if (distance <= unit.attackRange && unit.canAttack()) {
                // Attack!
                this.performAttack(unit, target);
            } else if (distance > unit.attackRange * 0.8) {
                // Move toward target
                this.moveToward(unit, target.position, deltaTime);
            }
        }

        // Apply separation (collision avoidance)
        this.applySeparation(unit);
        
        // Clamp to world bounds
        this.clampToWorld(unit);
    }

    private isTargetValid(targetId: string, attacker: Unit): boolean {
        const target = this.battle.getUnit(targetId);
        return target !== undefined && target.isActive && target.team !== attacker.team;
    }

    private findNearestEnemy(unit: Unit): string | null {
        let nearestId: string | null = null;
        let nearestDist = Infinity;

        for (const other of this.battle.units.values()) {
            if (other.id === unit.id || !other.isActive || other.team === unit.team) {
                continue;
            }

            const dist = unit.position.distance(other.position);
            if (dist < nearestDist) {
                nearestDist = dist;
                nearestId = other.id;
            }
        }

        return nearestId;
    }

    private moveToward(unit: Unit, target: Vector2, deltaTime: number): void {
        const direction = target.subtract(unit.position).normalize();
        const moveDistance = unit.speed * deltaTime;
        
        unit.position = unit.position.add(direction.multiply(moveDistance));
    }

    private applySeparation(unit: Unit): void {
        const separationRadius = unit.radius * 3;
        let separateX = 0;
        let separateY = 0;
        let count = 0;

        for (const other of this.battle.units.values()) {
            if (other.id === unit.id || !other.isActive) continue;

            const dist = unit.position.distance(other.position);
            if (dist < separationRadius && dist > 0) {
                const diff = unit.position.subtract(other.position);
                const normalized = diff.normalize();
                separateX += normalized.x / dist;
                separateY += normalized.y / dist;
                count++;
            }
        }

        if (count > 0) {
            separateX /= count;
            separateY /= count;
            
            const separation = new Vector2(separateX, separateY).normalize();
            const separationForce = unit.speed * 0.5; // Half speed for separation
            
            unit.position = unit.position.add(separation.multiply(separationForce * 0.016));
        }
    }

    private clampToWorld(unit: Unit): void {
        unit.position.x = Math.max(unit.radius, 
            Math.min(this.battle.config.worldWidth - unit.radius, unit.position.x));
        unit.position.y = Math.max(unit.radius,
            Math.min(this.battle.config.worldHeight - unit.radius, unit.position.y));
    }

    private performAttack(attacker: Unit, target: Unit): void {
        target.takeDamage(attacker.damage);
        attacker.resetAttackTimer();

        if (!target.isActive) {
            // Target died!
            attacker.kills++;
            this.battle.recordKill(attacker.team);
            attacker.targetId = null;
            
            // Could add: death effects, score updates, etc.
        }
    }
}
```

---

## Phase 6: Game Loop & Rendering (2 hours)

### 6.1 Create Battle Game Manager
**File**: `src/game/managers/BattleGameManager.ts` (NEW)

```typescript
import { BattleManager } from './BattleManager';
import { BattleAISystem } from '../systems/BattleAISystem';
import { BattleStats, BattlePhase } from '../types/battle';

export class BattleGameManager {
    public battle: BattleManager;
    public ai: BattleAISystem;
    public isPaused: boolean = false;
    public timeScale: number = 1.0;

    constructor() {
        this.battle = new BattleManager();
        this.ai = new BattleAISystem(this.battle);
    }

    start(): void {
        this.battle.startBattle();
    }

    update(deltaTime: number): void {
        if (this.isPaused || this.battle.phase === BattlePhase.FINISHED) {
            return;
        }

        const scaledDelta = deltaTime * this.timeScale;
        
        // Update AI (movement and combat)
        this.ai.update(scaledDelta);
        
        // Update battle state
        this.battle.update(scaledDelta);
    }

    togglePause(): void {
        if (this.battle.phase === BattlePhase.BATTLE) {
            this.isPaused = !this.isPaused;
        }
    }

    setTimeScale(scale: number): void {
        this.timeScale = Math.max(0, Math.min(5, scale));
    }

    reset(): void {
        this.battle.reset();
        this.ai = new BattleAISystem(this.battle);
        this.isPaused = false;
        this.timeScale = 1.0;
    }

    getStats(): BattleStats {
        return this.battle.getStats();
    }
}
```

### 6.2 Create Battle Canvas Component
**File**: `src/components/BattleCanvas.tsx` (NEW)

```tsx
import { useEffect, useRef, useCallback } from 'react';
import { BattleGameManager } from '../game/managers/BattleGameManager';

interface BattleCanvasProps {
    game: BattleGameManager;
}

export function BattleCanvas({ game }: BattleCanvasProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>();
    const lastTimeRef = useRef<number>(0);

    const render = useCallback((ctx: CanvasRenderingContext2D) => {
        const canvas = ctx.canvas;
        const width = canvas.width;
        const height = canvas.height;

        // Clear
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, width, height);

        // Draw grid
        drawGrid(ctx, width, height);

        // Camera offset (center the battle)
        const cameraX = -100;
        const cameraY = -100;

        ctx.save();
        ctx.translate(cameraX, cameraY);

        // Draw all units
        for (const unit of game.battle.units.values()) {
            unit.render(ctx);
        }

        ctx.restore();

        // Draw UI overlay
        drawUI(ctx, game, width, height);
    }, [game]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Set canvas size
        canvas.width = 1200;
        canvas.height = 800;

        const gameLoop = (timestamp: number) => {
            const deltaTime = lastTimeRef.current 
                ? (timestamp - lastTimeRef.current) / 1000 
                : 0;
            lastTimeRef.current = timestamp;

            // Update game
            game.update(Math.min(deltaTime, 0.1)); // Cap delta time

            // Render
            render(ctx);

            animationRef.current = requestAnimationFrame(gameLoop);
        };

        animationRef.current = requestAnimationFrame(gameLoop);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [game, render]);

    return (
        <canvas
            ref={canvasRef}
            className="battle-canvas"
            style={{
                border: '2px solid #333',
                borderRadius: '8px',
                maxWidth: '100%',
                height: 'auto'
            }}
        />
    );
}

function drawGrid(ctx: CanvasRenderingContext2D, width: number, height: number) {
    ctx.strokeStyle = '#2a2a3e';
    ctx.lineWidth = 1;

    const gridSize = 50;

    for (let x = 0; x <= width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }

    for (let y = 0; y <= height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
}

function drawUI(
    ctx: CanvasRenderingContext2D, 
    game: BattleGameManager, 
    width: number, 
    height: number
) {
    const stats = game.getStats();

    // Stats panel background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(10, 10, 250, 120);

    // Title
    ctx.font = 'bold 16px sans-serif';
    ctx.fillStyle = '#fff';
    ctx.fillText('⚔️ BATTLE STATS', 20, 30);

    // Blue team
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(20, 40, 15, 15);
    ctx.font = '14px sans-serif';
    ctx.fillStyle = '#fff';
    ctx.fillText(`Blue: ${stats.blueAlive} alive (${stats.blueKills} kills)`, 40, 52);

    // Red team
    ctx.fillStyle = '#ef4444';
    ctx.fillRect(20, 62, 15, 15);
    ctx.fillText(`Red: ${stats.redAlive} alive (${stats.redKills} kills)`, 40, 74);

    // Time
    ctx.fillStyle = '#aaa';
    ctx.fillText(`Time: ${stats.battleTime.toFixed(1)}s`, 20, 96);
    ctx.fillText(`Speed: ${game.timeScale.toFixed(1)}x`, 20, 116);

    // Winner announcement
    if (game.battle.winner) {
        const isBlue = game.battle.winner === 'BLUE';
        const text = isBlue ? '🏆 BLUE WINS!' : '🏆 RED WINS!';
        const color = isBlue ? '#3b82f6' : '#ef4444';

        ctx.font = 'bold 48px sans-serif';
        ctx.textAlign = 'center';
        
        // Glow effect
        ctx.shadowColor = color;
        ctx.shadowBlur = 20;
        ctx.fillStyle = color;
        ctx.fillText(text, width / 2, height / 2);
        
        ctx.shadowBlur = 0;
        ctx.textAlign = 'left';
    }
}
```

### 6.3 Create Battle Page
**File**: `src/pages/BattlePage.tsx` (NEW)

```tsx
import { useState, useMemo } from 'react';
import { BattleGameManager } from '../game/managers/BattleGameManager';
import { BattleCanvas } from '../components/BattleCanvas';
import { Button } from '@/components/ui/button';

export function BattlePage() {
    const [game] = useState(() => new BattleGameManager());
    const [tick, setTick] = useState(0); // Force re-render

    // Force re-render on interval to show live stats
    useMemo(() => {
        const interval = setInterval(() => {
            setTick(t => t + 1);
        }, 100);
        return () => clearInterval(interval);
    }, []);

    const stats = game.getStats();
    const canStart = game.battle.phase === 'SETUP';
    const canPause = game.battle.phase === 'BATTLE' && !game.battle.winner;
    const isPaused = game.isPaused;

    return (
        <div className="min-h-screen bg-[#0f0f1a] flex flex-col">
            {/* Header */}
            <header className="bg-[#1a1a2e] border-b border-gray-800 p-4">
                <h1 className="text-2xl font-bold text-white">⚔️ Helix Battlegrounds</h1>
                <p className="text-gray-400 text-sm mt-1">50 vs 50 Battle Simulator</p>
            </header>

            {/* Controls */}
            <div className="bg-[#16162a] p-4 flex gap-4 items-center flex-wrap">
                <Button
                    onClick={() => {
                        game.start();
                        setTick(t => t + 1);
                    }}
                    disabled={!canStart}
                    className="bg-green-600 hover:bg-green-700 text-white"
                >
                    ▶️ Start Battle
                </Button>

                <Button
                    onClick={() => {
                        game.togglePause();
                        setTick(t => t + 1);
                    }}
                    disabled={!canPause}
                    className="bg-yellow-600 hover:bg-yellow-700 text-white"
                >
                    {isPaused ? '▶️ Resume' : '⏸️ Pause'}
                </Button>

                <Button
                    onClick={() => {
                        game.reset();
                        setTick(t => t + 1);
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                    🔄 Reset
                </Button>

                <div className="ml-auto flex items-center gap-2">
                    <span className="text-gray-400 text-sm">Speed:</span>
                    {[0.5, 1, 2, 5].map(speed => (
                        <Button
                            key={speed}
                            onClick={() => {
                                game.setTimeScale(speed);
                                setTick(t => t + 1);
                            }}
                            variant={game.timeScale === speed ? 'default' : 'outline'}
                            size="sm"
                            className={game.timeScale === speed ? 'bg-gray-600' : ''}
                        >
                            {speed}x
                        </Button>
                    ))}
                </div>
            </div>

            {/* Canvas */}
            <div className="flex-1 flex justify-center items-center p-4">
                <BattleCanvas game={game} />
            </div>

            {/* Stats Bar */}
            <div className="bg-[#1a1a2e] border-t border-gray-800 p-4">
                <div className="flex justify-around text-center">
                    <StatBox 
                        label="Blue Alive" 
                        value={stats.blueAlive} 
                        color="text-blue-500" 
                    />
                    <StatBox 
                        label="Blue Kills" 
                        value={stats.blueKills} 
                        color="text-white" 
                    />
                    <StatBox 
                        label="Time" 
                        value={`${stats.battleTime.toFixed(1)}s`} 
                        color="text-yellow-500" 
                    />
                    <StatBox 
                        label="Red Kills" 
                        value={stats.redKills} 
                        color="text-white" 
                    />
                    <StatBox 
                        label="Red Alive" 
                        value={stats.redAlive} 
                        color="text-red-500" 
                    />
                </div>
            </div>
        </div>
    );
}

interface StatBoxProps {
    label: string;
    value: string | number;
    color: string;
}

function StatBox({ label, value, color }: StatBoxProps) {
    return (
        <div>
            <div className={`text-3xl font-bold ${color}`}>{value}</div>
            <div className="text-gray-500 text-sm mt-1">{label}</div>
        </div>
    );
}
```

---

## Phase 7: Wiring Everything Together (30 minutes)

### 7.1 Update App.tsx
**File**: `src/App.tsx`

Replace content with:

```tsx
import { BattlePage } from './pages/BattlePage';

function App() {
    return <BattlePage />;
}

export default App;
```

### 7.2 Clean up unused imports
Remove any broken imports from deleted files.

---

## Phase 8: Build & Deploy (20 minutes)

### 8.1 Build
```bash
npm run build
```

### 8.2 Test locally
```bash
npm run dev
```

### 8.3 Deploy
```bash
# Vercel
vercel --prod

# Or copy dist folder to any static host
```

---

## Summary of Changes

### New Files Created:
```
src/
├── types/
│   ├── battle.ts           # Team, BattleConfig, BattleStats
│   └── unitTypes.ts        # UnitClass, UNIT_STAT_CONFIG
├── game/
│   ├── entities/
│   │   └── Unit.ts         # Generic unit entity
│   ├── managers/
│   │   ├── BattleManager.ts    # Spawns units, tracks state
│   │   └── BattleGameManager.ts # Game loop wrapper
│   └── systems/
│       └── BattleAISystem.ts    # Unit AI
└── components/
    └── BattleCanvas.tsx    # Canvas rendering

src/pages/
└── BattlePage.tsx          # Main UI
```

### Modified Files:
```
src/
├── App.tsx                 # Switch to BattlePage
└── game/
    └── entities/
        └── Entity.ts       # May need minor adjustments
```

### Lines of Code:
- **New code**: ~900 lines
- **Modified code**: ~20 lines
- **Total effort**: ~8 hours (spread over 2-3 days)

---

## Testing Checklist

- [ ] `npm run build` succeeds
- [ ] 50 blue units spawn on left side
- [ ] 50 red units spawn on right side
- [ ] "Start Battle" button works
- [ ] Units move toward enemy team
- [ ] Combat happens (health bars decrease)
- [ ] Units die when health reaches 0
- [ ] Kill counter increments
- [ ] Battle ends when one team eliminated
- [ ] Winner displayed on screen
- [ ] Pause/Resume works during battle
- [ ] Time scale affects simulation speed
- [ ] Reset starts new battle
- [ ] 60 FPS maintained

---

*Ready to implement!* 🎮
