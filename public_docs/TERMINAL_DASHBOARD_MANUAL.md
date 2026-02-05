# Terminal Dashboard User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Dashboard Layout](#dashboard-layout)
3. [Metrics Explained](#metrics-explained)
4. [Color Coding](#color-coding)
5. [Faction Abbreviations](#faction-abbreviations)
6. [Interactive Controls](#interactive-controls)
7. [Configuration](#configuration)
8. [Special Features](#special-features)

---

## Introduction

### What is the Terminal Dashboard?

The Terminal Dashboard is a real-time, interactive visualization tool for monitoring multi-universe simulation campaigns. It provides a comprehensive view of simulation progress, faction statistics, diplomatic relationships, and performance metrics through an intuitive terminal-based interface.

### What is it Used For?

The dashboard serves several key purposes:

- **Real-time Monitoring**: Track simulation progress across multiple universes and runs simultaneously
- **Performance Analysis**: Monitor turn processing times, memory usage, and system performance
- **Faction Tracking**: Observe faction growth, military strength, and economic status
- **Diplomatic Intelligence**: View alliances, wars, trade relationships, and alliance blocs
- **Strategic Overview**: Access galaxy maps, victory progress, and military theater information
- **Alert Management**: Receive and review critical alerts and warnings during simulation

### How to Access It

The dashboard is automatically launched when running simulations through the multi-universe runner. To access it:

```bash
# Run a simulation campaign
python -m src.engine.simulate_campaign --config config/unified_simulation_config.json

# Or use the multi-universe runner
python -m src.engine.multi_universe_runner
```

The dashboard will appear in your terminal and update in real-time as the simulation progresses.

---

## Dashboard Layout

### Header Section

The top of the dashboard displays:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    MULTI-UNIVERSE SIMULATION DASHBOARD
Output: output/ | GPU: RTX 4090 (Device 0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

- **Title**: Identifies the dashboard
- **Output Directory**: Shows where simulation data is being saved
- **GPU Information**: Displays the selected GPU model and device ID (if GPU acceleration is enabled)

### Controls Bar

Located immediately below the header, the controls bar shows available keyboard shortcuts and current state:

```
Controls: (q)uit (p)ause (d)iplomacy (y)details (s)ummary (f)ilter (h)elp (a)lerts (v)ictory (m)ap
```

When paused or filtering, additional indicators appear:
- **PAUSED**: Yellow highlight when dashboard is paused
- **Filter: XXXX**: Shows active faction filter

### Performance & ETA Line

This line displays real-time performance metrics and estimated time to completion:

```
Elapsed: 5m 23s | ⏱ 2.34s/turn | 🚀 42.75 tps | 🧠 1024MB ↑ | ETA: 12m 45s
```

- **Elapsed**: Total time since session start
- **s/turn**: Average time to process one turn
- **tps**: Turns per second (throughput)
- **Memory**: Current memory usage with trend indicator
- **ETA**: Estimated time to complete all turns

### Universe Sections

Each universe being simulated has its own section:

```
[VOID_RECKONING] - Cores: Auto
  Progress: 2/5 Runs Completed
  Run 001: ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ Turn  45 | Running
```

- **Universe Name**: Displayed in brackets
- **Processor Affinity**: CPU core assignment
- **Progress**: Completed runs vs total runs
- **Run Status**: Individual run progress bars with turn numbers and status

### Galactic Summary

The dashboard supports two modes for the galactic summary:

#### FULL Mode

Displays a detailed boxed summary with comprehensive statistics:

```
     ╔══════════════ GLOBAL GALACTIC SUMMARY ════════════════╗
     ║ Planets: 300 total | 0 ntl (0%) | 16 cont (5%) | 284 held (95%) ║
     ║ Battles: ⚔ 45 active | 🚀 23 space | 🪖 22 ground              ║
     ║ Turn Losses: 💀 12.5K | 🚀 8,200 ships | 🪖 4,300 ground        ║
     ║ Total Deaths: 💀 145.2K | 🚀 98,100 ships | 🪖 47,100 ground     ║
     ║ Diplomacy: ⚔ 3 wars | 🤝 2 allies | 📦 5 trade                ║
     ║ Economy: 💰 Flowing | Tech: 🔬 245 pts | Flux: ⚡ 0 blocking     ║
     ║ ![CRIT] SYSTEMS NOMINAL                                      ║
     ╚══════════════════════════════════════════════════════════════╝
```

#### COMPACT Mode

Displays a single-line quick summary:

```
     [Q] Quick: P:300 N:0 B:45 C:12500 R:2.4M T:2.34s
```

Toggle between modes using the **`s`** key.

### Diplomacy Section

The diplomacy section shows relationships between factions:

```
     [GALACTIC DIPLOMACY] (SUMMARY)
     ⚔ 3 wars | 🤝 2 alliances | 📦 5 trades
     --- ALLIANCE BLOCS ---
     Bloc 1: [AUR, TRA]
     Bloc 2: [BIO, NEB]
```

Diplomacy view modes (cycle with **`d`**):
- **OFF**: Hide diplomacy section
- **SUMMARY**: Show counts of wars, alliances, and trades
- **EVERYTHING**: Show all diplomatic relationships
- **NO_WAR**: Show all relationships except wars

### Faction Statistics Table

The faction statistics table provides detailed information about each faction:

```
     #   TAG     SCORE   SYS OWN(A) CON(A) CTY B(AVG)   SB F(AVG)  A(AVG)      REQ   T WRS   W/L/D   L(S) L(G) POST
     1   1AUR    45.2K    12   8(1.2)  4(1.5)  45  65(1.4)  3 15(12)   8(6)    2.4M  45   0  12/3/2   120   45   EXP
     2   1TRA    38.7K    10   6(1.1)  3(1.3)  38  58(1.5)  2 12(10)   7(5)    1.8M  42   0   8/4/3    85   32   BAL
```

### Overlays

The dashboard includes several overlay screens that can be toggled:

#### Help Overlay (`h` or `?`)

```
   ╔════ INTERACTIVE SHORTCUTS ════╗
   ║ q : Quit Dashboard / Stop Sim ║
   ║ p : Pause/Resume Display      ║
   ║ d : Cycle Diplomacy Views    ║
   ║ y : Cycle Faction Details    ║
   ║ s : Cycle Galactic Summary   ║
   ║ f : Filter by Faction Tag     ║
   ║ t : Toggle Military Theaters  ║
   ║ v : Toggle Victory Progress   ║
   ║ a : Toggle Alert History      ║
   ║ m : Toggle Galaxy map         ║
   ║ e : Export / Save Screenshot  ║
   ║ h : Toggle Help Overlay       ║
   ║ 1-9 : Quick Filter Index      ║
   ╚═══════════════════════════════╝
```

#### Victory Overlay (`v`)

Shows progress toward victory conditions:

```
     ╔══════════ GALACTIC VICTORY PROGRESS - Turn 45 ═══════════╗
     ║ Aurelian Hegemony [1] ║ ████████████████░░░░░░░░░░░░░░░ ║  45.2% ║
     ║ Transcendent Order [2] ║ ████████████████░░░░░░░░░░░░░░░ ║  42.8% ║
     ╚══════════════════════════════════════════════════════════════╝
     Target: Control 75% of Galaxy Systems
     (Press 'v' to close, 'q' to quit)
```

#### Alerts Overlay (`a`)

Displays recent critical and warning alerts:

```
     ╔════════════ CRITICAL ALERT HISTORY ════════════╗
     ║ CRITICAL | Faction eliminated: ScrapLord Marauders ║
     ║ WARNING  | Low requisition: Nebula Drifters      ║
     ║ INFO     | Alliance formed: AUR-TRA              ║
     ╚══════════════════════════════════════════════════╝
```

#### Map Overlay (`m`)

Displays a tactical galaxy map:

```
     ╔═══════════════════════[ SDR-9 SCANNER ]═══════════════════════╗
     ║  Y-AXIS                                                       ║
     ║ 14 │ ···A···A·····B···B·····T····· │    ║
     ║ 10 │ ··A····A····B·····B·····T···· │    ║
     ║  6 │ ·A·····A····B·····B·····T···· │    ║
     ║  2 │ A·······A····B·····B·····T···· │    ║
     ║    └────────────────────────────────────    ║
     ║        00   10   20   30   40   54  X-AXIS      ║
     ╚═[ LIVE FEED OK ]══════════════════════════════[ m:CLOSE ]═╝
     SENSORS: ● Neutral | Held | Capital | · Deep Space
```

---

## Metrics Explained

### Global Metrics

| Metric | Description | Importance |
|--------|-------------|------------|
| **Planets** | Total number of planets in the galaxy | Indicates galaxy size and available territory |
| **Ntl (Neutral)** | Number of uncontrolled planets | Shows remaining unclaimed territory |
| **Cont (Contested)** | Number of planets being fought over | Indicates active conflict zones |
| **Held** | Number of planets under faction control | Shows colonization progress |
| **Battles** | Total active battles | Indicates overall conflict intensity |
| **Space Battles** | Battles occurring in space | Shows fleet engagement level |
| **Ground Battles** | Battles occurring on planets | Shows invasion/ground war activity |
| **Casualties** | Units lost this turn | Current turn combat intensity |
| **Total Deaths** | Cumulative casualties | Total war cost across simulation |
| **Diplomacy** | Wars, alliances, trade relationships | Political landscape overview |
| **Economy** | Economic flow status | Faction financial health |
| **Tech** | Average technology points | Research progress level |
| **Flux** | Storms blocking movement | Environmental hazards affecting travel |

### Performance Metrics

| Metric | Description | Importance |
|--------|-------------|------------|
| **Turn Time** | Average time to process one turn | Simulation speed indicator |
| **TPS (Turns Per Second)** | Throughput metric | Overall simulation efficiency |
| **Memory** | Current memory usage | System resource consumption |
| **ETA** | Estimated time to completion | Projected finish time |

### Faction Metrics

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **#** | Rank | Faction ranking by score |
| **TAG** | Faction Tag | 3-4 character faction identifier |
| **SCORE** | Total Score | Composite faction strength metric |
| **SYS** | Systems | Number of star systems controlled |
| **OWN(A)** | Owned (Avg) | Owned planets with average per system |
| **CON(A)** | Contested (Avg) | Contested planets and average number of cities on contested worlds |
| **CTY** | Cities | Total cities across all planets |
| **B(AVG)** | Buildings (Avg) | Total buildings with average per city |
| **SB** | Starbases | Number of starbases constructed |
| **F(AVG)** | Fleets (Avg) | Current fleets with average fleet size |
| **A(AVG)** | Armies (Avg) | Current armies with average army size |
| **REQ** | Requisition | Economic resource available |
| **T** | Tech | Technology level achieved |
| **WRS** | Wars | Number of active wars |
| **W/L/D** | Wins/Losses/Draws | Battle record |
| **L(S)** | Losses (Ship) | Ship casualties |
| **L(G)** | Losses (Ground) | Ground unit casualties |
| **POST** | Posture | Strategic stance (EXP/BAL/DEF) |

### Metric Importance

- **Score**: Primary indicator of overall faction strength
- **Systems/Planets**: Core territorial control metric
- **Fleets/Armies**: Military capability indicators
- **Requisition**: Economic power and ability to sustain operations
- **Tech**: Research progress and technological advantage
- **Wars**: Active conflicts requiring attention
- **Posture**: Strategic direction (Expansion/Balanced/Defense)

---

## Color Coding

### Text Colors

| Color | ANSI Code | Usage |
|-------|-----------|-------|
| **White** | `\033[97m` | Default text, neutral values |
| **Bold** | `\033[1m` | Emphasized text, headers |
| **Dim** | `\033[2m` | Secondary information, placeholders |
| **Red** | `\033[91m` | Errors, critical alerts, wars, losses |
| **Green** | `\033[92m` | Success, completed runs, held territory |
| **Yellow** | `\033[93m` | Warnings, in-progress, contested territory |
| **Blue** | `\033[94m` | Information, space battles, trade |
| **Cyan** | `\033[96m` | Neutral territory, alliances |
| **Magenta** | `\033[95m` | Special sections, headers |
| **Black** | `\033[30m` | Background highlights |

### Background Colors

| Color | ANSI Code | Usage |
|-------|-----------|-------|
| **On Yellow** | `\033[43m` | Paused state indicator |

### Trend Indicators

| Icon | Meaning |
|------|---------|
| **↑** (Green) | Increasing value (positive trend) |
| **↓** (Red) | Decreasing value (negative trend) |
| **→** (Dim) | Stable value (no change) |

### Progress Bar Colors

| Color | Meaning |
|-------|---------|
| **Green** | High completion (>60%) or healthy status |
| **Yellow** | Medium completion (30-60%) or warning status |
| **Dim White** | Low completion (<30%) or inactive status |
| **Dim** | Empty portion of progress bar |

### Status Colors

| Status | Color | Meaning |
|--------|-------|---------|
| **Running** | Green | Active simulation in progress |
| **Waiting** | Yellow | Queued or waiting for resources |
| **Done** | Green | Simulation completed successfully |
| **Error** | Red | Simulation encountered an error |

### Diplomatic Relationship Colors

| Relationship | Color | Icon |
|--------------|-------|------|
| **War** | Red | ⚔ |
| **Alliance** | Green/Cyan | 🤝 |
| **Vassal** | Cyan | 👑 |
| **Trade** | Blue | 💰 |

---

## Faction Abbreviations

### Void Reckoning Universe

| Abbreviation | Full Name |
|--------------|-----------|
| **TPL** | Templars of the Flux |
| **TRA** | Transcendent Order |
| **STE** | SteelBound Syndicate |
| **BIO** | BioTide Collective |
| **ALG** | Algorithmic Hierarchy |
| **NEB** | Nebula Drifters |
| **AUR** | Aurelian Hegemony |
| **VOI** | VoidSpawn Entities |
| **SCR** | ScrapLord Marauders |
| **PRM** | Primeval Sentinels |

### Faction Tag Format

Faction tags in the dashboard follow this format:
- **[Instance][Abbreviation]** - e.g., `1AUR` for Aurelian Hegemony, instance 1
- Maximum 4 characters total
- Instance number is omitted if only one instance exists

---

## Interactive Controls

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| **`q`** | Quit | Stop simulation and exit dashboard |
| **`p`** | Pause | Toggle pause/resume display updates |
| **`d`** | Diplomacy | Cycle through diplomacy view modes |
| **`y`** | Details | Cycle faction detail modes (HIDDEN/SUMMARY/EVERYTHING) |
| **`s`** | Summary | Toggle galactic summary mode (FULL/COMPACT) |
| **`f`** | Filter | Enter faction filter mode |
| **`t`** | Theaters | Toggle military theater overview |
| **`v`** | Victory | Toggle victory progress overlay |
| **`a`** | Alerts | Toggle alert history overlay |
| **`m`** | Map | Toggle galaxy map overlay |
| **`e`** or **`c`** | Export | Export current session data to file |
| **`h`** or **`?`** | Help | Toggle help overlay |
| **`1-9`** | Quick Filter | Filter to show faction at index N |
| **`Enter`** | Confirm | Confirm filter input |
| **`Esc`** | Cancel | Cancel filter input or close overlay |
| **`Backspace`** | Delete | Remove last character from filter |

### Filter Mode Instructions

1. Press **`f`** to enter filter mode
2. Type the faction tag (e.g., "AUR", "1TRA", "NEB")
3. Press **Enter** to apply the filter
4. Press **Esc** to cancel without filtering

The filter matches against:
- Faction tags (e.g., "AUR", "1TRA")
- Full faction names (e.g., "Aurelian")

### Overlay Usage

All overlays follow the same pattern:
- Press the shortcut key to open the overlay
- The overlay replaces the main dashboard view
- Press the same key or **`Esc`** to close the overlay
- Some overlays (like Victory) can remain open while simulation continues

### View Mode Cycles

#### Diplomacy Modes (`d`)
1. **OFF** - Hide diplomacy section
2. **SUMMARY** - Show counts only
3. **EVERYTHING** - Show all relationships
4. **NO_WAR** - Show all except wars

#### Faction Detail Modes (`y`)
1. **HIDDEN** - Hide faction statistics table
2. **SUMMARY** - Show top 10 factions
3. **EVERYTHING** - Show all factions

#### Galactic Summary Modes (`s`)
1. **FULL** - Show detailed boxed summary
2. **COMPACT** - Show single-line quick summary

---

## Configuration

### Dashboard Config File

The dashboard configuration is stored in `config/dashboard_config.json`:

```json
{
    "server": {
        "host": "localhost",
        "port": 5000,
        "debug": false
    },
    "streaming": {
        "buffer_size": 1000,
        "metrics_window_seconds": 60,
        "update_interval_ms": 2000
    },
    "visualization": {
        "max_data_points": 100,
        "faction_colors": {
            "Hegemony": "#FFD700",
            "Chaos": "#8B0000",
            "Aether-Kin": "#4169E1",
            "Marauders": "#228B22",
            "Tau": "#00CED1",
            "Hierarchs": "#32CD32",
            "Bio-Morphs": "#8B008B"
        },
        "heatmap_grid_size": 10
    },
    "cache": {
        "enabled": true,
        "ttl_seconds": 60
    }
}
```

### Configuration Options

#### Server Settings
- **host**: Server hostname for web dashboard
- **port**: Server port for web dashboard
- **debug**: Enable debug mode for development

#### Streaming Settings
- **buffer_size**: Number of data points to buffer
- **metrics_window_seconds**: Time window for rolling metrics
- **update_interval_ms**: Update frequency in milliseconds

#### Visualization Settings
- **max_data_points**: Maximum data points to display in charts
- **faction_colors**: Color mapping for factions
- **heatmap_grid_size**: Grid resolution for heatmaps

#### Cache Settings
- **enabled**: Enable/disable data caching
- **ttl_seconds**: Cache time-to-live in seconds

### Customizing Settings

To customize dashboard settings:

1. Open `config/dashboard_config.json`
2. Modify the desired values
3. Save the file
4. Restart the simulation for changes to take effect

Example: Change update frequency

```json
"streaming": {
    "update_interval_ms": 1000  // Update every second instead of 2 seconds
}
```

### Faction Colors

Customize faction colors by adding entries to the `faction_colors` object:

```json
"faction_colors": {
    "Aurelian_Hegemony": "#FFD700",
    "Transcendent_Order": "#00CED1",
    "BioTide_Collective": "#8B008B"
}
```

---

## Special Features

### Double-Buffering

The dashboard uses double-buffering to ensure smooth, flicker-free updates:

1. **Buffer Creation**: All display content is built in memory first
2. **Screen Clear**: Terminal is cleared once per frame
3. **Single Write**: Entire buffer is written in one operation
4. **Flush**: Output is flushed to ensure immediate display

This prevents visual artifacts and ensures consistent rendering.

### Data Caching

The dashboard implements intelligent caching to improve performance:

- **TTL-based Expiration**: Cached data expires after a configurable time
- **Automatic Invalidation**: Cache is invalidated when simulation is paused
- **Session Caching**: Last known state is preserved during pauses
- **Memory-efficient**: Only essential data is cached

Cache configuration in `dashboard_config.json`:

```json
"cache": {
    "enabled": true,
    "ttl_seconds": 60
}
```

### Number Formatting

Large numbers are automatically formatted with suffixes for readability:

| Range | Format | Example |
|-------|--------|---------|
| 0 - 999 | Integer | `42` |
| 1,000 - 999,999 | K suffix | `42.5K` |
| 1,000,000 - 999,999,999 | M suffix | `42.5M` |
| 1,000,000,000+ | B suffix | `42.5B` |

The `format_large_num()` function handles this formatting automatically.

### Alliance Group Detection

The dashboard automatically detects and displays alliance blocs:

1. **Graph Construction**: Builds a graph of alliance relationships
2. **Connected Components**: Identifies connected factions using BFS
3. **Group Coloring**: Assigns unique colors to each bloc
4. **Display**: Shows bloc membership in diplomacy section

Example output:

```
--- ALLIANCE BLOCS ---
Bloc 1: [AUR, TRA]
Bloc 2: [BIO, NEB]
```

### Trend Tracking

The dashboard tracks metric trends across turns:

- **Comparison**: Each turn is compared to the previous turn
- **Direction**: Up, Down, or Stable
- **Visual Indicators**: Color-coded arrows (↑↓→)
- **Global Trends**: Tracked for GLOBAL_ prefixed metrics

### Export Functionality

Press **`e`** or **`c`** to export current session data:

- **Format**: JSON
- **Location**: `reports/dashboard_exports/`
- **Filename**: `stats_export_YYYYMMDD_HHMMSS.json`
- **Content**: Complete current statistics snapshot

### GPU Information Display

The dashboard displays GPU information when available:

```
GPU: RTX 4090 (Device 0)
```

This is retrieved from the GPU utilities and shows:
- Model name
- Device ID (for multi-GPU systems)

### Error Handling

The dashboard includes robust error handling:

- **Graceful Degradation**: Continues running even if some data is unavailable
- **Error Display**: Critical errors are shown in the galactic summary
- **Traceback Display**: Full error traces are printed for failed runs
- **Status Indicators**: Color-coded status for each run

### Multi-Universe Support

The dashboard can monitor multiple universes simultaneously:

- **Independent Sections**: Each universe has its own section
- **Progress Tracking**: Separate progress bars for each universe
- **Run Management**: Track multiple runs per universe
- **Processor Affinity**: Shows CPU core assignment per universe

---

## Tips and Best Practices

### Performance Optimization

1. **Use COMPACT Mode**: Switch to compact summary mode (`s`) for faster updates
2. **Filter Factions**: Use filters (`f`) to focus on specific factions
3. **Hide Details**: Hide faction details (`y`) when not needed
4. **Disable Overlays**: Close overlays when not actively viewing them

### Monitoring Strategies

1. **Start with SUMMARY**: Begin with summary views to get the big picture
2. **Focus on Leaders**: Filter to top factions to track leaders
3. **Watch Alerts**: Keep alerts overlay (`a`) accessible for critical events
4. **Check Victory**: Periodically check victory progress (`v`) to see who's winning

### Debugging

1. **Pause on Error**: Dashboard pauses automatically on critical errors
2. **Review Tracebacks**: Error traces are displayed at the bottom of the screen
3. **Export Data**: Export (`e`) data for offline analysis
4. **Check Memory**: Monitor memory usage for potential leaks

---

## Troubleshooting

### Dashboard Not Updating

- Check if paused (look for "PAUSED" indicator)
- Press `p` to resume if paused
- Verify simulation is still running

### Flickering Display

- Ensure terminal supports ANSI color codes
- Try a different terminal emulator
- Check for background processes interfering with output

### Missing Data

- Wait for simulation to initialize
- Check for error messages in the galactic summary
- Verify database connection is healthy

### Keyboard Input Not Responding

- Ensure terminal has focus
- Check if filter mode is active (look for filter prompt)
- Press `Esc` to exit any active overlay

### Memory Usage High

- Switch to COMPACT mode (`s`)
- Reduce update frequency in config
- Filter to show fewer factions

---

## Appendix

### ANSI Color Reference

```
\033[0m    Reset
\033[1m    Bold
\033[2m    Dim
\033[91m   Red
\033[92m   Green
\033[93m   Yellow
\033[94m   Blue
\033[95m   Magenta
\033[96m   Cyan
\033[97m   White
\033[30m   Black (text)
\033[43m   Yellow (background)
```

### Unicode Characters Used

| Character | Usage |
|-----------|-------|
| ⚔ | War/Sword |
| 🤝 | Alliance/Handshake |
| 📦 | Trade/Package |
| 💰 | Economy/Money Bag |
| 🔬 | Tech/Microscope |
| ⚡ | Flux/Lightning |
| 💀 | Casualties/Skull |
| 🚀 | Space/Rocket |
| 🪖 | Ground/Soldier |
| 👑 | Vassal/Crown |
| ● | Neutral Planet |
| █ | Filled Progress |
| ░ | Empty Progress |
| ╔ ═ ╗ ║ ╚ ╝ | Box Drawing |

### File Locations

- **Dashboard Code**: `src/reporting/terminal_dashboard.py`
- **Config File**: `config/dashboard_config.json`
- **Faction Abbreviations**: `src/core/constants.py`
- **Exports**: `reports/dashboard_exports/`

---

*Version 1.0 | Last Updated: 2025*
