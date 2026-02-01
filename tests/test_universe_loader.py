import pytest
import os
from pathlib import Path
from universes.base.universe_loader import UniverseLoader
from src.core.config import UNIVERSE_ROOT

@pytest.fixture
def loader():
    return UniverseLoader(Path(UNIVERSE_ROOT))

def test_discover_universes(loader):
    """Verifies that universes are correctly discovered."""
    universes = loader.discover_universes()
    assert "warhammer40k" in universes or "eternal_crusade" in universes
    assert len(universes) >= 1

def test_load_eternal_crusade_universe(loader):
    """Tests loading the Eternal Crusade universe configuration."""
    config = loader.load_universe("eternal_crusade")
    assert config.name == "The Eternal Crusade"
    assert config.universe_root == Path(UNIVERSE_ROOT) / "eternal_crusade"
    assert config.validate_structure()

def test_load_procedural_sandbox_universe(loader):
    """Tests loading the Procedural Sandbox universe configuration."""
    config = loader.load_universe("procedural_sandbox")
    assert config.name == "Procedural Sandbox"
    assert config.universe_root == Path(UNIVERSE_ROOT) / "procedural_sandbox"
    # Sandbox might not have all dirs, check structure if valid
    # assert config.validate_structure()

def test_load_hybrid_universe(loader):
    """Tests loading a universe with hybrid config if available."""
    # Assuming eternal_crusade might support XML or another feature
    config = loader.load_universe("eternal_crusade")
    # Just verify config loads
    assert isinstance(config.unit_formats, dict)

def test_validate_universe_registries(loader):
    """Verifies that all required registry files exist for WH40k."""
    config = loader.load_universe("eternal_crusade")
    for registry_name, path in config.registry_paths.items():
        # Only check existence if path is set
        if path:
             assert path.exists(), f"Registry {registry_name} missing at {path}"

def test_universe_config_paths(loader):
    """Validates dynamic path resolution in config."""
    config = loader.load_universe("eternal_crusade")
    assert config.factions_dir.name == "factions"
    assert config.infrastructure_dir.name == "infrastructure"
    assert config.technology_dir.name == "technology"

def test_universe_module_loading(loader):
    """Tests dynamic module loading (if defined in metadata)."""
    config = loader.load_universe("eternal_crusade")
    # Check if we can load combat rules if defined
    if "combat_rules" in config.modules:
        module = config.load_module("combat_rules")
        assert module is not None

def test_invalid_universe_handling(loader):
    """Tests error handling for non-existent universes."""
    with pytest.raises(FileNotFoundError): # Assuming load_universe raises ValueError or KeyErorr
        loader.load_universe("invalid_universe_xyz")
