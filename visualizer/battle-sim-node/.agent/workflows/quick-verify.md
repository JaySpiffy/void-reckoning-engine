---
description: Quick verification without committing
---

# Quick Verify Workflow

Fast verification for iterative development.

## Steps

// turbo-all

1. **Build Only**
```bash
npm run build
```

2. **Run Specific Test**
```bash
npx playwright test tests/game.spec.ts --workers=1
```

## When to Use
- After making small changes
- Before committing
- When adding new features
