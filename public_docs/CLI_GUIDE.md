# CLI Usage Guide

The simulator is primarily controlled via `python run.py`. The simulator is designed for the **eternal_crusade** universe, with support for future expansion to additional settings.

## Universe Selection

The `--universe` parameter is available for future expansion but currently defaults to `eternal_crusade`.

- **Default**: `eternal_crusade`

Example: `python run.py campaign`

---

## 1. Campaign Mode (`campaign`)

Run 4X grand strategy campaigns across a procedurally generated galaxy.

### Quick Start

```bash
# Run a quick 30-turn campaign
python run.py campaign --quick

# Run a custom campaign
python run.py campaign --turns 100 --systems 50
```

### Batch Simulations

Run multiple identical simulations in parallel for data gathering.

```bash
# Run batch simulation defined in default config
python run.py campaign --batch

# Specify custom configuration and output
python run.py campaign --batch --config my_sim.json --output-dir ./results
```

---

## 2. Tactical Simulations (`simulate`)

Test combat rules or unit balance in isolation.

### Duel Mode (1v1)

```bash
# Duel between two units
python run.py simulate --mode duel --units "Zealot Infantry" "Hive Drone"
```

### Grand Royale

```bash
# Free-for-all between all factions
python run.py simulate --mode royale
```

### Fleet Battle

```bash
# Large space battle
python run.py simulate --mode fleet --faction1 "Iron_Vanguard" --faction2 "Void_Corsairs" --size 20
```

---

## 3. Query & Search (`query`)

Search through aggregated simulation reports and the `index.db`.

```bash
# Simple search for a specific event
python run.py query --search "Siege of Solar Primus"

# Filtered search
python run.py query --batch <batch_id> --category combat
```

---

## 4. Data Validation (`validate`)

Ensure integrity of universe data and rebuild optimized JSON registries.

```bash
# Rebuild registries
python run.py validate --rebuild-registries
```

---

## 5. Portal Management (Future Expansion)

Portal management features are available for future multi-universe expansion.

```bash
# List all portals
python run.py list-portals
```

---

## Command Reference Table

| Command    | Universe Parameter                    | Example                                       |
|------------|---------------------------------------|-----------------------------------------------|
| `campaign` | Optional (defaults to eternal_crusade) | `python run.py campaign --quick`              |
| `simulate` | Optional (defaults to eternal_crusade) | `python run.py simulate --mode duel`          |
| `validate` | Optional (defaults to eternal_crusade) | `python run.py validate --rebuild-registries` |
| `query`    | N/A                                   | `python run.py query --search "Event"`        |
| `analyze`  | N/A                                   | `python run.py analyze --type balance`        |

## Interactive Menu

Running `python run.py` without arguments launches the **Interactive Menu**. This allows you to choose your mode via a visual menu system.
