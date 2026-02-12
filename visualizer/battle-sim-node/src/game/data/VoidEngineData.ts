/**
 * Void Reckoning Engine Data Loader
 * Imports unit classes, stats, and configs from jayspiffy's engine
 * CLEAN CONVERSION - Health and damage properly scaled
 */

// Unit Class data from void-reckoning-engine/data/ground/unit_classes.json
export interface VoidUnitClass {
    id: string;
    name: string;
    stats: {
        hp: number;
        entity_count: number;
        armor: number;
        morale: number;
        melee_attack: number;
        melee_defense: number;
        ranged_attack: number;
        charge_bonus: number;
        weapon_strength: number;
        armor_piercing: number;
        speed: number;
    };
    attributes: string[];
    tech_tier: number;
    unlock_tech?: string;
}

// Raw data from jayspiffy's engine
export const VOID_UNIT_CLASSES: VoidUnitClass[] = [
    {
        id: "line_infantry",
        name: "Line Infantry",
        stats: {
            hp: 500,
            entity_count: 100,
            armor: 30,
            morale: 60,
            melee_attack: 25,
            melee_defense: 25,
            ranged_attack: 0,
            charge_bonus: 10,
            weapon_strength: 30,
            armor_piercing: 5,
            speed: 35
        },
        attributes: ["infantry"],
        tech_tier: 1
    },
    {
        id: "assault_marines",
        name: "Assault Marines",
        stats: {
            hp: 1000,
            entity_count: 50,
            armor: 80,
            morale: 85,
            melee_attack: 45,
            melee_defense: 40,
            ranged_attack: 20,
            charge_bonus: 30,
            weapon_strength: 45,
            armor_piercing: 15,
            speed: 40
        },
        attributes: ["infantry", "fearless"],
        tech_tier: 2,
        unlock_tech: "Tech_Unlock_Elite_Infantry"
    },
    {
        id: "battle_tank",
        name: "Battle Tank",
        stats: {
            hp: 2500,
            entity_count: 4,
            armor: 120,
            morale: 90,
            melee_attack: 20,
            melee_defense: 10,
            ranged_attack: 300,
            charge_bonus: 60,
            weapon_strength: 150,
            armor_piercing: 100,
            speed: 50
        },
        attributes: ["large", "armored"],
        tech_tier: 3,
        unlock_tech: "Tech_Unlock_Armor_Chassis"
    },
    {
        id: "war_titan",
        name: "War Titan",
        stats: {
            hp: 15000,
            entity_count: 1,
            armor: 150,
            morale: 100,
            melee_attack: 80,
            melee_defense: 60,
            ranged_attack: 500,
            charge_bonus: 90,
            weapon_strength: 800,
            armor_piercing: 500,
            speed: 60
        },
        attributes: ["massive", "terror"],
        tech_tier: 4,
        unlock_tech: "Tech_Unlock_Titan_Engine"
    },
    {
        id: "advanced_battlesuit",
        name: "Advanced Battlesuit",
        stats: {
            hp: 300,
            entity_count: 3,
            armor: 40,
            morale: 90,
            melee_attack: 30,
            melee_defense: 30,
            ranged_attack: 100,
            charge_bonus: 15,
            weapon_strength: 60,
            armor_piercing: 25,
            speed: 55
        },
        attributes: ["infantry", "advanced"],
        tech_tier: 3,
        unlock_tech: "Tech_Unlock_Advanced_Battlesuits"
    },
    {
        id: "heavy_weapon_platform",
        name: "Heavy Weapon Platform",
        stats: {
            hp: 400,
            entity_count: 5,
            armor: 20,
            morale: 70,
            melee_attack: 10,
            melee_defense: 10,
            ranged_attack: 400,
            charge_bonus: 0,
            weapon_strength: 200,
            armor_piercing: 80,
            speed: 15
        },
        attributes: ["armored", "heavy_support"],
        tech_tier: 3,
        unlock_tech: "Tech_Unlock_Support_Platforms"
    },
    {
        id: "assault_brawler_walker",
        name: "Assault Brawler Walker",
        stats: {
            hp: 800,
            entity_count: 1,
            armor: 80,
            morale: 95,
            melee_attack: 60,
            melee_defense: 50,
            ranged_attack: 50,
            charge_bonus: 40,
            weapon_strength: 300,
            armor_piercing: 150,
            speed: 40
        },
        attributes: ["large", "walker"],
        tech_tier: 4,
        unlock_tech: "Tech_Unlock_Walker_Combat"
    },
    {
        id: "apocalypse_titan",
        name: "Apocalypse Class Titan",
        stats: {
            hp: 45000,
            entity_count: 1,
            armor: 250,
            morale: 100,
            melee_attack: 120,
            melee_defense: 80,
            ranged_attack: 2500,
            charge_bonus: 150,
            weapon_strength: 4000,
            armor_piercing: 2000,
            speed: 35
        },
        attributes: ["massive", "terror", "god_engine"],
        tech_tier: 5,
        unlock_tech: "Tech_Unlock_Apocalypse_Titan"
    }
];

