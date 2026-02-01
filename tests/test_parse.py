import pytest
import os
from src.utils.unit_parser import parse_unit_file

@pytest.mark.skipif(not os.path.exists("universes/star_wars/factions/Imperial_Remnant/Space_Units/a9.md"), 
                    reason="Test file not found")
def test_parse_unit_file():
    unit_path = "universes/star_wars/factions/Imperial_Remnant/Space_Units/a9.md"
    faction = "Imperial_Remnant"
    
    unit = parse_unit_file(unit_path, faction)
    assert unit is not None
    assert hasattr(unit, 'name')
    # Since we don't know exact values without the file, generic checks
    assert unit.base_hp > 0

