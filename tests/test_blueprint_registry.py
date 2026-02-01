import pytest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from src.utils.blueprint_registry import BlueprintRegistry
from src.factories.unit_factory import UnitFactory
from src.core.universe_data import UniverseDataManager
from src.core.config import UNIVERSE_ROOT

@pytest.fixture
def blueprint_env(tmp_path):
    # Create a temp universe for testing overrides
    test_uni_name = "test_blueprint_uni"
    
    from src.core import config
    original_root = config.UNIVERSE_ROOT
    config.UNIVERSE_ROOT = str(tmp_path)
    
    test_uni_path = os.path.join(config.UNIVERSE_ROOT, test_uni_name)
    os.makedirs(os.path.join(test_uni_path, "blueprints"), exist_ok=True)
    os.makedirs(os.path.join(test_uni_path, "factions"), exist_ok=True)
    
    # Create a base blueprint for unit tests
    base_bp_dir = os.path.join(config.UNIVERSE_ROOT, "base", "blueprints")
    os.makedirs(base_bp_dir, exist_ok=True)
    with open(os.path.join(base_bp_dir, "base_infantry.json"), 'w') as f:
        json.dump({
            "id": "base_infantry",
            "name": "Base Infantry",
            "type": "infantry",
            "base_stats": {"hp": 100},
            "default_traits": []
        }, f)
    
    # Create a dummy config.json
    with open(os.path.join(test_uni_path, "config.json"), 'w') as f:
        json.dump({"name": test_uni_name, "version": "1.0.0", "factions": ["TestFaction"]}, f)
        
    # Create a dummy trait registry
    with open(os.path.join(test_uni_path, "factions", "traits_registry.json"), 'w') as f:
        json.dump({
            "TestTrait": {"modifiers": {"hull_structural_integrity": 1.1}}
        }, f)

    # Clear singleton for fresh test
    BlueprintRegistry._instance = None
    registry = BlueprintRegistry.get_instance()
    
    # Create a dummy faction
    faction_dir = os.path.join(test_uni_path, "factions", "TestFaction")
    os.makedirs(faction_dir, exist_ok=True)
    with open(os.path.join(faction_dir, "config.json"), 'w') as f:
        json.dump({"name": "TestFaction", "traits": []}, f)

    yield {
        "registry": registry,
        "test_uni_name": test_uni_name,
        "test_uni_path": test_uni_path
    }
    
    # Cleanup
    BlueprintRegistry._instance = None
    config.UNIVERSE_ROOT = original_root

def test_load_base_blueprints(blueprint_env):
    """Verify that base blueprints load correctly."""
    registry = blueprint_env["registry"]
    registry.load_blueprints(verbose=False)
    assert "base_infantry" in registry.list_blueprints()
    b = registry.get_blueprint("base_infantry")
    assert b["type"] == "infantry"
    assert b["base_stats"]["hp"] == 100

def test_blueprint_registry_singleton(blueprint_env):
    """Ensure singleton pattern works."""
    registry = blueprint_env["registry"]
    r2 = BlueprintRegistry.get_instance()
    assert registry is r2

def test_blueprint_override(blueprint_env):
    """Test that universe-specific blueprints override/merge with base."""
    registry = blueprint_env["registry"]
    test_uni_path = blueprint_env["test_uni_path"]
    
    # Create an override for base_infantry in test universe
    override_data = {
        "id": "base_infantry",
        "base_stats": {"hp": 200}, # Replace
        "universal_stats": {"hull_structural_integrity": 1.2}, # Multiply (1.0 * 1.2 = 1.2)
        "default_traits": ["UniTrait"] # Concatenate
    }
    with open(os.path.join(test_uni_path, "blueprints", "override.json"), 'w') as f:
        json.dump(override_data, f)
        
    registry.load_blueprints(universe_path=test_uni_path, verbose=False)
    
    b = registry.get_blueprint("base_infantry")
    assert b["base_stats"]["hp"] == 200 # Overridden
    assert "UniTrait" in b["default_traits"] # Concatenated

def test_unit_creation_from_blueprint_id(blueprint_env):
    """Verify factory creates units from blueprint IDs."""
    test_uni_name = blueprint_env["test_uni_name"]
    test_uni_path = blueprint_env["test_uni_path"]
    registry = blueprint_env["registry"]
    
    # Need to set active universe for DataManager to find registries
    UniverseDataManager.get_instance().load_universe_data(test_uni_name)
    
    # Build registries so factory finds the blueprint file
    from src.utils.registry_builder import build_blueprint_registry
    build_blueprint_registry(test_uni_path, verbose=False)
    
    registry.load_blueprints(verbose=False)
    
    unit = UnitFactory.create_from_blueprint_id("base_infantry", "TestFaction", traits=["TestTrait"])
    assert unit is not None
    assert unit.name == "Base Infantry" # From blueprint
    assert unit.base_hp == 100 # From blueprint

def test_blueprint_not_found(blueprint_env):
    """Handle missing blueprint gracefully."""
    unit = UnitFactory.create_from_blueprint_id("non_existent", "Faction")
    assert unit is None
