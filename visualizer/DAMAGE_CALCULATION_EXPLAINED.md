# Damage Calculation - Void Engine → Our Simulator

## 🔢 The Full Formula

Our damage numbers are **derived from Jayspiffy's Void Reckoning Engine**, then converted for our simulator:

### Step 1: Void Engine Raw Stats
From `void-reckoning-engine/data/ground/unit_classes.json`:

**Example: War Titan**
```json
{
  "name": "War Titan",
  "stats": {
    "weapon_strength": 800,
    "melee_attack": 80,
    "ranged_attack": 500,
    "hp": 15000,
    "armor": 150
  }
}
```

### Step 2: Conversion Formula (VoidEngineData.ts)
```typescript
damage = (weapon_strength + melee_attack + ranged_attack) / 30 * scaleFactor
```

**War Titan example:**
- (800 + 80 + 500) / 30 * 0.1
- = 1380 / 30 * 0.1
- = 46 * 0.1
- = **4.6 base damage**

### Step 3: Simulator Scaling (Unit.ts)
```typescript
this.damage = baseDamage * SIMULATION_CONFIG.damageScale * 10
```

**With default settings (damageScale = 0.1):**
- 4.6 * 0.1 * 10
- = **4.6 final damage per hit**

### Step 4: In-Game Application
**When attacking:**
```typescript
// Melee gets 1.5x multiplier
meleeDamage = damage * 1.5  // = 6.9

// Charge bonus (first 5 seconds)
chargeDamage = damage * 1.5 * 1.5  // = 10.35

// Armor reduction on target
actualDamage = damage * (1 - armor/(armor+100))
```

## 📊 Comparison Table

| Unit | Void Engine WS | Void Engine MA | Void Engine RA | Our Base Dmg | Final Dmg | HP |
|------|---------------|----------------|----------------|--------------|-----------|-----|
| Line Infantry | 30 | 25 | 0 | 0.18 | 1.8 | 50 |
| Assault Marines | 45 | 45 | 20 | 0.37 | 3.7 | 100 |
| Battle Tank | 150 | 20 | 300 | 1.57 | 15.7 | 250 |
| **War Titan** | **800** | **80** | **500** | **4.6** | **46** | **1500** |
| Apocalypse Titan | 4000 | 120 | 2500 | 22.1 | 221 | 4500 |

## 🎮 Why The Scaling?

**Problem:** Void Engine numbers are HUGE (weapon_strength: 800-4000)

**Our Solution:**
1. `/ 30` - Bring numbers down to reasonable scale
2. `* scaleFactor (0.1)` - Health/damage parity
3. `* damageScale (0.1)` - User-adjustable
4. `* 10` - Final multiplier for visible combat

**Result:** War Titan deals ~46 damage per hit, has 1500 HP
- Can kill infantry in 1-2 hits
- Dies after ~30-50 hits from other titans
- Feels powerful but not invincible

## ⚙️ User Adjustable

In the **Config** tab, you control:
- `damageScale: 0.01 to 0.5`
- Lower = longer battles
- Higher = quicker deaths

**Example with damageScale = 0.5:**
- War Titan: 46 * 0.5 * 10 = **230 damage per hit**
- One-shots most units!

## ✅ Summary

| Source | What It Is |
|--------|-----------|
| **Void Engine** | Base stats (weapon_strength, melee_attack, ranged_attack) |
| **Our Converter** | `(WS + MA + RA) / 30 * scaleFactor` |
| **Our Simulator** | `base * damageScale * 10` |
| **Armor** | Reduces by `armor / (armor + 100)` |
| **Melee Bonus** | 1.5x multiplier |
| **User Control** | damageScale slider |

**The damage IS from Jayspiffy's engine, just converted for real-time simulation!** ⚔️
