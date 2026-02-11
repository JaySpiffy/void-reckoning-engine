# Testing Guide

This project maintains rigorous test coverage to ensure stability. Tests are divided into core engine tests (universe-agnostic) and universe-specific validation tests. The simulator currently focuses on the **void_reckoning** universe.

## Running Tests

### Standard Execution
Runs all core engine and unit tests.
```bash
pytest
```

### Universe-Specific Tests
Test a specific universe implementation and its data integrity.
```bash
# Test void_reckoning only
pytest -m void_reckoning
pytest tests/test_multi_universe_runner.py -k void_reckoning
```

### Multi-Universe Integration (Future Expansion)
Verify that multiple universes can run in parallel without cross-contamination.
```bash
pytest tests/test_multi_universe_runner.py
pytest tests/test_universe_isolation.py
```

### Dashboard Tests
Verify the FastAPI backend and React frontend.
```bash
# Backend (FastAPI)
pytest src/reporting/dashboard_v2/tests

# Frontend (Vitest)
cd frontend
npm test
npm run test:coverage
```

## Test Structure
- `tests/`: Core engine unit and integration tests.
- `tests/universes/`: Tests specific to a particular setting (e.g., void_reckoning faction logic).
- `tests/utils/`: Shared test helpers and universe data loaders.

## Key Verification Commands
Beyond `pytest`, use CLI validation and a known-good simulation command to confirm runtime health:
```bash
# Check for broken unit stats or invalid tech links
python run.py validate --universe void_reckoning --rebuild-registries

# Typical simulation run used in this repository
python run.py multi-universe --config config/void_reckoning_config.json
```

## Adding New Tests
1. **Engine Logic**: Place in `tests/` and use mocks for universe-specific data.
2. **Universe Content**: Place in `tests/universes/` and use the `set_active_universe` fixture to load the correct context.
3. **Data Integrity**: New universes should be added to the `test_universe_loader.py` suite.

## Future Expansion

When additional universes are added, the following testing capabilities will be available:
- Multi-universe integration tests
- Cross-universe isolation verification
- Parallel execution validation

---
*Reference: [CLI Guide](docs/CLI_GUIDE.md) | [Universe Creation Guide](docs/UNIVERSE_CREATION_GUIDE.md)*
