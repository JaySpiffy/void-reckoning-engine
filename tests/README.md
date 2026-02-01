# Test Suite Documentation

This directory contains the universe-aware testing infrastructure for the 40k Campaign Simulator.

## Directory Structure
- `conftest.py`: Shared fixtures including `universe_loader`, `wh40k_universe`, and `star_trek_universe`.
- `utils/`: Helper utilities (`universe_test_helpers.py`).
- `test_universe_loader.py`: Validates universe discovery and loading.
- `test_multi_universe_runner.py`: Validates parallel execution.
- `test_universe_isolation.py`: Ensures data separation between universes.
- `universes/`: Universe-specific integration tests.
  - `test_star_trek_integration.py`
  - `test_wh40k_combat_phases.py`
- `combat/`: Generic combat logic tests.

## Running Tests
Run specific universe tests:
```bash
pytest -m wh40k
pytest -m star_trek
```

Run generic tests (universe-agnostic):
```bash
pytest -m "not universe"
```

## Writing New Tests
Use the shared fixtures to ensure your test runs in the correct context:

```python
# Generic test (uses warhammer context default or mocked engine)
def test_something(mock_engine):
    pass

# WH40k Specific
@pytest.mark.wh40k
def test_ork_logic(wh40k_universe):
    # wh40k_universe fixture ensures context is set
    pass

# Multi-Universe Parameterized
@pytest.mark.parametrize("universe_name", ["warhammer40k", "star_trek"])
def test_generic_feature(universe_name):
    set_active_universe(universe_name)
    pass
```
