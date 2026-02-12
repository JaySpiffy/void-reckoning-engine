/**
 * Battle Simulator Types
 * Team definitions, battle configuration, and statistics
 */

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
