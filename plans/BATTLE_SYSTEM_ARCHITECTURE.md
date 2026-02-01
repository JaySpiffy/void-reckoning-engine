# Battle System Architecture - Space & Ground Combat Integration

**Date:** 2026-01-27  
**Purpose:** Document how space and ground battle simulators work together to map out combat across different domains

---

## Overview

The Multi-Universe Strategy Engine implements a **dual-domain combat system** that seamlessly integrates **Space Battles** (fleets) and **Ground Battles** (armies) through a unified [`BattleManager`](src/managers/battle_manager.py:23).

---

## Core Architecture

### BattleManager - Central Combat Orchestrator

**File:** [`src/managers/battle_manager.py`](src/managers/battle_manager.py:23)

The [`BattleManager`](src/managers/battle_manager.py:23) is responsible for:
- **Space Battles** - Fleet engagements in orbit
- **Ground Invasions** - Landing armies on planets
- **Planet Battles** - Ground warfare between armies

```python
class BattleManager:
    """
    Handles all combat resolution:
    - Space Battles (Fleets)
    - Ground Invasions (Landing Logic)
    - Planet Battles (Ground War)
    """
```

---

## Space Battles

### How Space Battles Work

**Entry Point:** [`resolve_battles_at()`](src/managers/battle_manager.py:121)

When fleets from different factions meet at a location (Star System or Planet), the system:

1. **Detects Conflict** - Checks if opposing factions are present
2. **Evasion Check** - Fleets with high evasion rating may slip away
3. **Joins Existing Battle** - If battle already exists, fleets join it
4. **Creates New Battle** - If no battle exists, initializes new [`ActiveBattle`](src/managers/combat/active_battle.py)

### Space Combat Resolution

**Two Modes Available:**

#### 1. Real-Time Headless Mode (Default)
**File:** [`src/combat/tactical_engine.py`](src/combat/tactical_engine.py) - `resolve_real_time_combat()`

When enabled (or for high unit counts), battles resolve using:
- **5-Phase Combat System**:
  - Ability Phase
  - Movement Phase
  - Shooting Phase
  - Melee Phase
  - Morale Phase
- **GPU Acceleration** - CuPy for batch calculations
- **Tactical Grid** - 2D grid for unit positioning
- **Doctrine Modifiers** - Faction-specific combat bonuses
- **Mechanics Engine** - Faction-specific abilities

#### 2. Sequential Mode (Legacy)
**File:** [`src/combat/phase_executor.py`](src/combat/phase_executor.py) - `execute_battle_round()`

For lower unit counts or when real-time is disabled:
- Round-by-round resolution
- Maximum 2000 rounds (safety limit)
- Each round executes phases sequentially

### Space Combat Types

#### Fleet Engagements
**File:** [`src/combat/space_combat.py`](src/combat/space_combat.py)

**Boarding Phase:**
- Ships with "Star Fort" ability attempt to board enemy ships
- Uses dice-based resolution
- Damage based on `BOARDING_DAMAGE_PER_SUCCESS` and `BOARDING_HULL_PER_DIE`
- Universe rules can provide custom boarding logic

---

## Ground Battles

### How Ground Battles Work

**Entry Point:** [`InvasionManager`](src/managers/combat/invasion_manager.py:13)

Ground combat occurs through **invasions** - armies landing on planets to fight enemy forces.

### Invasion Flow

**File:** [`src/managers/combat/invasion_manager.py`](src/managers/combat/invasion_manager.py:13)

#### 1. Orbital Blockade Check (Phase 17)

```python
def _check_orbital_blockade(self, fleet, location):
    """Checks if hostile space units are in orbit preventing landings."""
```

- If hostile fleets are in orbit at the target planet
- Landing is blocked
- Fleet cannot disembark armies

#### 2. Army Embarkation

```python
def embark_army(self, fleet, army_group):
    """Army boards a Fleet (Transport)."""
```

- Validates fleet has transport capacity
- Transfers army to fleet's cargo
- Army state changes to `EMBARKED`
- Telemetry event logged

