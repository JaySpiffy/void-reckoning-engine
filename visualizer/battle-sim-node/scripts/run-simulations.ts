/**
 * Battle Simulation Runner
 * Run headless battles and collect statistics
 */

import { BattleManager } from '../src/game/managers/BattleManager.js';
import { Team, BattlePhase } from '../src/game/types/battle.js';
import { SIMULATION_CONFIG } from '../src/game/data/SimulationConfig.js';

interface SimulationResult {
    winner: Team | 'DRAW';
    duration: number;
    blueKills: number;
    redKills: number;
    blueSurvivors: number;
    redSurvivors: number;
    totalDamageDealt: number;
}

interface SimulationSummary {
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

function runSingleBattle(maxDuration: number = 300): SimulationResult {
    const battle = new BattleManager();
    battle.startBattle();
    
    let timeStep = 0.05;
    let elapsed = 0;
    
    while (battle.phase !== BattlePhase.FINISHED && elapsed < maxDuration) {
        battle.update(timeStep);
        elapsed += timeStep;
    }
    
    const blueUnits = Array.from(battle.units.values()).filter(u => u.team === Team.BLUE);
    const redUnits = Array.from(battle.units.values()).filter(u => u.team === Team.RED);
    
    const blueAlive = blueUnits.filter(u => u.isActive).length;
    const redAlive = redUnits.filter(u => u.isActive).length;
    
    let winner: Team | 'DRAW';
    if (blueAlive > 0 && redAlive === 0) winner = Team.BLUE;
    else if (redAlive > 0 && blueAlive === 0) winner = Team.RED;
    else winner = 'DRAW';
    
    return {
        winner,
        duration: elapsed,
        blueKills: battle.blueKills,
        redKills: battle.redKills,
        blueSurvivors: blueAlive,
        redSurvivors: redAlive,
        totalDamageDealt: Array.from(battle.units.values()).reduce((sum, u) => sum + u.damageDealt, 0)
    };
}

function runScenario(name: string, count: number, maxDuration: number = 300): { summary: SimulationSummary, results: SimulationResult[] } {
    const results: SimulationResult[] = [];
    
    for (let i = 0; i < count; i++) {
        results.push(runSingleBattle(maxDuration));
    }
    
    const runs = results.length;
    const blueWins = results.filter(r => r.winner === Team.BLUE).length;
    const redWins = results.filter(r => r.winner === Team.RED).length;
    const draws = results.filter(r => r.winner === 'DRAW').length;
    
    const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
    
    const summary: SimulationSummary = {
        scenario: name,
        runs,
        blueWins,
        redWins,
        draws,
        avgDuration: avg(results.map(r => r.duration)),
        avgBlueKills: avg(results.map(r => r.blueKills)),
        avgRedKills: avg(results.map(r => r.redKills)),
        avgBlueSurvivors: avg(results.map(r => r.blueSurvivors)),
        avgRedSurvivors: avg(results.map(r => r.redSurvivors))
    };
    
    return { summary, results };
}

// Run simulations
console.log('='.repeat(70));
console.log('VOIDHELIX BATTLE SIMULATOR - BALANCE TEST');
console.log('='.repeat(70));
console.log(`Team Size: ${SIMULATION_CONFIG.teamSize}v${SIMULATION_CONFIG.teamSize}`);
console.log(`Available Units: ${SIMULATION_CONFIG.availableUnitClasses.join(', ')}`);
console.log(`Health Scale: ${SIMULATION_CONFIG.healthScale}, Damage Scale: ${SIMULATION_CONFIG.damageScale}, Speed Scale: ${SIMULATION_CONFIG.speedScale}`);
console.log('');

const { summary, results } = runScenario('Standard 50v50', 20, 300);

console.log('RESULTS:');
console.log('-'.repeat(50));
console.log(`Scenario: ${summary.scenario}`);
console.log(`Runs: ${summary.runs}`);
console.log(`Blue Wins: ${summary.blueWins} (${((summary.blueWins/summary.runs)*100).toFixed(1)}%)`);
console.log(`Red Wins: ${summary.redWins} (${((summary.redWins/summary.runs)*100).toFixed(1)}%)`);
console.log(`Draws: ${summary.draws}`);
console.log('');
console.log(`Avg Duration: ${summary.avgDuration.toFixed(1)}s`);
console.log(`Avg Blue Kills: ${summary.avgBlueKills.toFixed(1)}`);
console.log(`Avg Red Kills: ${summary.avgRedKills.toFixed(1)}`);
console.log(`Avg Blue Survivors: ${summary.avgBlueSurvivors.toFixed(1)}`);
console.log(`Avg Red Survivors: ${summary.avgRedSurvivors.toFixed(1)}`);
console.log('');

console.log('INDIVIDUAL BATTLES:');
console.log('-'.repeat(50));
results.forEach((r, i) => {
    const win = r.winner === Team.BLUE ? 'BLUE' : r.winner === Team.RED ? 'RED' : 'DRAW';
    console.log(
        `Battle ${String(i + 1).padStart(2)}: ${win.padEnd(4)} wins in ${r.duration.toFixed(1).padStart(5)}s | ` +
        `Survivors: B${String(r.blueSurvivors).padStart(2)}/R${String(r.redSurvivors).padStart(2)} | ` +
        `Kills: B${String(r.blueKills).padStart(2)}/R${String(r.redKills).padStart(2)}`
    );
});

console.log('');
console.log('='.repeat(70));
console.log('BALANCE ANALYSIS:');
console.log('-'.repeat(50));

const winDiff = Math.abs(summary.blueWins - summary.redWins);
if (winDiff <= 2) {
    console.log('✓ Fairly balanced - win rates are close');
} else if (winDiff <= 5) {
    console.log('⚠ Slightly unbalanced - one side has advantage');
} else {
    console.log('✗ Significantly unbalanced');
}

if (summary.avgDuration < 30) {
    console.log('✗ Battles too short - units die too fast');
} else if (summary.avgDuration > 180) {
    console.log('⚠ Battles very long - may feel sluggish');
} else {
    console.log('✓ Good battle duration');
}

const totalKills = summary.avgBlueKills + summary.avgRedKills;
const killRate = totalKills / summary.avgDuration;
console.log(`Kill rate: ${killRate.toFixed(2)} kills/sec`);

if (killRate > 2) {
    console.log('✗ Very high kill rate - combat too deadly');
} else if (killRate < 0.3) {
    console.log('⚠ Low kill rate - combat too slow');
} else {
    console.log('✓ Good kill rate');
}

const avgTotalSurvivors = summary.avgBlueSurvivors + summary.avgRedSurvivors;
if (avgTotalSurvivors < 5) {
    console.log('✗ Bloodbath - almost everyone dies');
} else if (avgTotalSurvivors > 40) {
    console.log('⚠ Too many survivors - combat not decisive');
} else {
    console.log('✓ Good casualty rate');
}

console.log('='.repeat(70));
