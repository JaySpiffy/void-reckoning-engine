import { parse } from 'smol-toml';
import { LogCategory, logger } from './LogManager';

export interface WorldConfig {
    width: number;
    height: number;
    margin: number;
    spawn_min_distance: number;
    spawn_max_distance: number;
}

export interface PlayerStatsConfig {
    base_health: number;
    base_mana: number;
    base_speed: number;
    base_damage: number;
    base_attack_speed: number;
    base_attack_range: number;
    exp_base: number;
    exp_multiplier: number;
}

export interface WaveScalingConfig {
    base_enemy_count: number;
    count_increase_per_wave: number;
    base_spawn_interval: number;
    min_spawn_interval: number;
    interval_decrease_per_wave: number;
}

export interface AbilityConfig {
    dash_cost: number;
    nova_cost: number;
    chain_lightning_cost: number;
    ultimate_cost: number;
    dash_cooldown: number;
    nova_cooldown: number;
    chain_lightning_cooldown: number;
    ultimate_cooldown: number;
}

export interface GameConfig {
    world: WorldConfig;
    player: PlayerStatsConfig;
    waves: WaveScalingConfig;
    abilities: AbilityConfig;
}

export class ConfigManager {
    private config: GameConfig | null = null;
    private isLoaded: boolean = false;

    // Helper to fetch with a timeout
    private async fetchWithTimeout(resource: RequestInfo, options: RequestInit & { timeout?: number } = {}): Promise<Response> {
        const { timeout = 5000 } = options; // Default to 5 seconds

        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(resource, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);

        return response;
    }

    async loadConfig(): Promise<boolean> {
        try {
            logger.info(LogCategory.SYSTEM, 'Loading game configuration...');
            const response = await this.fetchWithTimeout(`${import.meta.env.BASE_URL}data/balance.toml`, { timeout: 10000 }); // 10 second timeout

            if (!response.ok) {
                throw new Error(`Failed to fetch config: ${response.statusText}`);
            }

            const tomlText = await response.text();
            this.config = parse(tomlText) as unknown as GameConfig;
            this.isLoaded = true;

            logger.info(LogCategory.SYSTEM, 'Game configuration loaded successfully');
            return true;
        } catch (error) {
            logger.error(LogCategory.SYSTEM, `Error loading configuration: ${error instanceof Error ? error.message : String(error)}`);
            return false;
        }
    }

    get<K extends keyof GameConfig>(key: K): GameConfig[K] {
        if (!this.config) {
            throw new Error(`Configuration not loaded! Called get(${key}) before loadConfig()`);
        }
        return this.config[key];
    }

    getAll(): GameConfig {
        if (!this.config) {
            throw new Error('Configuration not loaded!');
        }
        return this.config;
    }

    isReady(): boolean {
        return this.isLoaded;
    }
}

export const configManager = new ConfigManager();
