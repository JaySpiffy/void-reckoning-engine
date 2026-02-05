# Multi-Universe Strategy Engine - Project Documentation

## 1. Project Overview

### What is the Multi-Universe Strategy Engine?

The **Multi-Universe Strategy Engine** is a sophisticated grand strategy campaign simulator / 4X game engine built around the **Void Reckoning** universe—a science fiction setting featuring ten unique factions engaged in galactic warfare.

This is a **headless 4X simulation framework** designed for technical users interested in:
- AI Training (Reinforcement Learning)
- Data Science (Campaign Analytics)
- Robust Backend Logic for web-based strategy games

### Key Features and Capabilities

#### Strategic Systems
- **Ten Unique Factions**: Templars of the Flux, Transcendent Order, Steel-Bound Syndicate, Bio-Tide Collective, Algorithmic Hierarchy, Nebula Drifters, Aurelian Hegemony, Void-Spawn Entities, Scrap-Lord Marauders, Primeval Sentinels
- **Adaptive AI**: Strategic planner featuring Proactive Economic Reserving (early-game scaling), theater manager (Multi-front coordination), industrial allocator (RECOVERY mode), intelligence coordinator, and individual faction personalities
- **Portal System (Experimental)**: Interstellar travel through portal networks and queue-based fleet transfers
- **Task Force Management**: AI fleet coordination with SCOUT, RAID, DEF, ASSAULT types
- **Victory Conditions**: Flexible victory states including Conquest, Elimination, and Defender Survival

#### Combat Systems
- **Real-Time Battle Simulator**: High-fidelity, physics-based combat resolution with integrated space and ground layers
- **Empire at War Style Space Combat**: Tactical fleet engagements featuring targetable Hardpoints (Engines, Shields, Weapons) and ship crippling mechanics
- **Total War Style Ground Combat**: Scale-based planetary warfare with Morale & Suppression systems, flanking penalties, and unit routing
- **Tactical Support**: Off-map Orbital Bombardment provided by fleets in orbit to ground units
- **Cover & Terrain**: Dynamic cover system (Light/Heavy) affecting unit survival and mitigating damage
- **Faction Mechanics**: Unique resource systems and 11+ ability types synchronized with real-time state

#### Economic & Research Systems
- **Modular Ship Design**: Stellaris/Thrawn's Revenge Style architecture with Bow/Core/Stern sections and specialized slot types (S/M/L/X/P/G/H)
- **Research & Tech Tree**: Stellaris-Style card draw system with Hull & Unit Tech Locks, ensuring that advanced ship classes and ground units (e.g., Heavy Walkers, Titans) require dedicated research
- **Infinite Procedural Tech Scaling**: RP-based progression with infinite scaling
- **Specialized Utility Modules**: Advanced ship roles including Tractor Beams (gravitational slowing) and Interdiction Fields (warp-suppression)

#### Performance & Analytics
- **GPU Acceleration**: Full CuPy support with automatic CUDA detection, multi-GPU support, and device selection strategies
- **Parallel Execution**: Simulate multiple campaign scenarios simultaneously on dedicated CPU cores
- **Analytics Engine**: Economic health analysis, military efficiency tracking, industrial analysis, research analytics with predictive modeling
- **Alert System**: Real-time alerts with severity levels (CRITICAL, WARNING, INFO) triggered by anomaly detection
- **Telemetry System**: Comprehensive event tracking with real-time metrics aggregation

#### User Interface
- **Terminal Dashboard**: High-performance, low-latency CLI visualization for real-time campaign monitoring and batch results
- **15 CLI Commands**: Comprehensive simulation control via command-line interface
- **Interactive Menu**: 11-option menu system for easy access to all features

#### Developer Tools
- **Docker Support**: Multi-stage Dockerfile for FastAPI backend + React frontend with Docker Compose configuration
- **70+ Utility Scripts**: Maintenance and analysis tools in `scripts/` and `tools/`
- **Comprehensive Testing**: pytest with specific markers for targeted verification

### Current Project Status

**Version**: 1.0.0 (Void Reckoning Universe)

