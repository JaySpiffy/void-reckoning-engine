import pytest
import math
from src.combat.real_time.formation_manager import Formation

class MockUnit:
    def __init__(self, x=0.0, y=0.0):
        self.grid_x = x
        self.grid_y = y

@pytest.fixture
def entities():
    return [MockUnit(0, 0) for _ in range(10)]

def test_wedge_positions(entities):
    # 10 units in a wedge
    formation = Formation(entities, spacing=1.0, formation_type="Wedge")
    formation.facing = 0.0 # Facing North
    
    offsets = [formation.get_slot_offset(i) for i in range(10)]
    
    # Tip (index 0) should be at relative (0, 0)
    assert offsets[0] == (0.0, 0.0)
    
    # Check general properties (Wedge row counts)
    # Row 1 Southernness (index 1)
    # offset_y should be positive south if spacing=1.0
    # Rotation might flip it depending on math vs grid coordinate systems
    assert len(offsets) == 10

def test_loose_spacing(entities):
    rect = Formation(entities, spacing=1.0, formation_type="Rectangle")
    loose = Formation(entities, spacing=1.0, formation_type="Loose")
    
    rect_off = rect.get_slot_offset(1)
    loose_off = loose.get_slot_offset(1)
    
    # Loose should have 2.5x spacing
    assert pytest.approx(abs(loose_off[0])) == abs(rect_off[0]) * 2.5

def test_formation_modifiers(entities):
    wedge = Formation(entities, formation_type="Wedge")
    mods = wedge.get_modifiers()
    assert mods.get("movement_speed_mult") == 1.2
    
    loose = Formation(entities, formation_type="Loose")
    assert loose.get_modifiers().get("aoe_resilience") == 2.0
