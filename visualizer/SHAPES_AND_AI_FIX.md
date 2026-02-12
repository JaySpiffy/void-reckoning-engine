# Unique Shapes & Fixed Titan AI ✅

## 🎨 New Unit Shapes (Darwin's Island Style)

Each unit type now has a unique shape instead of all being circles:

| Unit Type | Shape | Visual |
|-----------|-------|--------|
| **Titans** | Hexagon | ⬡ Large hexagon |
| **Tanks** | Square | ⬜ Armored box |
| **Walkers** | Diamond | ◆ Walker legs |
| **Support** | Star | ⭐ Heavy weapons |
| **Infantry** | Triangle | ▲ Pointing forward |
| **Battlesuits** | Circle | ● Classic circle |
| **Slime/Default** | Blob | 🟢 Wobbly amoeba |

### Shape Features:
- **Slimes wobble** - Blobby amoeba animation
- **Triangles rotate** - Point in movement direction
- **Squares rotate** - Face the way they're moving
- **Hexagons pulse** - Titans glow and pulse
- **All have team color borders** and class-colored inner details

## 🤖 Fixed Titan/Ranged AI

**Before**: Titans would rush in and melee like idiots
**After**: Proper ranged behavior

### New Ranged AI Logic:
```
if (target in range) {
    → STOP and shoot
} else if (too close) {
    → BACK UP to optimal range
} else if (too far) {
    → Move closer slowly
} else {
    → Stay at optimal distance
}
```

### Ranged Unit Behavior:
- **Optimal range**: 70% of max range
- **Too close threshold**: 30% of max range
- **Back up speed**: 80% speed when way too close
- **Approach speed**: 60% speed when advancing
- **Stay still**: When in sweet spot, just shoot

### Melee Unit Behavior:
- **Charge directly** at target
- **Full speed** when closing
- **Stop and attack** when in range

## 🎯 What Titans Do Now

1. **Stay back** at 70% of their massive range
2. **Launch missiles** from across the battlefield
3. **Launch interceptors** every 2 seconds
4. **Back up** if enemies get too close
5. **Never melee** unless forced

## 🎮 Visual Differences

**Titans (Hexagon)**:
- Large hexagonal shape
- Slow, heavy movement
- Long-range missiles
- Interceptor swarms

**Tanks (Square)**:
- Boxy, armored look
- Rotate to face direction
- Medium range
- Heavy damage

**Infantry (Triangle)**:
- Point forward
- Fast movement
- Charge in quickly
- Close combat

**Slimes (Blob)**:
- Wobbly amoeba shape
- Unique wobble animation
- Flexible appearance
- Fun and distinct

## 🚀 Test It

**http://localhost:5173**

1. Look at the different shapes in formations
2. Watch titans stay back and fire missiles
3. See triangles charge in while hexagons stay back
4. Slimes wobble as they move!

## ✨ Combat Roles Are Now Clear!

- 🔷 **Hexagons** = Long-range artillery
- ⬜ **Squares** = Mid-range tanks  
- ▲ **Triangles** = Fast chargers
- ⭐ **Stars** = Support platforms
- ◆ **Diamonds** = Walker units
- ● **Circles** = Standard units
- 🟢 **Slimes** = Unique defaults
