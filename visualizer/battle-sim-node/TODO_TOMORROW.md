# Tomorrow's TODO - Darwin's Island ReHelixed

## Priority 1: AI Simulations & Automated Testing

### Better Autoplay AI
- [ ] Implement "Simulation Mode" - AI plays entire game automatically
  - Auto-evolve when paths available
  - Auto-buy mutations
  - Auto-build structures
  - Auto-select best abilities
- [ ] Add simulation speed controls (1x, 5x, 10x, 50x speed)
- [ ] Generate simulation reports:
  - Average survival time
  - Most popular evolution paths
  - DNA accumulation rates
  - Enemy kill counts

### Headless Simulation Runner
- [ ] Create Node.js simulation script (no browser needed)
- [ ] Run 100+ simulations overnight
- [ ] Collect statistics on:
  - Balance (which DNA types are too strong/weak)
  - Evolution path popularity
  - Difficulty curve (when do players usually die)
  - Loot drop rates
- [ ] Export results to JSON/CSV for analysis

### AI Behavior Improvements
- [ ] Smarter enemy targeting (prioritize dangerous enemies)
- [ ] Better positioning (kite enemies, avoid corners)
- [ ] Ability usage strategy (save cooldowns for waves)
- [ ] Evolution choice AI (pick optimal paths based on current DNA)

---

## Priority 2: Lua Components Standardization

### Audit Existing Lua Components
- [ ] Find all `.lua` files in the project
- [ ] Document what each Lua component does
- [ ] Identify which are:
  - Still needed
  - Deprecated/outdated
  - Duplicated
  - Need porting to TypeScript

### Standardization Tasks
- [ ] Create Lua → TypeScript migration guide
- [ ] Standardize naming conventions
- [ ] Extract common Lua utilities into shared modules
- [ ] Add type definitions for Lua interfaces
- [ ] Document Lua/TS interoperability layer

### Lua Files to Review
- [ ] Config files (should they be JSON/TOML instead?)
- [ ] Entity definitions
- [ ] Behavior scripts
- [ ] Effect systems
- [ ] Any game logic still in Lua

---

## Priority 3: Balance & Polish (If Time Permits)

### Balance Testing
- [ ] Review DNA gain rates (too fast/slow?)
- [ ] Check evolution requirements (too easy/hard?)
- [ ] Test late-game difficulty (waves 20+)
- [ ] Verify all evolution paths are reachable

### UI Polish
- [ ] Add loading screen
- [ ] Better error handling/display
- [ ] Sound effects for evolution, loot drops
- [ ] Particle effects for DNA absorption

---

## Notes

**Simulation Mode Purpose:**
- Test 1000s of game sessions automatically
- Find balance issues without manual play
- Generate data for balancing decisions
- Validate that all content is accessible

**Lua Standardization Purpose:**
- Consistent codebase (TS vs Lua)
- Easier maintenance
- Better IDE support
- Type safety

---

*Created: 2026-02-05*
