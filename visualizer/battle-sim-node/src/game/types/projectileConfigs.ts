/**
 * ELEMENT PROJECTILE CONFIGS - Shared constants for ability and combat systems
 *
 * These configs define the visual and gameplay properties for each element type's projectiles.
 */

import { ElementType, DamageType } from './index';

export interface ElementProjectileConfig {
    speed: number;
    radius: number;
    color: string;
    glowColor: string;
    damage: number;
    damageType: DamageType;
    pierce: number;
    dotDamage?: number;
    dotDuration?: number;
    slowPercent?: number;
    slowDuration?: number;
    chainCount?: number;
    lifetime: number;
}

export const ELEMENT_PROJECTILE_CONFIGS: Record<ElementType, ElementProjectileConfig> = {
    [ElementType.NONE]: {
        speed: 600,
        radius: 6,
        color: '#60a5fa',
        glowColor: '#3b82f6',
        damage: 1,
        damageType: DamageType.PHYSICAL,
        pierce: 0,
        lifetime: 1.5,
    },
    [ElementType.FIRE]: {
        speed: 550,
        radius: 8,
        color: '#f97316',
        glowColor: '#ef4444',
        damage: 1.5,
        damageType: DamageType.FIRE,
        pierce: 2,
        dotDamage: 5,
        dotDuration: 3,
        lifetime: 1.5,
    },
    [ElementType.ICE]: {
        speed: 650,
        radius: 7,
        color: '#60a5fa',
        glowColor: '#3b82f6',
        damage: 0.8,
        damageType: DamageType.ICE,
        pierce: 3,
        slowPercent: 0.5,
        slowDuration: 2,
        lifetime: 1.5,
    },
    [ElementType.LIGHTNING]: {
        speed: 800,
        radius: 5,
        color: '#facc15',
        glowColor: '#eab308',
        damage: 1.2,
        damageType: DamageType.LIGHTNING,
        pierce: 0,
        chainCount: 3,
        lifetime: 1.0,
    },
    [ElementType.POISON]: {
        speed: 500,
        radius: 7,
        color: '#4ade80',
        glowColor: '#22c55e',
        damage: 0.6,
        damageType: DamageType.POISON,
        pierce: 1,
        dotDamage: 8,
        dotDuration: 5,
        lifetime: 2.0,
    },
    [ElementType.ARCANE]: {
        speed: 700,
        radius: 9,
        color: '#c084fc',
        glowColor: '#a855f7',
        damage: 2.0,
        damageType: DamageType.ARCANE,
        pierce: 5,
        lifetime: 1.2,
    },
};
