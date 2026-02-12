# Priority 2: AI Enhancement Plan

## Overview
Enhance the SmartAutoplaySystem to play more intelligently, making better decisions about evolution, mutations, building, and combat.

---

## Phase 1: Evolution Strategy (2-3 hours) ✅ COMPLETE

### Current State
AI picks evolution paths by matching dominant DNA type only.

### Target State
AI analyzes:
- Current DNA distribution
- Stat bonuses vs current needs
- Path synergies
- Wave progression

### Implementation

```typescript
interface EvolutionStrategy {
  // Score evolution paths based on multiple factors
  scorePath(path: EvolutionPath, genome: Genome): number;
  
  // Consider current game state
  considerWave(wave: number): void;
  
  // Check if evolution is beneficial now
  shouldEvolveNow(): boolean;
}
```

### Files to Modify
- `src/game/systems/SmartAutoplaySystem.ts`

### Testing
- Run 50 simulations before/after
- Compare average waves survived
- Track evolution choices

---

## Phase 2: Mutation Purchasing (2 hours) ✅ COMPLETE

### Current State
AI doesn't buy mutations.

### Target State
AI auto-buys mutations when beneficial:
- DNA stabilization when corrupted
- Purity increase for dominant type focus
- Randomize DNA when stuck

### Implementation

```typescript
interface MutationStrategy {
  // Evaluate if mutation is worth buying
  evaluateMutation(type: MutationType): number; // 0-100 score
  
  // Check mutation points efficiency
  getBestMutation(): MutationType | null;
  
  // Auto-purchase on interval
  checkAndBuyMutations(): void;
}
```

### Files to Modify
- `src/game/systems/SmartAutoplaySystem.ts`
- `src/game/systems/MutationSystem.ts` (minor)

### Testing
- Track mutation purchases per game
- Compare DNA stability (corruption levels)

---

## Phase 3: Building AI (2-3 hours) ✅ COMPLETE

### Current State
AI has building disabled (`autoBuild: false`).

### Target State
AI builds strategically:
- Walls at choke points
- Towers near player for defense
- Healing shrines when health is low
- Resource generators early game

### Implementation

```typescript
interface BuildingStrategy {
  // Find optimal build position
  findBuildPosition(type: BuildingType): Vector2 | null;
  
  // Prioritize what to build
  getBuildPriority(): BuildingType[];
  
  // Check resources and necessity
  shouldBuildNow(): boolean;
}
```

### Files to Modify
- `src/game/systems/SmartAutoplaySystem.ts`
- `src/game/systems/BuildingSystem.ts` (minor)

### Testing
- Count buildings per game
- Measure defensive effectiveness
- Track resource efficiency

---

## Phase 4: Combat Improvements (2 hours) - Future Enhancement

### Current State
AI has basic targeting and ability usage.

### Target State
AI uses advanced tactics:
- Ability combos (freeze → dash)
- AOE positioning
- Kiting strategy refinement
- Wave-specific tactics

### Implementation

```typescript
interface CombatStrategy {
  // Advanced ability combos
  checkAbilityCombos(): void;
  
  // Position for AOE
  calculateAOEPosition(): Vector2;
  
  // Wave-specific behavior
  adaptToWave(wave: number, enemyTypes: EnemyType[]): void;
}
```

### Files to Modify
- `src/game/systems/SmartAutoplaySystem.ts`

### Testing
- Compare damage output
- Measure health efficiency
- Track ability usage patterns

---

## Implementation Order

### Hour 1-2: Evolution Enhancement
1. Create evolution scoring system
2. Add stat analysis
3. Test and tune

### Hour 3: Mutation Purchasing
1. Add mutation evaluation
2. Auto-purchase logic
3. Integration with SmartAutoplaySystem

### Hour 4-5: Building AI
1. Position finding algorithm
2. Build priority system
3. Enable autoBuild with conditions

### Hour 6: Combat Polish
1. Ability combos
2. AOE positioning
3. Final testing

---

## Success Criteria

| Metric | Before | Target |
|--------|--------|--------|
| Avg Waves Survived | ~8 | 15+ |
| Avg Evolutions | ~1 | 2+ |
| Avg Mutations | 0 | 3+ |
| Avg Buildings | 0 | 3+ |
| Avg Score | ~2000 | 4000+ |

---

## Testing Protocol

For each phase:

```bash
# Run 100 simulations
# In-game: Simulation Lab → Run Batch (100)

# Collect metrics:
# - Average waves survived
# - Average score
# - Evolution choices
# - Mutation purchases
# - Buildings constructed
# - Cause of death distribution
```

---

## File Structure

```
src/game/systems/
├── SmartAutoplaySystem.ts      # Main AI (enhance)
├── MutationSystem.ts            # Minor updates
├── BuildingSystem.ts            # Minor updates
└── SimulationManager.ts         # For testing

New files (if needed):
├── strategies/
│   ├── EvolutionStrategy.ts
│   ├── MutationStrategy.ts
│   └── BuildingStrategy.ts
```

---

## Notes

- Keep changes modular (easy to disable)
- Add configuration options
- Log AI decisions for debugging
- Maintain backward compatibility (toggle old/new AI)