// Get unit class by ID
export function getVoidUnitClass(id: string): VoidUnitClass | undefined {
    return VOID_UNIT_CLASSES.find(c => c.id === id);
}

// Get all unit classes for a tech tier
export function getVoidUnitsByTier(tier: number): VoidUnitClass[] {
    return VOID_UNIT_CLASSES.filter(c => c.tech_tier <= tier);
}

/**
 * CLEAN CONVERSION FORMULAS
 * 
 * Health: HP / 10 (so 500 HP → 50 health, 15000 HP → 1500 health)
 * 
 * Damage: Use appropriate stat based on unit type
 *   - Ranged units (ranged_attack > 0): Use weapon_strength / 10
 *   - Melee units: Use melee_attack / 5 (melee hits faster)
 *   - Mixed: Use weapon_strength / 10 (primary weapon)
 * 
 * This creates consistent damage-to-health ratios
 */
export function convertVoidStats(voidClass: VoidUnitClass, scaleFactor: number = 0.1) {
    const s = voidClass.stats;
    
    // HEALTH: Simple conversion
    const maxHealth = s.hp * scaleFactor;  // 500 * 0.1 = 50, 15000 * 0.1 = 1500
    
    // DAMAGE: Use weapon_strength as primary damage stat
    // Increased scale factor for more impactful combat
    // weapon_strength represents the unit's main weapon power
    // armor_piercing allows bypassing armor (e.g., 100 AP = ignore 100 armor)
    let baseDamage = s.weapon_strength * 0.15;  // 30 * 0.15 = 4.5, 800 * 0.15 = 120
    
    // RANGED ATTACK RANGE
    // Based on ranged_attack stat - higher = longer range
    let attackRange: number;
    if (s.ranged_attack > 0) {
        // Ranged units: 150 + (ranged_attack / 5) 
        // Infantry with 0 RA: won't use this
        // Titan with 500 RA: 150 + 100 = 250 range
        attackRange = 150 + (s.ranged_attack / 5);
    } else {
        // Melee only: short range
        attackRange = 30 + (s.melee_attack / 3);
    }
    
    // ATTACK COOLDOWN: Faster for light units, slower for heavy
    // Speed 15 (platform): 2.6s cooldown
    // Speed 60 (titan): 1.5s cooldown
    const attackCooldown = Math.max(0.8, 3.5 - (s.speed / 30));
    
    // MOVEMENT SPEED: Visual speed for simulator
    // Scale up for visual feel
    const speed = s.speed * 2.5;
    
    // RADIUS: Based on entity_count (smaller count = bigger individual units)
    // entity_count 100 (infantry): radius 12
    // entity_count 1 (titan): radius 25
    const radius = Math.max(10, Math.min(30, 35 - (s.entity_count / 5)));
    
    return {
        maxHealth,
        speed,
        damage: baseDamage,
        attackRange,
        attackCooldown,
        radius,
        armor: s.armor,
        armorPiercing: s.armor_piercing,  // Used to bypass target armor
        morale: s.morale,
        attributes: voidClass.attributes
    };
}

// Get display color based on attributes
export function getVoidUnitColor(attributes: string[] = []): string {
    if (attributes.includes('massive')) return '#fbbf24'; // Amber for titans
    if (attributes.includes('large')) return '#f97316'; // Orange for large
    if (attributes.includes('walker')) return '#a855f7'; // Purple for walkers
    if (attributes.includes('armored')) return '#64748b'; // Slate for armor
    if (attributes.includes('advanced')) return '#06b6d4'; // Cyan for advanced
    return '#94a3b8'; // Default gray
}

// Get unit role icon
export function getVoidUnitRoleIcon(attributes: string[]): string {
    if (attributes.includes('massive')) return '👑';
    if (attributes.includes('heavy_support')) return '🎯';
    if (attributes.includes('walker')) return '🦿';
    if (attributes.includes('armored')) return '🛡️';
    if (attributes.includes('infantry')) return '⚔️';
    return '◆';
}

// Balance check helper
export function getUnitBalanceInfo(): string {
    let info = "UNIT BALANCE CHECK\n==================\n\n";
    
    for (const unit of VOID_UNIT_CLASSES) {
        const stats = convertVoidStats(unit, 0.1);
        const dps = stats.damage / stats.attackCooldown;
        const armorReduction = stats.armor / (stats.armor + 100);
        const survivability = stats.maxHealth / (1 - armorReduction);
        
        info += `${unit.name} (T${unit.tech_tier})\n`;
        info += `  HP: ${stats.maxHealth.toFixed(0)} | DMG: ${stats.damage.toFixed(1)} | Armor: ${stats.armor} (${(armorReduction*100).toFixed(0)}%)\n`;
        info += `  AP: ${stats.armorPiercing} | DPS: ${dps.toFixed(1)} | Range: ${stats.attackRange.toFixed(0)}\n`;
        info += `  Survivability: ${survivability.toFixed(0)} | Speed: ${stats.speed.toFixed(0)}\n\n`;
    }
    
    return info;
}

// Log balance info to console
console.log(getUnitBalanceInfo());
