/**
 * Battle Manager with Interceptors and Wide Formations
 */

import { Unit } from '../entities/Unit';
import { BattleProjectile, HitEffect } from '../entities/BattleProjectile';
import { Interceptor } from '../entities/Interceptor';
import { Vec2 } from '../utils/Vector2';
import { Team, DEFAULT_BATTLE_CONFIG, BattlePhase } from '../types/battle';
import type { BattleConfig, BattleStats } from '../types/battle';
import { VOID_UNIT_CLASSES } from '../data/VoidEngineData';
import { SIMULATION_CONFIG } from '../data/SimulationConfig';
import { BattleAISystem } from '../systems/BattleAISystem';

export class BattleManager {
    public units: Map<string, Unit> = new Map();
    public projectiles: BattleProjectile[] = [];
    public interceptors: Interceptor[] = [];
    public hitEffects: HitEffect[] = [];
    public config: BattleConfig;
    public phase: BattlePhase = BattlePhase.SETUP;
    public battleTime: number = 0;
    public winner: Team | null = null;
    public blueKills: number = 0;
    public redKills: number = 0;
    
    private nextEntityId: number = 1;
    private unitCounters: Map<Team, number> = new Map();
    private interceptorSpawnTimer: Map<string, number> = new Map();
    private aiSystem: BattleAISystem;

    constructor(config: Partial<BattleConfig> = {}) {
        this.config = { ...DEFAULT_BATTLE_CONFIG, ...config };
        this.unitCounters.set(Team.BLUE, 1);
        this.unitCounters.set(Team.RED, 1);
        this.aiSystem = new BattleAISystem(this);
        this.spawnInitialUnits();
    }

    private generateId(): string {
        return `unit_${this.nextEntityId++}`;
    }

    private getNextUnitNumber(team: Team): number {
        const current = this.unitCounters.get(team) || 1;
        this.unitCounters.set(team, current + 1);
        return current;
    }

    private spawnInitialUnits(): void {
        const availableClasses = VOID_UNIT_CLASSES.filter(
            c => SIMULATION_CONFIG.availableUnitClasses.includes(c.id)
        );
        
        if (availableClasses.length === 0) {
            availableClasses.push(VOID_UNIT_CLASSES[0], VOID_UNIT_CLASSES[1]);
        }

        this.spawnTeamFormation(Team.BLUE, SIMULATION_CONFIG.teamSize, availableClasses);
        this.spawnTeamFormation(Team.RED, SIMULATION_CONFIG.teamSize, availableClasses);
    }