**Status**: Alpha - Active Development

The engine is in active development with core simulation systems functional. The architecture has been refactored to use modular, decoupled patterns including Service Locator, Repository Pattern, Command Pattern, and Event Bus.

---

## 2. Void Reckoning Universe

### Universe Lore and Concept

The Void Reckoning is a galaxy torn asunder by **"Aether Rifts"**—tears in reality where the laws of physics break down and subjective will overrides objective fact. There is no central government, only warring archetypes struggling for survival, dominance, or transcendence.

#### Core Concepts

- **The Aether**: A dimension of pure energy and thought. It is the source of FTL travel ("Rift-Walking") and "Resonance" (magic/resonants).
- **Conviction**: The measure of a being's ability to impose their will on the Aether. High conviction shields against fluxing and powers weapons.
- **Resonance Nodes**: Strategic points in space where the Aether is stable enough to be harvested.

### The 10 Playable Factions

| Faction | Archetype | Motto | Core Mechanic |
|---------|-----------|-------|---------------|
| **Templars of the Flux** | Crusader | "Steel obeys the Will." | *Conviction* - Gains power from zeal and righteous kills |
| **Transcendent Order** | Resonator | "Flesh is a cage. The Aether is freedom." | *Resonant Dominance* - Masters of morale and mental warfare |
| **Steel-Bound Syndicate** | Industrial | "Reality is non-negotiable." | *Industrial Might* - Overwhelming production and attrition |
| **Bio-Tide Collective** | Biological | *Hunger.* | *Biomass* - Feeds on death to fuel rapid growth |
| **Algorithmic Hierarchy** | Machine | "Logic is absolute." | *Logic Core & Reanimation* - Undying mechanical legions |
| **Nebula Drifters** | Outlaw | "We sow the wind." | *Raid Economy* - Gains wealth through aggression and speed |
| **Aurelian Hegemony** | Order | "For the Light, We Stand." | *Plasma Mastery* - High risk, high reward energy weapons |
| **Void-Spawn Entities** | Chaos | *(Incomprehensible screaming)* | *Aether Overload* - Reality-fluxing magic and instability |
| **Scrap-Lord Marauders** | Horde | "FUROR!!!" | *Furor!* - Momentum-based combat power |
| **Primeval Sentinels** | Elder | "The Stars Remember." | *Eternal* - Elite units that never truly die |

#### Faction Details

**1. Templars of the Flux (The Crusader Archetype)**
A warrior culture that believes the Aether is a test of faith. They wield "Conviction Rifles" that fire projectiles sheathed in psychic energy. Their armor is inscribed with prayers that literally harden the metal against attacks.

**2. Transcendent Order (The Resonator Archetype)**
A monastic transhumanist society. They seek to shed their physical forms and become pure energy. They use "Aether Lances" and "Flux Skiffs" to manipulate the battlefield, turning their enemies' own aggression against them.

**3. Steel-Bound Syndicate (The Industrial Archetype)**
Stubborn materialists who reject the Aether. They rely on "Null-Field Generators" and massive kinetic artillery to deny their enemies' magic. Their ships are flying fortresses of cold, hard steel.

**4. Bio-Tide Collective (The Biological Archetype)**
An endless biological tide that consumes everything in its path. They adapt rapidly, incorporating the genetic strengths of their enemies.

**5. Algorithmic Hierarchy (The Machine Archetype)**
A theocratic AI collective that worships the "Great Algorithm." They view organic life as inefficient and seek to "optimize" the galaxy through assimilation.

**6. Nebula Drifters (The Outlaw Archetype)**
A loose confederation of pirates and anarchists who value freedom above all. They rely on speed and hit-and-run tactics to plunder resources from the slower superpowers.

**7. Aurelian Hegemony (The Order Archetype)**
A utopian authoritarian state that seeks to unite the galaxy under a single, perfect order. They use advanced plasma technology and diplomacy to enforce their will.

**8. Void-Spawn Entities (The Chaos Archetype)**
Nightmares given form. Entities of pure Aether that spill forth from the Rifts to spread madness and destruction. They defy the laws of physics.

