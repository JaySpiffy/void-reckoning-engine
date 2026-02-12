---
description: Full integration testing before major releases
---

# Integration Testing Workflow

Run comprehensive tests before merges or releases.

## Steps

// turbo-all

1. **Clean Build**
```bash
rm -rf dist && npm run build
```

2. **Run All Tests**
```bash
npx playwright test --workers=1
```

3. **Check Console Logs**
```bash
cat test-results/screenshots/console-logs.txt
```

4. **Verify No Errors**
- Errors should be 0
- Only expected logs (vite connection, React DevTools info)

5. **Visual Regression (Optional)**
```bash
ls -la test-results/screenshots/
```

## Integration Checklist

Before merge/release, verify:

- [ ] Build passes with no warnings
- [ ] All tests pass (9/9 currently)
- [ ] No console errors in logs
- [ ] No `console.log` statements in code
- [ ] New features have tests
- [ ] Documentation updated (if API changed)

## Quick Command
```bash
npm run build && npx playwright test --workers=1 && echo "✅ Ready for merge!"
```
