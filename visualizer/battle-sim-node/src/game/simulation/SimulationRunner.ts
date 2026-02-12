/**
 * Automated Battle Simulation Runner
 * Runs multiple battles and collects statistics for balance analysis
 */

import { BattleManager } from '../managers/BattleManager';
import { Team, BattlePhase } from '../types/battle';
import { SIMULATION_CONFIG } from '../data/SimulationConfig';

export interface SimulationResult {
    winner: Team | 'DRAW';
    duration: number;
    blueKills: number;
    redKills: number;
    blueSurvivors: number;
    redSurvivors: number;
    totalDamageDealt: number;
}

export interface SimulationSummary {
    scenario: string;
    runs: number;
    blueWins: number;
    redWins: number;
    draws: number;
    avgDuration: number;
    avgBlueKills: number;
    avgRedKills: number;
    avgBlueSurvivors: number;
    avgRedSurvivors: number;
}

export class SimulationRunner {
    private results: SimulationResult[] = [];
    
    /**
     * Run a single battle simulation
     */
    runSingleBattle(maxDuration: number = 300): SimulationResult {
        const battle = new BattleManager();
        battle.startBattle();
        
        let timeStep = 0.05; // 50ms steps
        let elapsed = 0;
        
        while (battle.phase !== BattlePhase.FINISHED && elapsed < maxDuration) {
            battle.update(timeStep);
            elapsed += timeStep;
        }
        
        // Collect results
        const blueUnits = Array.from(battle.units.values()).filter(u => u.team === Team.BLUE);
        const redUnits = Array.from(battle.units.values()).filter(u => u.team === Team.RED);
        
        const blueAlive = blueUnits.filter(u => u.isActive).length;
        const redAlive = redUnits.filter(u => u.isActive).length;
        
        const blueKills = battle.blueKills;
        const redKills = battle.redKills;
        
        const totalDamage = Array.from(battle.units.values())
            .reduce((sum, u) => sum + u.damageDealt, 0);
        
        let winner: Team | 'DRAW';
        if (blueAlive > 0 && redAlive === 0) winner = Team.BLUE;
        else if (redAlive > 0 && blueAlive === 0) winner = Team.RED;
        else winner = 'DRAW';
        
        return {
            winner,
            duration: elapsed,
            blueKills,
            redKills,
            blueSurvivors: blueAlive,
            redSurvivors: redAlive,
            totalDamageDealt: totalDamage
        };
    }
    
    /**
     * Run multiple battles and collect statistics
     */
    runScenario(name: string, count: number, maxDuration: number = 300): SimulationSummary {
        this.results = [];
        
        for (let i = 0; i < count; i++) {
            this.results.push(this.runSingleBattle(maxDuration));
        }
        
        return this.summarize(name);
    }
    
    private summarize(scenario: string): SimulationSummary {
        const runs = this.results.length;
        const blueWins = this.results.filter(r => r.winner === Team.BLUE).length;
        const redWins = this.results.filter(r => r.winner === Team.RED).length;
        const draws = this.results.filter(r => r.winner === 'DRAW').length;
        
        const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
        
        return {
            scenario,
            runs,
            blueWins,
            redWins,
            draws,
            avgDuration: avg(this.results.map(r => r.duration)),
            avgBlueKills: avg(this.results.map(r => r.blueKills)),
            avgRedKills: avg(this.results.map(r => r.redKills)),
            avgBlueSurvivors: avg(this.results.map(r => r.blueSurvivors)),
            avgRedSurvivors: avg(this.results.map(r => r.redSurvivors))
        };
    }
    
    /**
     * Get detailed results from last run
     */
    getLastResults(): SimulationResult[] {
        return [...this.results];
    }
}

// Format results for console output
export function formatSummary(summary: SimulationSummary, results: SimulationResult[]): string {
    let output = '';
    
    output += '='.repeat(60) + '\n';
    output += 'VOIDHELIX BATTLE SIMULATOR - BALANCE TEST\n';
    output += '='.repeat(60) + '\n';
    output += `Team Size: ${SIMULATION_CONFIG.teamSize}v${SIMULATION_CONFIG.teamSize}\n`;
    output += `Available Units: ${SIMULATION_CONFIG.availableUnitClasses.join(', ')}\n`;
    output += `Health Scale: ${SIMULATION_CONFIG.healthScale}, Damage Scale: ${SIMULATION_CONFIG.damageScale}\n`;
    output += '\n';
    
    output += 'RESULTS:\n';
    output += '-'.repeat(40) + '\n';
    output += `Scenario: ${summary.scenario}\n`;
    output += `Runs: ${summary.runs}\n`;
    output += `Blue Wins: ${summary.blueWins} (${((summary.blueWins/summary.runs)*100).toFixed(1)}%)\n`;
    output += `Red Wins: ${summary.redWins} (${((summary.redWins/summary.runs)*100).toFixed(1)}%)\n`;
    output += `Draws: ${summary.draws}\n`;
    output += '\n';
    output += `Avg Duration: ${summary.avgDuration.toFixed(1)}s\n`;
    output += `Avg Blue Kills: ${summary.avgBlueKills.toFixed(1)}\n`;
    output += `Avg Red Kills: ${summary.avgRedKills.toFixed(1)}\n`;
    output += `Avg Blue Survivors: ${summary.avgBlueSurvivors.toFixed(1)}\n`;
    output += `Avg Red Survivors: ${summary.avgRedSurvivors.toFixed(1)}\n`;
    output += '\n';
    
    output += 'INDIVIDUAL BATTLES:\n';
    output += '-'.repeat(40) + '\n';
    results.forEach((r, i) => {
        const win = r.winner === Team.BLUE ? 'BLUE' : r.winner === Team.RED ? 'RED' : 'DRAW';
        output += `Battle ${i + 1}: ${win} wins in ${r.duration.toFixed(1)}s | ` +
                  `Survivors: B${r.blueSurvivors}/R${r.redSurvivors} | ` +
                  `Kills: B${r.blueKills}/R${r.redKills}\n`;
    });
    
    output += '\n';
    output += '='.repeat(60) + '\n';
    
    // Balance analysis
    output += 'BALANCE ANALYSIS:\n';
    output += '-'.repeat(40) + '\n';
    
    const winDiff = Math.abs(summary.blueWins - summary.redWins);
    if (winDiff <= 1) {
        output += '✓ Fairly balanced - win rates are close\n';
    } else if (winDiff <= 3) {
        output += '⚠ Slightly unbalanced - one side has advantage\n';
    } else {
        output += '✗ Significantly unbalanced\n';
    }
    
    if (summary.avgDuration < 30) {
        output += '✗ Battles too short - units die too fast\n';
    } else if (summary.avgDuration > 180) {
        output += '⚠ Battles very long - may feel sluggish\n';
    } else {
        output += '✓ Good battle duration\n';
    }
    
    const totalKills = summary.avgBlueKills + summary.avgRedKills;
    const killRate = totalKills / summary.avgDuration;
    output += `Kill rate: ${killRate.toFixed(2)} kills/sec\n`;
    
    if (killRate > 2) {
        output += '✗ Very high kill rate - combat too deadly\n';
    } else if (killRate < 0.3) {
        output += '⚠ Low kill rate - combat too slow\n';
    } else {
        output += '✓ Good kill rate\n';
    }
    
    output += '='.repeat(60) + '\n';
    
    return output;
}
