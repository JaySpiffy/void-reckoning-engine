import pytest
from src.core.game_config import GameConfig, MultiUniverseConfig
from pydantic import ValidationError

class TestGameConfigValidation:
    def test_default_config(self):
        config = GameConfig()
        assert config.max_turns == 50
        assert config.diplomacy_enabled
        # Check new Item 8.2 defaults
        assert config.colonization_cost == 1000
        assert config.max_fleet_size == 20
        assert config.max_build_time == 5

    def test_validation_error(self):
        with pytest.raises(ValidationError):
            GameConfig(max_turns=-1)
            
    def test_from_dict(self):
        data = {
            "campaign": {
                "turns": 100,
                "num_systems": 30
            },
            "performance": {
                "logging_level": "debug"
            },
            "extra_field": "value"
        }
        config = GameConfig.from_dict(data)
        assert config.max_turns == 100
        assert config.num_systems == 30
        assert config.performance_logging_level == "debug"
        # Check raw config preservation
        assert config.raw_config["extra_field"] == "value"

    def test_multi_universe_config(self):
        data = {
            "mode": "multi",
            "active_universe": "test_uni",
            "universes": [
                {"name": "uni1", "enabled": True, "num_runs": 2},
                {"name": "uni2", "enabled": False}
            ]
        }
        # Note: from_dict calls validate_multi_universe_config which checks for simple existence using UniverseLoader
        # We might need to mock UniverseLoader to avoid failure if universes don't exist
        # But for strictly Pydantic structure check:
        # We can bypass from_dict validation hook by instantiating directly if we just want to test structure
        
        # However, let's try to verify structure validation
        with pytest.raises(ValidationError):
            MultiUniverseConfig(universes=[{"name": "uni1", "num_runs": 0}]) # num_runs must be > 0