    private spawnTeamFormation(team: Team, count: number, unitClasses: typeof VOID_UNIT_CLASSES): void {
        const isBlue = team === Team.BLUE;
        
        // MUCH wider spacing
        const spacing = 80; 
        const rows = Math.max(3, Math.ceil(Math.sqrt(count * 0.6)));
        const cols = Math.ceil(count / rows);
        
        const formationWidth = cols * spacing;
        const formationHeight = rows * spacing;
        
        // Start further apart
        const startX = isBlue 
            ? SIMULATION_CONFIG.spawnMargin + 300
            : SIMULATION_CONFIG.worldWidth - SIMULATION_CONFIG.spawnMargin - formationWidth - 300;
        
        const startY = (SIMULATION_CONFIG.worldHeight - formationHeight) / 2;
        
        // Sort by tier - stronger units in back
        const sortedClasses = [...unitClasses].sort((a, b) => 
            (b.stats.hp * b.stats.weapon_strength) - (a.stats.hp * a.stats.weapon_strength)
        );
        
        for (let i = 0; i < count; i++) {
            const row = Math.floor(i / cols);
            const col = i % cols;
            
            // Wide spacing with slight randomization
            const x = startX + col * spacing + (Math.random() * 20 - 10);
            const y = startY + row * spacing + (Math.random() * 20 - 10);
            
            // Assign unit type - mix in formation
            const tierIndex = Math.min(Math.floor(i / (count / sortedClasses.length)), sortedClasses.length - 1);
            const unitClass = sortedClasses[tierIndex] || sortedClasses[0];
            
            const id = this.generateId();
            
            const unit = new Unit({
                id,
                position: Vec2.create(
                    Math.max(50, Math.min(SIMULATION_CONFIG.worldWidth - 50, x)),
                    Math.max(50, Math.min(SIMULATION_CONFIG.worldHeight - 50, y))
                ),
                team,
                voidClass: unitClass
            });
            
            // INCREASE RANGES significantly
            if (unit.isRanged) {
                unit.attackRange *= 3; // 3x range for ranged
            } else {
                unit.attackRange *= 1.5; // 1.5x for melee
            }
            
            unit.unitNumber = this.getNextUnitNumber(team);
            this.units.set(id, unit);
            
            // Initialize interceptor spawn timer for carrier-type units
            if (unitClass.attributes.includes('massive') || unitClass.stats.ranged_attack > 200) {
                this.interceptorSpawnTimer.set(id, 0);
            }
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
        
        // Update AI (handles targeting, movement, attacks)
        this.aiSystem.update(deltaTime);
        
        // Update units (animations, cooldowns)
        for (const unit of this.units.values()) {
            if (unit.isActive) {
                unit.update(deltaTime);
            }
        }
        
        // Update interceptors
        this.updateInterceptors(deltaTime);
        
        // Spawn new interceptors from carriers
        this.spawnInterceptors(deltaTime);
        
        // Update projectiles
        this.updateProjectiles(deltaTime);
        
        // Update hit effects
        for (const effect of this.hitEffects) {
            effect.update(deltaTime);
        }
        this.hitEffects = this.hitEffects.filter(e => e.isActive);
        
        this.checkVictory();
    }

    private updateInterceptors(deltaTime: number): void {
        const allUnits = Array.from(this.units.values());
        
        for (const interceptor of this.interceptors) {
            if (!interceptor.isActive) continue;
            
            const parent = this.units.get(interceptor.parentId);
            interceptor.customUpdate(deltaTime, parent || null, allUnits);
        }
        
        this.interceptors = this.interceptors.filter(i => i.isActive);
    }

    private spawnInterceptors(deltaTime: number): void {
        for (const [unitId, timer] of this.interceptorSpawnTimer.entries()) {
            const unit = this.units.get(unitId);
            if (!unit || !unit.isActive) {
                this.interceptorSpawnTimer.delete(unitId);
                continue;
            }
            
            const newTimer = timer + deltaTime;
            
            // Spawn interceptor every 2 seconds from carrier units
            if (newTimer >= 2.0) {
                this.spawnInterceptor(unit);
                this.interceptorSpawnTimer.set(unitId, 0);
            } else {
                this.interceptorSpawnTimer.set(unitId, newTimer);
            }
        }
    }

    private spawnInterceptor(parent: Unit): void {
        const interceptor = new Interceptor({
            position: Vec2.add(parent.position, Vec2.create(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40
            )),
            parentId: parent.id,
            team: parent.team,
            color: parent.color
        });
        
        this.interceptors.push(interceptor);
    }

    private updateProjectiles(deltaTime: number): void {
        for (const projectile of this.projectiles) {
            if (!projectile.isActive) continue;
            
            projectile.update(deltaTime);
            
            for (const unit of this.units.values()) {
                if (!unit.isActive) continue;
                if (unit.id === projectile.sourceId) continue;
                
                const sourceUnit = this.units.get(projectile.sourceId);
                if (sourceUnit && unit.team === sourceUnit.team) continue;
                
                if (projectile.checkCollision(unit.position, unit.radius)) {
                    this.handleProjectileHit(projectile, unit);
                    break;
                }
            }
        }
        
        this.projectiles = this.projectiles.filter(p => p.isActive);
    }

    private handleProjectileHit(projectile: BattleProjectile, target: Unit): void {
        const prevHealth = target.health;
        const source = this.units.get(projectile.sourceId);
        // Pass armor piercing from source unit (if source exists)
        const armorPiercing = source?.armorPiercing ?? 0;
        target.takeDamage(projectile.damage, 'PHYSICAL' as any, projectile.sourceId, armorPiercing);
        const actualDamage = prevHealth - Math.max(0, target.health);
        
        const hitColor = projectile.projectileType === 'laser' ? '#22d3ee' : 
                        projectile.projectileType === 'missile' ? '#f97316' : '#ffffff';
        this.hitEffects.push(new HitEffect(target.position, hitColor, 15));
        
        if (source) {
            source.damageDealt += actualDamage;
        }
        
        if (!target.isActive) {
            if (source) {
                source.kills++;
                source.morale = Math.min(source.maxMorale, source.morale + 15);
            }
            this.recordKill(source?.team || Team.BLUE);
        }
    }

    spawnProjectile(config: {
        source: Unit;
        target: Unit;
        damage: number;
    }): void {
        const source = config.source;
        const target = config.target;
        
        let projType: 'laser' | 'bullet' | 'missile' | 'plasma' = 'bullet';
        let color = '#ffffff';
        let speed = 500;
        
        if (source.voidClass.attributes.includes('massive')) {
            projType = 'missile';
            color = '#f97316';
            speed = 300;
        } else if (source.voidClass.attributes.includes('advanced')) {
            projType = 'laser';
            color = '#22d3ee';
            speed = 900;
        } else if (source.voidClass.stats.ranged_attack > 200) {
            projType = 'plasma';
            color = '#a855f7';
            speed = 400;
        } else if (source.isRanged) {
            projType = 'bullet';
            color = '#fbbf24';
            speed = 700;
        }

        const distance = Vec2.distance(source.position, target.position);
        const timeToHit = distance / speed;
        const predictedPos = Vec2.add(
            target.position,
            Vec2.mul(target.velocity, timeToHit)
        );
        
        const finalDirection = Vec2.normalize(Vec2.sub(predictedPos, source.position));
        
        const projectile = new BattleProjectile({
            position: Vec2.add(source.position, Vec2.mul(finalDirection, source.radius + 5)),
            velocity: Vec2.mul(finalDirection, speed),
            damage: config.damage,
            sourceId: source.id,
            targetId: target.id,
            color,
            type: projType,
            lifetime: 4.0
        });
        
        this.projectiles.push(projectile);
    }

    spawnMeleeEffect(source: Unit, target: Unit, damage: number): void {
        const hitPos = Vec2.add(
            source.position,
            Vec2.mul(Vec2.normalize(Vec2.sub(target.position, source.position)), source.radius + 10)
        );
        
        this.hitEffects.push(new HitEffect(hitPos, '#ef4444', 12));
        
        const prevHealth = target.health;
        // Pass source's armor piercing to penetrate target armor
        target.takeDamage(damage, 'PHYSICAL' as any, source.id, source.armorPiercing);
        const actualDamage = prevHealth - Math.max(0, target.health);
        
        source.damageDealt += actualDamage;
        
        if (!target.isActive) {
            source.kills++;
            source.morale = Math.min(source.maxMorale, source.morale + 15);
            this.recordKill(source.team);
            source.targetId = null;
        }
    }

    private checkVictory(): void {
        const blueAlive = this.getAliveCount(Team.BLUE);
        const redAlive = this.getAliveCount(Team.RED);
        
        if (blueAlive === 0 && this.battleTime > 1) {
            this.phase = BattlePhase.FINISHED;
            this.winner = Team.RED;
        } else if (redAlive === 0 && this.battleTime > 1) {
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

    getTeamStats(team: Team) {
        const units = Array.from(this.units.values()).filter(u => u.team === team);
        const alive = units.filter(u => u.isActive);
        const interceptors = this.interceptors.filter(i => i.team === team && i.isActive).length;
        
        return {
            total: units.length,
            alive: alive.length,
            interceptors,
            killed: team === Team.BLUE ? this.blueKills : this.redKills,
            avgHealth: alive.length > 0 
                ? alive.reduce((sum, u) => sum + u.healthPercent, 0) / alive.length 
                : 0,
            avgMorale: alive.length > 0
                ? alive.reduce((sum, u) => sum + u.moralePercent, 0) / alive.length
                : 0,
            unitTypes: this.getUnitTypeBreakdown(team),
            totalDamage: alive.reduce((sum, u) => sum + u.damageDealt, 0),
        };
    }

    private getUnitTypeBreakdown(team: Team): Map<string, number> {
        const breakdown = new Map<string, number>();
        for (const unit of this.units.values()) {
            if (unit.team === team && unit.isActive) {
                const name = unit.voidClass.name;
                breakdown.set(name, (breakdown.get(name) || 0) + 1);
            }
        }
        return breakdown;
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
        this.projectiles = [];
        this.interceptors = [];
        this.hitEffects = [];
        this.interceptorSpawnTimer.clear();
        this.nextEntityId = 1;
        this.unitCounters.set(Team.BLUE, 1);
        this.unitCounters.set(Team.RED, 1);
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

    getEnemies(team: Team): Unit[] {
        return this.getAllActiveUnits().filter(u => u.team !== team);
    }

    getAllies(team: Team): Unit[] {
        return this.getAllActiveUnits().filter(u => u.team === team);
    }

    getFormationInfo(): { blue: string; red: string } {
        const blueUnits = Array.from(this.units.values()).filter(u => u.team === Team.BLUE);
        const redUnits = Array.from(this.units.values()).filter(u => u.team === Team.RED);
        const blueInterceptors = this.interceptors.filter(i => i.team === Team.BLUE && i.isActive).length;
        const redInterceptors = this.interceptors.filter(i => i.team === Team.RED && i.isActive).length;
        
        return {
            blue: `${blueUnits.length} units${blueInterceptors > 0 ? ` + ${blueInterceptors} drones` : ''}`,
            red: `${redUnits.length} units${redInterceptors > 0 ? ` + ${redInterceptors} drones` : ''}`
        };
    }
}