#### 3. Army Disembarkation (Landing)

```python
def disembark_army(self, fleet, target_node):
    """Army unloads from Fleet to Planet Node."""
```

- Validates drop zone exists (LandingZone province)
- Army state changes to `IDLE`
- Armies merge with existing ground forces
- Telemetry event logged

#### 4. Ground Combat Resolution

**File:** [`src/combat/ground_combat.py`](src/combat/ground_combat.py)

**Melee Phase:**
```python
def resolve_melee_phase(active_army, enemy_army, round_num, ...):
    """Phase 18: Executes Melee Resolution for Ground Units."""
```

- Ground units engage in melee combat
- Uses `MA` (Melee Attack) stat for hit chance
- Damage calculation with mitigation
- Component targeting (armor, hull, etc.)
- Mechanics engine integration for faction abilities

### Ground Combat Types

#### Unopposed Conquest (Colonization)
**File:** [`src/managers/combat/invasion_manager.py`](src/managers/combat/invasion_manager.py:203)

```python
def handle_unopposed_conquest(self, location, occupier):
    """Phase 21: Handles peaceful annexation of neutral worlds."""
```

- Single faction arrives at neutral planet
- No resistance expected
- Planet ownership transfers peacefully
- **Tech Lock** enforced (destroys incompatible buildings)

#### Contested Conquest (Invasion)

**File:** [`src/managers/battle_manager.py`](src/managers/battle_manager.py:196)

When multiple factions have forces at a planet:
- Battle state initialized
- All armies and fleets join as participants
- **Defender Identification:**
  - Fleets arriving this turn are defenders
  - Resident armies are defenders
  - Attacker is anyone not arriving this turn

---

## Space-to-Ground Integration

### Orbital Supremacy to Ground Invasion

**Flow:**

```
1. Space Battle Won
   ↓
2. Orbital Blockade Cleared
   ↓
3. Fleets Land Armies
   ↓
4. Ground Combat Begins
   ↓
5. Planet Conquered
```

### BattleManager Integration Points

**File:** [`src/managers/battle_manager.py`](src/managers/battle_manager.py)

| Method | Purpose | Integration |
|--------|---------|-------------|
| [`resolve_battles_at()`](src/managers/battle_manager.py:121) | Detects conflicts at locations, joins existing battles, creates new battles |
| [`process_active_battles()`](src/managers/battle_manager.py:208) | Ticks all active battles, handles retreats, resolves combat |
| [`_join_active_battle()`](src/managers/battle_manager.py:324) | Adds fleets/armies to existing battles |
| [`_initialize_new_battle()`](src/managers/battle_manager.py:355) | Creates battle state, initializes combat grid |
| [`_finalize_battle()`](src/managers/battle_manager.py:316) | Handles planet ownership, logs results |

### InvasionManager Integration Points

**File:** [`src/managers/combat/invasion_manager.py`](src/managers/combat/invasion_manager.py)

| Method | Purpose | Integration |
|--------|---------|-------------|
| [`process_invasions()`](src/managers/combat/invasion_manager.py:26) | Checks fleets for invasion orders |
| [`embark_army()`](src/managers/combat/invasion_manager.py:88) | Loads armies onto fleets |
| [`disembark_army()`](src/managers/combat/invasion_manager.py:150) | Lands armies on planets |
| [`handle_conquest()`](src/managers/combat/invasion_manager.py:212) | Transfers planet ownership |
| [`enforce_tech_lock()`](src/managers/combat/invasion_manager.py:231) | Destroys incompatible buildings |

---

## Domain Separation

The system maintains strict **domain separation** between space and ground combat:

### Space Domain
- **Units:** Ships (Fleets)
- **Locations:** Star Systems, Orbital Space
- **Combat Type:** Ship-to-Ship, Boarding
- **Resolution:** [`resolve_real_time_combat()`](src/combat/tactical_engine.py) or sequential rounds
- **Key File:** [`src/combat/space_combat.py`](src/combat/space_combat.py)

