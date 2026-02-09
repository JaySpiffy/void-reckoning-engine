# Native Pulse: Rust Integration Master Roadmap

## Void Reckoning Engine

> [!IMPORTANT]
> This roadmap synthesizes the architectural directives from the "God Perspective" and "Native Pulse" design documents. It serves as the master execution guide for migrating core engine components from Python to Rust.

---

## 1. Initiative Overview

**Goal**: Transition the Void Reckoning Engine from a Python-heavy simulation to a high-performance **Python Brain / Rust Body** architecture.
**Target Performance**: 100x speedup in pathfinding, 50x in combat, 20x in economy/auditing.
**Key Technology**: `PyO3` for zero-copy bridging, `Rust` for core simulation logic, `Python` for high-level orchestration/AI.

### Architecture: The "God Perspective"

The new architecture introduces complete observability ("God Perspective") by embedding instrumentation directly into the Rust core.

- **Decision Instrumentation**: Why did the AI do X? (Captured in Rust)
- **Causal Traceability**: Event A caused Event B. (Linked via Correlation IDs)
- **State Auditing**: Is the simulation valid? (Continuous Rust-speed checks)
- **Deterministic Replay**: Re-run specific ticks exactly.

---

## 2. Migration Phases (Critical Path)

### 🏗️ Phase 1: Foundation & Mobility (The "Body")

**Scope**: `Pathfinder`, `GraphTopology`, `MovementCalculator`.
**Docs**: `09_phase1_migration_pathfinding.md`
**Why First?**: Movement is the most expensive operation (A*) and has the fewest dependencies on other game systems. It establishes the `PyO3` patterns for the rest of the project.

- [ ] **Step 1.1**: Set up Rust crate structure (`void-reckoning-rust`).
- [ ] **Step 1.2**: Implement `GraphTopology` (Hex grid, obstacles).
- [ ] **Step 1.3**: Implement `Pathfinder` (A*, JPS, FlowFields).
- [ ] **Step 1.4**: Create Python bindings (`PyGraph`, `PyPathfinder`) and swap out `navigation_manager.py`.

### ⚔️ Phase 2: Conflict Resolution (The "Fists")

**Scope**: `CombatResolver`, `Ballistics`, `DamageCalculations`.
**Docs**: `10_phase2_migration_combat.md`
**Why Second?**: Depends on mobility (Phase 1) for range/LoS checks but is self-contained enough to be parallelized.

- [ ] **Step 2.1**: Implement `ballistics` (hit probability, tracking).
- [ ] **Step 2.2**: Implement `damage` (armor penetration, shields, hull).
- [ ] **Step 2.3**: Build `CombatResolver` loop.
- [ ] **Step 2.4**: Bind to `combat_simulator.py`.

### ⚖️ Phase 3: The Auditor (The "Conscience")

**Scope**: `GlobalAuditor`, `StateValidator`, `SanityChecks`.
**Docs**: `11_phase3_migration_auditor.md`
**Why Third?**: Needs to validate data structures involved in Phases 1 & 2. Running these checks in Python is currently too slow to happen every tick.

- [ ] **Step 3.1**: Define Rust `Validator` traits.
- [ ] **Step 3.2**: Port consistency rules (Unit integrity, Resource conservation).
- [ ] **Step 3.3**: Implement background "Silent Rot" detection.

### 💰 Phase 4: Economy (The "Metabolism")

**Scope**: `ResourceCalculator`, `BudgetAllocator`, `InsolvencyHandler`.
**Docs**: `12_phase4_migration_economy.md`
**Why Fourth?**: Deeply coupled with almost every game object. Migrating this requires the other systems (especially the Rust data structures for Units/Planets) to be stable.

- [ ] **Step 4.1**: Implement `ResourceCalculator` (Income/Upkeep).
- [ ] **Step 4.2**: Implement `BudgetAllocator` (Priority queues).
- [ ] **Step 4.3**: Bind to `economy_manager.py`.

---

## 3. Bridge Layer Specification

**Doc**: `08_pyo3_bridge_layer_specification.md`

We will explicitly **avoid** complex object synchronization where possible.

- **Pattern**: "Rust Owns the Truth".
- **Data Flow**: Python passes *Commands* -> Rust updates *State* -> Rust returns *View/Events*.
- **Safety**: Use `PyResult` for all boundary crossings. `panic!` in Rust must catch_unwind before hitting Python.

## 4. Testing Strategy

**Doc**: `13_testing_validation_strategy.md`

1. **Unit Tests (Rust)**: Test core logic (e.g., "Does A* find the shortest path?"). Run via `cargo test`.
2. **Integration Tests (Python)**: Test bindings (e.g., "Can I instantiate a Rust Pathfinder from Python?"). Run via `pytest`.
3. **Parity Tests**: Run Python and Rust implementations side-by-side on the same seed. Assert outputs match 100%.

## Phase 5: Verification & Integration (Current Focus)

While the functional core is complete, the "God Perspective" observability layer is missing from the Rust modules.

### [ ] Step 5.1: Observability Injection

- [ ] **Bridge**: Expand `CorrelationContext` to support event logging and decision recording.
- [ ] **Combat**: Instrument `BattleEngine` to log target selection reasons and damage events.
- [ ] **Auditor**: Instrument `ValidationEngine` to log rule failures with context.
- [ ] **Economy**: Instrument `IncomeEngine` to log budget allocation decisions.

### [ ] Step 5.2: Python Integration

- [ ] Update `void_reckoning_bridge` to expose `get_event_log()` and `get_decision_log()`.
- [ ] Connect Python `Telemetry` system to consume Rust logs.

## 5. Immediate Next Steps (Phase 1 Execution)

1. Initialize `native_pulse/void_reckoning_rust` cargo workspace.
2. Add `pyo3` and `maturin` dependencies.
3. Copy `GraphTopology` logic from `navigation_manager.py` to Rust struct.
