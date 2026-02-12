# AI Development & Workflow Automation Strategies

This document outlines strategies to enhance automated AI code generation, development workflows, logging, and general automation for the **Darwin's Island ReHelixed** project.

## 1. AI Code Generation & Context Awareness

To get the best out of AI coding assistants, **Context is King**.

### **Persistent Context Files**
- **Architecture Decision Records (ADRs)**: Maintain a folder `docs/adr` where significant architectural choices are logged. AI agents can read this to understand *why* things are the way they are.
- **`AI_CONTEXT.md`**: A single source of truth for high-level project goals, tech stack rules (e.g., "Always use functional components"), and current active objectives. This can be fed into the AI context window at the start of sessions.
- **Rule Files**: Utilize `.cursorrules` or similar configuration files to enforce coding standards (e.g., "No default exports", "Use strong typing for all interfaces") automatically during generation.

### **Prompt Engineering for Code Generation**
- **"Chain of Thought" Templates**: Create templates for complex tasks that force the AI to:
  1.  Analyze the request.
  2.  List affected files.
  3.  Propose a plan.
  4.  Execute.
  5.  Verify.

## 2. Automated Testing & Verification

Shift verification left—make the AI (and CI) check work immediately.

### **Self-Validating Agents**
- **Test-Driven Generation**: Ask the AI to write the *test* first (e.g., specific Playwright spec), run it (it fails), then write the code to pass it.
- **Bot Integration Tests**: Expand the **Autoplay System** (F9) into a headless verification bot.
  - *Idea*: Use the Autoplay logic in a GitHub Action to play the game for 5 minutes. If the "Game Over" screen is reached or FPS drops below 30, fail the build.