### Ground Domain
- **Units:** Ground Armies (ArmyGroups)
- **Locations:** Planet Provinces, Landing Zones
- **Combat Type:** Melee, Ranged (via shooting)
- **Resolution:** [`resolve_melee_phase()`](src/combat/ground_combat.py)
- **Key File:** [`src/combat/ground_combat.py`](src/combat/ground_combat.py)

### Cross-Domain Interactions

1. **Orbital Blockade:** Space fleets prevent ground landings
2. **Invasion:** Fleets transport armies to planets
3. **Orbital Bombardment:** Space ships attack ground targets
4. **Conquest:** Space victory leads to ground invasion

---

## Shared Systems

### 5-Phase Combat System

**File:** [`src/combat/combat_phases.py`](src/combat/combat_phases.py)

Both space and ground combat use the same phase system:

| Phase | Class | Description |
|--------|--------|-------------|
| Ability | [`AbilityPhase`](src/combat/combat_phases.py:378) | Units use abilities before other actions |
| Movement | [`MovementPhase`](src/combat/combat_phases.py:24) | Units move on tactical grid |
| Shooting | [`ShootingPhase`](src/combat/combat_phases.py:192) | Units fire weapons at enemies |
| Melee | [`MeleePhase`](src/combat/combat_phases.py:488) | Units engage in close combat |
| Morale | [`MoralePhase`](src/combat/combat_phases.py:549) | Units check for routing/breaking |

### GPU Acceleration

**File:** [`src/core/gpu_utils.py`](src/core/gpu_utils.py)

Both domains benefit from GPU acceleration:

- **Space:** Batch shooting, flow field pathfinding
- **Ground:** Batch stat synthesis for unit calculations
- **Shared:** CuPy array operations for vectorized calculations

### Tactical Grid

**File:** [`src/combat/tactical_grid.py`](src/combat/tactical_grid.py)

- 2D grid system for unit positioning
- Distance calculations
- Movement validation
- Line-of-sight support
- Reality Anchor integration

---

## Combat State Management

**File:** [`src/managers/combat/active_battle.py`](src/managers/combat/active_battle.py)

The [`ActiveBattle`](src/managers/combat/active_battle.py) class tracks:
- Participating fleets
- Participating armies
- Battle state (round number, finished status)
- Battle statistics
- Tactical grid
- Universe rules and faction metadata

---

## Retreat System

**File:** [`src/managers/combat/retreat_handler.py`](src/managers/combat/retreat_handler.py)

- Handles unit retreats from battles
- Space fleet retreats
- Ground army retreats
- Route calculation to safe locations

---

## Telemetry & Logging

Both space and ground combat share:
- **Event Categories:** COMBAT, MOVEMENT, CAMPAIGN
- **Detailed Logging:** JSON and text logs per battle
- **Battle Composition:** Unit types, veterancy levels
- **Damage Tracking:** Damage dealt, units destroyed

---

## Key Integration Points

### 1. Orbital Blockade Prevents Ground Combat
Space battles must be resolved before armies can land on contested planets.

### 2. Space Victory Enables Ground Invasion
After winning orbital supremacy, fleets can disembark armies to invade.

### 3. Ground Combat Resolves Planet Ownership
After ground combat is won, planet ownership transfers to victor.

### 4. Tech Lock Enforces Faction Rules
When a planet is conquered, buildings incompatible with the new owner are destroyed (Scorched Earth mechanic).

---

## Summary

The battle system is designed with **clear domain separation** but **tight integration**:

1. **Space Domain** - Fleets fight in orbit using ship weapons and boarding
2. **Ground Domain** - Armies fight on planets using melee and ranged attacks
3. **Cross-Domain** - Orbital blockades, invasions, bombardment
4. **Shared Infrastructure** - 5-phase system, GPU acceleration, tactical grid, telemetry

This architecture allows for:
- **Independent space battles** without ground interference
- **Independent ground battles** without orbital interference
- **Seamless transitions** from space to ground via invasions
- **Unified state management** through the BattleManager

---

**Documented:** 2026-01-27  
**Analyzer:** Roo (Multi-Universe Strategy Engine Analysis)
