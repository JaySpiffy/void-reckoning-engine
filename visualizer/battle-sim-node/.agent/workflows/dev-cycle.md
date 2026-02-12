---
description: Full development cycle - build, test, verify, commit
---

# Development Workflow

This workflow runs the complete development cycle for Darwin's Island ReHelixed.

## Steps

// turbo-all

1. **Type Check**
```bash
npx tsc --noEmit
```

2. **Lint**
```bash
npm run lint -- --max-warnings=0
```

3. **Build**
```bash
npm run build
```

4. **Run Tests (Single Worker for WSL2 stability)**
```bash
npx playwright test --workers=1
```

5. **Commit Changes** (if all above pass)
```bash
git add . && git commit -m "chore: automated development cycle"
```

## Auto-Recovery

If tests fail:
1. Check `test-results/` for screenshots
2. Review `test-results/screenshots/console-logs.txt`
3. Fix issues and re-run workflow
