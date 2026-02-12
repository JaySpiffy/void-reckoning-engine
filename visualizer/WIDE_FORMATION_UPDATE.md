# Wide Formations & Protoss-Style Carriers ✅

## 🎯 Major Changes

### 1. Much Wider Formations
- **Spacing**: 80px between units (was 35px)
- **Start distance**: 600px apart (was ~200px)
- **Formation width**: Shallower rows, more spread out
- **Result**: Units don't pile up anymore!

### 2. 3x Longer Attack Ranges
- **Ranged units**: 3x range (can shoot from much further)
- **Melee units**: 1.5x range
- Titans and heavy units can attack from across the battlefield

### 3. Protoss-Style Interceptors (Deployment Ships)
Carrier-type units (Titans, heavy ranged) now launch small attack drones!

**Interceptor Features:**
- 🛸 Small glowing drones orbit their parent ship
- ⚔️ Automatically attack nearby enemies
- 🔄 Every 2 seconds, new drones launch
- 💀 Die in one hit (fragile)
- 🎯 Orbit around targets when attacking

**Visuals:**
- Glowing body with cyan/purple color
- Red ring when attacking
- Trail effect while moving

### 4. Extreme Anti-Stacking
- **Separation distance**: 3x unit radius
- **Push strength**: 3x overlap force
- Units will NOT stand on top of each other

## 🎮 New Combat Flow

```
Before:                    After:
████████████              █  █  █  █
████████████      →       █  █  █  █
████████████              █  █  █  █
(units stacked)           (spread out)
                          🛸🛸 (interceptors flying)
```

## 📊 Unit Behavior

**Formation Layout:**
- Wide rectangular formations
- Stronger units in back rows
- 600px gap between teams at start

**Combat:**
- Ranged units engage from far away
- Carriers launch interceptors continuously
- Interceptors swarm enemies
- Melee units charge in after
- No stacking - everyone has personal space

**Interceptor Spawning:**
- Titans: Launch every 2 seconds
- Heavy weapon platforms: Launch every 2 seconds
- Max lifetime: 15 seconds per interceptor
- Auto-replace when they die

## 🎨 Visual Updates

**Left Panel:**
- Shows interceptor count per team
- "🛸 Drones: 12" indicator

**Battlefield:**
- Spread out formations visible
- Interceptors orbiting carriers
- Long-range laser fire
- No more unit pile-ups

## 🚀 How to Test

**http://localhost:5173**

1. Click **"Config"** tab
2. Set Team Size to 30-50 (for clearer view)
3. Click **Apply & Reset**
4. Click **Start Battle**
5. Watch:
   - Units spread out in wide formations
   - Titans launch interceptors (glowing dots)
   - Long-range combat from distance
   - No stacking!

## ⚔️ Dynamic Combat Achieved!

No more 100 guys standing on top of each other!
