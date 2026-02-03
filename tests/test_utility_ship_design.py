import pytest
from unittest.mock import MagicMock
from src.services.ship_design_service import ShipDesignService
from src.core.ship_sections import SECTIONS

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    # Mock faction manager
    faction = MagicMock()
    faction.unlocked_techs = ["Tech_Unlock_Tractor_Beam", "Tech_Unlock_Interdiction"]
    faction.weapon_registry = {}
    engine.factions = {"TestFaction": faction}
    engine.get_faction.return_value = faction
    return engine

def test_tractor_titan_design(mock_engine):
    ai_mgr = MagicMock()
    ai_mgr.engine = mock_engine
    designer = ShipDesignService(ai_mgr)
    
    # Test Titan Stern with Tractor section
    # Force the role to 'Tractor'
    design = designer.generate_design("TestFaction", "Titan", "Tractor")
    
    # Check if Tractor Beams are present
    component_names = []
    for c in design["components"]:
        name = c.get("Name") or c.get("name")
        if name: component_names.append(name)
    
    print(f"DEBUG: Component names: {component_names}")
    assert any("Tractor Beam" in name for name in component_names)
    
    # Check if slot exists in sections
    sections = SECTIONS["Titan"]["Stern"]
    assert "Tractor" in sections
    assert "T" in sections["Tractor"]

def test_interdictor_battleship_design(mock_engine):
    ai_mgr = MagicMock()
    ai_mgr.engine = mock_engine
    designer = ShipDesignService(ai_mgr)
    
    # Test Battleship Stern with Interdictor section
    design = designer.generate_design("TestFaction", "Battleship", "Interdictor")
    
    # Check if Interdiction Fields are present
    component_names = []
    for c in design["components"]:
        name = c.get("Name") or c.get("name")
        if name: component_names.append(name)
        
    print(f"DEBUG Battleship: {component_names}")
    assert any("Interdiction Field" in name for name in component_names)
    
    # Check if slot exists in sections
    sections = SECTIONS["Battleship"]["Stern"]
    assert "Interdictor" in sections
    assert "I" in sections["Interdictor"]

def test_interdictor_cruiser_design(mock_engine):
    ai_mgr = MagicMock()
    ai_mgr.engine = mock_engine
    designer = ShipDesignService(ai_mgr)
    
    # Test Cruiser Stern with Interdictor section
    design = designer.generate_design("TestFaction", "Cruiser", "Interdictor")
    
    # Check if Interdiction Field is present
    component_names = []
    for c in design["components"]:
        name = c.get("Name") or c.get("name")
        if name: component_names.append(name)
        
    print(f"DEBUG Cruiser: {component_names}")
    assert any("Interdiction Field" in name for name in component_names)
    
    # Check if slot exists in sections
    sections = SECTIONS["Cruiser"]["Stern"]
    assert "Interdictor" in sections
    assert "I" in sections["Interdictor"]
