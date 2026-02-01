
import unittest
from src.models.unit import Unit, Ship, Regiment, Component
from src.factories.unit_factory import UnitFactory

class TestComponentFix(unittest.TestCase):
    def test_unit_component_scaling(self):
        # Create a unit with 500 HP
        unit = Unit(name="Test Unit", ma=50, md=50, hp=500, armor=10, damage=10, 
                    abilities={}, authentic_weapons=["Bolter"])
        
        # Bolter should be in weapon_db or we use fallback
        # Since we are in a test and haven't loaded registries, it might use fallback or fail lookup.
        # But generate_components is called during init (via apply_dna_to_legacy or subclass init)
        
        # Check if Bolter exists with correct HP (10% of 500 = 50)
        weapons = [c for c in unit.components if c.type == "Weapon"]
        self.assertTrue(len(weapons) > 0, "Unit should have at least one weapon")
        for w in weapons:
            self.assertEqual(w.max_hp, 50, f"Weapon HP should be 50 (10% of 500), got {w.max_hp}")
            self.assertEqual(w.current_hp, 50)
            self.assertFalse(w.is_destroyed)

    def test_procedural_ship_scaling(self):
        # Emulate RecruitmentService's new procedural ship creation
        design_components = [
            {"component": "Macro-Cannon", "slot": "Weapon", "type": "Weapon"},
            {"name": "Void Shield Generator", "type": "Defense", "hp": 200}
        ]
        
        ship = Ship(name="Test Cruiser", ma=40, md=40, hp=500, armor=12, damage=0,
                    abilities={"Tags": ["Ship", "Cruiser"]}, faction="Imperium",
                    components_data=design_components)
        
        # Check Hull (should be 500)
        hulls = [c for c in ship.components if c.type == "Hull"]
        self.assertEqual(hulls[0].max_hp, 500)
        
        # Check Weapons (should be 10% of 500 = 50)
        weapons = [c for c in ship.components if c.name == "Macro-Cannon"]
        self.assertEqual(len(weapons), 1)
        self.assertEqual(weapons[0].max_hp, 50)
        
    def test_starbase_component_generation(self):
        from src.models.starbase import Starbase
        from src.models.star_system import StarSystem
        
        system = StarSystem("Test System", 0, 0)
        sb = Starbase(name="Test Station", faction="Imperium", system=system, tier=2)
        
        # Check components
        # T2 should have Hull, Shield, and Defense Batteries T2
        names = [c.name for c in sb.components]
        print(f"Starbase components: {names}")
        self.assertIn("Starbase Core T2", names)
        self.assertIn("Void Shield Generator T2", names)
        self.assertIn("Defense Batteries T2", names)
        
        # Check weapon stats
        batteries = [c for c in sb.components if "Batteries" in c.name][0]
        self.assertIsNotNone(batteries.weapon_stats)
        self.assertEqual(batteries.weapon_stats["Attacks"], 8) # 4 * tier

if __name__ == '__main__':
    unittest.main()
