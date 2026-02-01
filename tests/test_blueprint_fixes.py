import pytest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from src.utils.blueprint_registry import BlueprintRegistry
from src.factories.unit_factory import UnitFactory
from src.utils.unit_parser import parse_unit_file
from src.core.universe_data import UniverseDataManager
from src.core.config import UNIVERSE_ROOT

@pytest.fixture
def fixes_env(tmp_path):
    # Mock UNIVERSE_ROOT
    from src.core import config
    original_root = config.UNIVERSE_ROOT
    config.UNIVERSE_ROOT = str(tmp_path)
    
    test_uni_name = "test_fixes_uni"
    test_uni_path = os.path.join(config.UNIVERSE_ROOT, test_uni_name)
    os.makedirs(os.path.join(test_uni_path, "blueprints"), exist_ok=True)
    os.makedirs(os.path.join(test_uni_path, "factions", "TestFaction"), exist_ok=True)
    
    # Create a dummy config.json
    with open(os.path.join(test_uni_path, "config.json"), 'w') as f:
        json.dump({"name": test_uni_name, "version": "1.0.0", "factions": ["TestFaction"]}, f)
        
    # Clear singleton for fresh test
    BlueprintRegistry._instance = None
    registry = BlueprintRegistry.get_instance()
    
    yield {
        "registry": registry,
        "test_uni_name": test_uni_name,
        "test_uni_path": test_uni_path
    }
    
    # Cleanup
    BlueprintRegistry._instance = None
    UniverseDataManager._instance = None # Reset DataManager too
    config.UNIVERSE_ROOT = original_root

def test_weapon_blueprint_rejection(fixes_env):
    """Verify that weapon blueprints are not instantiated as units."""
    registry = fixes_env["registry"]
    test_uni_path = fixes_env["test_uni_path"]
    
    weapon_bp = {
        "id": "test_weapon",
        "name": "Test Weapon",
        "type": "weapon",
        "base_stats": {"damage": 20},
        "universal_stats": {"weapon_kinetic_damage": 1.5}
    }
    with open(os.path.join(test_uni_path, "blueprints", "weapon.json"), 'w') as f:
        json.dump(weapon_bp, f)
        
    registry.load_blueprints(universe_path=test_uni_path, verbose=False)
    
    unit = UnitFactory.create_from_blueprint_id("test_weapon", "TestFaction")
    assert unit is None, "Weapon blueprint should not return a Unit object."

def test_universal_stats_merging(fixes_env):
    """Verify that markdown universal_stats merge with blueprint defaults."""
    registry = fixes_env["registry"]
    test_uni_name = fixes_env["test_uni_name"]
    test_uni_path = fixes_env["test_uni_path"]
    
    infantry_bp = {
        "id": "base_infantry",
        "name": "Base Infantry",
        "type": "infantry",
        "base_stats": {"hp": 100},
        "universal_stats": {
            "hull_structural_integrity": 1.0,
            "mobility_speed_tactical": 1.0
        }
    }
    with open(os.path.join(test_uni_path, "blueprints", "infantry.json"), 'w') as f:
        json.dump(infantry_bp, f)
        
    # Load registry for the parser to find it
    registry.load_blueprints(universe_path=test_uni_path, verbose=False)
    
    # We must build the registry file for UniverseDataManager to find it
    from src.utils.registry_builder import build_blueprint_registry
    build_blueprint_registry(test_uni_path, verbose=False)
    
    UniverseDataManager.get_instance().load_universe_data(test_uni_name)
    
    # Create a markdown file that overrides ONLY one metric
    # The parser uses lowercase blueprint_id comparison
    md_content = """# Test Unit
Blueprint ID: base_infantry

## Parser Data
```json
{
  "blueprint_id": "base_infantry",
  "universal_stats": {
    "hull_structural_integrity": 2.0
  }
}
```
"""
    md_path = os.path.join(test_uni_path, "factions", "TestFaction", "unit.md")
    with open(md_path, 'w') as f:
        f.write(md_content)
        
    unit = parse_unit_file(md_path, "TestFaction")
    assert unit is not None
    
    # Check that hull_structural_integrity is overridden
    assert unit.universal_stats["hull_structural_integrity"] == pytest.approx(2.0)
    # Check that mobility_speed_tactical is RETAINED from blueprint
    assert unit.universal_stats["mobility_speed_tactical"] == pytest.approx(1.0)
