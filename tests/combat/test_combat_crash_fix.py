
import unittest
from unittest.mock import MagicMock
from src.managers.battle_manager import BattleManager
from src.managers.combat.active_battle import ActiveBattle
from src.combat.combat_state import CombatState
from src.models.fleet import Fleet
from src.models.unit import Unit

class TestCombatCrashFix(unittest.TestCase):
    def test_add_faction_units_exists(self):
        """Verify CombatState has add_faction_units method."""
        state = CombatState({}, {}, {})
        self.assertTrue(hasattr(state, 'add_faction_units'), "CombatState missing add_faction_units method")
        
    def test_active_battle_add_fleet(self):
        """Verify ActiveBattle.add_fleet calls add_faction_units without error."""
        # 1. Setup Mock Engine
        engine = MagicMock()
        engine.factions.get.return_value = MagicMock()
        
        # 2. Setup Combat State
        state = CombatState({}, {}, {})
        # Ensure grid exists
        state.initialize_battle()
        
        # 3. Setup Active Battle
        battle = ActiveBattle("TestLoc", state, 1, context=MagicMock())
        battle.context.strategic_ai.get_task_force_for_fleet.return_value = None
        
        from src.models.unit import Ship
        
        # 4. Setup Fleet
        fleet = Fleet("Fleet1", "Imperium", "TestLoc")
        # Add a ship
        ship = Ship(name="Cruiser", ma=10, md=10, hp=100, armor=10, damage=10, abilities={}, faction="Imperium")
        ship.keywords = ["Ship"]
        fleet.units.append(ship)
        
        # 5. Call add_fleet (This triggered the crash)
        try:
            battle.add_fleet(fleet)
        except AttributeError as e:
            self.fail(f"ActiveBattle.add_fleet raised AttributeError: {e}")
            
        # 6. Verify Unit Added to State
        self.assertIn("Imperium", state.armies_dict)
        self.assertEqual(len(state.armies_dict["Imperium"]), 1)
        self.assertEqual(state.armies_dict["Imperium"][0].name, "Cruiser")

if __name__ == "__main__":
    unittest.main()
