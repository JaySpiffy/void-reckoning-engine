import sys
import os
import unittest
from unittest.mock import MagicMock

# Add workspace to sys.path
sys.path.append(os.getcwd())

from src.models.unit import Unit
from src.combat.ability_manager import AbilityManager
from src.core.universe_data import UniverseDataManager

class TestMassiveAbilityProgression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure massive files exist (should be already generated)
        # Initialize UniverseDataManager
        cls.udm = UniverseDataManager.get_instance()
        cls.registry = cls.udm.get_ability_database()
        cls.am = AbilityManager(cls.registry)
        print(f"Registry Size: {len(cls.registry)}")
        sample_keys = [k for k in cls.registry.keys() if "massive" in k or k.startswith("space_")][:5]
        print(f"Sample Keys: {sample_keys}")

    def test_massive_pool_size(self):
        """Verify the registry has indeed 10,000+ entries."""
        self.assertGreaterEqual(len(self.registry), 10000)
        print(f"Registry Size: {len(self.registry)}")

    def test_level_up_discovery(self):
        """Verify unit gains a new Level 1 ability on level up."""
        unit = Unit(name="Test Unit", unit_class="Infantry", faction="Imp")
        unit.domain = "ground"
        
        context = {"ability_manager": self.am}
        
        # Gain XP for Level 2 (Needs 100)
        unit.gain_xp(110, context)
        
        self.assertEqual(unit.level, 2)
        self.assertAlmostEqual(unit.experience, 10.0) # 110 - 100
        self.assertEqual(len(unit.abilities), 1)
        
        ab_id = list(unit.abilities.keys())[0]
        self.assertTrue(ab_id.startswith("ground_"))
        self.assertTrue(ab_id.endswith("_v1"))
        print(f"Discovered: {ab_id}")

    def test_space_unit_domain(self):
        """Verify space units only get space abilities."""
        unit = Unit(name="Strike Cruiser", unit_class="Cruiser", faction="Imp")
        unit.domain = "space"
        
        context = {"ability_manager": self.am}
        unit.gain_xp(150, context)
        
        ab_id = list(unit.abilities.keys())[0]
        self.assertTrue(ab_id.startswith("space_"))
        print(f"Ship Discovered: {ab_id}")

    def test_upgrade_logic(self):
        """Verify that discovery logic correctly upgrades existing abilities."""
        unit = Unit(name="Veteran Marines", unit_class="Infantry", faction="Imp")
        unit.domain = "ground"
        
        # Predetermine an ability to avoid random chance during initial setup
        base_id = None
        for k in self.registry:
            if k.startswith("ground_") and k.endswith("_v1"):
                base_id = k.rsplit("_v", 1)[0]
                break
        
        # Force inject Level 1
        v1_id = f"{base_id}_v1"
        unit.abilities = {v1_id: self.registry[v1_id]}
        
        # Force RNG to always pick upgrade if upgrade_candidates exists
        old_random = self.am._rng.random
        self.am._rng.random = lambda: 0.1 # < 0.3 means upgrade
        
        context = {"ability_manager": self.am}
        
        # Gain XP for Level 2 (Needs 100)
        unit.gain_xp(105, context) 
        
        # Restore RNG
        self.am._rng.random = old_random
        
        print(f"Abilities: {list(unit.abilities.keys())}")
        
        # Should have exactly 1 or 2 abilities depending on how many levels we passed. 
        # Actually gain_xp wraps in a while loop.
        # L1 -> L2 (XP 100): Upgrade to V2
        # L2 -> L3 (XP 120): Upgrade to V3
        
        # Check that we have a version > 1
        v_current = [k for k in unit.abilities.keys() if k.startswith(base_id)]
        self.assertEqual(len(v_current), 1)
        self.assertIn("_v", v_current[0])
        ver = int(v_current[0].split("_v")[-1])
        self.assertGreater(ver, 1)
        print(f"Upgraded to: {v_current[0]}")

if __name__ == "__main__":
    unittest.main()
