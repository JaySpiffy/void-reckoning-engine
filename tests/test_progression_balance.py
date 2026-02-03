import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add workspace to sys.path
sys.path.append(os.getcwd())

from src.models.unit import Unit
from src.combat.ability_manager import AbilityManager

class TestProgressionBalance(unittest.TestCase):
    def test_max_level_constraint(self):
        """Verify that UNIT_MAX_LEVEL in balance.py is respected."""
        # Patch the constant inside the Unit module's gain_xp method where it's imported
        with patch('src.core.balance.UNIT_MAX_LEVEL', 5):
            unit = Unit(name="Test Unit", faction="Imp", unit_class="Infantry")
            unit.level = 4
            unit.experience = 0
            
            # Threshold for L4 is 120 (approx)
            # Threshold for L5 would be 144
            unit.gain_xp(1000) 
            
            self.assertEqual(unit.level, 5) # Should be capped at 5

    def test_xp_growth_exponent(self):
        """Verify that UNIT_XP_GROWTH_EXPONENT in balance.py affects thresholds."""
        with patch('src.core.balance.UNIT_XP_GROWTH_EXPONENT', 2.0):
            unit = Unit(name="Test Unit", faction="Imp")
            
            # L1 threshold: 100 * (2.0^0) = 100
            # L2 threshold: 100 * (2.0^1) = 200
            self.assertEqual(unit.get_xp_threshold(1), 100)
            self.assertEqual(unit.get_xp_threshold(2), 200)

    def test_xp_award_ratios(self):
        """Verify that AbilityManager uses XP award ratios from balance.py."""
        with patch('src.core.balance.UNIT_XP_AWARD_DAMAGE_RATIO', 1.0):
            with patch('src.core.balance.UNIT_XP_PER_LEVEL_BASE', 10000): # Avoid level up
                registry = {"test_ability": {"payload_type": "damage", "damage": 100}}
                am = AbilityManager(registry)
                
                unit = Unit(name="Attacker", faction="Imp")
                # Ensure unit has gain_xp
                self.assertTrue(hasattr(unit, "gain_xp"))
                
                # Mock target to avoid actual damage logic but return values
                target = MagicMock()
                target.take_damage.return_value = (0, 100, False, None) # s_dmg, h_dmg, killed, destroyed_comp
                
                result = {"damage": 0, "killed": False}
                context = {"battle_state": MagicMock()}
                
                am._handle_damage(unit, target, registry["test_ability"], result, context=context)
                
                # 100 damage (h_dmg) * 1.0 ratio = 100 XP
                self.assertEqual(unit.experience, 100)

if __name__ == "__main__":
    unittest.main()
