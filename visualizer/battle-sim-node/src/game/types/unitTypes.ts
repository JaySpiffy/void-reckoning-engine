/**
 * Unit Type Definitions
 * Different unit classes with their stats and abilities
 */

export enum UnitClass {
    GRUNT = 'GRUNT',       // Basic melee - balanced
    ARCHER = 'ARCHER',     // Ranged - fragile but long range
    TANK = 'TANK',         // Heavy - slow, high HP, high damage
    MAGE = 'MAGE'          // Spellcaster - AOE, medium range
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

// Visual indicator colors for unit classes (shown as center dot)
export const UNIT_CLASS_COLORS: Record<UnitClass, string> = {
    [UnitClass.GRUNT]: '#666666',
    [UnitClass.ARCHER]: '#0ea5e9',
    [UnitClass.TANK]: '#64748b',
    [UnitClass.MAGE]: '#a855f7'
};
