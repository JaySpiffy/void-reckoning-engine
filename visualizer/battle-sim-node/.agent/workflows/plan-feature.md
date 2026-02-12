---
description: Plan a new feature before implementation
---

# Feature Planning Workflow

**ALWAYS run this workflow before implementing any new feature.**

## Pre-Implementation Checklist

Before writing ANY code, complete these steps:

### 1. Understand the Request
- [ ] Can I restate the feature in one sentence?
- [ ] What files will be affected?
- [ ] Are there similar patterns already in the codebase?

### 2. Research Existing Code
```bash
# Search for related patterns
grep -r "similar_keyword" src/
```

### 3. Design the Solution
Create a brief plan with:
- **Files to modify**: List existing files
- **Files to create**: List new files with paths
- **Dependencies**: What imports are needed?
- **Edge cases**: What could go wrong?

### 4. Write Tests First (TDD)
// turbo
```bash
npx playwright test tests/[feature].spec.ts --workers=1
```
- Test should FAIL initially (no implementation yet)

### 5. Implement Incrementally
- Make smallest possible change
- Verify after each change:
// turbo
```bash
npm run build
```

### 6. Integration Check
// turbo
```bash
npx playwright test --workers=1
```

## Decision Tree

```
Is this a NEW system?
├─ Yes → Use /new-system workflow
└─ No → Is this modifying existing behavior?
         ├─ Yes → Write regression test FIRST
         └─ No → Is this a bug fix?
                  ├─ Yes → Reproduce in test, then fix
                  └─ No → Document change in commit message
```

## Anti-Patterns to Avoid

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Big bang changes | Small, verified increments |
| `console.log` debugging | Use `LogManager` |
| Magic numbers | Extract to constants |
| `any` type | Define proper interfaces |
| `setTimeout` in game logic | Use `deltaTime` timers |
| Skipping tests | Always verify before commit |