**9. Scrap-Lord Marauders (The Horde Archetype)**
Brutal, fun-loving marauders who build weapons from scrap. They literally believe their red vehicles go faster, and because of the Aether, they do.

**10. Primeval Sentinels (The Elder Archetype)**
The dying remnants of the first galactic civilization. They protect the Star-Lattice gates and seek to prevent the younger races from destroying reality.

### Faction Diplomatic Relationships

#### Alliances
- **Pact of Order**: Templars of the Flux + Steel-Bound Syndicate + Aurelian Hegemony (Uneasy alliance against Chaos)
- **The Transcendent**: Transcendent Order + Primeval Sentinels (Seek understanding of Aether)

#### Hostilities
- **Eternal War**: Templars of the Flux vs Void-Spawn Entities
- **Ideological Rivals**: Steel-Bound Syndicate (Materialist) vs Transcendent Order (Spiritualist)
- **Predator & Prey**: Bio-Tide Collective vs Everyone

### Universe-Specific Mechanics

#### Aether
- Source of FTL travel ("Rift-Walking")
- Powers "Resonance" (magic/resonants)
- Can be harvested at Resonance Nodes

#### Conviction
- Measure of ability to impose will on the Aether
- High conviction shields against fluxing
- Powers weapons and abilities

#### Resonance Nodes
- Strategic points in space
- Stable enough to harvest Aether
- Key resource locations for faction expansion

#### Technology & Magic
The universe blends Sci-Fi and Fantasy:
- **Rift-Walking**: FTL travel through hell
- **Null-Field**: Localized bubbles of enforced physics
- **Conviction**: Faith-based shielding
- **Biomancy**: Flesh-shaping magic

---

## 3. Simulation Architecture

### Directory Structure and Organization

```
Multi-Universe Strategy Engine/
├── universes/              # Universe-specific data and rules
│   ├── base/              # Base universe templates
│   ├── void_reckoning/    # Primary universe
│   │   ├── factions/       # Faction data, traits, abilities
│   │   ├── infrastructure/ # Building definitions
│   │   ├── technology/     # Tech trees and research
│   │   └── units/          # Unit rosters
│   ├── cosmic_ascendancy/  # Additional universe
│   ├── procedural_sandbox/ # Procedural generation universe
│   └── test_universe_import/
├── src/
│   ├── ai/                # AI systems and decision making
│   ├── analysis/          # Analytics and data analysis
│   ├── builders/          # Entity builders
│   ├── cli/               # Command-line interface
│   ├── combat/            # Combat systems
│   ├── commands/          # Command pattern implementations
│   ├── config/            # Configuration management
│   ├── core/              # Core systems and interfaces
│   ├── data/              # Data repositories
│   ├── engine/            # Simulation engines
│   ├── events/            # Event system
│   ├── factories/         # Entity factories
│   ├── generators/        # Procedural generation
│   ├── managers/          # Game state managers
│   ├── mechanics/         # Game mechanics
│   ├── models/            # Data models
│   ├── reporting/         # Reporting and analytics
│   ├── repositories/      # Data access layer
│   ├── services/          # Business logic services
│   ├── tools/            # Utility tools
│   └── utils/            # Utility functions
├── scripts/               # Maintenance and analysis scripts
├── tests/                 # Test suite
├── config/                # Configuration files
├── data/                  # Shared data files
├── plans/                 # Planning documentation
├── public_docs/           # Public documentation
└── tools/                 # Additional tools
```

### Key Managers and Their Responsibilities

