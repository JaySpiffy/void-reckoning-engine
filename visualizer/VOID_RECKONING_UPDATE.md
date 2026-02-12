# Void Reckoning Engine Integration ✅

## 🎯 What's New

### 1. Jayspiffy's Void Engine Data
The simulator now uses **actual unit data** from jayspiffy's Void Reckoning Engine:

**Unit Classes Imported:**
- `line_infantry` - Basic troops (500 HP, 100 entities)
- `assault_marines` - Elite infantry (1000 HP, fearless)
- `battle_tank` - Armored vehicle (2500 HP, ranged)
- `war_titan` - Massive war machine (15000 HP, terror)
- `heavy_weapon_platform` - Artillery (400 HP, 400 ranged attack)
- `assault_brawler_walker` - Walker unit (800 HP, melee focus)
- `advanced_battlesuit` - Powered armor (300 HP, advanced)
- `apocalypse_titan` - God-engine (45000 HP, god_engine)

### 2. Unit Nameplates
Every unit now displays:
- **Role icon** (👑 for titans, 🛡️ for armor, ⚔️ for infantry, etc.)
- **Short name** (e.g., "LI" for Line Infantry)
- **Unit number** (e.g., "#1", "#2")
- **Health bar** (when damaged)

### 3. Detailed Unit Info Panel
Click any unit to see:
```
⚔️ Line Infantry #1
Team: BLUE
HP: 45/50 (90%)
Morale: 58/60
Armor: 30
Damage: 12.5
Range: 25
Speed: 70
Kills: 2
Pos: (245, 380)
Target: #42
```

### 4. Simulation Config System
Easy-to-adjust variables in `SimulationConfig.ts`:

```typescript
SIMULATION_CONFIG = {
    teamSize: 50,              // Units per side
    healthScale: 0.1,          // Global HP multiplier
    damageScale: 0.1,          // Global DMG multiplier
    speedScale: 2.0,           // Movement speed multiplier
    
    availableUnitClasses: [    // Which units to use
        "line_infantry",
        "assault_marines",
        "battle_tank",
        "war_titan"
    ],
    
    showNameplates: true,
    showHealthBars: true,
    showUnitIds: true,
}
```

### 5. Battle Presets
Quick presets for different battle types:
- **Quick**: 20v20, fast combat
- **Standard**: 50v50, balanced
- **Epic**: 100v100, slow and massive
- **Titan**: 10v10, only titans

### 6. Enhanced Tactical Info
**Team Stats Panel shows:**
- Alive / Total count
- Total kills
- Average health %
- Average morale %
- Unit type breakdown (e.g., "5x Line Infantry, 3x Tank")

**Visual indicators:**
- Crown 👑 for winning team
- Morale affects combat effectiveness
- Armor reduces damage
- Selected unit shows range circle
- Hover highlights units

---

## 🎮 Controls

| Action | How |
|--------|-----|
| **Start Battle** | Click "▶ Start" |
| **Pause** | Click "⏸" button |
| **Reset** | Click "🔄 Reset" |
| **Pan Camera** | Click and drag |
| **Zoom** | +/- buttons |
| **Inspect Unit** | Click on any unit |
| **Change Preset** | Click "Config" → select preset |
| **Speed** | 0.5x, 1x, 2x, 5x buttons |

---

## 📊 Data Flow

```
jayspiffy's Void Engine
    ↓
void-reckoning-engine/data/ground/unit_classes.json
    ↓
VoidEngineData.ts (imported)
    ↓
convertVoidStats() (scaled for simulation)
    ↓
Unit entity (with nameplate, armor, morale)
    ↓
BattleCanvas (rendered with glow + info)
```

---

## 🔧 Adjusting Simulation

Edit `src/game/data/SimulationConfig.ts`:

```typescript
// Make battles faster
healthScale: 0.05,  // Units die quicker
damageScale: 0.2,   // More damage

// Use only titans
availableUnitClasses: ["war_titan", "apocalypse_titan"],

// Bigger battles
teamSize: 100,
```

---

## ✅ Features Summary

- ✅ Real Void Reckoning Engine unit data
- ✅ 8 different unit types with unique stats
- ✅ Unit nameplates (icon + name + number)
- ✅ Detailed unit inspection panel
- ✅ Configurable simulation variables
- ✅ Battle presets (Quick/Standard/Epic/Titan)
- ✅ Team stats with unit breakdown
- ✅ Armor and morale systems
- ✅ Range indicators for selected units
- ✅ Click-to-select units
- ✅ Pan and zoom camera
- ✅ Mini-map with viewport

---

## 🚀 Running

**Already live at**: http://localhost:5173

Click **"Start"** to watch Void Reckoning Engine units battle! ⚔️
