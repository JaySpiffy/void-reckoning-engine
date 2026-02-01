import pytest
from src.managers.tech_manager import TechManager
from src.models.faction import Faction
from src.managers.campaign_initializer import CampaignInitializer
from src.core.game_config import GameConfig
from unittest.mock import MagicMock

def test_tech_effect_parsing():
    """Verify that TechManager correctly parses effects from markdown-style strings."""
    tm = TechManager(tech_dir="temp", game_config={})
    
    # Mock some effects
    tm.tech_effects["Test Tech"] = ["+10% Damage", "+20% Research Speed", "Unlocks [Unit]"]
    
    # Test individual parsing
    assert tm.parse_effect_to_modifier("+10% Damage") == ("damage_mult", 0.1)
    assert tm.parse_effect_to_modifier("+20% Research Speed") == ("research_speed_mult", 0.2)
    assert tm.parse_effect_to_modifier("Unlocks [Unit]") is None # Not a stat mod
    
    effects = tm.get_tech_effects("Test Tech")
    assert len(effects) == 3

def test_faction_passive_modifiers():
    """Verify that Faction.unlock_tech applies passive modifiers correctly."""
    f = Faction("Test Faction")
    tm = TechManager(tech_dir="temp", game_config={})
    
    # Setup tech with effect
    tm.tech_effects["Military Doctrine"] = ["+15% Damage"]
    
    # 1. Check baseline
    assert f.get_modifier("damage_mult") == 1.0
    
    # 2. Unlock tech
    f.unlock_tech("Military Doctrine", turn=1, tech_manager=tm)
    
    # 3. Verify modifier application
    # 1.0 (base) * (1.0 + 0.15) = 1.15
    assert f.get_modifier("damage_mult") == pytest.approx(1.15)
    assert f.passive_modifiers["damage_mult"] == 0.15

def test_procedural_evolution_trigger():
    """Verify that CampaignInitializer triggers procedural evolution."""
    engine = MagicMock()
    # Mocking necessary engine attributes
    engine.config = MagicMock()
    engine.config.paths = {"tech": "temp"}
    engine.game_config = {"simulation": {"enable_tech_evolution": True}}
    engine.universe_config = MagicMock()
    engine.universe_config.name = "test_uni"
    engine.universe_data = MagicMock()
    engine.universe_data.get_physics_profile.return_value = {}
    engine.manager_overrides = {}
    
    # Mock TechManager to verify call
    tm_mock = MagicMock()
    initializer = CampaignInitializer(engine, manager_overrides={"tech_manager": tm_mock})
    
    # Call core managers setup where evolution happens
    initializer._setup_core_managers()
    
    # Verify evolution call
    tm_mock.apply_procedural_evolution.assert_called_once()

if __name__ == "__main__":
    # If run directly, execute basic tests
    test_tech_effect_parsing()
    test_faction_passive_modifiers()
    print("Self-tests passed!")