| Manager | File | Responsibilities |
|---------|------|------------------|
| **AIManager** | `src/managers/ai_manager.py` | Coordinates AI decision making, delegates to strategic planner and theater manager |
| **StrategicPlanner** | `src/ai/strategic_planner.py` | Creates long-term strategic plans, war goals, resource allocation |
| **TheaterManager** | `src/ai/theater_manager.py` | Manages multi-front operations, theater analysis |
| **EconomyManager** | `src/managers/economy_manager.py` | Income, upkeep, construction, recruitment, bankruptcy handling |
| **DiplomacyManager** | `src/managers/diplomacy_manager.py` | Relations, treaties, war exhaustion, diplomatic actions |
| **BattleManager** | `src/managers/battle_manager.py` | Combat resolution, battle initialization |
| **FleetManager** | `src/managers/fleet_manager.py` | Fleet operations, movement, task force coordination |
| **TechManager** | `src/managers/tech_manager.py` | Research, tech tree progression, unlocks |
| **CampaignManager** | `src/managers/campaign_manager.py` | Main campaign orchestration, turn processing |
| **GalaxyGenerator** | `src/managers/galaxy_generator.py` | Procedural galaxy map generation |
| **IntelligenceManager** | `src/managers/intelligence_manager.py` | Fog of war, reconnaissance, intel gathering |
| **PortalManager** | `src/managers/portal_manager.py` | Inter-universe portal travel |
| **WeatherManager** | `src/managers/weather_manager.py` | Dynamic weather events, flux storms |
| **BankingManager** | `src/managers/banking_manager.py` | Loan system, interest processing |
| **MissionManager** | `src/managers/mission_manager.py` | Mission assignment and tracking |
| **PersistenceManager** | `src/managers/persistence_manager.py` | Save/load game state |
| **CacheManager** | `src/managers/cache_manager.py` | Performance optimization through caching |
| **AssetManager** | `src/managers/asset_manager.py` | Asset loading and management |

### Game Loop and Simulation Flow

The gameplay loop follows this sequence:

1. **Campaign Initialization**
   - Load Universe Configuration
   - Initialize Factions
   - Generate Galaxy Map

2. **Turn Processing Loop**
   - AI Strategic Planning
   - Research & Tech Progression
   - Weather & Flux Storms
   - Economic Management
   - Diplomacy Processing
   - Military Operations
   - Combat Encounters (if any)
   - Unit XP & Ability Leveling
   - Check Victory Conditions
   - Increment Turn

3. **Victory Conditions**
   - Conquest
   - Elimination
   - Defender Survival

### System Interactions

The simulation uses an event-driven architecture with the following key interactions:

- **Service Locator**: Centralized dependency injection (`src/core/service_locator.py`)
- **Repository Pattern**: Data access abstraction for Factions, Fleets, Planets, and Units (`src/repositories/`)
- **Command Pattern**: Encapsulated actions with Undo/Redo support (`src/commands/`)
- **Event Bus**: Decoupled event-driven communication (`src/core/event_bus.py`)

---

## 4. Core Systems

### AI System

#### Strategic Planner
Located at: [`src/ai/strategic_planner.py`](src/ai/strategic_planner.py)

The Strategic Planner creates long-term strategic plans for factions including:
- War goals and diplomatic objectives
- Target systems and priority planets
- Multi-front coordination through sub-plans
- Contingency planning

Key Features:
- **Proactive Economic Reserving**: Early-game scaling for rapid expansion
- **Theater-Level Planning**: Analyzes all theaters and creates coordinated strategies
- **Bankruptcy Recovery**: Special strategies for bankrupt factions
- **AI Decision Trace**: Logging for debugging AI decisions

#### Theater Manager
Located at: [`src/ai/theater_manager.py`](src/ai/theater_manager.py)

Manages multi-front operations:
- Theater analysis and classification
- Front line identification
- Resource allocation per theater
- Coordinated multi-front strategies

#### Adaptive Learning
Located at: [`src/ai/adaptation/`](src/ai/adaptation/)

The AI system includes adaptive learning components:
- **Opponent Profiler**: Analyzes enemy strategies
- **Dynamic Weights**: Adjusts priorities based on game state
- **Composition Optimizer**: Optimizes fleet/army composition
- **Coalition Builder**: Manages alliance strategies

#### Economic Engine
Located at: [`src/ai/economic_engine.py`](src/ai/economic_engine.py)

AI economic decision making:
- Resource allocation optimization
- Production queue management
- Bankruptcy prevention
- Industrial scaling

