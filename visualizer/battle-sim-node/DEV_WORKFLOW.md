# Quick Development Workflow

## 🚀 Quick Start Commands

### Start Dev Server (Fast Mode)
```bash
npm run dev:quick
```
Skips type checking for fastest startup.

### Restart Dev Server
```bash
npm run dev:restart
```
Kills existing server and starts fresh.

### Standard Dev Server
```bash
npm run dev
```
Full startup with type checking.

---

## 🧪 Testing Commands

### Run All Tests (Headless)
```bash
npm run test:headless
```
Fast, no UI - perfect for CI.

### Run Tests with UI
```bash
npm test
# or
npm run test:ui
```
See browser interactions.

### Debug Tests
```bash
npm run test:debug
```
Step through tests.

---

## ✅ Validation Commands

### Full Validation (Before Commit)
```bash
npm run validate
```
Runs: type-check → lint → build test

### Individual Checks
```bash
npm run type-check    # TypeScript only
npm run lint          # ESLint only
npm run build         # Build test
```

---

## 🔄 Development Loop

### Quick Edit-Test Cycle
1. **Make changes** to code
2. **Refresh browser** - Vite hot reloads automatically
3. **Check console** for errors

### Before Committing
1. **Run validation**:
   ```bash
   npm run validate
   ```
2. **Run tests**:
   ```bash
   npm run test:headless
   ```
3. **Commit** if all pass

---

## 🎯 When to Refresh localhost:5173

**Vite has Hot Module Replacement (HMR)** - most changes auto-reload!

### Manual Refresh Needed When:
- Adding new files
- Changing TypeScript types that affect many files
- Console shows "[vite] hot updated" but behavior seems off
- After running `npm install`

### Auto-Reloads (No Refresh Needed):
- Component JSX changes
- CSS/style changes
- Most game logic changes
- Hook modifications

---

## 📊 Testing Simulation Mode

1. **Open Debug Panel**: Press `F10`
2. **Open Simulation Lab**: Click "🧪 Simulation Lab" button
3. **Configure**: Set duration, waves, speed
4. **Run**: Click "▶ Run Single Simulation"
5. **View Results**: See stats in real-time

---

## 🐛 Debugging Tips

### Check for Errors
```bash
# Browser console errors
# Look for red text in browser dev tools

# Type errors
npm run type-check

# Lint errors
npm run lint
```

### Common Issues

**Port already in use:**
```bash
npm run dev:restart
```

**Type errors not showing:**
```bash
npm run type-check
```

**Cache issues:**
```bash
rm -rf node_modules/.vite
npm run dev:restart
```

---

## 📝 Git Workflow

### Before Committing
```bash
npm run validate    # Check everything
npm run test        # Run tests
git add -A
git commit -m "feat: description"
```

### Bypass Hooks (Emergency Only)
```bash
git commit -m "fix: urgent fix" --no-verify
```

---

## 🎮 Game Controls (Testing)

| Key | Action |
|-----|--------|
| WASD | Move |
| Mouse | Aim/Shoot |
| F9 | Toggle Autoplay |
| F10 | Debug Panel |
| T | Element Evolution |
| Y | DNA Evolution |
| M | Mutation Shop |
| ESC/P | Pause |

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/game/systems/SimulationManager.ts` | Simulation engine |
| `src/game/systems/SmartAutoplaySystem.ts` | Smart AI |
| `src/game/ui/SimulationPanel.tsx` | Simulation UI |
| `src/game/managers/GameManager.ts` | Main game loop |
| `src/App.tsx` | Entry point |

---

*Last updated: 2026-02-06*
