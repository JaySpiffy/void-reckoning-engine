# POST (Posture) System Expansion Plan (V2)

## Multi-Universe Strategy Engine - Void Reckoning Universe

---

## 1. Structural Critique & Refinements

The original plan is excellent in its breadth (101 postures), but requires technical tightening to be maintainable and effective in a real-time simulation environment.

### 🚩 Key Technical Refinements

1. **Metric Standardization**: Instead of descriptive AI behaviors, each posture will now map to specific **Target Scoring Weights** and **Economic Budget Tiers**.
2. **Posture Hierarchy**: Grouping the 101 postures into **Base Categories** (Aggressive, Defensive, etc.) to allow for "Fallback Behaviors" if a specific specialized posture's conditions aren't perfectly met.
3. **City-Founding Integration**: Explicitly adding "Urban Expansion" logic to the `COLONIAL` and `BOOM` postures to utilize the new `ArmyGroup.found_city()` mechanic.
4. **Performance Optimization**: Using a **Transition Matrix** instead of checking 100+ trigger conditions every turn. Factions will only "look" for postures in adjacent or related categories.

---

## 2. Updated General Postures (Selected Additions & Changes)

### Category: Expansion & Settlement (Enhanced)

*Integrated with Phase 7 City Founding Mechanics*

| Posture | Code | Description | Unique Mechanic | Trigger |
|---------|------|-------------|-----------------|---------|
| **Pioneering** | PION | Rapid planetary settlement | +50% weight for `Pioneer` production; 2x weight for `found_city` on suitable hexes. | `unclaimed_suitable_hexes > 5` |
| **Metropolitan**| METR | Urban density focus | Prioritize building in `Capital` and `ProvinceCapital` nodes (maxing slots). | `owned_cities > 3` AND `slots_available > 10` |
| **Frontier Guard**| FRNT | Protect new colonies | Armies stay within 2 hexes of newly founded cities for 10 turns. | `city_founded_last_5_turns` |

### Category: Aggressive (Refined)

| Posture | Code | Change/Addition | AI Behavior Change |
|---------|------|-----------------|---------------------|
| **Blitzkrieg** | BLITZ| Refined Triggers | Now requires `mobility_speed > 1.2` average across fleets. |
| **Scorched Earth**| SCORCH| Added Logic | If `losing_planet` is true, prioritize destroying buildings before evacuation. |

---

## 3. Implementation Logic (Phase 2 & 3 Update)

### New Posture Selection Algorithm (The "Weighted Lottery")

Instead of just picking the highest score, we use a weighted distribution to prevent "AI oscillation":

1. **Filter**: Get all valid postures for the faction.
2. **Base Score**: 50 pts if `trigger_conditions` are met.
3. **Personality Bonus**: +20 pts if `posture.category` matches `personality.primary_bias`.
4. **Inertia**: +30 pts to `current_posture` to prevent flickering.
5. **Roll**: Randomly select from postures within 10% of the top score.

### Target Scoring Integration

Each posture now overrides the `TargetScoringService` weights:

```python
# Example: PIONEERING Posture Overrides
POSTURE_WEIGHTS = {
    "PION": {
        "distance": 0.5,      # Care less about distance
        "resource_yield": 1.5, # Focus on high-yield hexes
        "suitability": 2.0     # CRITICAL: Focus on hexes where can_found_city() is true
    }
}
```

---

## 4. Faction-Specific Posture Overhauls

### Algorithmic Hierarchy (Refined)

- **Logic Sync (LOGIC)**: Now applies a global +10% accuracy bonus to all units if within 5 tiles of a `Capital` (reflecting centralized processing).

### Templars of the Flux (Refined)

- **Crusade (CRUS)**: Now grants `Conviction` stacks specifically when founding a city on an "Anomaly" hex.

---

## 5. Deployment Plan (Revised)

1. **Registry Migration**: Convert `posture_registry.json` to the new hierarchical format.
2. **Weight Mapping**: Connect all 101 postures to the `TargetScoringService` weight system.
3. **Dashboard Integration**: Add a "Posture Icon" (e.g., ⚔️ for BLITZ, 🧱 for TURT) to the faction summary line.
4. **Settler logic**: Ensure `COLONIAL` and `PIONEERING` postures correctly prioritize the `Pioneer` unit blueprint I just added.

---
> [!IMPORTANT]
> This plan assumes the `ArmyGroup.found_city()` method is functional (Verified in Phase 7).
