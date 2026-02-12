/**
 * Battle Unit Entity with Shape Variety
 * Different shapes for different unit types - inspired by Darwin's Island
 */

import { Entity } from './Entity';
import { DamageType } from '../types';
import type { Vector2 } from '../types';
import { Team, TEAM_CONFIG } from '../types/battle';
import { Vec2 } from '../utils/Vector2';
import type { VoidUnitClass } from '../data/VoidEngineData';
import { 
    convertVoidStats, 
    getVoidUnitColor,
    getVoidUnitRoleIcon 
} from '../data/VoidEngineData';
import { SIMULATION_CONFIG } from '../data/SimulationConfig';

export interface UnitConfig {
    id?: string;
    position: Vector2;
    team: Team;
    voidClass: VoidUnitClass;
}

// Shape types for different units
export type UnitShape = 'circle' | 'square' | 'triangle' | 'hexagon' | 'slime' | 'diamond' | 'star';

export class Unit extends Entity {
    public team: Team;
    public voidClass: VoidUnitClass;
    public health: number;
    public maxHealth: number;
    public morale: number;
    public maxMorale: number;
    public armor: number;
    public armorPiercing: number;  // Ignores this much of target's armor
    public targetId: string | null = null;
    public attackTimer: number = 0;
    public kills: number = 0;
    public unitNumber: number = 0;
    public damageDealt: number = 0;
    
    // Animation
    public animFrame: number = 0;
    public isMoving: boolean = false;
    public bobOffset: number = Math.random() * Math.PI * 2;
    public lastAttackTime: number = 0;
    public attackAnim: number = 0;
    public slimeWobble: number = Math.random() * Math.PI * 2;
    
    // Stats
    public damage: number;
    public attackRange: number;
    public attackCooldown: number;
    public unitSpeed: number;
    public roleIcon: string;
    public classColor: string;
    public isRanged: boolean;
    public shape: UnitShape;
    public rotation: number = 0;

    constructor(config: UnitConfig) {
        const stats = convertVoidStats(config.voidClass, SIMULATION_CONFIG.healthScale);
        
        super({
            position: config.position,
            type: 'ENEMY' as any,
            radius: stats.radius,
            color: TEAM_CONFIG[config.team].color
        });
        
        if (config.id) {
            (this.id as string) = config.id;
        }
        
        this.team = config.team;
        this.voidClass = config.voidClass;
        
        // Determine shape based on unit type
        this.shape = this.determineShape();
        
        // Stats
        this.maxHealth = stats.maxHealth;
        this.health = this.maxHealth;
        this.maxMorale = config.voidClass.stats.morale;
        this.morale = this.maxMorale;
        this.armor = stats.armor;
        this.armorPiercing = stats.armorPiercing;
        
        // Combat stats - CLEAN: damage already scaled, just apply user multiplier
        this.damage = stats.damage * SIMULATION_CONFIG.damageScale;
        this.attackRange = stats.attackRange;
        this.attackCooldown = stats.attackCooldown;
        this.unitSpeed = stats.speed * SIMULATION_CONFIG.speedScale;
        this.radius = stats.radius;
        this.isRanged = config.voidClass.stats.ranged_attack > 0;
        
        // Visual
        this.roleIcon = getVoidUnitRoleIcon(config.voidClass.attributes);
        this.classColor = getVoidUnitColor(config.voidClass.attributes);
        
        this.isActive = true;
        this.isVisible = true;
    }

    private determineShape(): UnitShape {
        const name = this.voidClass.name.toLowerCase();
        const attrs = this.voidClass.attributes;
        
        // Titans and massive units
        if (name.includes('titan') || attrs.includes('massive')) {
            return 'hexagon';
        }
        // Tanks and armored
        if (name.includes('tank') || attrs.includes('armored')) {
            return 'square';
        }
        // Walker units
        if (name.includes('walker')) {
            return 'diamond';
        }
        // Support/heavy weapon
        if (name.includes('platform') || name.includes('support')) {
            return 'star';
        }
        // Infantry
        if (name.includes('infantry') || name.includes('marine')) {
            return 'triangle';
        }
        // Battlesuits
        if (name.includes('battlesuit')) {
            return 'circle';
        }
        // Default based on size
        if (this.voidClass.stats.hp > 1000) {
            return 'hexagon';
        } else if (this.voidClass.stats.hp > 500) {
            return 'square';
        }
        
        return 'slime'; // Default fun shape
    }

