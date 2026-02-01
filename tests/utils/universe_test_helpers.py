import os
import json
from unittest.mock import MagicMock
from src.core.universe_data import UniverseDataManager
from src.models.faction import Faction

def load_test_units_for_universe(universe_name: str, faction_name: str):
    """Loads real unit data for testing a specific universe faction."""
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data(universe_name)
    # Check if we have a units registry or loader in the universe
    # This is a basic implementation for now
    if hasattr(udm.universe_config, "load_module"):
         try:
             # Try to load units if a units module exists
             return udm.universe_config.load_module("units")
         except ImportError:
             pass
    return None

def create_mock_faction_manager(universe_name: str, faction_name: str):
    """Creates a mock faction manager with universe context."""
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data(universe_name)
    
    mock_faction = MagicMock(spec=Faction)
    mock_faction.name = faction_name
    mock_faction.universe = universe_name
    
    # Load raw data if possible to populate defaults
    factions = udm.get_factions_database() if hasattr(udm, 'get_factions_database') else []
    # logic to find faction data
    
    return mock_faction

def get_universe_combat_rules(universe_name: str):
    """Loads combat rules module for testing."""
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data(universe_name)
    return udm.universe_config.load_module("combat_rules")

def get_universe_personalities(universe_name: str):
    """Loads AI personalities module for testing."""
    udm = UniverseDataManager.get_instance()
    udm.load_universe_data(universe_name)
    return udm.universe_config.load_module("ai_personalities")
