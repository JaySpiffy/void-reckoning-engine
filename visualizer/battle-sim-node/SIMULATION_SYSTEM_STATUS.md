# Simulation System - Status Report

## ✅ What's Already Built

### 1. SmartAutoplaySystem (`src/game/systems/SmartAutoplaySystem.ts`)
**Status: Working**

AI that plays the game intelligently:
- ✅ Auto-evolves based on dominant DNA type
- ✅ Smart targeting (prioritizes dangerous enemies)
- ✅ Positioning (kiting, retreating when low health)
- ✅ Ability usage (dash to escape, AOE when grouped)
- ✅ Configuration options (aggressiveness, preferred range, etc.)

**Usage:**
```typescript
import { smartAutoplaySystem } from './game/systems/SmartAutoplaySystem';

// Enable AI
smartAutoplaySystem.enable();

// Or toggle with F9 in-game
```

### 2. SimulationManager (`src/game/systems/SimulationManager.ts`)
**Status: Working**

Headless game runner for high-speed simulation:
- ✅ Runs game without rendering
- ✅ Configurable speed (1x to 100x)
- ✅ Tracks results (waves, kills, DNA, evolutions)
- ✅ End conditions (max time, max wave, death)
- ✅ Smart AI integration

**Usage:**
```typescript
import { SimulationManager } from './game/systems/SimulationManager';

const sim = new SimulationManager({
  maxDuration: 600,  // 10 minutes
  maxWave: 20,
  speed: 100,        // 100x speed
  useSmartAI: true,
});

const result = await sim.runSimulation();
```

### 3. SimulationPanel UI (`src/game/ui/SimulationPanel.tsx`)
**Status: Working**

In-game simulation control panel:
- ✅ Run single simulation
- ✅ Run batch simulations (10, 50, 100 runs)
- ✅ Configure parameters (speed, duration, waves)
- ✅ Toggle Smart AI
- ✅ View results summary
- ✅ Access from game menu

**Access:** Open menu → "Simulation Lab" button

### 4. SimulationDashboard (`src/game/ui/SimulationDashboard.tsx`)
**Status: Working**

Analytics dashboard for simulation results:
- ✅ Overview charts (survival rate, performance)
- ✅ DNA analysis (type distribution, correlation)
- ✅ Evolution path tracking
- ✅ Balance recommendations
- ✅ Sample data generator for testing

**Access:** Open menu → "Analytics Dashboard" button

### 5. SimulationAnalyzer (`src/game/systems/SimulationAnalyzer.ts`)
**Status: Working**

Data processing engine:
- ✅ Statistical analysis
- ✅ Balance recommendations
- ✅ Difficulty curve analysis
- ✅ DNA type effectiveness
- ✅ Evolution path popularity

### 6. SimulationLogger (`src/game/systems/SimulationLogger.ts`)
**Status: Working**

Structured file logging with sessions:
- ✅ Session-based logging with unique IDs
- ✅ Log rotation and compression
- ✅ Multiple log levels (DEBUG, INFO, WARN, ERROR, METRIC)
- ✅ Async file output to `simulation_results/`
- ✅ Session statistics aggregation

**Usage:**
```typescript
import { simulationLogger } from './game/systems/SimulationLogger';

// Start a session
const sessionId = simulationLogger.startSession({ batchSize: 100 });

// Log results
simulationLogger.logResult(result);

// End session
simulationLogger.endSession();
```

### 7. SimulationMetrics (`src/game/systems/SimulationMetrics.ts`)
**Status: Working**

Real-time metrics collection and analytics:
- ✅ Per-frame snapshot recording
- ✅ Batch metrics aggregation
- ✅ Balance reports (DNA types, evolution paths, difficulty curve)
- ✅ Comparative analysis (before/after)
- ✅ CSV export for external analysis

**Usage:**
```typescript
import { simulationMetrics } from './game/systems/SimulationMetrics';

// Start session
simulationMetrics.startSession(sessionId);

// Record snapshots during simulation
simulationMetrics.recordSnapshot({
  timestamp: Date.now(),
  gameTime: 120,
  wave: 5,
  playerHealth: 80,
  // ... more fields
});

// End and get metrics
const snapshots = simulationMetrics.endSession(result);

// Generate reports
const report = simulationMetrics.generateBalanceReport(sessions);
```

### 8. SimulationReplay (`src/game/systems/SimulationReplay.ts`)
**Status: Working**

Deterministic replay recording and playback:
- ✅ Frame-by-frame state capture
- ✅ LocalStorage persistence
- ✅ Replay metadata (duration, waves, score, success)
- ✅ Compression for storage efficiency

**Usage:**
```typescript
import { simulationReplay } from './game/systems/SimulationReplay';

// Start recording
const replayId = simulationReplay.startRecording({
  speed: 100,
  useSmartAI: true,
  maxDuration: 600,
});

// Stop and save
simulationReplay.stopRecording({
  wavesCompleted: 12,
  score: 5000,
  success: true,
});

// Load and play
const replay = simulationReplay.loadReplay(replayId);
```

---

## 📊 Current Simulation Features

### Running Simulations

