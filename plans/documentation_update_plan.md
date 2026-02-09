# Documentation Update Plan

## Overview
This plan outlines the comprehensive documentation update required for the Multi-Universe Strategy Engine. The project has evolved significantly since the last documentation update, with major new systems including Rust combat engine integration, observability systems, command pattern implementation, Dashboard v2 API, and more.

## Current State Analysis

### Key Changes Since Last Documentation
1. **Main Universe**: Changed from `eternal_crusade` to `void_reckoning` (original IP)
2. **Rust Integration**: High-performance combat engine via `void_reckoning_bridge`
3. **Observability System**: Causal tracing, replay analysis, snapshot management
4. **Command Pattern**: Attack, build, move fleet commands with command bus
5. **Dashboard v2** (In Development): FastAPI-based dashboard with WebSocket support
6. **Event Bus**: Central event dispatcher with subscriber pattern
7. **Faction Mechanics Engine**: Pluggable faction-specific mechanics system
8. **AI System**: Strategic planner, theater manager, adaptation engine, coalition builder
9. **Multi-Universe Architecture**: Parallel execution with portal traversal
10. **Repository Pattern**: Data access layer for factions, fleets, planets, systems, units
11. **Factory Pattern**: Unit, weapon, tech, design, hull mutation factories

### Available Universes
- void_reckoning (main - 10 factions) - Only active universe currently

### CLI Commands
- campaign, simulate, validate, config, multi-universe, dashboard, portal, analyze, query, cross-universe, generate, export

## Documentation Structure

### 1. README.md (Project Root)
**Purpose**: High-level project overview and quick start guide
**Audience**: Both users and developers

**Sections to Include**:
- Project title and description
- Quick start commands
- Core features (updated with current systems)
- Architecture overview
- Available universes
- CLI command summary
- Installation instructions
- Quick reference table
- Links to detailed documentation

**Key Updates**:
- Update universe references from eternal_crusade to void_reckoning
- Add Rust combat engine section
- Update feature list with new systems
- Update quick start examples
- Note that Dashboard v2 is in development
- Note that void_reckoning is the only active universe

### 2. USER_GUIDE.md (public_docs/)
**Purpose**: Practical guide for running simulations and analyzing results
**Audience**: Users who want to run simulations

**Sections to Include**:
- Installation and setup
- Running campaigns
- Running tactical simulations
- Using the dashboard
- Querying and analyzing results
- Multi-universe simulations
- Configuration options
- Troubleshooting common issues

### 3. DEVELOPER_GUIDE.md (public_docs/)
**Purpose**: Technical guide for contributors
**Audience**: Developers contributing to the codebase

**Sections to Include**:
- Development environment setup
- Project structure overview
- Coding standards and conventions
- Testing guidelines
- Adding new universes
- Adding new factions
- Extending the combat system
- Working with the Rust bridge
- Event system usage
- Command pattern usage
- Contributing guidelines

### 4. ARCHITECTURE_OVERVIEW.md (public_docs/)
**Purpose**: High-level system architecture documentation
**Audience**: Both users and developers

**Sections to Include**:
- Multi-universe architecture
- Core engine components
- Data flow diagrams
- System interactions
- Technology stack
- Design patterns used
- Performance considerations

**Mermaid Diagrams**:
- Overall system architecture
- Multi-universe flow
- Data flow between components
- Event system flow

### 5. PROJECT_STRUCTURE.md (public_docs/) - UPDATE
**Purpose**: Detailed project structure documentation
**Audience**: Developers

**Updates Required**:
- Update universe references to void_reckoning
- Add new directories (observability, commands, ai/, etc.)
- Update Rust integration paths
- Update dashboard v2 structure
- Add factory pattern directories
- Add repository pattern directories

### 6. GAME_LOOP.md (public_docs/) - UPDATE
**Purpose**: Complete game loop documentation
**Audience**: Developers

**Updates Required**:
- Verify current game loop implementation
- Add new hooks for faction mechanics
- Update with event system integration
- Add command pattern integration
- Update with observability hooks

### 7. CLI_GUIDE.md (public_docs/) - UPDATE
**Purpose**: CLI usage documentation
**Audience**: Both users and developers

**Updates Required**:
- Update universe references to void_reckoning
- Add new commands (cross-universe, generate, export)
- Update examples with current options
- Add multi-universe command examples
- Update dashboard command documentation

### 8. MULTI_UNIVERSE_GUIDE.md (public_docs/) - UPDATE
**Purpose**: Multi-universe simulation guide
**Audience**: Advanced users and developers

**Updates Required**:
- Update to reflect void_reckoning as only active universe
- Note multi-universe architecture is preserved for future expansion
- Update with current universe list (void_reckoning only)
- Add troubleshooting for current implementation
- Update architecture diagrams

### 9. RUST_COMBAT_ENGINE.md (public_docs/) - NEW
**Purpose**: Rust combat engine integration documentation
**Audience**: Developers

**Sections to Include**:
- Overview of Rust integration
- Building the Rust bridge
- Using the Rust combat engine
- Performance benefits
- API reference
- Troubleshooting
- Extending the Rust engine

**Key Files**:
- `native_pulse/void_reckoning_bridge/src/lib.rs`
- `src/combat/rust_tactical_engine.py`

### 10. OBSERVABILITY_SYSTEM.md (public_docs/) - NEW
**Purpose**: Observability system documentation
**Audience**: Developers

