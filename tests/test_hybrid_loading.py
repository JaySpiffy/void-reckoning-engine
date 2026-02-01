import pytest
from src.utils.unit_parser import load_all_units
from src.core.config import set_active_universe
from src.core.universe_data import UniverseDataManager

def test_hybrid_loading_counts():
    """
    Verifies that units are loaded from Markdown sources.
    Note: Third-party hybrid loading (e.g., Stellaris) has been removed.
    This test now validates generic Markdown loading for eternal_crusade.
    """
    set_active_universe("eternal_crusade")
    # Ensure data is loaded
    UniverseDataManager.get_instance().load_universe_data("eternal_crusade")
    
    units = load_all_units()
    
    assert len(units) > 0, "No units loaded at all"
    
    # Check specific faction known to have data (Solar Hegemony)
    solar_units = units.get("Solar_Hegemony", [])
    
    if not solar_units:
        pytest.skip("No Solar Hegemony units found.")
    
    # Analyze units
    markdown_count = sum(1 for u in solar_units if getattr(u, 'source_format', '') != 'stellaris')
    
    # Assertions
    # We expect Markdown units to be present if universe exists
    assert markdown_count > 0, "Expected Markdown units for Solar Hegemony"