    get speed(): number {
        const moraleMultiplier = 0.5 + (this.morale / this.maxMorale) * 0.5;
        return this.unitSpeed * this.getSpeedMultiplier() * moraleMultiplier;
    }

    get displayName(): string {
        return `${this.voidClass.name} #${this.unitNumber}`;
    }

    get shortName(): string {
        const words = this.voidClass.name.split(' ');
        if (words.length === 1) return words[0].slice(0, 3);
        return words.map(w => w[0]).join('');
    }

    get healthPercent(): number {
        return this.health / this.maxHealth;
    }

    get moralePercent(): number {
        return this.morale / this.maxMorale;
    }

    takeDamage(amount: number, _type: DamageType, _source?: string, armorPiercing: number = 0): void {
        // Armor piercing reduces effective armor (but not below 0)
        const effectiveArmor = Math.max(0, this.armor - armorPiercing);
        const armorReduction = effectiveArmor / (effectiveArmor + 100);
        const actualDamage = amount * (1 - armorReduction);
        
        this.health -= actualDamage;
        this.morale -= actualDamage / this.maxHealth * 20;
        
        if (this.health <= 0) {
            this.health = 0;
            this.isActive = false;
        }
        if (this.morale <= 0) {
            this.morale = 0;
        }
    }

    canAttack(): boolean {
        return this.attackTimer <= 0 && this.isActive;
    }

    resetAttackTimer(): void {
        this.attackTimer = this.attackCooldown;
        this.lastAttackTime = this.age;
        this.attackAnim = 1.0;
    }

    update(deltaTime: number): void {
        if (!this.isActive) return;
        
        this.animFrame += deltaTime * 10;
        this.slimeWobble += deltaTime * 5;
        
        // Check if moving
        const moveSpeed = Vec2.magnitude(this.velocity);
        this.isMoving = moveSpeed > 5;
        
        // Rotation for non-circular shapes
        if (this.isMoving) {
            this.rotation = Math.atan2(this.velocity.y, this.velocity.x);
        }
        
        // Attack cooldown
        if (this.attackTimer > 0) {
            this.attackTimer -= deltaTime;
        }
        
        // Attack animation decay
        if (this.attackAnim > 0) {
            this.attackAnim -= deltaTime * 5;
            if (this.attackAnim < 0) this.attackAnim = 0;
        }
        
        // Movement with bobbing
        if (this.isMoving) {
            const bob = Math.sin(this.animFrame * 2 + this.bobOffset) * 3;
            this.position = Vec2.add(this.position, Vec2.mul(this.velocity, deltaTime));
            if (this.shape !== 'slime') {
                this.position.y += bob * deltaTime * 0.5;
            }
        }
        
        this.velocity = Vec2.zero();
        this.age += deltaTime;
        
        // Morale recovery
        if (this.morale < this.maxMorale) {
            this.morale += deltaTime * 5;
        }
    }

    render(ctx: CanvasRenderingContext2D, isHovered: boolean = false, isSelected: boolean = false): void {
        if (!this.isVisible) return;

        const isAlive = this.isActive;
        const bobY = (this.isMoving && this.shape !== 'slime') ? Math.sin(this.animFrame * 2 + this.bobOffset) * 3 : 0;
        const attackPulse = this.attackAnim > 0 ? Math.sin(this.attackAnim * Math.PI) * 5 : 0;
        const drawX = this.position.x;
        const drawY = this.position.y + bobY;
        const bodyRadius = this.radius + attackPulse * 0.3;

        // Selection/hover ring
        if (isSelected || isHovered) {
            this.drawRing(ctx, drawX, drawY, this.radius + 6 + attackPulse, isSelected);
        }

        // Glow
        if (isAlive) {
            ctx.shadowColor = this.color;
            ctx.shadowBlur = isHovered ? 20 : 12;
        }

        // Draw based on shape
        ctx.fillStyle = isAlive ? this.color : '#475569';
        
        switch (this.shape) {
            case 'slime':
                this.renderSlime(ctx, drawX, drawY, bodyRadius);
                break;
            case 'square':
                this.renderSquare(ctx, drawX, drawY, bodyRadius);
                break;
            case 'triangle':
                this.renderTriangle(ctx, drawX, drawY, bodyRadius);
                break;
            case 'hexagon':
                this.renderHexagon(ctx, drawX, drawY, bodyRadius);
                break;
            case 'diamond':
                this.renderDiamond(ctx, drawX, drawY, bodyRadius);
                break;
            case 'star':
                this.renderStar(ctx, drawX, drawY, bodyRadius);
                break;
            default:
                this.renderCircle(ctx, drawX, drawY, bodyRadius);
        }
        
        ctx.shadowBlur = 0;

        // Border
        ctx.strokeStyle = isAlive ? '#ffffff' : '#64748b';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Inner detail
        if (isAlive) {
            this.renderInnerDetail(ctx, drawX, drawY);
        }

        // Nameplate and health
        if (SIMULATION_CONFIG.showNameplates && isAlive) {
            this.renderNameplate(ctx, drawX, drawY);
        }
        if (SIMULATION_CONFIG.showHealthBars && isAlive) {
            this.renderHealthBar(ctx, drawX, drawY);
        }
        if (isSelected && isAlive) {
            this.renderRangeIndicator(ctx, drawX, drawY);
        }
    }

