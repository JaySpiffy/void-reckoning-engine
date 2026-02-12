---
description: Add a new game system with proper logging and tests
---

# New System Workflow

Standard process for adding new game systems.

## Steps

1. **Create System File**
   - Location: `src/game/systems/[SystemName].ts`
   - Export singleton: `export const systemName = new SystemName();`
   - Import LogManager: `import { logger, LogCategory } from '../managers/LogManager';`

2. **Add Export to Index**
   - Update `src/game/systems/index.ts`

3. **Integrate with GameManager**
   - Add system reference in `GameManager.ts`
   - Call system in appropriate lifecycle method (`update`, `render`, etc.)

4. **Create Test**
   - Location: `tests/[system-name].spec.ts`
   - Follow pattern from `tests/autoplay.spec.ts`

5. **Verify**
```bash
npm run build && npx playwright test --workers=1
```

// turbo
6. **Commit**
```bash
git add . && git commit -m "feat: add [SystemName]"
```

## Logging Standards

```typescript
// At system initialization
logger.info(LogCategory.SYSTEM, '[SystemName] initialized');

// In update loops (sparingly)
logger.debug(LogCategory.GAMEPLAY, '[SystemName] update', { entityCount });

// On errors
logger.error(LogCategory.SYSTEM, '[SystemName] failed', { error });
```