#### Tactical AI
Located at: [`src/ai/tactical_ai.py`](src/ai/tactical_ai.py)

Combat-level AI decisions:
- Target selection
- Ability usage
- Formation adjustments
- Retreat decisions

### Combat System

#### Space Combat
Located at: [`src/combat/space_combat.py`](src/combat/space_combat.py)

**Features:**
- Real-time tactical combat with high-frequency resolution
- Targetable Hardpoints (Engines, Shields, Weapons)
- Ship crippling mechanics
- Formation-based positioning
- Shield regeneration
- Armor penetration
- Critical hits
- Boarding actions

**Combat Phases:**
1. Ability Phase
2. Movement Phase
3. Shooting Phase
4. Melee Phase
5. Morale Phase

**Utility Modules:**
- **Tractor Beam (T)**: Slows enemy ships, prevents retreat
- **Interdiction Field (I)**: Suppresses warp drives, blocks retreat
- **Shield Booster (S)**: Enhances shield regeneration
- **Repair Drone (R)**: Repairs hull damage during combat
- **ECM Suite (E)**: Reduces enemy accuracy

#### Ground Combat
Located at: [`src/combat/ground_combat.py`](src/combat/ground_combat.py)

**Features:**
- Hex-based tactical grid
- Unit types: Infantry, Vehicles, Heroes, Artillery, Aircraft
- Cover system (Light/Heavy)
- Morale system with routing
- Suppression mechanics
- Building combat
- Orbital bombardment support

**Unit Categories:**
| Unit Type | Role | Strengths | Weaknesses |
|-----------|------|-----------|------------|
| Infantry | Frontline, capture | High morale, cover bonus | Low damage, vulnerable to AoE |
| Vehicles | Fire support, breakthrough | High damage, armor | Limited cover use, expensive |
| Heroes | Leadership, special abilities | Buff allies, powerful abilities | Limited availability, high value |
| Artillery | Indirect fire support | Long range, area damage | Weak in direct combat |
| Aircraft | Mobility, reconnaissance | High mobility, bypass terrain | Vulnerable to AA, fuel limits |

**Cover System:**
| Cover Type | Damage Reduction | Availability |
|------------|------------------|---------------|
| Light Cover | 25% | Forests, craters, debris |
| Heavy Cover | 50% | Buildings, bunkers, fortifications |
| Urban Cover | 40% | City blocks, ruins |
| No Cover | 0% | Open terrain, plains |

**Morale States:**
| State | Effect | Recovery |
|-------|--------|----------|
| Steady | Normal combat effectiveness | N/A |
| Shaken | -20% accuracy, -10% damage | Rally from heroes |
| Broken | Cannot attack, -50% movement | Retreat to safe hex |
| Routed | Flees battlefield, removed | Cannot recover |

#### Combat Components

Located at: [`src/combat/components/`](src/combat/components/)

| Component | File | Description |
|-----------|-------|-------------|
| HealthComponent | `health_component.py` | Manages unit health and damage |
| ArmorComponent | `armor_component.py` | Manages unit armor and damage mitigation |
| WeaponComponent | `weapon_component.py` | Manages weapon systems and firing |
| MoraleComponent | `morale_component.py` | Handles morale and routing |
| MovementComponent | `movement_component.py` | Manages unit movement capabilities |
| StatsComponent | `stats_component.py` | Core unit statistics |
| TraitComponent | `trait_component.py` | Manages unit traits |
| CrewComponent | `crew_component.py` | Tracks crew status and casualties |

### Economy System

Located at: [`src/managers/economy_manager.py`](src/managers/economy_manager.py)

**Features:**
- Resource income calculation
- Upkeep processing
- Construction queue management
- Recruitment system
- Bankruptcy handling (RECOVERY mode)
- Loan system (Iron Bank)

**Economic Cycle:**
1. Process Loans & Interest (Priority 1)
2. Pre-calculate economics (ResourceHandler)
3. Collect Income
4. Pay Maintenance
5. Process Construction Queue
6. Handle Trade Routes
7. Check Insolvency

