/**
 * Battle Game Manager
 * Main entry point for the battle simulator - wraps BattleManager and BattleAISystem
 */

import { BattleManager } from './BattleManager';
import { BattleAISystem } from '../systems/BattleAISystem';
import { BattlePhase } from '../types/battle';
import type { BattleStats } from '../types/battle';

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

    get isFinished(): boolean {
        return this.battle.phase === BattlePhase.FINISHED;
    }

    get winner() {
        return this.battle.winner;
    }
}