**Option 1: In-Game (Browser)**
1. Open game menu (ESC)
2. Click "Simulation Lab"
3. Configure settings
4. Click "Run Simulation" or "Run Batch"

**Option 2: Programmatic**
```typescript
const sim = new SimulationManager(config);
const result = await sim.runSimulation();
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `maxDuration` | Max game time (seconds) | 600 |
| `maxWave` | Wave to reach | 20 |
| `speed` | Simulation speed multiplier | 100 |
| `useSmartAI` | Use SmartAutoplaySystem | true |
| `startWave` | Starting wave | 1 |
| `seed` | RNG seed (optional) | random |
| `recordReplay` | Record replay for playback | false |
| `sessionId` | Session ID for grouping runs | undefined |

### Results Collected

```typescript
interface SimulationResult {
  id: string;
  duration: number;
  wavesCompleted: number;
  enemiesKilled: number;
  mutationsPurchased: number;      // NEW: Tracked by AI
  buildingsConstructed: number;    // NEW: Tracked by AI
  score: number;
  dnaAcquired: Record<DNAType, number>;
  evolutionHistory: Array<{ wave: number; path: string }>;
  finalStats: { health, damage, speed, level };
  causeOfDeath?: string;
  success: boolean;
  replayId?: string;               // NEW: If replay was recorded
  sessionId?: string;              // NEW: For session grouping
}
```

---

## 🎯 What's Working Well

1. **Smart AI** - Makes intelligent decisions, survives multiple waves
2. **High-Speed Sim** - Can run 100x real-time
3. **Batch Runs** - Can queue multiple simulations
4. **Data Collection** - Tracks all important metrics
5. **UI Integration** - Easy to use from within game

---

## 🔧 Known Issues & Gaps

### 1. TypeScript Errors (Pre-existing)
- Some unused variables in SmartAutoplaySystem
- Type mismatches in simulation code
- **Does not affect runtime functionality**

### 2. Missing Features
- ❌ Command-line batch runner (Node.js script)
- ❌ Overnight simulation mode
- ❌ CSV/JSON export from UI
- ❌ Regression testing (compare builds)

### 3. AI Enhancements (Completed)
- ✅ **Evolution Strategy** - Multi-factor scoring (DNA match, stat synergy, purity, generation)
- ✅ **Mutation Purchasing** - Auto-buy with priority (purity → stability → resistance)
- ✅ **Building Placement** - Strategic walls/towers/shrines based on health/enemies/resources

---

## 🚀 Quick Start Guide

### Run a Single Simulation
```typescript
import { simulationManager } from './game/systems/SimulationManager';

const result = await simulationManager.runSimulation();
console.log(`Survived ${result.wavesCompleted} waves`);
console.log(`Killed ${result.enemiesKilled} enemies`);
```

### Run Batch Analysis
```typescript
const results: SimulationResult[] = [];

for (let i = 0; i < 100; i++) {
  const result = await simulationManager.runSimulation();
  results.push(result);
}

// Analyze
const survivalRate = results.filter(r => r.success).length / results.length;
const avgWaves = results.reduce((a, r) => a + r.wavesCompleted, 0) / results.length;
```

### Use the UI
1. Start game: `./run.sh`
2. Open menu (ESC or P)
3. Click "Simulation Lab"
4. Adjust settings
5. Click "Run Batch (10)"
6. Watch results populate
7. Click "Open Dashboard" for analytics

---

## 📈 Recommended Next Steps

### ✅ Completed
- TypeScript errors fixed - strict mode enabled
- Enhanced AI with evolution, mutation, and building strategies
- Simulation infrastructure (logging, metrics, replays)

### Priority 1: CLI Tool
Create a Node.js script for overnight batch runs:
```bash
npm run sim:batch -- -n 1000 -o results.json
```

### Priority 2: Regression Testing
Compare simulation results between builds to catch balance regressions.

### Priority 3: Visualization
- Replay playback in UI
- Real-time metrics graphs during simulation
- Heatmaps of player death locations

### Priority 4: Advanced Analytics
- Machine learning model training on simulation data
- Predictive balance analysis
- Automatic difficulty adjustment recommendations

---

## 📊 Example Output

```json
{
  "id": "sim_1707421234567_abc123",
  "duration": 245.3,
  "wavesCompleted": 12,
  "enemiesKilled": 87,
  "mutationsPurchased": 5,
  "buildingsConstructed": 3,
  "score": 3240,
  "dnaAcquired": {
    "GRASS": 15,
    "VOID": 8,
    "BEAST": 22
  },
  "evolutionHistory": [
    { "wave": 3, "path": "sprout", "name": "Sprout" },
    { "wave": 8, "path": "shambler", "name": "Shambler" }
  ],
  "finalStats": {
    "health": 45,
    "maxHealth": 120,
    "damage": 35,
    "speed": 140,
    "level": 8
  },
  "causeOfDeath": "Overwhelmed by enemies",
  "success": false,
  "replayId": "replay_1707421234567_def456",
  "sessionId": "session_1707421000000_ghi789"
}
```

---

**Status:** Simulation system is functional and ready for use! 🎉