**Resources:**
- **Requisition (REQ)**: Primary currency for construction and recruitment
- **Research Points (RP)**: Used for technology research

**Budgets:**
- Research Budget
- Construction Budget
- Navy Budget
- Army Budget

### Diplomacy System

Located at: [`src/managers/diplomacy_manager.py`](src/managers/diplomacy_manager.py)

**Features:**
- Relationship tracking (-100 to +100 scale)
- Treaty management (Peace, War, Alliance, Trade, etc.)
- War exhaustion system
- Grudge system
- Coalition management
- Proactive diplomacy AI

**Diplomatic Actions:**
- Declare War
- Offer Peace
- Form Alliance
- Trade Agreements
- Demand Tribute
- Insult/Praise

**War Exhaustion:**
- Increases with combat losses
- Reaches 100% triggers forced peace checks
- Affects willingness to continue wars

**Treaty Types:**
- Peace
- War
- Alliance
- Trade Agreement
- Non-Aggression Pact
- Defensive Pact
- Federation

---

## 5. Data Models

### Faction Model

Located at: [`src/models/faction.py`](src/models/faction.py)

**Key Attributes:**
- `name`: Faction identifier
- `uid`: Unique GUID (dual-passport system)
- `requisition`: Current REQ balance
- `budgets`: Budget allocations (research, construction, navy, army)
- `armies`: List of army groups
- `fleets`: List of fleets
- `research_points`: Current RP stockpile
- `research_income`: Per-turn RP generation
- `research_queue`: Research projects queue
- `active_projects`: Active research projects (up to 3 slots)
- `unlocked_techs`: List of unlocked technologies
- `home_planet_name`: Capital planet
- `visible_planets`: Currently visible planets
- `known_planets`: Discovered planets
- `known_factions`: Encountered factions
- `intelligence_memory`: Memory of planet states
- `explored_systems`: Fully scouted systems
- `exploration_frontier`: Priority exploration targets
- `fleet_intel`: Known enemy fleet information
- `active_strategic_plan`: Current strategic plan
- `strategic_posture`: EXPANSION, CONSOLIDATION, DEFENSIVE
- `design_preference`: ANTI_SHIELD, ANTI_ARMOR, AREA_EFFECT
- `personality_id`: AI personality identifier

**Quirks (Data-Driven):**
- `diplomacy_bonus`: Diplomatic modifier
- `retreat_threshold_mod`: Retreat threshold modifier
- `research_multiplier`: Research speed modifier
- `evasion_rating`: Evasion chance
- `casualty_plunder_ratio`: Plunder from casualties
- `navy_recruitment_mult`: Navy recruitment modifier
- `army_recruitment_mult`: Army recruitment modifier
- `biomass_hunger`: Biomass consumption rate
- `threat_affinity`: Threat affinity

### Fleet Model

Located at: [`src/models/fleet.py`](src/models/fleet.py)

**Key Attributes:**
- `name`: Fleet identifier
- `faction`: Owner faction
- `ships`: List of ships in fleet
- `location`: Current location (system/planet)
- `task_force_type`: SCOUT, RAID, DEF, ASSAULT
- `stance`: Combat stance
- `fuel`: Current fuel level

### Unit Model

Located at: [`src/models/unit.py`](src/models/unit.py)

**Key Attributes:**
- `name`: Unit identifier
- `faction`: Owner faction
- `unit_class`: Unit class/type
- `domain`: "space" or "ground"
- `blueprint_id`: Blueprint reference
- `cost`: Unit cost
- `rank`: Regular, Veteran, Elite
- `level`: Current level (1-10)
- `experience`: Current XP
- `xp_gain_rate`: XP gain multiplier
- `abilities`: Available abilities
- `cooldowns`: Ability cooldowns

**Component-Based Architecture:**
- `health_comp`: Health and shield management
- `armor_comp`: Armor and damage mitigation
- `weapon_comps`: List of weapon components
- `morale_comp`: Morale and routing
- `trait_comp`: Unit traits
- `movement_comp`: Movement capabilities
- `stats_comp`: Core statistics (MA, MD, damage, etc.)
- `crew_comp`: Crew status (for ships)

