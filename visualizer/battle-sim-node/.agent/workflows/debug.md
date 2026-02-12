---
description: Debug test failures and analyze logs
---

# Debug Workflow

Process for debugging test failures.

## Steps

1. **Run Failed Test in Debug Mode**
```bash
npx playwright test tests/[test-file].spec.ts --debug
```

2. **Check Screenshots**
```bash
ls -la test-results/
```

3. **Analyze Console Logs**
```bash
cat test-results/screenshots/console-logs.txt
```

4. **Check for Common Issues**
   - [ ] Canvas focus issues (add `await page.click('canvas')`)
   - [ ] ESM compatibility (`__dirname` → `process.cwd()`)
   - [ ] Race conditions (use proper waits)
   - [ ] Resource contention (use `--workers=1`)

5. **Verify Fix**
// turbo
```bash
npm run build && npx playwright test --workers=1
```

## Quick Fixes

| Symptom | Solution |
|---------|----------|
| Timeout on button click | Add `await page.waitForTimeout(500)` |
| Element not found | Check selector, add visibility wait |
| Keyboard not working | Add `await page.click('canvas')` before keys |
| `__dirname` error | Use `process.cwd()` |
