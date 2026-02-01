import pytest
import os
import tempfile
import json
import shutil
from src.core.game_config import GameConfig, MultiUniverseConfig, validate_multi_universe_config
from src.core import config
from universes.base.universe_loader import UniverseLoader

@pytest.fixture
def config_env():
    # Create a dummy universe directory for testing
    test_dir = tempfile.mkdtemp()
    universes_dir = os.path.join(test_dir, "universes")
    os.makedirs(universes_dir)
    
    # Mock active universe path logic
    original_universe_root = config.UNIVERSE_ROOT
    config.UNIVERSE_ROOT = universes_dir
    
    # Create a "test_universe"
    uni_path = os.path.join(universes_dir, "test_verse")
    os.makedirs(uni_path)
    os.makedirs(os.path.join(uni_path, "factions"))
    os.makedirs(os.path.join(uni_path, "technology"))
    
    with open(os.path.join(uni_path, "config.json"), 'w') as f:
        json.dump({
            "name": "Test Verse",
            "rules": {"test_rule": True}
        }, f)
        
    yield {
        "test_dir": test_dir,
        "universes_dir": universes_dir,
        "uni_path": uni_path
    }
    
    # Cleanup
    shutil.rmtree(test_dir)
    config.UNIVERSE_ROOT = original_universe_root

def test_game_config_defaults():
    """Test GameConfig default initialization."""
    cfg = GameConfig()
    assert cfg.max_turns == 50
    assert cfg.diplomacy_enabled is True

def test_game_config_from_dict():
    """Test GameConfig parsing from dictionary."""
    data = {
        "campaign": {"turns": 100},
        "mechanics": {"enable_diplomacy": False},
        "performance": {"logging_level": "debug"}
    }
    cfg = GameConfig.from_dict(data)
    assert cfg.max_turns == 100
    assert cfg.diplomacy_enabled is False
    assert cfg.performance_logging_level == "debug"

def test_multi_universe_config(config_env):
    """Test MultiUniverseConfig parsing."""
    data = {
        "mode": "multi",
        "active_universe": "test_verse",
        "universes": [
            {"name": "test_verse", "num_runs": 5, "campaign": {"turns": 10}}
        ]
    }
    cfg = GameConfig.from_dict(data)
    assert isinstance(cfg, MultiUniverseConfig)
    assert len(cfg.universes) == 1
    u_conf = cfg.universes[0]
    assert u_conf.name == "test_verse"
    assert u_conf.num_runs == 5
    # Check merged config
    assert u_conf.game_config["campaign"]["turns"] == 10

def test_universe_discovery(config_env):
    """Test UniverseLoader discovery."""
    loader = UniverseLoader(config_env["universes_dir"])
    discovered = loader.discover_universes()
    assert "test_verse" in discovered