### Planet Model

Located at: [`src/models/planet.py`](src/models/planet.py)

**Key Attributes:**
- `name`: Planet identifier
- `system`: Parent star system
- `owner`: Controlling faction
- `population`: Current population
- `max_population`: Maximum population capacity
- `income`: REQ income
- `buildings`: Constructed buildings
- `terrain`: Terrain type
- `resources`: Available resources

### Component-Based Unit Architecture

The Unit model uses a component-based architecture for flexibility:

**Component Types:**
1. **HealthComponent**: HP, shield, regeneration
2. **ArmorComponent**: Armor value, damage mitigation
3. **WeaponComponent**: Weapon systems, firing logic
4. **MoraleComponent**: Morale value, routing behavior
5. **TraitComponent**: Unit traits and special abilities
6. **MovementComponent**: Movement speed, capabilities
7. **StatsComponent**: Core combat stats (MA, MD, damage, etc.)
8. **CrewComponent**: Crew status (ships only)

This allows for:
- Easy addition of new unit types
- Modular ability systems
- Flexible stat configurations
- Universe-specific mechanics

---

## 6. Entry Points and Usage

### run.py Interactive Menu

Located at: [`run.py`](run.py)

The main entry point provides an interactive menu with the following options:

| Option | Description |
|--------|-------------|
| 1 | Quick Campaign (30 turns) |
| 2 | Batch Campaign (100 runs) |
| 3 | Multi-Universe Parallel Simulation |
| 4 | Tactical Combat |
| 5 | Data Validation |
| 6 | Select Active Universe |
| 7 | Cross-Universe Duel (1v1) |
| 8 | Multi-Universe Fleet Battle (Mixed) |
| 9 | Launch Terminal Dashboard (Demo) |
| 10 | Custom Report Export |
| 0 | Exit |

### CLI Commands

Located at: [`src/cli/commands/`](src/cli/commands/)

| Command | File | Description |
|---------|------|-------------|
| `campaign` | `campaign_cmd.py` | Run campaign simulation |
| `simulate` | `simulate_cmd.py` | Run tactical combat |
| `dashboard` | `dashboard_cmd.py` | Launch terminal dashboard |
| `validate` | `validate_cmd.py` | Validate configurations |
| `analyze` | `analyze_cmd.py` | Analyze campaign data |
| `export` | `export_cmd.py` | Export reports |
| `config` | `config_cmd.py` | Configuration management |
| `generate` | `generate_cmd.py` | Generate assets |
| `multi-universe` | `multi_universe_cmd.py` | Multi-universe simulation |
| `cross-universe` | `cross_universe_cmd.py` | Cross-universe operations |
| `portal` | `portal_cmd.py` | Portal management |
| `query` | `query_cmd.py` | Query game state |

### How to Run Simulations

#### Quick Start
```bash
# Launch interactive menu
python run.py

# Run quick campaign
python run.py campaign --universe void_reckoning --quick

# Run batch campaign
python run.py campaign --universe void_reckoning --batch

# Run tactical combat
python run.py simulate --mode duel

# Launch dashboard
python run.py dashboard
```

#### Campaign Simulation
```bash
# Basic campaign
python run.py campaign --universe void_reckoning --turns 30

# Campaign with custom settings
python run.py campaign --universe void_reckoning --turns 100 --factions 4 --seed 42

# Batch simulation
python run.py campaign --universe void_reckoning --batch --runs 100
```

#### Multi-Universe Simulation
```bash
# Run multiple universes in parallel
python run.py multi-universe --universes void_reckoning,cosmic_ascendancy

# Cross-universe duel
python run.py cross-universe --mode duel --universe1 void_reckoning --universe2 cosmic_ascendancy
```

#### Data Validation
```bash
# Validate all configurations
python run.py validate

# Validate specific universe
python run.py validate --universe void_reckoning
```

---

## 7. Current Project Status

### What's Working