    private drawRing(ctx: CanvasRenderingContext2D, x: number, y: number, radius: number, isSelected: boolean): void {
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.strokeStyle = isSelected ? '#fbbf24' : 'rgba(255,255,255,0.5)';
        ctx.lineWidth = 2;
        ctx.setLineDash(isSelected ? [] : [3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    private renderSlime(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
        // Blobby amoeba shape that wobbles
        const points = 8;
        const wobble = Math.sin(this.slimeWobble) * 3;
        
        ctx.beginPath();
        for (let i = 0; i <= points; i++) {
            const angle = (i / points) * Math.PI * 2;
            const radiusVariation = Math.sin(angle * 3 + this.slimeWobble) * 4;
            const radius = r + radiusVariation + wobble;
            const px = x + Math.cos(angle) * radius;
            const py = y + Math.sin(angle) * radius;
            
            if (i === 0) {
                ctx.moveTo(px, py);
            } else {
                ctx.lineTo(px, py);
            }
        }
        ctx.closePath();
        ctx.fill();
    }

    private renderSquare(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
        const size = r * 1.8;
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(this.rotation);
        ctx.fillRect(-size/2, -size/2, size, size);
        ctx.restore();
    }

    private renderTriangle(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(this.rotation);
        ctx.beginPath();
        ctx.moveTo(r * 1.5, 0);
        ctx.lineTo(-r * 0.75, r * 1.3);
        ctx.lineTo(-r * 0.75, -r * 1.3);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
    }

    private renderHexagon(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const angle = (i / 6) * Math.PI * 2;
            const px = x + Math.cos(angle) * r * 1.3;
            const py = y + Math.sin(angle) * r * 1.3;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fill();
    }

    private renderDiamond(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
        ctx.beginPath();
        ctx.moveTo(x, y - r * 1.5);
        ctx.lineTo(x + r * 1.2, y);
        ctx.lineTo(x, y + r * 1.5);
        ctx.lineTo(x - r * 1.2, y);
        ctx.closePath();
        ctx.fill();
    }

    private renderStar(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
        const spikes = 5;
        const outerRadius = r * 1.4;
        const innerRadius = r * 0.6;
        
        ctx.beginPath();
        for (let i = 0; i < spikes * 2; i++) {
            const angle = (i / (spikes * 2)) * Math.PI * 2 - Math.PI / 2;
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const px = x + Math.cos(angle) * radius;
            const py = y + Math.sin(angle) * radius;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fill();
    }

    private renderCircle(ctx: CanvasRenderingContext2D, x: number, y: number, r: number): void {
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
    }

    private renderInnerDetail(ctx: CanvasRenderingContext2D, x: number, y: number): void {
        const r = this.radius;
        
        // Class color inner shape
        ctx.fillStyle = this.classColor;
        
        switch (this.shape) {
            case 'slime':
                ctx.beginPath();
                ctx.arc(x, y, r * 0.4, 0, Math.PI * 2);
                ctx.fill();
                break;
            case 'square':
                ctx.fillRect(x - r * 0.3, y - r * 0.3, r * 0.6, r * 0.6);
                break;
            case 'triangle':
                ctx.beginPath();
                ctx.arc(x, y, r * 0.3, 0, Math.PI * 2);
                ctx.fill();
                break;
            default:
                ctx.beginPath();
                ctx.arc(x, y, r * 0.4, 0, Math.PI * 2);
                ctx.fill();
        }
        
        // Weapon indicator
        if (this.isRanged) {
            ctx.fillStyle = '#22d3ee';
            ctx.beginPath();
            ctx.arc(x + r * 0.3, y - r * 0.3, 3, 0, Math.PI * 2);
            ctx.fill();
        } else {
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x - 3, y);
            ctx.lineTo(x + 3, y);
            ctx.moveTo(x, y - 3);
            ctx.lineTo(x, y + 3);
            ctx.stroke();
        }
    }

    private renderNameplate(ctx: CanvasRenderingContext2D, x: number, y: number): void {
        const text = SIMULATION_CONFIG.showUnitIds 
            ? `${this.roleIcon}${this.shortName}#${this.unitNumber}`
            : `${this.roleIcon}${this.shortName}`;
        
        ctx.font = 'bold 10px monospace';
        ctx.textAlign = 'center';
        
        const metrics = ctx.measureText(text);
        const padding = 3;
        const boxWidth = metrics.width + padding * 2;
        const boxHeight = 14;
        const boxX = x - boxWidth / 2;
        const boxY = y - this.radius - 20;
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(boxX, boxY, boxWidth, boxHeight);
        ctx.strokeStyle = this.color;
        ctx.lineWidth = 1;
        ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);
        
        ctx.fillStyle = '#ffffff';
        ctx.fillText(text, x, boxY + 10);
        ctx.textAlign = 'left';
    }

    private renderHealthBar(ctx: CanvasRenderingContext2D, x: number, y: number): void {
        const barWidth = this.radius * 2.5;
        const barHeight = 5;
        const barX = x - barWidth / 2;
        const barY = y - this.radius - 12;

        ctx.fillStyle = '#1e293b';
        ctx.fillRect(barX, barY, barWidth, barHeight);

        const pct = this.healthPercent;
        const color = pct > 0.6 ? '#22c55e' : pct > 0.3 ? '#eab308' : '#ef4444';
        ctx.fillStyle = color;
        ctx.fillRect(barX, barY, barWidth * pct, barHeight);
        
        // Morale bar
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(barX, barY + 6, barWidth, 2);
        ctx.fillStyle = this.moralePercent > 0.5 ? '#3b82f6' : '#f59e0b';
        ctx.fillRect(barX, barY + 6, barWidth * this.moralePercent, 2);
    }

    private renderRangeIndicator(ctx: CanvasRenderingContext2D, x: number, y: number): void {
        ctx.beginPath();
        ctx.arc(x, y, this.attackRange, 0, Math.PI * 2);
        ctx.strokeStyle = this.isRanged ? 'rgba(34, 211, 238, 0.25)' : 'rgba(239, 68, 68, 0.25)';
        ctx.lineWidth = 1;
        ctx.setLineDash([8, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
        
        ctx.fillStyle = this.isRanged ? '#22d3ee' : '#ef4444';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(this.isRanged ? `RANGED ${this.shape.toUpperCase()}` : `MELEE ${this.shape.toUpperCase()}`, x, y - this.attackRange - 5);
        ctx.textAlign = 'left';
    }

    distanceToUnit(other: Unit): number {
        return Vec2.distance(this.position, other.position);
    }

    isEnemyOf(other: Unit): boolean {
        return this.team !== other.team;
    }

    getCoordinates(): string {
        return `${Math.round(this.position.x)},${Math.round(this.position.y)}`;
    }

    getStatusText(): string {
        if (!this.isActive) return 'DEAD';
        if (this.morale < 20) return 'ROUTING';
        if (this.morale < 50) return 'WAVERING';
        if (this.attackAnim > 0) return 'ATTACKING';
        if (this.isMoving) return 'MOVING';
        if (this.targetId) return 'ENGAGING';
        return 'IDLE';
    }

    getDetailedInfo(): string {
        return `
${this.displayName} [${this.getStatusText()}]
Shape: ${this.shape.toUpperCase()} | ${this.voidClass.attributes.join(', ')}
HP: ${Math.round(this.health)}/${Math.round(this.maxHealth)} (${(this.healthPercent * 100).toFixed(0)}%)
Morale: ${Math.round(this.morale)}/${Math.round(this.maxMorale)}
Armor: ${this.armor} | AP: ${this.armorPiercing} | Damage: ${this.damage.toFixed(1)}
Range: ${this.attackRange.toFixed(0)} | Speed: ${this.speed.toFixed(0)}
Kills: ${this.kills} | Dealt: ${this.damageDealt.toFixed(0)} DMG
Position: ${this.getCoordinates()}
Weapon: ${this.isRanged ? 'RANGED' : 'MELEE'}
        `.trim();
    }
}
