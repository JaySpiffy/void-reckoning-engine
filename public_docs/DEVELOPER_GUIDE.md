# Developer Guide

This guide is for developers who want to contribute to the Multi-Universe Strategy Engine. It covers development setup, architecture patterns, testing, and contribution guidelines.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Core Systems](#core-systems)
- [Design Patterns](#design-patterns)
- [Testing](#testing)
- [Contributing](#contributing)

## Development Setup

### Prerequisites

- **Python 3.8+** (tested up to 3.11)
- **Rust toolchain** (for combat engine development)
- **Git** (for version control)

### Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd <repository-name>

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install Rust toolchain (for combat engine)
rustup update stable
rustup default stable
```

### Building the Rust Combat Engine

```bash
# Navigate to Rust bridge
cd native_pulse/void_reckoning_bridge

# Build and install
maturin develop

# Test the build
python -c "from void_reckoning_bridge import RustCombatEngine; print('Rust engine available')"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m void_reckoning
pytest -m performance
pytest -m integration
pytest -m gpu
pytest -m analytics

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Architecture

### Core Architecture

The Multi-Universe Strategy Engine uses a modular, decoupled architecture with several key design patterns:

- **Dependency Injection**: [`DIContainer`](src/core/di_container.py) and [`ServiceLocator`](src/core/service_locator.py)
- **Event Bus**: [`EventBus`](src/events/event_bus.py) for loose coupling
- **Command Pattern**: [`CommandBus`](src/commands/command_bus.py) for action management
- **Repository Pattern**: Data access layer in [`src/repositories/`](src/repositories/)
- **Factory Pattern**: Unit, weapon, tech, design generation in [`src/factories/`](src/factories/)

### Directory Structure

```
src/
├── ai/                      # AI components (strategic planner, theater manager, etc.)
├── analysis/                # Analysis tools
├── combat/                  # Combat system (space, ground, tactical)
├── commands/               # Command pattern implementation
├── core/                    # Core infrastructure (config, DI, event bus)
├── engine/                  # Simulation runners (multi-universe, batch)
├── events/                  # Event system (event bus, subscribers)
├── factories/              # Factory pattern (unit, weapon, tech, design)
├── managers/               # Domain managers (campaign, economy, diplomacy, AI)
├── mechanics/               # Faction mechanics engine
├── models/                  # Data models (unit, fleet, planet, faction)
├── observability/          # Causal tracing, replay, snapshot management
├── reporting/               # Analytics and dashboard systems
├── repositories/           # Data access layer
├── services/               # Business logic services
└── utils/                  # Utility functions
```

## Core Systems

### Event Bus

The central event dispatcher enables loose coupling between systems.

```python
from src.events.event_bus import EventBus

# Get singleton instance
event_bus = EventBus.get_instance()

# Subscribe to events
def handle_combat_event(event):
    # Handle combat event
    pass

# Publish events
event_bus.publish("combat_started", {"faction": "Templars", "location": "System-7"})
```

### Command Pattern

Actions are encapsulated as commands with undo/redo support.

```python
from src.commands.command_bus import CommandBus

# Execute command
CommandBus.execute(AttackCommand(
    attacker="Templars_of_the_Flux",
    target="BioTide_Collective",
    location="System-7"
))

# Undo last command
CommandBus.undo()
```

### Dependency Injection

Services and managers are injected via DI container.

```python
from src.core.service_locator import ServiceLocator

# Get service
campaign_manager = ServiceLocator.get("campaign_manager")
```

## Design Patterns

### Repository Pattern

Data access is abstracted through repositories for clean separation of concerns.

Available repositories:
- [`FactionRepository`](src/repositories/faction_repository.py)
- [`FleetRepository`](src/repositories/fleet_repository.py)
- [`PlanetRepository`](src/repositories/planet_repository.py)
- [`SystemRepository`](src/repositories/system_repository.py)
- [`UnitRepository`](src/repositories/unit_repository.py)

### Factory Pattern

Factories generate game objects with consistent interfaces.

Available factories:
- [`UnitFactory`](src/factories/unit_factory.py)
- [`WeaponFactory`](src/factories/weapon_factory.py)
- [`TechFactory`](src/factories/tech_factory.py)
- [`DesignFactory`](src/factories/design_factory.py)
- [`HullMutationFactory`](src/factories/hull_mutation_factory.py)
- [`LandFactory`](src/factories/land_factory.py)

## Core Systems

### Combat System

The combat system supports both Python and Rust implementations:

- **Space Combat**: Fleet engagements with hardpoints and ship crippling
- **Ground Combat**: Hex-based tactical warfare with morale and suppression
- **Rust Combat Engine**: High-performance native calculations via [`void_reckoning_bridge`](native_pulse/void_reckoning_bridge/src/lib.rs)
- **Tactical Grid**: Hex-based positioning with terrain effects

### AI System

The AI system uses a modular architecture with multiple coordinators:

- **Strategic Planner**: High-level decision making with war goals
- **Theater Manager**: Multi-front operations
- **Economic Engine**: Resource management and economic health monitoring
- **Intelligence Coordinator**: Espionage and intelligence operations
- **Personality Manager**: Dynamic faction personality loading
- **Tech Doctrine Manager**: Research strategy management

### Mechanics Engine

Faction-specific mechanics are loaded dynamically and applied at strategic hooks.

```python
from src.mechanics.faction_mechanics_engine import FactionMechanicsEngine

# Apply mechanics
mechanics_engine.apply_mechanics("Templars_of_the_Flux", "economy_phase", context)
```

## Testing

### Test Structure

Tests are organized by category using pytest markers:

```bash
# Run all tests
pytest

# Run specific categories
pytest -m void_reckoning
pytest -m performance
pytest -m integration
pytest -m gpu
pytest -m analytics
```

### Writing Tests

Tests should follow these guidelines:

- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Include assertions for expected behavior
- Add docstrings explaining test purpose
- Keep functions focused and single-purpose
- Use meaningful variable names

### Test Markers

Available pytest markers:
- `void_reckoning`: Void Reckoning specific tests
- `performance`: Performance benchmarks
- `integration`: Full data layer integration tests
- `gpu`: GPU-specific tests
- `analytics`: Analytics engine tests

## Contributing

### Code Style Guidelines

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write descriptive docstrings
- Keep functions focused and single-purpose
- Use meaningful variable names

### Pull Request Process

1. Fork the repository
2. Create a descriptive branch name
3. Make your changes focused on a single feature or bug fix
4. Write tests for new functionality
5. Update documentation if needed
6. Ensure all tests pass

### Reporting Issues

When reporting bugs or requesting features:

- Use GitHub Issues with clear descriptions
- Include steps to reproduce the issue
- Provide expected vs actual behavior
- Include environment details (Python version, OS, etc.)

### Adding New Features

Consider the following when adding features:

- **Compatibility**: How does this affect existing universes?
- **Performance**: What is the performance impact?
- **Documentation**: What documentation needs updating?
- **Testing**: What tests are needed?

### Architecture Decisions

When making architectural changes:

- Maintain backward compatibility where possible
- Use deprecation warnings for breaking changes
- Update relevant documentation
- Consider impact on existing universes
- Run full test suite before merging

## Additional Resources

- [User Guide](USER_GUIDE.md) - End-user documentation
- [CLI Guide](CLI_GUIDE.md) - Command reference
- [Architecture Overview](ARCHITECTURE_OVERVIEW.md) - High-level architecture
- [Multi-Universe Guide](MULTI_UNIVERSE_GUIDE.md) - Multi-universe architecture
- [Project Structure](PROJECT_STRUCTURE.md) - Detailed project structure
- [Game Loop](GAME_LOOP.md) - Complete game loop documentation
