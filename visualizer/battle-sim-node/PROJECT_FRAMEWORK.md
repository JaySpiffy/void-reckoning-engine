# Fantasy Zombs - Project Framework

## CRITICAL RULES - READ BEFORE ANY CHANGES

### 1. File Import Hierarchy (NEVER BREAK THIS)
```
Level 0: types/core.ts, systems/DNACore.ts (NO IMPORTS ALLOWED)
Level 1: types/abilities.ts, types/index.ts, systems/EvolutionTree.ts
Level 2: entities/, systems/ (except DNASystem), utils/
Level 3: systems/DNASystem.ts, managers/
Level 4: ui/, App.tsx
```

**NEVER create circular imports. If TypeScript builds but runtime fails with "undefined", you have a circular import.**

### 2. Before Making Any Changes
1. Read the file you're about to edit completely
2. Check all files that import from it
3. Ensure your changes don't break the import hierarchy
4. Run `npm run build` before deploying

### 3. Type Safety Requirements
- NEVER use `any` type in new code
- ALWAYS define return types for public methods
- ALWAYS use strict TypeScript checks
- If you see `@ts-ignore`, remove it and fix properly

### 4. System Architecture

#### Combat System
- Player shoots projectiles on mouse hold (SHMUP style)
- Projectiles have collision detection
- Enemies have health and take damage
- Damage numbers appear on hit

#### Ability System
- Slot 1: Basic attack (auto-fire on mouse hold)
- Slots 2-5: Special abilities (cooldown-based)
- Tooltips show on hover

#### Evolution System
- DNA absorbed from killed enemies
- Evolution paths unlock based on DNA + kills + time
- 3 tiers per DNA type (Base → Stage 1 → Stage 2)

### 5. Testing Checklist Before Deploy
- [ ] `npm run build` passes with no errors
- [ ] Player can move with WASD
- [ ] Player can shoot by holding mouse
- [ ] Enemies spawn and take damage
- [ ] Enemies die when health reaches 0
- [ ] Game doesn't crash on start/restart
- [ ] No console errors

### 6. Common Mistakes to Avoid

**DON'T:**
- Import from `./index` in files that are re-exported from index
- Create circular dependencies between systems
- Use runtime values before they're defined
- Skip type annotations on public APIs
- Deploy without testing the build

**DO:**
- Create separate "Core" files for shared types
- Use explicit type imports: `import type { X } from './file'`
- Test the game actually works after changes
- Keep the UI responsive (no blocking operations)

### 7. File Organization

```
src/game/
├── types/
│   ├── core.ts          # LEVEL 0 - No deps
│   ├── abilities.ts     # LEVEL 1 - Imports core only
│   └── index.ts         # LEVEL 1 - Re-exports
├── systems/
│   ├── DNACore.ts       # LEVEL 0 - No deps
│   ├── EvolutionTree.ts # LEVEL 1 - Imports DNACore
│   ├── DNASystem.ts     # LEVEL 3 - Imports DNACore, EvolutionTree
│   ├── CombatSystem.ts  # LEVEL 2
│   ├── AbilitySystem.ts # LEVEL 2
│   └── ...
├── entities/
│   ├── Entity.ts        # LEVEL 2
│   ├── Player.ts        # LEVEL 2
│   ├── Enemy.ts         # LEVEL 2
│   └── Projectile.ts    # LEVEL 2
├── managers/
│   ├── GameManager.ts   # LEVEL 3
│   └── EntityManager.ts # LEVEL 3
└── ui/
    └── GameUI.tsx       # LEVEL 4
```

### 8. Debugging Tips

**If you see "Cannot read properties of undefined":**
1. Check for circular imports
2. Check import order (is the value defined before use?)
3. Check if enum is being used before module loads

**If build passes but game doesn't work:**
1. Check browser console for errors
2. Verify all singletons are properly initialized
3. Check event listeners are set up

### 9. Performance Guidelines
- Use object pooling for particles/projectiles
- Don't create new objects in update loops
- Use `requestAnimationFrame` for rendering
- Limit collision checks with spatial partitioning

### 10. Documentation Requirements
- Add JSDoc comments to all public methods
- Explain "why" not just "what"
- Document any non-obvious behavior
