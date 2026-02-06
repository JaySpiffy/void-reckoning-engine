# Void Reckoning: Polyglot Architecture Redesign
## Project Structure Plan

**Document Version:** 1.0  
**Date:** 2026-02-06  
**Status:** Planning Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Proposed Directory Layout](#proposed-directory-layout)
3. [Module Boundaries](#module-boundaries)
4. [File Naming Conventions](#file-naming-conventions)
5. [Build System Configuration](#build-system-configuration)
6. [Shared Definitions](#shared-definitions)
7. [Migration Strategy](#migration-strategy)

---

## Overview

This document defines the project structure for transitioning Void Reckoning from a pure Python codebase to a polyglot architecture. The new structure separates concerns across multiple languages while maintaining clear boundaries and enabling incremental migration.

### Language Responsibilities

| Language | Responsibility | Performance Critical |
|----------|----------------|---------------------|
| **Rust** | Simulation Core (tactical math, combat resolution, spatial indexing) | Yes |
| **C++/Rust** | Galaxy State with ECS (Entity Component System) | Yes |
| **Python** | Turn Orchestrator (sequential faction logic - Total War style) | Moderate |
| **SQLite/Parquet** | Data Layer (persistence, analytics) | N/A |

---

## Proposed Directory Layout

```
void-reckoning/
├── Cargo.toml                          # Rust workspace configuration
├── CMakeLists.txt                      # C++ build configuration
├── setup.py                            # Python package configuration
├── pyproject.toml                      # Modern Python build metadata
├── requirements.txt                    # Python dependencies
├── requirements-dev.txt                # Python dev dependencies
├── README.md
├── LICENSE
├── .gitignore
│
├── rust/                               # Rust workspace root
│   ├── Cargo.toml                      # Workspace manifest
│   ├── Cargo.lock                      # Dependency lock file
│   │
│   ├── simulation_core/                # Rust: Simulation Core
│   │   ├── Cargo.toml                  # Simulation core crate
│   │   ├── src/
│   │   │   ├── lib.rs                  # Library root
│   │   │   ├── mod.rs                  # Module declarations
│   │   │   │
│   │   │   ├── tactical/               # Tactical math and calculations
│   │   │   │   ├── mod.rs
│   │   │   │   ├── ballistics.rs       # Ballistic calculations
│   │   │   │   ├── damage.rs           # Damage resolution
│   │   │   │   ├── hit_resolution.rs   # Hit chance calculations
│   │   │   │   └── modifiers.rs        # Damage modifiers
│   │   │   │
│   │   │   ├── combat/                 # Combat resolution
│   │   │   │   ├── mod.rs
│   │   │   │   ├── resolver.rs         # Combat resolution engine
│   │   │   │   ├── phases.rs           # Combat phase management
│   │   │   │   ├── rounds.rs           # Round-based combat
│   │   │   │   └── outcomes.rs         # Outcome generation
│   │   │   │
│   │   │   ├── spatial/                # Spatial indexing
│   │   │   │   ├── mod.rs
│   │   │   │   ├── grid.rs             # Spatial grid implementation
│   │   │   │   ├── quadtree.rs         # Quadtree indexing
│   │   │   │   ├── partition.rs        # Spatial partitioning
│   │   │   │   └── queries.rs          # Spatial queries
│   │   │   │
│   │   │   ├── physics/                # Physics calculations
│   │   │   │   ├── mod.rs
│   │   │   │   ├── movement.rs         # Movement physics
│   │   │   │   ├── collision.rs        # Collision detection
│   │   │   │   └── vectors.rs         # Vector mathematics
│   │   │   │
│   │   │   ├── ffi/                    # Foreign Function Interface
│   │   │   │   ├── mod.rs
│   │   │   │   ├── python.rs           # Python bindings (PyO3)
│   │   │   │   └── cpp.rs              # C++ bindings (cbindgen)
│   │   │   │
│   │   │   └── types/                  # Core types
│   │   │       ├── mod.rs
│   │   │       ├── combat.rs           # Combat-related types
│   │   │       ├── spatial.rs          # Spatial types
│   │   │       └── result.rs           # Result types
│   │   │
│   │   ├── tests/                      # Rust tests
│   │   │   ├── tactical/
│   │   │   ├── combat/
│   │   │   └── spatial/
│   │   │
│   │   └── benches/                    # Rust benchmarks
│   │       ├── tactical_bench.rs
│   │       └── spatial_bench.rs
│   │
│   ├── ecs/                            # Rust/C++: Entity Component System
│   │   ├── Cargo.toml                  # ECS crate
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── mod.rs
│   │   │   │
│   │   │   ├── core/                   # ECS core implementation
│   │   │   │   ├── mod.rs
│   │   │   │   ├── world.rs            # World/Universe container
│   │   │   │   ├── entity.rs           # Entity ID and management
│   │   │   │   ├── component.rs        # Component trait
│   │   │   │   ├── archetype.rs        # Archetype storage
│   │   │   │   └── query.rs            # Query system
│   │   │   │
│   │   │   ├── components/             # Component definitions
│   │   │   │   ├── mod.rs
│   │   │   │   ├── position.rs         # Position component
│   │   │   │   ├── velocity.rs         # Velocity component
│   │   │   │   ├── health.rs           # Health component
│   │   │   │   ├── faction.rs          # Faction ownership
│   │   │   │   ├── combat.rs           # Combat stats
│   │   │   │   └── economy.rs          # Economy data
│   │   │   │
│   │   │   ├── systems/                # ECS systems
│   │   │   │   ├── mod.rs
│   │   │   │   ├── movement.rs         # Movement system
│   │   │   │   ├── combat.rs           # Combat system
│   │   │   │   ├── economy.rs          # Economy system
│   │   │   │   └── diplomacy.rs        # Diplomacy system
│   │   │   │
│   │   │   ├── resources/              # ECS resources
│   │   │   │   ├── mod.rs
│   │   │   │   ├── time.rs             # Time tracking
│   │   │   │   ├── rng.rs              # Random number generator
│   │   │   │   └── config.rs           # Configuration
│   │   │   │
│   │   │   ├── galaxy/                 # Galaxy state management
│   │   │   │   ├── mod.rs
│   │   │   │   ├── state.rs            # Galaxy state
│   │   │   │   ├── star_systems.rs     # Star system entities
│   │   │   │   ├── fleets.rs           # Fleet entities
│   │   │   │   └── planets.rs          # Planet entities
│   │   │   │
│   │   │   └── ffi/                    # Foreign Function Interface
│   │   │       ├── mod.rs
│   │   │       └── python.rs           # Python bindings
│   │   │
│   │   ├── tests/
│   │   └── benches/
│   │
│   └── cpp_bridge/                     # Rust: C++ bridge (optional)
│       ├── Cargo.toml
│       ├── src/
│       │   ├── lib.rs
│       │   └── bridge.rs               # C++ interoperability
│       └── include/
│           └── bridge.h                # Generated C headers
│
├── cpp/                                # C++ components (if used)
│   ├── CMakeLists.txt                  # C++ project configuration
│   ├── include/
│   │   ├── ecs/
│   │   │   ├── world.hpp
│   │   │   ├── entity.hpp
│   │   │   └── component.hpp
│   │   └── bridge/
│   │       └── rust_bridge.hpp
│   ├── src/
│   │   ├── ecs/
│   │   │   ├── world.cpp
│   │   │   ├── entity.cpp
│   │   │   └── component.cpp
│   │   └── bridge/
│   │       └── rust_bridge.cpp
│   └── tests/
│
├── src/                                # Python: Turn Orchestrator & Legacy
│   ├── __init__.py
│   │
│   ├── orchestrator/                   # Turn Orchestrator (NEW)
│   │   ├── __init__.py
│   │   ├── turn_orchestrator.py        # Main orchestrator
│   │   ├── faction_processor.py       # Per-faction turn processing
│   │   ├── phase_manager.py           # Turn phase management
│   │   ├── action_queue.py             # Action queuing
│   │   └── state_sync.py               # State synchronization with ECS
│   │
│   ├── ai/                             # AI logic (Python)
│   │   ├── __init__.py
│   │   ├── ai_manager.py
│   │   ├── decision_engine.py
│   │   └── strategies/
│   │       ├── aggressive.py
│   │       ├── defensive.py
│   │       └── expansionist.py
│   │
│   ├── diplomacy/                      # Diplomacy system (Python)
│   │   ├── __init__.py
│   │   ├── diplomacy_manager.py
│   │   ├── treaty_system.py
│   │   └── relations.py
│   │
│   ├── economy/                        # Economy logic (Python)
│   │   ├── __init__.py
│   │   ├── economy_manager.py
│   │   ├── resource_flow.py
│   │   └── production.py
│   │
│   ├── combat/                         # Combat (MIGRATING to Rust)
│   │   ├── __init__.py
│   │   ├── combat_orchestrator.py      # Python wrapper for Rust core
│   │   ├── combat_context.py           # Combat context management
│   │   └── legacy/                     # Legacy Python combat (to remove)
│   │       ├── space_combat.py
│   │       └── ground_combat.py
│   │
│   ├── core/                           # Core systems (Python)
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── interfaces.py
│   │   ├── service_locator.py
│   │   └── telemetry.py
│   │
│   ├── managers/                       # Managers (Python)
│   │   ├── __init__.py
│   │   ├── faction_manager.py
│   │   ├── fleet_manager.py
│   │   ├── tech_manager.py
│   │   └── mission_manager.py
│   │
│   ├── reporting/                      # Reporting & telemetry
│   │   ├── __init__.py
│   │   ├── dashboard_provider.py
│   │   ├── combat_replay.py
│   │   └── reporter.py
│   │
│   ├── repositories/                   # Data access (Python)
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── faction_repository.py
│   │   └── fleet_repository.py
│   │
│   ├── models/                         # Data models (Python)
│   │   ├── __init__.py
│   │   ├── faction.py
│   │   ├── fleet.py
│   │   └── planet.py
│   │
│   ├── cli/                            # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   └── utils/                          # Utilities
│       ├── __init__.py
│       └── helpers.py
│
├── data/                               # Game data
│   ├── blueprints/                     # Unit/ship blueprints
│   │   ├── ground/
│   │   ├── ships/
│   │   └── buildings/
│   ├── traits/                         # Trait definitions
│   ├── tech/                           # Technology trees
│   └── config/                         # Configuration files
│
├── schema/                             # Shared definitions (NEW)
│   ├── protobuf/                       # Protocol Buffer definitions
│   │   ├── combat.proto                # Combat message types
│   │   ├── galaxy.proto                # Galaxy state types
│   │   ├── entity.proto                # Entity/component types
│   │   └── events.proto                # Event types
│   │
│   ├── json_schema/                    # JSON schemas
│   │   ├── blueprint_schema.json
│   │   ├── config_schema.json
│   │   └── save_schema.json
│   │
│   └── types/                          # Shared type definitions
│       ├── common_types.md             # Documentation of shared types
│       └── mapping.md                  # Language type mappings
│
├── database/                           # Database layer
│   ├── sqlite/                         # SQLite implementations
│   │   ├── migrations/                # Database migrations
│   │   ├── schema.sql                  # Database schema
│   │   └── repositories.py             # SQLite repositories
│   │
│   └── parquet/                        # Parquet for analytics
│       ├── schema.py                   # Parquet schema definitions
│       └── writers.py                 # Parquet writers
│
├── bindings/                           # Generated bindings (NEW)
│   ├── python/                         # Python bindings
│   │   ├── simulation_core/            # Generated from Rust (PyO3)
│   │   └── ecs/                        # Generated from Rust (PyO3)
│   │
│   └── cpp/                            # C++ bindings
│       └── rust_bridge.h               # Generated from Rust (cbindgen)
│
├── tests/                              # Integration tests
│   ├── integration/                    # Cross-language integration tests
│   │   ├── test_python_rust.py
│   │   ├── test_ecs_orchestrator.py
│   │   └── test_end_to_end.py
│   │
│   ├── performance/                   # Performance tests
│   │   └── benchmark_polyglot.py
│   │
│   └── fixtures/                       # Test fixtures
│       ├── test_galaxy.json
│       └── test_combat.json
│
├── scripts/                            # Utility scripts
│   ├── build.sh                        # Build all components
│   ├── build.bat                       # Windows build script
│   ├── test.sh                         # Run all tests
│   ├── migrate_data.py                 # Data migration utilities
│   └── generate_bindings.py            # Binding generation
│
├── docs/                               # Documentation
│   ├── architecture/                   # Architecture docs
│   │   ├── overview.md
│   │   ├── polyglot_design.md
│   │   └── migration_guide.md
│   │
│   ├── api/                            # API documentation
│   │   ├── python_api.md
│   │   ├── rust_api.md
│   │   └── ffi_reference.md
│   │
│   └── guides/                         # Developer guides
│       ├── getting_started.md
│       ├── contributing.md
│       └── debugging.md
│
├── plans/                              # Planning documents
│   ├── 01_project_structure.md        # This document
│   ├── 02_migration_phases.md          # Migration phases
│   └── 03_performance_targets.md       # Performance targets
│
├── tools/                              # Development tools
│   ├── generate_proto.py               # Protocol buffer generation
│   ├── validate_schema.py              # Schema validation
│   └── benchmark_runner.py             # Benchmark runner
│
├── universes/                          # Universe configurations
│   ├── base/
│   │   ├── universe_config.py
│   │   └── physics_profiles.json
│   └── custom/
│
├── public_docs/                        # Public documentation
│   └── ...
│
└── config/                            # Runtime configuration
    ├── unified_simulation_config.json
    └── test_output_style.json
```

---

## Module Boundaries

### 1. Rust Simulation Core (`rust/simulation_core/`)

**Purpose:** High-performance tactical calculations and combat resolution.

**Responsibilities:**
- Ballistic and damage calculations
- Hit chance resolution
- Combat phase management
- Spatial indexing and queries
- Physics simulations (movement, collision)

**Boundaries:**
- **Inputs:** Combat context, entity positions, combat stats (via FFI)
- **Outputs:** Combat results, damage outcomes, spatial queries (via FFI)
- **Dependencies:** None (pure Rust, minimal external deps)
- **Exposed via:** PyO3 bindings to Python

**Key Modules:**
- `tactical/` - Mathematical calculations
- `combat/` - Combat resolution logic
- `spatial/` - Spatial data structures
- `physics/` - Physics engine
- `ffi/` - Foreign function interface

### 2. ECS Galaxy State (`rust/ecs/` or `cpp/ecs/`)

**Purpose:** Entity Component System for galaxy state management.

**Responsibilities:**
- Entity lifecycle management
- Component storage and retrieval
- System execution (movement, combat, economy)
- Galaxy state serialization

**Boundaries:**
- **Inputs:** Entity creation requests, component updates (via FFI)
- **Outputs:** Entity queries, state snapshots (via FFI)
- **Dependencies:** Simulation core (for combat calculations)
- **Exposed via:** PyO3 bindings to Python

**Key Modules:**
- `core/` - ECS core (world, entity, component)
- `components/` - Component definitions
- `systems/` - ECS systems
- `galaxy/` - Galaxy-specific entities and systems
- `resources/` - Global resources

### 3. Python Turn Orchestrator (`src/orchestrator/`)

**Purpose:** Sequential faction turn processing (Total War style).

**Responsibilities:**
- Turn phase management (begin, action, end)
- Faction action orchestration
- Action queuing and execution
- State synchronization with ECS

**Boundaries:**
- **Inputs:** Galaxy state (from ECS), faction AI decisions
- **Outputs:** Action commands, state updates (to ECS)
- **Dependencies:** ECS (via bindings), AI modules, diplomacy, economy
- **Calls:** Rust simulation core for combat resolution

**Key Modules:**
- `turn_orchestrator.py` - Main orchestrator
- `faction_processor.py` - Per-faction turn logic
- `phase_manager.py` - Phase transitions
- `action_queue.py` - Action management
- `state_sync.py` - ECS synchronization

### 4. Data Layer (`database/`)

**Purpose:** Persistence and analytics data storage.

**Responsibilities:**
- SQLite database for game state persistence
- Parquet files for analytics and reporting
- Data migration and transformation

**Boundaries:**
- **Inputs:** Game state snapshots, combat results
- **Outputs:** Query results, analytics data
- **Dependencies:** None (storage layer)
- **Used by:** Python orchestrator, reporting modules

**Key Modules:**
- `sqlite/` - SQLite operations
- `parquet/` - Parquet analytics

### 5. Shared Definitions (`schema/`)

**Purpose:** Common type definitions and schemas across languages.

**Responsibilities:**
- Protocol buffer definitions for cross-language communication
- JSON schemas for configuration and data validation
- Type mapping documentation

**Boundaries:**
- **Used by:** All language modules
- **Generated:** Bindings, validation code

**Key Modules:**
- `protobuf/` - Protocol buffer definitions
- `json_schema/` - JSON schemas
- `types/` - Type documentation

---

## File Naming Conventions

### Rust Files

| Pattern | Description | Examples |
|---------|-------------|----------|
| `module_name.rs` | Module implementation | `ballistics.rs`, `damage.rs` |
| `mod.rs` | Module declaration (directory root) | `tactical/mod.rs` |
| `lib.rs` | Library root | `simulation_core/src/lib.rs` |
| `main.rs` | Binary entry point | `bin/main.rs` |
| `*_bench.rs` | Benchmark file | `tactical_bench.rs` |
| `test_*.rs` | Test file | `test_combat.rs` |

**Naming Rules:**
- Use `snake_case` for files and directories
- Use `PascalCase` for types, `snake_case` for functions
- Use `SCREAMING_SNAKE_CASE` for constants

### C++ Files

| Pattern | Description | Examples |
|---------|-------------|----------|
| `module_name.cpp` | Implementation | `world.cpp`, `entity.cpp` |
| `module_name.hpp` | Header | `world.hpp`, `entity.hpp` |
| `module_name.h` | C-compatible header | `rust_bridge.h` |

**Naming Rules:**
- Use `snake_case` for files and directories
- Use `PascalCase` for classes, `snake_case` for functions
- Use `SCREAMING_SNAKE_CASE` for constants

### Python Files

| Pattern | Description | Examples |
|---------|-------------|----------|
| `module_name.py` | Module implementation | `turn_orchestrator.py` |
| `__init__.py` | Package marker | `orchestrator/__init__.py` |
| `test_*.py` | Test file | `test_python_rust.py` |
| `conftest.py` | Pytest configuration | `tests/conftest.py` |

**Naming Rules:**
- Use `snake_case` for files and directories
- Use `PascalCase` for classes, `snake_case` for functions and variables
- Use `SCREAMING_SNAKE_CASE` for constants

### Schema Files

| Pattern | Description | Examples |
|---------|-------------|----------|
| `entity.proto` | Protocol buffer | `combat.proto`, `galaxy.proto` |
| `*_schema.json` | JSON schema | `blueprint_schema.json` |
| `*.sql` | SQL schema | `schema.sql` |

### Cross-Language Consistency

| Concept | Rust | C++ | Python | Protocol Buffer |
|---------|------|-----|--------|-----------------|
| Module/Package | `simulation_core` | `ecs` | `simulation_core` | `SimulationCore` |
| Type | `CombatResult` | `CombatResult` | `CombatResult` | `CombatResult` |
| Function | `resolve_combat` | `resolveCombat` | `resolve_combat` | `resolve_combat` |
| Constant | `MAX_DAMAGE` | `MAX_DAMAGE` | `MAX_DAMAGE` | `MAX_DAMAGE` |

---

## Build System Configuration

### Rust Workspace (`Cargo.toml`)

```toml
[workspace]
members = [
    "rust/simulation_core",
    "rust/ecs",
    "rust/cpp_bridge",
]
resolver = "2"

[workspace.dependencies]
# Shared dependencies across workspace crates
pyo3 = { version = "0.20", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
prost = "0.12"
```

### Simulation Core Crate (`rust/simulation_core/Cargo.toml`)

```toml
[package]
name = "simulation_core"
version = "0.1.0"
edition = "2021"

[lib]
name = "simulation_core"
crate-type = ["cdylib", "rlib"]

[dependencies]
pyo3 = { workspace = true }
serde = { workspace = true }
prost = { workspace = true }
nalgebra = "0.32"  # Linear algebra
rand = "0.8"

[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "tactical_bench"
harness = false
```

### ECS Crate (`rust/ecs/Cargo.toml`)

```toml
[package]
name = "void_reckoning_ecs"
version = "0.1.0"
edition = "2021"

[lib]
name = "void_reckoning_ecs"
crate-type = ["cdylib", "rlib"]

[dependencies]
pyo3 = { workspace = true }
serde = { workspace = true }
simulation_core = { path = "../simulation_core" }
bevy_ecs = "0.12"  # ECS framework
```

### C++ Build (`CMakeLists.txt`)

```cmake
cmake_minimum_required(VERSION 3.20)
project(VoidReckoning)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/cpp/include
    ${CMAKE_SOURCE_DIR}/bindings/cpp
)

# ECS library
add_library(ecs_lib
    cpp/src/ecs/world.cpp
    cpp/src/ecs/entity.cpp
    cpp/src/ecs/component.cpp
)

# Bridge library
add_library(rust_bridge
    cpp/src/bridge/rust_bridge.cpp
)

# Tests
enable_testing()
add_subdirectory(cpp/tests)
```

### Python Build (`pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel", "maturin>=1.0"]
build-backend = "setuptools.build_meta"

[project]
name = "void-reckoning"
version = "0.2.0"
description = "Polyglot Grand Strategy Campaign Engine"
requires-python = ">=3.9"
dependencies = [
    "numpy>=1.24",
    "pandas>=2.0",
    "pyarrow>=12.0",
    "protobuf>=4.0",
    "sqlalchemy>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[tool.setuptools]
packages = ["src"]

[tool.maturin]
module-name = "simulation_core._core"
```

### Build Scripts

#### `scripts/build.sh` (Unix)
```bash
#!/bin/bash
set -e

echo "Building Rust workspace..."
cd rust && cargo build --release && cd ..

echo "Building Python bindings..."
maturin develop --release

echo "Building C++ components (if needed)..."
# cmake -S cpp -B cpp/build && cmake --build cpp/build

echo "Generating protocol buffers..."
python scripts/generate_proto.py

echo "Build complete!"
```

#### `scripts/build.bat` (Windows)
```batch
@echo off
echo Building Rust workspace...
cd rust && cargo build --release && cd ..

echo Building Python bindings...
maturin develop --release

echo Generating protocol buffers...
python scripts\generate_proto.py

echo Build complete!
```

---

## Shared Definitions

### Protocol Buffers (`schema/protobuf/`)

Protocol buffers define the cross-language communication layer.

**`combat.proto`**
```protobuf
syntax = "proto3";

package void_reckoning.combat;

message CombatRequest {
    uint64 attacker_id = 1;
    uint64 defender_id = 2;
    repeated CombatUnit units = 3;
    CombatContext context = 4;
}

message CombatResult {
    repeated DamageEvent damage_events = 1;
    CombatOutcome outcome = 2;
    uint32 rounds_fought = 3;
}

message CombatUnit {
    uint64 entity_id = 1;
    uint32 health = 2;
    uint32 attack_power = 3;
    uint32 defense = 4;
}
```

**`galaxy.proto`**
```protobuf
syntax = "proto3";

package void_reckoning.galaxy;

message GalaxyState {
    repeated StarSystem systems = 1;
    repeated Fleet fleets = 2;
    uint64 turn_number = 3;
}

message StarSystem {
    uint64 entity_id = 1;
    string name = 2;
    Position position = 3;
    repeated Planet planets = 4;
}

message Position {
    float x = 1;
    float y = 2;
    float z = 3;
}
```

### JSON Schemas (`schema/json_schema/`)

**`blueprint_schema.json`**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Unit Blueprint",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "name": { "type": "string" },
    "type": { "enum": ["ground", "ship", "building"] },
    "stats": {
      "type": "object",
      "properties": {
        "health": { "type": "integer" },
        "attack": { "type": "integer" },
        "defense": { "type": "integer" }
      },
      "required": ["health", "attack", "defense"]
    }
  },
  "required": ["id", "name", "type", "stats"]
}
```

### Type Mapping (`schema/types/mapping.md`)

| Protocol Buffer | Rust | C++ | Python |
|-----------------|------|-----|--------|
| `uint64` | `u64` | `uint64_t` | `int` |
| `int32` | `i32` | `int32_t` | `int` |
| `float` | `f32` | `float` | `float` |
| `string` | `String` | `std::string` | `str` |
| `repeated T` | `Vec<T>` | `std::vector<T>` | `List[T]` |
| `message` | `struct` | `struct` | `@dataclass` |

---

## Migration Strategy

### Phase 1: Foundation (No Code Changes)

1. **Create directory structure** - Set up new directories without moving code
2. **Define shared schemas** - Create protocol buffer definitions
3. **Set up build system** - Configure Cargo, CMake, and pyproject.toml

### Phase 2: Rust Simulation Core

1. **Implement tactical math** - Ballistics, damage, hit resolution
2. **Implement spatial indexing** - Grid, quadtree, partitioning
3. **Create Python bindings** - PyO3 integration
4. **Write tests** - Unit tests and benchmarks

### Phase 3: ECS Galaxy State

1. **Implement ECS core** - World, entity, component
2. **Define galaxy components** - Position, health, faction, combat
3. **Implement galaxy systems** - Movement, combat, economy
4. **Create Python bindings** - PyO3 integration

### Phase 4: Turn Orchestrator

1. **Create orchestrator module** - New Python code
2. **Implement faction processor** - Sequential turn logic
3. **Integrate with ECS** - State synchronization
4. **Migrate Python managers** - Gradual migration

### Phase 5: Data Layer

1. **Implement SQLite persistence** - Database migrations
2. **Implement Parquet analytics** - Analytics writers
3. **Migrate existing data** - Data transformation scripts

### Phase 6: Cleanup

1. **Remove legacy code** - Delete migrated Python modules
2. **Update documentation** - Architecture docs, API docs
3. **Performance optimization** - Based on benchmarks

### Minimizing Disruption

- **Parallel development**: New code exists alongside legacy code
- **Feature flags**: Toggle between legacy and new implementations
- **Gradual migration**: One module at a time
- **Comprehensive testing**: Ensure parity at each step

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Python Turn Orchestrator                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Faction AI   │  │ Diplomacy    │  │ Economy      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ PyO3 Bindings
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Rust ECS Galaxy State                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ World        │  │ Components   │  │ Systems      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Internal Calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Rust Simulation Core                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Tactical     │  │ Combat       │  │ Spatial      │          │
│  │ Math         │  │ Resolution   │  │ Indexing     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Protocol Buffers
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           Data Layer                             │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ SQLite       │  │ Parquet      │                             │
│  │ Persistence  │  │ Analytics    │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Review this plan** - Confirm structure and conventions
2. **Create migration phases document** - Detailed step-by-step migration plan
3. **Set up build system** - Initialize Cargo, CMake, and pyproject.toml
4. **Define protocol buffers** - Create initial .proto files
5. **Begin Phase 1** - Foundation setup

---

## Appendix: Key Decisions

### Why Rust for Simulation Core?
- Performance: Zero-cost abstractions, efficient memory management
- Safety: Memory safety without garbage collection
- Ecosystem: Excellent numerical libraries (nalgebra, ndarray)
- FFI: First-class Python support via PyO3

### Why ECS for Galaxy State?
- Performance: Cache-friendly data layout
- Flexibility: Easy to add new components and systems
- Scalability: Handles thousands of entities efficiently
- Industry standard: Proven pattern in game engines

### Why Python for Orchestrator?
- Rapid development: Easy to iterate on game logic
- AI integration: Python's ML ecosystem
- Existing codebase: Leverage current Python investment
- Glue language: Excellent FFI support

### Why Protocol Buffers?
- Cross-language: Native support in Rust, C++, Python
- Efficient: Binary serialization, smaller than JSON
- Schema-driven: Type-safe, versioned
- Industry standard: Widely adopted

---

**Document End**
