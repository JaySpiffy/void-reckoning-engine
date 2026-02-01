# Multi-Universe Simulation Codebase - Technical Report

**Document Version:** 1.0  
**Date:** 2025-02-01  
**Scope:** Code Architecture and Technical Implementation  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [Tech Stack and Dependencies](#tech-stack-and-dependencies)
4. [Directory Structure](#directory-structure)
5. [Core Data Models](#core-data-models)
6. [Architecture Overview](#architecture-overview)
7. [Key Systems](#key-systems)
8. [Configuration Management](#configuration-management)
9. [Testing Infrastructure](#testing-infrastructure)
10. [Technical Debt and Patterns](#technical-debt-and-patterns)
11. [Performance Considerations](#performance-considerations)
12. [Conclusion](#conclusion)

---

## Executive Summary

The Multi-Universe Simulator is a complex grand strategy campaign engine built in Python that supports parallel simulation across multiple science fiction universes. The system features sophisticated mechanics including combat, diplomacy, economy, research, AI decision-making, and inter-universe portal travel. The architecture follows a modular design with clear separation of concerns across models, managers, services, and components.

---

## Project Overview

### Purpose
A high-fidelity grand strategy simulation engine capable of running multiple independent universes in parallel, with support for cross-universe interactions through portal mechanics.

### Key Features
- Multi-universe parallel execution
- Faction-based gameplay with AI personalities
- Tactical combat system with component-based units
- Diplomacy and treaty management
- Economy with requisition, construction, and research
- Warp storm/weather systems
- Portal-based inter-universe travel
- GPU-accelerated combat calculations
- Comprehensive telemetry and reporting

### Supported Factions
ZEA, SCA, RIF, SOL, VOI, ASC, IRO, CYB, ANC, HIV

---

## Tech Stack and Dependencies

### Core Technologies
| Technology | Version | Purpose |
|------------|----------|---------|
| Python | 3.7+ | Primary language |
| Pydantic | Latest | Data validation and configuration |
| NumPy | Latest | Numerical computations |
| CuPy | Optional | GPU acceleration |

### Key Python Libraries
- **Standard Library:** `random`, `math`, `json`, `csv`, `os`, `sys`, `hashlib`, `time`, `queue`, `threading`, `dataclasses`, `typing`
- **External:** `psutil` (system monitoring), `pytest` (testing)

### Entry Points
- Console script: `sim-engine` → `src.cli.main`
- Direct execution: `python run.py`

---

## Directory Structure

```
multi-universe-simulator/
├── src/                          # Source code
│   ├── ai/                        # AI systems
│   ├── analysis/                  # Analytics
│   ├── builders/                  # Entity builders
│   ├── cli/                      # Command-line interface
│   ├── combat/                    # Combat system
│   ├── commands/                  # CLI commands
│   ├── config/                    # Configuration
│   ├── core/                     # Core utilities
│   ├── data/                     # Data management
│   ├── engine/                   # Simulation engine
│   ├── events/                   # Event system
│   ├── factories/                 # Object factories
│   ├── generators/               # Procedural generation
│   ├── managers/                 # Game managers
│   ├── mechanics/                 # Game mechanics
│   ├── models/                    # Data models
│   ├── reporting/                 # Reporting and telemetry
│   ├── repositories/              # Data repositories
│   ├── services/                  # Business services
│   ├── strategies/                # AI strategies
│   └── utils/                    # Utilities
├── config/                       # Configuration files
├── data/                         # Game data
├── universes/                    # Universe definitions
├── tests/                        # Test suite
├── plans/                        # Planning documents
├── docs/                         # Documentation
├── run.py                        # Main entry point
└── setup.py                      # Package setup
```

---

## Core Data Models

### Model Hierarchy

```
Model Layer
├── Faction
├── StarSystem
├── Planet
├── Fleet
├── ArmyGroup
├── Starbase
├── Unit (Component-based)
│   ├── Ship
│   └── Regiment
├── ResearchProject
└── SpyNetwork
```

### Key Model Classes

#### Faction ([`src/models/faction.py`](src/models/faction.py))
The central entity representing a playable faction.

**Key Attributes:**
- `name`: Faction identifier
- `uid`: GUID for dual-passport system
- `requisition`: Primary currency
- `budgets`: Allocated budgets (research, construction, navy, army)
- `research_points`, `research_queue`, `active_research`: Research system
- `unlocked_techs`, `tech_unlocked_turns`: Technology tracking
- `visible_planets`, `known_planets`, `known_factions`: Fog of War
- `intelligence_memory`: Exploration data
- `personality_id`: AI personality reference
- `quirks`: Data-driven faction traits

**Key Methods:**
- `load_from_registry()`: Load personality data
- Economy and diplomacy tracking

#### Planet ([`src/models/planet.py`](src/models/planet.py))
Represents a celestial body within a star system.

**Key Attributes:**
- `name`, `system`, `orbit_index`: Positional data
- `owner`: Controlling faction
- `planet_class`: Procedurally generated type
- `income_req`: Requisition income
- `building_slots`, `buildings`: Infrastructure
- `construction_queue`, `unit_queue`: Production
- `max_queue_size`: Queue limits
- `garrison_strength`, `garrison_capacity`: Defense
- `naval_slots`, `army_slots`: Unit capacity
- `starbase`: Orbital station reference
- `provinces`: Province nodes (lazy loaded)

**Key Methods:**
- `available_production_slots()`: Queue capacity
- `recalc_stats()`: Recalculate based on buildings/provinces
- `process_construction()`: Advance building queue
- `process_production()`: Advance unit queue

#### StarSystem ([`src/models/star_system.py`](src/models/star_system.py))
Represents a star system with planets and topology.

**Key Attributes:**
- `name`, `x`, `y`: Galactic coordinates
- `planets`: List of planets
- `connections`: Warp lanes to other systems
- `nodes`: Internal graph nodes (topology)
- `warp_points`: Portal access points
- `starbases`: Starbase units

**Key Methods:**
- `generate_topology()`: Creates spiral mesh graph with ~300 nodes
- `add_planet()`: Add planet to system

#### Fleet ([`src/models/fleet.py`](src/models/fleet.py))
Represents a naval force capable of interstellar travel.

**Key Attributes:**
- `id`, `faction`, `location`: Identity
- `destination`, `travel_progress`, `travel_duration`: Movement
- `units`: List of Unit objects
- `is_destroyed`: State flag
- `requisition`: Local fleet fund
- `cargo_armies`: Transported armies
- `current_node`, `route`: Graph-based movement
- `is_engaged`: Combat state
- `tactical_directive`: Combat doctrine
- `portal_aware`, `in_portal_transit`: Portal state

**Key Methods:**
- `calculate_power()`: Fleet combat power
- `move_to()`: Initiate movement
- `consolidate()`: Merge with other fleets
- `embark_army()`, `disembark_army()`: Transport

#### ArmyGroup ([`src/models/army.py`](src/models/army.py))
Represents a ground force on a planet surface.

**Key Attributes:**
- `id`, `faction`, `units`: Identity
- `location`, `destination`: Graph node positions
- `state`: IDLE, MOVING, GARRISONED, EMBARKED
- `transport_fleet`: Transport reference
- `movement_points`, `current_mp`: Movement
- `has_retreated_this_turn`: Retreat limit

**Key Methods:**
- `retreat()`: Break engagement
- `reset_turn_flags()`: Reset per-turn flags

#### Starbase ([`src/models/starbase.py`](src/models/starbase.py))
Static space station inheriting from Unit.

**Key Attributes:**
- `tier`: Upgrade level (1-5)
- `system`: Parent system
- `modules`: Installed modules
- `hangar_capacity`: Fighter capacity
- `naval_slots`: Shipyard capacity
- `unit_queue`: Production queue
- `ftl_inhibitor`: Blocks enemy movement
- `is_under_construction`: Construction state

**Key Methods:**
- `recalc_tier_stats()`: Update stats based on tier

#### Unit ([`src/models/unit.py`](src/models/unit.py))
Component-based unit entity (ECS pattern).

**Key Attributes:**
- `name`, `faction`, `unit_class`, `domain`: Identity
- `blueprint_id`: Reference to blueprint
- `cost`: Build cost
- `rank`: Veteran status
- Components: `health_comp`, `armor_comp`, `weapon_comps`, `morale_comp`, `trait_comp`, `movement_comp`, `stats_comp`

**Key Methods:**
- `add_component()`: Attach component
- `take_damage()`: Damage handling with mitigation
- `is_alive()`: Check survival status

**Component Types:**
- [`HealthComponent`](src/combat/components/health_component.py): HP, shields, regen
- [`ArmorComponent`](src/combat/components/armor_component.py): Damage mitigation
- [`WeaponComponent`](src/combat/components/weapon_component.py): Weapon systems
- [`MoraleComponent`](src/combat/components/morale_component.py): Morale state
- [`TraitComponent`](src/combat/components/trait_component.py): Special traits
- [`MovementComponent`](src/combat/components/movement_component.py): Movement stats
- [`StatsComponent`](src/combat/components/stats_component.py): Core stats (MA, MD, damage, etc.)

#### ResearchProject ([`src/models/research_project.py`](src/models/research_project.py))
Tracks active research progress.

**Key Attributes:**
- `tech_id`: Technology identifier
- `total_cost`: Research points required
- `progress`: Current progress

**Key Methods:**
- `invest(amount)`: Add RP, return overflow
- `remaining_cost`: Calculate remaining
- `is_complete`: Check completion

#### SpyNetwork ([`src/models/spy_network.py`](src/models/spy_network.py))
Represents intelligence operations in a target faction.

**Key Attributes:**
- `target_faction`: Target faction name
- `infiltration_level`: 0-100 progress
- `is_exposed`: Discovery state
- `agents`: List of agent roles
- `points_invested`: Total investment
- `established_turn`: Creation turn

**Key Methods:**
- `grow()`, `degrade()`: Modify infiltration
- `expose()`: Trigger discovery
- `to_dict()`, `from_dict()`: Serialization

---

## Architecture Overview

### Architectural Patterns

#### 1. Component-Based Entity System (ECS)
Units use a component-based architecture for flexibility:

```
Unit
├── HealthComponent (HP, shields, regen)
├── ArmorComponent (mitigation, facing)
├── WeaponComponent[] (weapons list)
├── MoraleComponent (morale state)
├── TraitComponent (special abilities)
├── MovementComponent (speed, MP)
└── StatsComponent (MA, MD, damage, etc.)
```

#### 2. Manager Pattern
Specialized managers handle specific domains:

| Manager | Responsibility |
|---------|----------------|
| [`CampaignEngine`](src/managers/campaign_manager.py) | Central orchestration |
| [`TurnProcessor`](src/managers/turn_processor.py) | Turn execution loop |
| [`EconomyManager`](src/managers/economy_manager.py) | Economic cycle |
| [`DiplomacyManager`](src/managers/diplomacy_manager.py) | Diplomatic relations |
| [`TechManager`](src/managers/tech_manager.py) | Technology trees |
| [`FleetManager`](src/managers/fleet_manager.py) | Fleet operations |
| [`BattleManager`](src/managers/battle_manager.py) | Combat resolution |
| [`PortalManager`](src/managers/portal_manager.py) | Inter-universe travel |
| [`IntelligenceManager`](src/managers/intelligence_manager.py) | Fog of War |
| [`GalaxyGenerator`](src/managers/galaxy_generator.py) | Map creation |

#### 3. Service Layer
Business logic separated into services:

| Service | Responsibility |
|---------|----------------|
| [`ConstructionService`](src/services/construction_service.py) | Building production |
| [`RecruitmentService`](src/services/recruitment_service.py) | Unit recruitment |
| [`RelationService`](src/services/relation_service.py) | Faction relations |
| [`DiplomaticActionHandler`](src/services/diplomatic_action_handler.py) | Diplomatic actions |
| [`PathfindingService`](src/services/pathfinding_service.py) | Route calculation |
| [`ShipDesignService`](src/services/ship_design_service.py) | Ship design |

#### 4. Factory Pattern
Object creation via factories:

| Factory | Purpose |
|---------|---------|
| [`UnitFactory`](src/factories/unit_factory.py) | Unit instantiation |
| [`TechFactory`](src/factories/tech_factory.py) | Technology generation |
| [`WeaponFactory`](src/factories/weapon_factory.py) | Weapon creation |
| [`DesignFactory`](src/factories/design_factory.py) | Ship designs |

#### 5. Strategy Pattern
AI behaviors via strategy classes:

| Strategy | Purpose |
|----------|---------|
| [`StandardStrategy`](src/ai/strategies/standard.py) | Default AI behavior |
| [`TacticalStrategy`](src/ai/strategies/tactical.py) | Combat tactics |
| [`EconomicStrategy`](src/ai/strategies/economic.py) | Economic decisions |

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Campaign │  │  Multi   │  │ Validate │  │  Query  │ │
│  │  Command │  │ Universe │  │ Command  │  │ Command │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
└───────┼──────────────┼──────────────┼──────────────┼───────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                               │
┌───────────────────────────────────▼──────────────────────────────────┐
│                      CampaignEngine                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ TurnProcessor │  │ EconomyMgr   │  │ DiplomacyMgr │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ TechManager  │  │ FleetManager │  │ BattleMgr    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ StrategicAI  │  │ PortalMgr    │  │ Intelligence │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└───────────────────────────────────────────────────────────────────┘
        │                  │                  │
┌───────▼──────────┬─────▼──────────┬─────▼──────────┐
│  Model Layer     │  Combat System  │  Services      │
│  ┌──────────┐   │  ┌──────────┐  │  ┌──────────┐ │
│  │ Faction  │   │  │ Tactical │  │  │ Pathfind │ │
│  │ Planet   │   │  │  Grid    │  │  │ Relation │ │
│  │ Fleet    │   │  │ Tracker  │  │  │ Recruit  │ │
│  │ Army     │   │  │ Resolver │  │  │ Construct│ │
│  │ Unit     │   │  └──────────┘  │  └──────────┘ │
│  └──────────┘   │                │               │
└─────────────────┴────────────────┴───────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│              Data Layer (Repositories & Config)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │Registry  │  │  Config  │  │Universe  │  │  DB    │ │
│  │ Builders │  │  Loader  │  │  Loader  │  │ Indexer│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### Turn Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Turn Start                             │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  Global Phase          │
        │  - Warp Storms        │
        │  - Diplomacy Events   │
        │  - Portal Transfers   │
        └────────────┬────────────┘
                     │
    ┌────────────────▼────────────────┐
    │   Sequential Faction Turns     │
    │  ┌────────────────────────┐  │
    │  │ 1. Economy Phase      │  │
    │  │    - Income           │  │
    │  │    - Upkeep           │  │
    │  │    - Budget Allocation │  │
    │  └────────────────────────┘  │
    │  ┌────────────────────────┐  │
    │  │ 2. Construction Phase │  │
    │  │    - Buildings        │  │
    │  │    - Units           │  │
    │  └────────────────────────┘  │
    │  ┌────────────────────────┐  │
    │  │ 3. Research Phase    │  │
    │  │    - Tech Progress    │  │
    │  └────────────────────────┘  │
    │  ┌────────────────────────┐  │
    │  │ 4. AI Decision Phase │  │
    │  │    - Movement         │  │
    │  │    - Attacks         │  │
    │  │    - Diplomacy       │  │
    │  └────────────────────────┘  │
    │  ┌────────────────────────┐  │
    │  │ 5. Combat Phase      │  │
    │  │    - Resolve Battles  │  │
    │  └────────────────────────┘  │
    └────────────────┬────────────────┘
                     │
        ┌────────────▼────────────┐
        │  End of Turn          │
        │  - Telemetry Flush   │
        │  - Save State        │
        │  - Report Generation  │
        └────────────┬────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│                    Next Turn                           │
└─────────────────────────────────────────────────────────┘
```

---

## Key Systems

### 1. Combat System

#### Architecture
The combat system uses a multi-layered architecture:

```
Combat System
├── CombatSimulator (Facade)
│   ├── CombatState (State Management)
│   ├── TacticalGrid (Spatial Partitioning)
│   ├── CombatTracker (Logging)
│   ├── PhaseExecutor (Phase Logic)
│   └── CrossUniverseHandler (Multi-Verse)
├── Tactical Engine
│   ├── TargetSelector
│   ├── MovementCalculator
│   ├── SalvageProcessor
│   └── MassCombatResolver
└── Components
    ├── HealthComponent
    ├── ArmorComponent
    ├── WeaponComponent
    └── TraitComponent
```

#### Key Classes

**CombatState ([`src/combat/combat_state.py`](src/combat/combat_state.py))**
- Manages battle state and initialization
- Tracks active factions, units, and statistics
- Handles stalemate detection
- Manages victory points and objectives

**TacticalGrid ([`src/combat/tactical_grid.py`](src/combat/tactical_grid.py))**
- Spatial partitioning for combat
- Grid-based positioning (30-100 cells based on unit count)
- Supports GPU acceleration via CuPy

**CombatTracker ([`src/combat/combat_tracker.py`](src/combat/combat_tracker.py))**
- Logs combat events
- Tracks unit snapshots
- Generates combat reports

**PhaseExecutor ([`src/combat/phase_executor.py`](src/combat/phase_executor.py))**
- Executes combat phases in sequence:
  1. Psychic Phase
  2. Shooting Phase
  3. Boarding Phase
  4. Melee Phase
  5. Morale Phase

#### Combat Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Combat Initialization                        │
│  1. Load armies_dict {faction: [units]}              │
│  2. Create CombatState                                │
│  3. Initialize TacticalGrid (size based on unit count)  │
│  4. Initialize CombatTracker                            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   Combat Round Loop     │
        │  ┌──────────────────┐  │
        │  │ Psychic Phase    │  │
        │  │ - Abilities      │  │
        │  │ - Psychic Damage │  │
        │  └──────────────────┘  │
        │  ┌──────────────────┐  │
        │  │ Shooting Phase   │  │
        │  │ - Target Select  │  │
        │  │ - Damage Calc    │  │
        │  │ - Mitigation     │  │
        │  └──────────────────┘  │
        │  ┌──────────────────┐  │
        │  │ Boarding Phase   │  │
        │  │ - Boarding Acts  │  │
        │  └──────────────────┘  │
        │  ┌──────────────────┐  │
        │  │ Melee Phase     │  │
        │  │ - Close Combat  │  │
        │  └──────────────────┘  │
        │  ┌──────────────────┐  │
        │  │ Morale Phase    │  │
        │  │ - Morale Checks │  │
        │  │ - Routing      │  │
        │  └──────────────────┘  │
        │  ┌──────────────────┐  │
        │  │ Cleanup Phase   │  │
        │  │ - Remove Dead   │  │
        │  │ - Update Grid   │  │
        │  └──────────────────┘  │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   Victory Check        │
        │  - All enemies routed? │
        │  - Max rounds reached?│
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   Combat End           │
        │  - Generate Report     │
        │  - Process Salvage    │
        │  - Update Telemetry   │
        └────────────────────────┘
```

### 2. Economy System

#### Components

**EconomyManager ([`src/managers/economy_manager.py`](src/managers/economy_manager.py))**
- Orchestrates economic cycle
- Delegates to specialized components:
  - `ResourceHandler`: Income/upkeep calculation
  - `BudgetAllocator`: Spending decisions
  - `InsolvencyHandler`: Bankruptcy management
  - `RecruitmentService`: Unit production
  - `ConstructionService`: Building production

**Economic Cycle**

```
┌─────────────────────────────────────────────────────────────┐
│              Economic Phase (Per Faction)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Banking Cycle (Iron Bank)                  │   │
│  │    - Process loans                             │   │
│  │    - Apply interest                            │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 2. Precalculation (ResourceHandler)           │   │
│  │    - Calculate income                          │   │
│  │    - Calculate upkeep                          │   │
│  │    - Build faction_econ_cache                  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 3. Budget Allocation (BudgetAllocator)        │   │
│  │    - Determine economic mode (Development/      │   │
│  │      Crisis/Recovery/Expansion)               │   │
│  │    - Allocate to research/construction/        │   │
│  │      navy/army                                │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 4. Production (Recruitment/Construction)       │   │
│  │    - Advance queues                            │   │
│  │    - Spawn units/buildings                    │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 5. Insolvency Check (InsolvencyHandler)       │   │
│  │    - Detect bankruptcy                         │   │
│  │    - Trigger recovery mode                    │   │
│  │    - Apply penalties                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3. Diplomacy System

#### Components

**DiplomacyManager ([`src/managers/diplomacy_manager.py`](src/managers/diplomacy_manager.py))**
- Delegates to specialized services:
  - `RelationService`: Faction relationships
  - `TreatyCoordinator`: Treaty management
  - `DiplomaticActionHandler`: Action processing

**Treaty States**
- Peace
- War
- Alliance
- Defensive Pact
- Trade Agreement
- Non-Aggression Pact

**Diplomatic Features**
- War exhaustion tracking
- Grudge system
- Treaty cooldowns
- Forced peace (exhaustion)
- Relation modifiers

### 4. Research System

#### Components

**TechManager ([`src/managers/tech_manager.py`](src/managers/tech_manager.py))**
- Loads tech trees from JSON
- Manages research projects
- Handles tech upgrades
- Supports procedural evolution

**ResearchProject ([`src/models/research_project.py`](src/models/research_project.py))**
- Tracks individual research progress
- Handles overflow RP
- Reports completion status

### 5. AI System

#### Components

**StrategicAI ([`src/managers/ai_manager.py`](src/managers/ai_manager.py))**
- Central AI coordinator
- Manages strategic planning
- Coordinates theater operations

**StrategicPlanner ([`src/ai/strategic_planner.py`](src/ai/strategic_planner.py))**
- Creates strategic plans
- Analyzes theaters
- Sets war goals
- Manages sub-plans for multi-front operations

**TheaterManager ([`src/ai/theater_manager.py`](src/ai/theater_manager.py))**
- Analyzes operational theaters
- Identifies front lines
- Manages theater-specific strategies

**AI Decision Process**

```
┌─────────────────────────────────────────────────────────────┐
│              AI Decision Cycle                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. Situation Analysis                           │   │
│  │    - Economic health                            │   │
│  │    - Military strength                          │   │
│  │    - Diplomatic status                          │   │
│  │    - Theater analysis                           │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 2. Strategic Planning                         │   │
│  │    - Select war goal                          │   │
│  │    - Identify targets                          │   │
│  │    - Allocate theaters                         │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 3. Budget Allocation                         │   │
│  │    - Determine economic mode                   │   │
│  │    - Allocate resources                       │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 4. Fleet Operations                          │   │
│  │    - Movement orders                          │   │
│  │    - Attack targets                           │   │
│  │    - Consolidate fleets                       │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 5. Diplomatic Actions                       │   │
│  │    - Propose treaties                        │   │
│  │    - Declare war                             │   │
│  │    - Respond to offers                       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 6. Portal System

#### Components

**PortalManager ([`src/managers/portal_manager.py`](src/managers/portal_manager.py))**
- Manages inter-universe fleet transfers
- Handles incoming/outgoing queue commands
- Validates portal commands
- Injects fleets from other universes

**FleetQueueManager ([`src/managers/fleet_queue_manager.py`](src/managers/fleet_queue_manager.py))**
- Singleton queue manager
- Coordinates cross-universe transfers
- Tracks fleet injection/removal

**Portal Flow**

```
┌─────────────────────────────────────────────────────────────┐
│              Portal Transfer Process                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Universe A: Outgoing                            │   │
│  │ 1. Fleet enters portal node                    │   │
│  │ 2. PortalManager creates REMOVE_FLEET command  │   │
│  │ 3. Fleet serialized and queued                 │   │
│  └──────────────────────────────────────────────────┘   │
│                        │                               │
│                        ▼                               │
│              ┌───────────────┐                         │
│              │ Queue Manager │                         │
│              │  Singleton    │                         │
│              └───────────────┘                         │
│                        │                               │
│                        ▼                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Universe B: Incoming                           │   │
│  │ 1. PortalManager processes INJECT_FLEET       │   │
│  │ 2. Validate command                          │   │
│  │ 3. Register faction if new                   │   │
│  │ 4. Find closest portal exit                  │   │
│  │ 5. Hydrate fleet and add to game            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 7. Telemetry and Reporting

#### Components

**TelemetryCollector ([`src/reporting/telemetry.py`](src/reporting/telemetry.py))**
- Thread-safe event logging
- Metrics aggregation with sliding windows
- JSON log generation
- Database flushing support

**Event Categories**
- ECONOMY
- COMBAT
- DIPLOMACY
- MOVEMENT
- CONSTRUCTION
- SYSTEM
- CAMPAIGN
- STRATEGY
- DOCTRINE
- TECHNOLOGY
- INTELLIGENCE
- PORTAL
- HERO
- OPTIMIZATION

**ReportOrganizer ([`src/reporting/organizer.py`](src/reporting/organizer.py))**
- Organizes report output
- Manages run directories
- Generates summary reports

---

## Configuration Management

### Configuration Files

| File | Purpose |
|------|---------|
| [`config/unified_simulation_config.json`](config/unified_simulation_config.json) | Main simulation config |
| [`config/eternal_crusade_config.json`](config/eternal_crusade_config.json) | Eternal Crusade universe |
| [`config/balance_config.json`](config/balance_config.json) | Game balance values |
| [`config/alert_rules.yaml`](config/alert_rules.yaml) | Alert system rules |
| [`config/analytics_config.yaml`](config/analytics_config.yaml) | Analytics settings |

### GameConfig ([`src/core/game_config.py`](src/core/game_config.py))

Pydantic-based configuration object with typed fields:

```python
class GameConfig(BaseModel):
    max_turns: int
    num_systems: int
    min_planets_per_system: int
    max_planets_per_system: int
    starting_fleets: int
    base_requisition: int
    colonization_cost: int
    max_fleet_size: int
    max_build_time: int
    victory_planet_threshold: int
    tech_cost_multiplier: float
    diplomacy_enabled: bool
    fow_enabled: bool
    performance_logging_level: str
    sandbox_mode: bool
    procedural_faction_limit: int
```

### MultiUniverseConfig

Extends GameConfig for parallel universe execution:

```python
class MultiUniverseConfig(BaseModel):
    mode: str = "multi"
    universes: List[UniverseConfig]
    global_defaults: GameConfig
    multi_universe_settings: Dict
    simulation: Dict
```

### Universe Loader ([`universes/base/universe_loader.py`](universes/base/universe_loader.py))

Dynamically loads universe-specific configurations:

- Factions directory
- Infrastructure directory
- Technology directory
- Units directory
- Registry paths

### Path Management ([`src/core/config.py`](src/core/config.py))

Dynamic path resolution based on active universe:

```python
# Global paths recompute based on ACTIVE_UNIVERSE
INFRA_DIR, TECH_DIR, FACTIONS_DIR, DATA_DIR, UNITS_DIR
REGISTRY_BUILDING, REGISTRY_TECH, REGISTRY_WEAPON, 
REGISTRY_ABILITY, REGISTRY_FACTION
```

---

## Testing Infrastructure

### Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures
├── test_models.py                 # Model tests
├── test_combat_mechanics.py      # Combat tests
├── test_diplomacy.py             # Diplomacy tests
├── test_economy_manager.py        # Economy tests
├── test_tech_manager.py          # Research tests
├── test_ai_strategies.py         # AI tests
├── test_portal_system.py          # Portal tests
├── test_config_validation.py      # Config tests
├── integration/                 # Integration tests
│   ├── test_gpu_combat_flow.py
│   ├── test_gpu_movement_batch.py
│   └── test_gpu_production.py
└── performance/                 # Performance tests
    └── test_performance_regression.py
```

### Test Categories

| Category | Description |
|----------|-------------|
| Unit Tests | Individual component testing |
| Integration Tests | Cross-component interaction |
| Performance Tests | Regression testing |
| GPU Tests | CuPy acceleration tests |

### Key Test Files

- `test_models.py`: Model serialization/deserialization
- `test_combat_mechanics.py`: Combat resolution
- `test_diplomacy.py`: Treaty and relation logic
- `test_economy_manager.py`: Economic cycles
- `test_ai_strategies.py`: AI decision making
- `test_portal_system.py`: Cross-universe transfers

---

## Technical Debt and Patterns

### Known Technical Debt

1. **Circular Dependencies**
   - Some modules have import cycles
   - Mitigated with TYPE_CHECKING imports

2. **Legacy Code**
   - Old combat system still present (`combat_legacy`)
   - Gradual migration to new tactical engine

3. **Mixed Patterns**
   - Some managers use direct state access
   - Others use repository pattern
   - Inconsistent service injection

4. **Configuration Complexity**
   - Multiple config formats (JSON, YAML)
   - Dynamic path resolution can be confusing

5. **Performance Caching**
   - Multiple dirty flag patterns
   - Inconsistent cache invalidation

### Architectural Decisions

1. **Component-Based Units**
   - **Rationale:** Flexibility for unit customization
   - **Trade-off:** More complex initialization

2. **Manager Pattern**
   - **Rationale:** Clear separation of concerns
   - **Trade-off:** Increased coordination overhead

3. **Service Layer**
   - **Rationale:** Reusable business logic
   - **Trade-off:** Additional abstraction layer

4. **Pydantic Config**
   - **Rationale:** Type safety and validation
   - **Trade-off:** Learning curve for contributors

5. **Thread-Safe Telemetry**
   - **Rationale:** Real-time monitoring
   - **Trade-off:** Lock overhead

### Code Patterns

| Pattern | Usage | Location |
|---------|--------|----------|
| Singleton | FleetQueueManager, RNGManager | Various |
| Factory | UnitFactory, TechFactory | src/factories/ |
| Strategy | AI behaviors | src/ai/strategies/ |
| Repository | FleetRepository | src/repositories/ |
| Observer | Telemetry events | src/reporting/ |
| Command | CLI commands | src/cli/commands/ |
| Facade | CombatSimulator | src/combat/ |

---

## Performance Considerations

### Optimization Strategies

1. **Caching**
   - Faction economy cache
   - Fleet power caching
   - Dirty flag pattern for invalidation

2. **Spatial Partitioning**
   - TacticalGrid for combat
   - SpatialGrid for fleet queries

3. **GPU Acceleration**
   - CuPy for batch operations
   - GPUTracker for combat calculations

4. **Lazy Loading**
   - Province nodes on planets
   - Universe-specific data

5. **Profiling**
   - `@profile_method` decorator
   - Performance metrics collection

### Performance Metrics

Tracked metrics include:
- Economy phase time
- Combat resolution time
- Fleet consolidation time
- Memory usage
- CPU utilization

---

## Conclusion

The Multi-Universe Simulator represents a sophisticated grand strategy engine with a well-organized architecture. The modular design with clear separation between models, managers, services, and components enables maintainability and extensibility. Key strengths include:

- Component-based unit system for flexibility
- Comprehensive manager pattern for domain separation
- Service layer for reusable business logic
- Pydantic-based configuration for type safety
- Thread-safe telemetry for real-time monitoring
- GPU acceleration for performance-critical paths

Areas for improvement include:
- Resolving circular dependencies
- Consolidating legacy code
- Standardizing service injection
- Simplifying configuration management
- Improving cache consistency

The codebase demonstrates solid software engineering practices and provides a strong foundation for continued development of the multi-universe simulation system.

---

**Document End**
