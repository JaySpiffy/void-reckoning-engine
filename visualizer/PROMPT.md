# Node Battle Simulator - Implementation Prompt

## Goal
Transform the survival game at `node-draft/battle-sim-node` into a **50v50 battle simulator**.

## What to Build
A "Totally Accurate Battlegrounds" style battle visualizer where:
- 50 Blue units spawn on the LEFT
- 50 Red units spawn on the RIGHT
- Units auto-fight until one team is eliminated
- Spectator camera (overview, not WASD follow)
- Speed controls (0.5x, 1x, 2x, 5x)
- Start/Pause/Reset controls

## Implementation Plan
See `IMPLEMENTATION_PLAN.md` for detailed file-by-file instructions.

## Key Files to Create
1. `src/types/battle.ts` - Team enum, BattleConfig, BattleStats
2. `src/types/unitTypes.ts` - UnitClass enum, UNIT_STAT_CONFIG
3. `src/game/entities/Unit.ts` - Generic unit (replaces Player/Enemy)
4. `src/game/managers/BattleManager.ts` - Spawns 50v50, tracks victory
5. `src/game/managers/BattleGameManager.ts` - Game loop wrapper
6. `src/game/systems/BattleAISystem.ts` - Find enemy, move, attack
7. `src/components/BattleCanvas.tsx` - Canvas rendering
8. `src/pages/BattlePage.tsx` - Main UI

## Key Files to Modify
1. `src/App.tsx` - Replace with BattlePage
2. Remove: DNASystem, Evolution, Building, Loot (not needed)

## Constraints
- ✅ Use existing Entity base class
- ✅ Use existing CollisionSystem if needed
- ✅ Use existing InputSystem for camera (optional)
- ✅ Keep 60 FPS with 100 units
- ✅ All units are circles (no new assets needed)

## Success Criteria
- [ ] `npm run build` succeeds
- [ ] 50v50 spawns correctly
- [ ] Battle resolves (units die, winner declared)
- [ ] Speed controls work
- [ ] 60 FPS maintained

## Notes
- This is a COPY of the original - modify freely
- Keep code simple and readable
- Don't worry about perfect architecture - just make it work!
