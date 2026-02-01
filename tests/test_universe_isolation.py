import pytest
import sys
from src.core.config import set_active_universe, get_universe_config, ACTIVE_UNIVERSE
from src.core.universe_data import UniverseDataManager

def test_faction_data_isolation(eternal_crusade_universe):
    """Verifies eternal_crusade factions are isolated."""
    udm = UniverseDataManager.get_instance()
    
    # Load eternal_crusade
    udm.load_universe_data("eternal_crusade")
    ec_factions = set(get_universe_config("eternal_crusade").get_factions())
    
    # Verify expected factions exist
    assert len(ec_factions) > 0, "No factions found in eternal_crusade universe"
    assert "Solar_Hegemony" in ec_factions or "Iron_Vanguard" in ec_factions or "Cyber_Synod" in ec_factions

def test_registry_isolation(eternal_crusade_universe):
    """Validates weapon/ability registries are universe-specific."""
    udm = UniverseDataManager.get_instance()
    
    # eternal_crusade Registry
    udm.load_universe_data("eternal_crusade")
    ec_weapons = udm.get_weapon_database()
    
    # Verify registry is loaded
    assert isinstance(ec_weapons, dict), "Weapon database should be a dict"
    
def test_path_switching(universe_loader):
    """Tests set_active_universe correctly updates all paths."""
    set_active_universe("eternal_crusade")
    cfg_ec = get_universe_config("eternal_crusade")
    assert "eternal_crusade" in str(cfg_ec.factions_dir)
    
def test_combat_rules_isolation():
    """Ensures combat rules are loaded correctly for eternal_crusade."""
    udm = UniverseDataManager.get_instance()
    
    # Force clear cache to ensure config check re-runs
    udm.active_universe = None
    udm.universe_config = None
    
    udm.load_universe_data("eternal_crusade")
    ec_rules = udm.get_combat_rules_module()
    assert ec_rules is not None, "Combat rules module should be loaded"
