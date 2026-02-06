# POST (Posture) System Expansion Plan (V3)

## Multi-Universe Strategy Engine - Void Reckoning Universe

---

## 1. Executive Summary

This plan serves as the final refinement for the Posture System Expansion. It bridges the gap between the massive variety of the original 101 postures and the technical precision required for a high-performance simulation.

### 🌟 Key Enhancements in V3

1. **Archetype Mapping**: All 101 postures are now mapped to **12 Core Behavior Archetypes** (Blitz, Turtle, Boom, Pioneer, etc.).
2. **City-Founding Synergy**: Postures like `PIONEERING` and `COLONIAL` now explicitly prioritize the `found_city()` mechanic and `Pioneer` unit production.
3. **Hysteresis (Anti-Oscillation)**: Uses a "Weighted Lottery" with a 30% "Inertia" bonus to prevent factions from switching postures too frequently.
4. **Faction-Specific Integration**: Faction quirks (e.g., `biomass_hunger`, `conviction`) are now directly influenced by active postures.

---

## 2. Core Behavior Archetypes (High-Level)

Instead of individual logic for 101 postures, the AI uses these 12 patterns. Specific postures within these patterns provide "flavor" stat tweaks.

| Archetype | Focus | Primary Modifiers |
|-----------|-------|-------------------|
| **BLITZ** | Speed & Offense | +50% Speed, -20% Defense |
| **TURTLE**| Defense & Forts | +50% Defense, -30% Expansion |
| **BOOM**  | Economy & Tech  | +30% Income, +25% Research |
| **PIONEER**| Settlement     | +100% `found_city` weight |
| **RAID**  | Loot & Harass   | +40% Loot, avoid major fleets |
| **DIPLO** | Alliances      | +20 Diplomacy, focus on Vassals |
| **TOTAL** | Existential War| 100% Military Focus, ignore debt |
| **ATTRIT**| Resource Grind | Efficient trades, long-term buildup |
| **ADAPT** | Counter-Play   | Rapidly changes based on enemy tech |
| **ELITE** | Quality         | +20% Damage, higher unit costs |
| **SWARM** | Quantity        | -30% Unit Cost, mass production |
| **SURVIV**| Desperation     | Retreat to capital, scorched earth |

---

## 3. General Postures (101) - Refined Triggers

*Note: For brevity, only selected critical changes are shown. All 101 postures from V1 are retained but mapped to the Archetypes above.*

### Selected New "Urban" Postures

| Posture | Code | Archetype | Unique Mechanic | Trigger |
|---------|------|-----------|-----------------|---------|
| **Metropolitan**| METR | BOOM | Prioritizes `City` upgrades over new colonies. | `owned_cities >= 3` |
| **Frontier Guard**| FRNT | TURTLE | Armies tether to cities founded in the last 10 turns. | `new_city_active == True` |
| **Expeditionary**| EXPD | PIONEER | Faster `Pioneer` movement through Flux Anomalies. | `anomalies_detected > 2` |

---

## 4. Implementation Logic

### The "Weighted Lottery" Algorithm

To prevent "AI Flickering" (switching every turn), the `PostureManager` uses the following score calculation:

1. **Trigger Score**: +50 base if conditions (Threat, Econ, Turn) are met.
2. **Inertia**: +30 score to the **Current Posture** to ensure commitment.
3. **Personality Alignment**: +20 if Archetype matches `personality.primary_bias`.
4. **Selection**: The system picks any posture within 10% of the top score to allow for "emergent variety."

### Target Scoring Weights (Example)

```python
# PIONEERING Posture Override
POSTURE_WEIGHTS = {
    "PION": {
        "income": 0.5,         # Care less about immediate cash
        "suitability": 3.0,    # MUST find flat/safe hexes for cities
        "distance": 1.5        # Happy to go a bit further for prime land
    }
}
```

---

## 5. Faction-Specific Hooks

- **Bio-Tide Collective (`CONSUMPTION`)**: On posture active: `biomass_hunger += 0.5`. On posture deactivation: Reset.
- **Templars of the Flux (`CRUSADE`)**: Unlocks the `Crusade` mission type which generates `Conviction` on a 2x scale.
- **Algorithmic Hierarchy (`LOGIC`)**: All units within 5 hexes of a `Logic Hub` (Capital) gain +15% Accuracy.

---

## 6. Migration & Deployment Plan

1. **Phase 1**: Convert `posture_registry.md` into `posture_registry.json`.
2. **Phase 2**: Inject posture weights into `TargetScoringService.py`.
3. **Phase 3**: Update `terminal_dashboard.py` to show posture icons (e.g., 🚀 for PION, ⚔️ for BLITZ).
4. **Phase 4**: Verification via Headless Simulation.

---
> [!NOTE]
> This V3 plan integrates the feedback from the Phase 7 City Founding verification and the Phase 15 Logistics Safeguards.