**Core Systems:**
- ✅ Campaign initialization and turn processing
- ✅ Faction initialization with personalities
- ✅ Galaxy map generation
- ✅ Economy system (income, upkeep, construction, recruitment)
- ✅ Diplomacy system (relations, treaties, war exhaustion)
- ✅ Research system with tech trees
- ✅ Space combat with hardpoints and phases
- ✅ Ground combat with hex grid and cover
- ✅ AI strategic planning
- ✅ AI theater management
- ✅ Multi-universe architecture
- ✅ Portal system (experimental)
- ✅ GPU acceleration (CuPy)
- ✅ Analytics engine
- ✅ Terminal dashboard
- ✅ CLI commands

**Void Reckoning Universe:**
- ✅ All 10 factions defined
- ✅ Faction lore and personalities
- ✅ Combat phases defined
- ✅ Tech trees for all factions
- ✅ Unit rosters
- ✅ Building definitions
- ✅ Faction traits

### Known Issues

Based on README analysis and codebase inspection:

**Path Mismatches:**
- Some references in documentation may point to outdated file paths
- The `mechanics_registry.json` file is referenced in config but may not exist in all universes

**Missing Directories:**
- Some universe directories may have incomplete structure
- Not all universes have full implementations

**Experimental Features:**
- Portal system is in active development
- Multi-universe cross-events are experimental
- Some AI features are still being refined

**Performance Considerations:**
- Large-scale simulations may require GPU acceleration
- Memory usage can be high for long campaigns
- Cache management may need optimization

### Version Information

**Engine Version:** 1.0.0
**Void Reckoning Universe Version:** 1.0.0

**Python Requirements:**
- Python 3.8+
- See [`requirements.txt`](requirements.txt) for full dependencies

**Development Requirements:**
- See [`requirements-dev.txt`](requirements-dev.txt) for development dependencies

**Testing:**
- pytest for unit tests
- See [`pytest.ini`](pytest.ini) for test configuration

---

## Appendix

### File References

**Core Engine:**
- [`src/core/service_locator.py`](src/core/service_locator.py) - Dependency injection
- [`src/core/event_bus.py`](src/core/event_bus.py) - Event system
- [`src/core/constants.py`](src/core/constants.py) - Game constants

**Simulation:**
- [`src/engine/simulation_runner.py`](src/engine/simulation_runner.py) - Main simulation runner
- [`src/engine/simulate_campaign.py`](src/engine/simulate_campaign.py) - Campaign simulation
- [`src/engine/multi_universe_runner.py`](src/engine/multi_universe_runner.py) - Multi-universe runner

**Combat:**
- [`src/combat/combat_simulator.py`](src/combat/combat_simulator.py) - Main combat simulator
- [`src/combat/combat_phases.py`](src/combat/combat_phases.py) - Combat phase definitions
- [`src/combat/real_time/simulation_loop.py`](src/combat/real_time/simulation_loop.py) - Real-time loop

**Void Reckoning:**
- [`universes/void_reckoning/config.json`](universes/void_reckoning/config.json) - Universe config
- [`universes/void_reckoning/LORE.md`](universes/void_reckoning/LORE.md) - Universe lore
- [`universes/void_reckoning/ai_personalities.py`](universes/void_reckoning/ai_personalities.py) - AI personalities
- [`universes/void_reckoning/combat_phases.py`](universes/void_reckoning/combat_phases.py) - Combat rules

**Documentation:**
- [`README.md`](README.md) - Main project documentation
- [`plans/simulation_refactoring_analysis.md`](plans/simulation_refactoring_analysis.md) - Refactoring notes

### Additional Resources

**Utility Scripts:**
- [`scripts/`](scripts/) - 70+ maintenance and analysis scripts
- [`tools/`](tools/) - Additional tools

**Testing:**
- [`tests/`](tests/) - Comprehensive test suite

**Configuration:**
- [`config/`](config/) - Configuration files
- [`data/`](data/) - Shared data files

---

*This documentation is based on the actual codebase structure as of the analysis date. For the most current information, refer to the source code and inline documentation.*