**Sections to Include**:
- System overview
- Causal tracing
- Replay analysis
- Snapshot management
- Event logging
- Telemetry integration
- Usage examples

**Key Files**:
- `src/observability/causal_tracer.py`
- `src/observability/replay_analyzer.py`
- `src/observability/snapshot_manager.py`
- `src/observability/replay_engine.py`
- `src/observability/graph_store.py`

### 11. COMMAND_PATTERN.md (public_docs/) - NEW
**Purpose**: Command pattern implementation documentation
**Audience**: Developers

**Sections to Include**:
- Command pattern overview
- Available commands
- Creating new commands
- Command bus usage
- Undo/redo functionality
- Examples

**Key Files**:
- `src/commands/command_bus.py`
- `src/commands/attack_command.py`
- `src/commands/build_command.py`
- `src/commands/move_fleet_command.py`
- `src/commands/base_command.py`

### 12. DASHBOARD_V2_API.md (public_docs/) - NEW
**Purpose**: Dashboard v2 API documentation
**Audience**: Developers

**Note**: Dashboard v2 is currently in development. This documentation should be marked as work-in-progress.

**Sections to Include**:
- API overview
- WebSocket endpoints
- REST API routes
- Authentication
- Real-time updates
- Testing the API
- Extending the dashboard

**Key Files**:
- `src/reporting/dashboard_v2/api/main.py`
- `src/reporting/dashboard_v2/api/routes/`
- `src/reporting/dashboard_v2/api/websocket.py`

### 13. FACTION_MECHANICS.md (public_docs/) - NEW
**Purpose**: Faction mechanics engine documentation
**Audience**: Developers

**Sections to Include**:
- Mechanics engine overview
- Creating faction-specific mechanics
- Mechanics hooks
- Mechanics loader
- Examples from void_reckoning
- Testing mechanics

**Key Files**:
- `src/mechanics/faction_mechanics_engine.py`
- `src/mechanics/mechanics_loader.py`
- `universes/void_reckoning/mechanics_registry.json`

### 14. EVENT_BUS_ARCHITECTURE.md (public_docs/) - NEW
**Purpose**: Event bus system documentation
**Audience**: Developers

**Sections to Include**:
- Event bus overview
- Event types
- Subscribing to events
- Publishing events
- Built-in subscribers
- Creating custom subscribers
- Event flow diagrams

**Key Files**:
- `src/events/event_bus.py`
- `src/events/event.py`
- `src/events/subscribers/telemetry_subscriber.py`
- `src/events/subscribers/dashboard_subscriber.py`

### 15. AI_SYSTEM_ARCHITECTURE.md (public_docs/) - NEW
**Purpose**: AI system documentation
**Audience**: Developers

**Sections to Include**:
- AI system overview
- Strategic planner
- Theater manager
- Adaptation engine
- Coalition builder
- Personality system
- AI strategies
- Extending AI behavior

**Key Files**:
- `src/ai/strategic_planner.py`
- `src/ai/theater_manager.py`
- `src/ai/adaptation/learning_engine.py`
- `src/ai/coalition_builder.py`
- `src/ai/posture_system.py`

### 16. UNIVERSE_CREATION_GUIDE.md (public_docs/) - UPDATE
**Purpose**: Guide for creating new universes
**Audience**: Developers

**Updates Required**:
- Update with current universe structure
- Add void_reckoning examples
- Update config.json schema
- Add faction mechanics setup
- Add AI personalities setup
- Update with current file paths

## Implementation Order

### Phase 1: Core Documentation (Priority)
1. Update README.md
2. Create USER_GUIDE.md
3. Create DEVELOPER_GUIDE.md
4. Create ARCHITECTURE_OVERVIEW.md

### Phase 2: System Documentation
5. Update PROJECT_STRUCTURE.md
6. Update GAME_LOOP.md
7. Update CLI_GUIDE.md
8. Update MULTI_UNIVERSE_GUIDE.md

### Phase 3: New System Documentation
9. Create RUST_COMBAT_ENGINE.md
10. Create OBSERVABILITY_SYSTEM.md
11. Create COMMAND_PATTERN.md
12. Create DASHBOARD_V2_API.md

### Phase 4: Advanced System Documentation
13. Create FACTION_MECHANICS.md
14. Create EVENT_BUS_ARCHITECTURE.md
15. Create AI_SYSTEM_ARCHITECTURE.md
16. Update UNIVERSE_CREATION_GUIDE.md

## Documentation Standards

### Markdown Formatting
- Use proper markdown headers (##, ###)
- Include code blocks with language specification
- Use mermaid diagrams for architecture visualization
- Include file path references in format: [`filename.py`](relative/path/to/file.py)
- Keep line length reasonable for readability

### Code Examples
- Provide working code examples
- Include import statements
- Add comments explaining key parts
- Test examples before including

### Diagrams
- Use mermaid for flowcharts and sequence diagrams
- Keep diagrams simple and readable
- Avoid double quotes ("") and parentheses () inside square brackets ([])
- Label all nodes and edges clearly

### Cross-References
- Link between related documentation
- Reference specific files with line numbers where relevant
- Include links to related code sections

## Review Process

Each documentation file should be reviewed for:
- Accuracy against current codebase
- Clarity and readability
- Completeness of coverage
- Consistency with other documentation
- Working code examples
- Correct mermaid diagram syntax

## Notes

- All documentation should be in `public_docs/` directory except README.md which stays at project root
- Use clear, descriptive filenames
- Include table of contents for longer documents
- Update this plan as new systems are added or existing systems change
