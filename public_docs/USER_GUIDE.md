# User Guide

The Multi-Universe Strategy Engine is a sophisticated grand strategy campaign simulator. This guide is designed for users who want to run simulations, analyze results, and understand the core mechanics of the Void Reckoning universe.

## Table of Contents

- [Quick Start](#quick-start)
- [Running Campaigns](#running-campaigns)
- [Tactical Simulations](#tactical-simulations)
- [Dashboard](#dashboard)
- [Querying Results](#querying-results)
- [Configuration](#configuration)

## Quick Start

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build Rust combat engine (optional, falls back to Python if unavailable)
cd native_pulse/void_reckoning_bridge
maturin develop
cd ../..
```

### Run a Campaign

```bash
# Quick campaign with default settings
python run.py campaign --universe void_reckoning --quick

# Custom campaign
python run.py campaign --universe void_reckoning --turns 100 --systems 20
```

### Run Tactical Simulation

```bash
# Duel between two units
python run.py simulate --mode duel --units "Zealot Infantry" "Hive Drone"

# Grand Royale (all factions)
python run.py simulate --mode royale

# Fleet battle
python run.py simulate --mode fleet --faction1 "Templars_of_the_Flux" --faction2 "BioTide_Collective" --size 20
```

### Launch Dashboard

```bash
# Launch terminal dashboard
python run.py dashboard

# Monitor active simulation
python run.py dashboard --monitor
```

## Running Campaigns

Campaigns are the primary way to experience the Void Reckoning universe. Each campaign simulates a galaxy with factions competing for control and victory.

### Campaign Options

| Option | Description | Example |
|---------|-------------|----------|
| `--quick` | Quick 30-turn campaign | `python run.py campaign --quick` |
| `--turns N` | Set number of turns | `python run.py campaign --turns 500` |
| `--systems N` | Number of star systems | `python run.py campaign --systems 50` |
| `--min-planets N` | Minimum planets per system | `python run.py campaign --min-planets 1` |
| `--max-planets N` | Maximum planets per system | `python run.py campaign --max-planets 5` |
| `--gpu` | Enable GPU acceleration | `python run.py campaign --gpu` |
| `--gpu-strategy auto|first|most_vram|most_cores|specific` | GPU device selection | `python run.py campaign --gpu --gpu-strategy auto` |
| `--batch` | Run multiple simulations | `python run.py campaign --batch` |

### Victory Conditions

Campaigns end when one of the following conditions is met:

- **Conquest**: Control all star systems
- **Elimination**: Eliminate all enemy factions
- **Defender Survival**: Survive until turn limit

### Understanding the Void Reckoning Universe

The Void Reckoning universe features ten unique factions, each with distinct playstyles and mechanics:

| Faction | Playstyle | Key Mechanics |
|----------|----------|---------------|
| **Templars of the Flux** | Religious Warriors | Conviction resource, morale bonuses |
| **Transcendent Order** | Psychic Mastery | Flux Energy, telekinetic abilities |
| **Steel-Bound Syndicate** | Industrial Might | Industrial Capacity, heavy armor |
| **Bio-Tide Collective** | Biological Horde | Biomass, rapid reproduction |
| **Algorithmic Hierarchy** | Technological Supremacy | Processing Power, drone swarms |
| **Nebula Drifters** | Raiders & Pirates | Salvage, stealth, boarding |
| **Aurelian Hegemony** | Diplomatic Empire | Trade Credits, allied fleets |
| **Void-Spawn Entities** | Dimensional Invaders | Corruption, dark energy |
| **Scrap-Lord Marauders** | Resource Scavengers | Scrap, improvised weapons |
| **Primeval Sentinels** | Precursor Civilization | Time Energy, ancient tech |

## Tactical Simulations

Tactical simulations allow you to test combat mechanics and unit balance in isolation.

### Simulation Modes

| Mode | Description | Example |
|------|-------------|----------|
| `duel` | 1v1 combat between two units | `python run.py simulate --mode duel --units "Unit A" "Unit B"` |
| `royale` | Free-for-all with all factions | `python run.py simulate --mode royale` |
| `fleet` | Large-scale fleet battle | `python run.py simulate --mode fleet --faction1 "Faction A" --faction2 "Faction B" --size 50` |

### Unit Categories

Units in Void Reckoning fall into several categories:

- **Infantry**: Frontline combat units with morale bonuses
- **Vehicles**: Armored units with high damage output
- **Heroes**: Special units with powerful abilities
- **Artillery**: Long-range indirect fire support
- **Aircraft**: High mobility and reconnaissance

### Combat Mechanics

- **Morale System**: Units break and route when morale reaches critical levels
- **Suppression System**: Heavy fire reduces combat effectiveness
- **Cover System**: Light and heavy cover provide damage reduction
- **Orbital Bombardment**: Fleets provide ground support
- **Ability Progression**: Units gain XP and unlock abilities during combat

## Dashboard

The terminal dashboard provides real-time monitoring of campaigns and simulations.

### Dashboard Features

- **Real-time Updates**: Live turn-by-turn progress
- **Faction Statistics**: Economic score, military power, tech level
- **Diplomatic Relations**: Alliance blocs and war status
- **Global Summary**: Active battles, flux storms, neutral worlds
- **Batch Monitoring**: Track multiple simulation runs with aggregated statistics

### Interactive Controls

| Key | Action |
|-----|--------|
| `q` / `Ctrl+C` | Quit dashboard |
| `p` | Pause/Resume updates |
| `r` | Force refresh |
| `d` | Toggle detailed faction stats |
| `s` | Toggle galactic summary |
| `y` | Toggle galactic diplomacy |
| `f` | Filter factions by name |
| `1-9` | Quick filter by faction index |

### Configuration Options

The dashboard behavior can be configured via environment variables and command-line flags:

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DASHBOARD_REFRESH_RATE` | Update interval in milliseconds | 500 |
| `DASHBOARD_SHOW_DETAILS` | Show detailed faction stats | true |
| `DASHBOARD_COLOR_SCHEME` | Color scheme (auto/light/dark) | auto |

## Querying Results

The query command allows you to search through simulation reports and the indexed database.

### Query Examples

```bash
# Search for specific events
python run.py query --search "Orbital Bombardment"

# Filter by faction
python run.py query --faction "Templars_of_the_Flux" --category combat

# Query specific batch
python run.py query --batch <batch_id> --turns 100
```

### Query Filters

| Filter | Description |
|--------|-------------|
| `--faction` | Filter by faction name |
| `--category` | Filter by event category (combat, diplomacy, economy) |
| `--search` | Search for specific text in events |
| `--turns` | Filter by turn range |
| `--batch` | Specify batch ID |

## Configuration

### Universe Configuration

The active universe is `void_reckoning`. Configuration files are located in the `config/` directory.

### Key Configuration Files

| File | Description |
|-------|-------------|
| `void_reckoning_config.json` | Main simulation configuration |
| `dashboard_config.json` | Dashboard settings |
| `alert_rules.yaml` | Alert system rules |
| `analytics_config.yaml` | Analytics engine configuration |

### Configuration Parameters

Key parameters in `void_reckoning_config.json`:

- `campaign.turns`: Number of turns to simulate
- `campaign.num_systems`: Number of star systems
- `combat.use_rust`: Enable Rust combat engine (default: true)
- `combat.max_duration_seconds`: Maximum combat duration
- `economy.base_income_req`: Base income requirement
- `units.max_fleet_size`: Maximum fleet size
- `units.max_land_army_size`: Maximum army size

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Dashboard not updating** | Press `r` to force refresh |
| **High CPU usage** | Increase `refresh_rate` or use `--quiet` mode |
| **GPU not detected** | Ensure Rust bridge is built with `maturin develop` |
| **Simulation crashes** | Check logs in `logs/` directory |
| **Import errors** | Run `python run.py validate --universe void_reckoning --rebuild-registries` |

## Additional Resources

- [CLI Guide](CLI_GUIDE.md) - Complete command reference
- [Architecture Overview](ARCHITECTURE_OVERVIEW.md) - High-level system architecture
- [Multi-Universe Guide](MULTI_UNIVERSE_GUIDE.md) - Multi-universe architecture
- [Developer Guide](DEVELOPER_GUIDE.md) - Technical contribution guidelines
