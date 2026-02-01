import unittest
import math
from src.combat.real_time.formation_manager import Formation

class MockUnit:
    def __init__(self, x=0.0, y=0.0):
        self.grid_x = x
        self.grid_y = y

class TestAdvancedFormations(unittest.TestCase):
    def setUp(self):
        self.entities = [MockUnit(0, 0) for _ in range(10)]
        
    def test_wedge_positions(self):
        # 10 units in a wedge
        # Row 0: 1 unit (index 0)
        # Row 1: 2 units (index 1, 2)
        # Row 2: 3 units (index 3, 4, 5)
        # Row 3: 4 units (index 6, 7, 8, 9)
        formation = Formation(self.entities, spacing=1.0, formation_type="Wedge")
        formation.facing = 0.0 # Facing North
        
        offsets = [formation.get_slot_offset(i) for i in range(10)]
        
        # Tip (index 0) should be at relative (0, 0) since center is calculated from all
        # Actually, get_slot_offset returns relative to center.
        # If facing North, Y decreases as we go North in Grid?
        # Standard Grid Y Down. North = -Y.
        
        # Row 0 tip: offset_y for row 0 is 0. 
        # But wait, my rotation logic:
        # ox, -oy where math 90 is North.
        # ox * cos(90) - oy * sin(90) = -oy
        # ox * sin(90) + oy * cos(90) = ox
        # returns (-oy, -ox) -> wait.
        
        # Tip unit (index 0): row=0, pos=0. offset_x=0, offset_y=0. returns (0, 0).
        self.assertEqual(offsets[0], (0.0, 0.0))
        
        # Row 1 (index 1, 2): row=1. offset_y = 1.0.
        # if facing North: 
        # math_angle = 90 - 0 = 90.
        # rot_x = 0*cos(90) - 1*sin(90) = -1
        # rot_y = 0*sin(90) + 1*cos(90) = 0
        # returns (-1.0, 0.0) -> Wait.
        
        # Row 1 should be "South" of Row 0 if tip is at front.
        # In Grid, South is +Y.
        # My wedge logic: offset_y = row * spacing.
        # If row 0 is at 0, row 1 is at 1.0.
        # Result rot_y = 0.
        
        # Let's re-check _rotate_offset logic.
        print(f"DEBUG: Wedge Index 1 Offset (North): {offsets[1]}")
        print(f"DEBUG: Wedge Index 3 Offset (North): {offsets[3]}")

    def test_loose_spacing(self):
        rect = Formation(self.entities, spacing=1.0, formation_type="Rectangle")
        loose = Formation(self.entities, spacing=1.0, formation_type="Loose")
        
        rect_off = rect.get_slot_offset(1)
        loose_off = loose.get_slot_offset(1)
        
        # Loose should have 2.5x spacing
        self.assertAlmostEqual(abs(loose_off[0]), abs(rect_off[0]) * 2.5)

    def test_formation_modifiers(self):
        wedge = Formation(self.entities, formation_type="Wedge")
        mods = wedge.get_modifiers()
        self.assertEqual(mods.get("movement_speed_mult"), 1.2)
        
        loose = Formation(self.entities, formation_type="Loose")
        self.assertEqual(loose.get_modifiers().get("aoe_resilience"), 2.0)

if __name__ == "__main__":
    unittest.main()
