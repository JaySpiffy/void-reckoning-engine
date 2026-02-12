# 🏈 Last Hit Blitz

**Branch:** `last-hit-blitz`  
**Type:** Fork/Experimental Game Mode  
**Goal:** Teach coding through building a Madden/FIFA-style football simulation

---

## Concept

Transform the survival RPG into a football simulation where:
- **Characters/Mobs** → Football Players (11 per team)
- **DNA Types** → Player Archetypes/Positions
- **Stats** → FIFA Ultimate Team style (0-100 ratings)
- **Combat** → Football plays with random outcomes
- **Evolution** → Player development/training

---

## Architecture Strategy

### Shared Code (with main branch)
- Core entity system (`Entity.ts`, base classes)
- Utility functions (`Vector2.ts`, `IdGenerator.ts`)
- UI components (Button, Panel, modals)
- Event system (`EventEmitter.ts`)
- Build system, config, types infrastructure

### Football-Specific Code (this branch only)
- `src/football/` - New directory for all football logic
- Player stats system (FIFA-style ratings)
- Play simulation engine
- Match/season management
- Football field rendering
- Team management UI

### Modified Shared Code
- `src/game/types/` - Extend types to support football mode
- Entry point (`App.tsx`) - Mode selection (Survival vs Football)

---

## Core Systems to Build

### 1. Player Rating System (FIFA Style)
```typescript
interface FootballStats {
  // Physical
  pace: number;           // 0-100
  acceleration: number;
  stamina: number;
  strength: number;
  
  // Offensive
  passing: number;        // Accuracy
  deepBall: number;       // Long passes
  throwPower: number;     // QB specific
  
  // Ball Skills
  catching: number;
  routeRunning: number;   // Getting open
  ballSecurity: number;   // Fumble chance
  
  // Defensive
  tackling: number;
  coverage: number;       // Pass defense
  passRush: number;       // Getting to QB
  
  // Mental
  awareness: number;      // Read plays, react
  clutch: number;         // Performance under pressure
}
```

### 2. Position System
```typescript
type Position = 
  | 'QB'   // Quarterback
  | 'RB'   // Running Back  
  | 'WR'   // Wide Receiver
  | 'TE'   // Tight End
  | 'OL'   // Offensive Line
  | 'DL'   // Defensive Line
  | 'LB'   // Linebacker
  | 'CB'   // Cornerback
  | 'S'    // Safety
  | 'K'    // Kicker
  | 'P';   // Punter
```

### 3. Play Simulation Engine
- Play selection (Run, Pass, Special Teams)
- Matchup resolution (player stats vs player stats)
- Random outcome generation with stat-weighted probabilities
- Chain of events (Snap → Blocking → Route Running → Throw → Catch/Tackle/INT)
- Yardage calculation

### 4. Game Flow
- Kickoff → Drives → Scoring → Possession change
- 4 quarters, clock management
- Score tracking
- Play-by-play log

---

## Teaching Opportunities

1. **Entity-Component-System pattern** - How players interact
2. **Probability/Weighted Random** - How stats affect outcomes
3. **State Machines** - Game flow (pre-snap → play → post-play)
4. **Data Structures** - Roster management, playbooks
5. **Algorithms** - Matchup resolution, AI play calling
6. **UI/UX** - Real-time simulation display, stat visualization

---

## File Structure

```
src/
├── football/
│   ├── entities/
│   │   ├── FootballPlayer.ts      # Extends Entity with football stats
│   │   ├── Team.ts                # 11 players + management
│   │   └── Ball.ts                # Football entity
│   ├── systems/
│   │   ├── PlayEngine.ts          # Core play simulation
│   │   ├── MatchupResolver.ts     # 1v1 stat comparisons
│   │   ├── GameClock.ts           # Time management
│   │   ├── SeasonManager.ts       # Multi-game seasons
│   │   └── DraftSystem.ts         # Player generation
│   ├── data/
│   │   ├── Playbook.ts            # Available plays
│   │   ├── PlayerArchetypes.ts    # Position templates
│   │   └── Names.ts               # Random name generation
│   ├── ui/
│   │   ├── FootballGameUI.tsx     # Main game screen
│   │   ├── PlayCallPanel.tsx      # Choose your play
│   │   ├── MatchupVisualizer.tsx  # Show key matchups
│   │   ├── PlayerCard.tsx         # FIFA-style stat card
│   │   ├── SeasonDashboard.tsx    # League standings
│   │   └── DraftScreen.tsx        # Player drafting
│   └── types/
│       └── football.ts            # Football-specific types
├── game/                          # Original survival game (preserved)
└── App.tsx                        # Mode selector entry point
```

---

## Getting Started (Teaching Path)

### Lesson 1: Player Creation
- Create `FootballPlayer` class
- Generate random players with stats
- Display FIFA-style player cards

### Lesson 2: Single Matchup
- 1v1: WR vs CB
- Stat comparison logic
- Outcome: Catch, Incompletion, Interception

### Lesson 3: Full Play
- QB → WR chain
- Pass rush affecting throw
- Blocking giving time

### Lesson 4: Full Drive
- Series of plays
- Down/distance tracking
- Scoring

### Lesson 5: Full Game
- Two teams
- Full rules (kickoffs, punts, field goals)
- Clock management

---

*Last Hit Blitz - Where Evolution Meets the End Zone*
