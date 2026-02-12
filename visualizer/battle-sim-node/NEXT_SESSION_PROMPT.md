# Next Session Prompt

**Copy and paste this into your next session:**

---

```
Continue from SESSION_HANDOFF.md. The simulation infrastructure has been 
committed (Logger, Metrics, Replay systems). Now I need to:

1. Clean up outdated documentation:
   - Delete FOOTBALL_SIMULATION_SUMMARY.md (football moved to separate repo)
   - Delete TODAY_SESSION.md (all football content, outdated)
   - Update AI_ENHANCEMENT_PLAN.md - mark phases 1-3 as complete
   - Update PROJECT_STATUS.md - Priority 2 is done

2. Add unit tests:
   - Create tests/unit/SmartAutoplaySystem.test.ts
   - Create tests/unit/SimulationManager.test.ts
   - Create tests/unit/SimulationInfrastructure.test.ts

3. Validate:
   - npm run type-check (should pass)
   - npm run build (should pass)
   - npm test (should pass)

See SESSION_HANDOFF.md for full context and usage examples.
```

---

## Quick Reference

### Files to Delete
```
FOOTBALL_SIMULATION_SUMMARY.md
TODAY_SESSION.md
```

### Files to Update
```
AI_ENHANCEMENT_PLAN.md      # Mark phases 1-3 complete
PROJECT_STATUS.md           # Priority 2 is done, not "next"
TODO_TOMORROW.md           # Clean up completed items
```

### New Test Files to Create
```
tests/unit/SmartAutoplaySystem.test.ts
tests/unit/SimulationManager.test.ts
tests/unit/SimulationInfrastructure.test.ts
```

---

## Current State Summary

- ✅ TypeScript strict mode - clean build
- ✅ AI Systems complete (evolution, mutation, building)
- ✅ Simulation infrastructure committed
- ⚠️ Documentation has outdated references
- ⚠️ Missing unit tests for AI/simulation
