
# Convenience Scripts

This directory contains easy-to-use wrapper scripts for common workflows. These scripts call the main `run.py` CLI with appropriate defaults.

## Available Scripts

### `setup.py`
**Usage:** `python scripts/setup.py`
- Checks Python version and directory structure.
- Builds initial registries.
- Runs data validation.
- Recommended for first-time users.

### `validate.py`
**Usage:** `python scripts/validate.py [--quick]`
- Rebuilds registries (unless `--quick` is passed).
- Validates all unit data, tech trees, and buildings.
- Reports errors and warnings.

### `simulate.py`
**Usage:** `python scripts/simulate.py [args]`
**Interactive Mode:** Run without arguments to select a mode from a menu.
**Examples:**
- `python scripts/simulate.py --mode duel --units "Space Marine" "Ork Boy"`
- `python scripts/simulate.py --mode fleet --size 50`

### `quick_test.py`
**Usage:** `python scripts/quick_test.py`
- Runs a quick health check sequence:
  1. Validation
  2. Sample System Duel
- Use this to verify the environment is working correctly after changes.