### **Visual Regression Automation**
- Use **Argos** or **Percy** (or continue with Playwright's persistent snapshots) to auto-detect UI changes. AI can often break styles; these tools catch that instantly.

## 3. Advanced Logging & Observability

`console.log` is insufficient for complex AI debugging.

### **Structured Logging System**
- Replace direct console calls with a semantic logger (e.g., `LogManager`).
- **Features**:
  - **Levels**: DEBUG, INFO, WARN, ERROR.
  - **Categories**: `[Combat]`, `[Input]`, `[AI]`.
  - **Context**: Attach entity IDs or frame numbers to every log.
  - **Exfiltration**: In dev, logs render to the console. In CI/Headless, logs are written to a file artifact (JSON format) for parsing.

### **Performance Telemetry**
- Implement a `TelemetrySystem` that tracks:
  - Average FPS over 10s intervals.
  - Entity count.
  - Memory usage (if available).
- Failsafe: If FPS < 30 for 3 consecutive seconds, auto-trigger a "Performance Snapshot" (dump current state to JSON) for AI analysis.

## 4. Workflow Automation (CI/CD++)

Optimize the feedback loop.

### **Git Hooks (`husky`)**
- **Pre-commit**: Run `tsc` (type check) and `eslint`. Don't let the AI commit broken code.
- **Pre-push**: Run unit tests.

### **GitHub Actions Enhancements**
- **Auto-Labeling**: Use an LLM action to label PRs based on file changes (e.g., `area/combat`, `area/ui`).
- **AI Code Review**: Use tools like Codium or customized actions to have an AI review the AI's code (double-check pattern).

## 5. Implementation Roadmap

### Phase 1 (Immediate) ✅ COMPLETE
- [x] Create `LogManager.ts` to replace `console.log`.
- [x] Create `docs/AI_CONTEXT.md`.
- [x] Integrate `LogManager` into `InputSystem`.

### Phase 2 (Next Sprint)
- [ ] Implement "Bot verification" in CI (headless autoplay).
- [ ] Add JSON log artifact upload to CI.
- [ ] Set up `husky` for pre-commit type checking.

### Phase 3 (Future)
- [ ] Build a "Self-Healing" workflow where test failures trigger a new AI agent prompt to fix the error automatically.

---

## 6. Advanced Strategies (Session Learnings)

### **Parallel Test Execution**
- **Problem**: WSL2 + Playwright parallelism causes timeouts due to resource contention.
- **Solution**: Use `--workers=1` in CI or increase timeouts. In `playwright.config.ts`:
  ```typescript
  workers: process.env.CI ? 1 : undefined,
  ```

### **Exposing Game State for Testing**
- **Pattern**: Assign key objects to `window` for Playwright introspection.
  ```typescript
  (window as any).game = gameManager;
  ```
- **Benefit**: Tests can verify internal state (e.g., `window.game.autoplaySystem.isEnabled()`).

### **ESM Compatibility**
- **Pitfall**: `__dirname` doesn't exist in ESM contexts (Vite).
- **Solution**: Use `process.cwd()` or `import.meta.url`.

### **Debug Log Discipline**
- **Rule**: All `console.log` statements must be removed before merge.
- **Enforcement**: Add an ESLint rule (`no-console`) or a pre-commit grep check.

### **AI Agent Memory**
- **Idea**: Persist learnings (like "slow effects need manual cleanup") to `docs/KNOWN_ISSUES.md`.
- **Benefit**: Future agents (or sessions) can reference this to avoid repeating mistakes.

---

## 7. Recommended Tools & Integrations

| Tool | Purpose |
|------|---------|
| **Husky** | Git hooks for pre-commit/pre-push checks |
| **lint-staged** | Run linters only on staged files |
| **Argos / Percy** | Visual regression testing |
| **Codecov** | Track test coverage over time |
| **Sentry** | Runtime error tracking in production |
| **OpenTelemetry** | Distributed tracing for complex systems |

---

## 8. Automated Agent Workflows

The following workflows are available in `.agent/workflows/` for AI-assisted development:

| Workflow | Path | Purpose |
|----------|------|---------|
| **Dev Cycle** | `/dev-cycle` | Full build → test → commit cycle |
| **Quick Verify** | `/quick-verify` | Fast iteration checks |
| **New System** | `/new-system` | Adding game systems with logging |
| **Debug** | `/debug` | Test failure analysis |

### Using Workflows
AI agents can reference these by viewing the workflow file:
```
view_file: .agent/workflows/[workflow-name].md
```

### `// turbo` Annotation
Workflows marked with `// turbo` above a command can be auto-executed by agents without user approval.

---

## 9. Self-Sufficient AI Development Patterns

### Autonomous Code Quality
```
1. Make change
2. Run `npm run build` (type check + bundle)
3. Run `npx playwright test --workers=1` (verification)
4. If fail → analyze error → fix → repeat
5. Commit only when green
```

### Error Recovery Protocol
1. **Build Errors**: Check TypeScript compiler output, fix types
2. **Test Timeouts**: Use `--workers=1`, add explicit waits
3. **Focus Issues**: Add `await page.click('canvas')` before keyboard input
4. **Missing Elements**: Verify selector, check visibility

### Minimizing User Interaction
- **Pre-commit Validation**: Always verify before committing
- **Self-Documenting Changes**: Use clear commit messages
- **Artifact Updates**: Keep `task.md` and `walkthrough.md` current
- **Log Analysis**: Parse captured logs before asking for help

---

## 10. Future Automation Ideas

### Self-Healing CI
```yaml
# Pseudocode for GitHub Action
on: [test_failure]
steps:
  - name: Analyze Error
    run: cat test-results/error.log | llm-analyze
  - name: Generate Fix
    run: llm-generate-fix --context=error.log
  - name: Apply and Verify
    run: git apply fix.patch && npm test
```

### Performance Regression Detection
- Track FPS baseline in CI
- Alert if FPS drops >10% vs main branch
- Auto-bisect to find regressing commit

### Code Coverage Gates
- Require 80%+ coverage for new files
- Block merge if coverage drops


