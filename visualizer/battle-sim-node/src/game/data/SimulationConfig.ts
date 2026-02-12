/**
 * Simulation Configuration
 * Easily adjustable variables for the battle simulation
 */

// Simulation Variables - Adjust these to tune the battle
export const SIMULATION_CONFIG = {
    // Unit Counts
    teamSize: 50,                    // Units per team (50 = 50v50)
    
    // Unit Selection - which unit classes to use
    availableUnitClasses: [
        "line_infantry",
        "assault_marines", 
        "battle_tank",
        "heavy_weapon_platform",
        "war_titan"
    ] as string[],
    
    // Stat Scaling - multiply all void engine stats by this
    healthScale: 0.1,                // Health multiplier (0.1 = 10x faster battles)
    damageScale: 1.0,                // Damage multiplier (1.0 = normal)
    speedScale: 2.5,                // Movement speed multiplier (higher = faster engagement)
    
    // Battlefield
    worldWidth: 3000,
    worldHeight: 2000,
    spawnMargin: 200,
    
    // AI Behavior
    aiUpdateRate: 1,                // How often AI updates (1 = every frame)
    targetSearchRange: 500,         // How far units look for targets
    separationRadius: 3,            // Collision avoidance multiplier
    attackRangeBuffer: 0.8,         // Start moving when at (range * buffer)
    
    // Visual
    showNameplates: true,
    showHealthBars: true,
    showRangeIndicators: false,
    showUnitIds: true,
    showCoordinates: false,
    
    // Camera
    defaultZoom: 1.0,
    minZoom: 0.3,
    maxZoom: 3.0,
    
    // Game Speed
    defaultTimeScale: 1.0,
    timeScales: [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
};

// Debug/Development Settings
export const DEBUG_CONFIG = {
    showFps: false,
    showCollisionBoxes: false,
    showTargetLines: false,
    logCombat: false,
    invincibleUnits: false
};

// Preset configurations for different battle types
export const BATTLE_PRESETS = {
    quick: {
        teamSize: 20,
        healthScale: 0.05,
        damageScale: 0.2,
        speedScale: 3.0
    },
    standard: {
        teamSize: 50,
        healthScale: 0.1,
        damageScale: 0.1,
        speedScale: 2.0
    },
    epic: {
        teamSize: 100,
        healthScale: 0.2,
        damageScale: 0.05,
        speedScale: 1.5
    },
    titan: {
        teamSize: 10,
        availableUnitClasses: ["war_titan", "apocalypse_titan"],
        healthScale: 0.01,
        damageScale: 0.01,
        speedScale: 1.0
    }
};

// Apply a preset
export function applyPreset(presetName: keyof typeof BATTLE_PRESETS) {
    const preset = BATTLE_PRESETS[presetName];
    Object.assign(SIMULATION_CONFIG, preset);
}

// Get current config summary
export function getConfigSummary(): string {
    return `
Simulation Config:
- Team Size: ${SIMULATION_CONFIG.teamSize}v${SIMULATION_CONFIG.teamSize}
- Health Scale: ${SIMULATION_CONFIG.healthScale}x
- Damage Scale: ${SIMULATION_CONFIG.damageScale}x
- Speed Scale: ${SIMULATION_CONFIG.speedScale}x
- Unit Types: ${SIMULATION_CONFIG.availableUnitClasses.length}
- World: ${SIMULATION_CONFIG.worldWidth}x${SIMULATION_CONFIG.worldHeight}
    `.trim();
}
