import unittest
from unittest.mock import MagicMock, Mock
# src modules
from src.managers.combat.retreat_handler import RetreatHandler
from src.managers.battle_manager import BattleManager
from src.models.fleet import Fleet
from src.combat.combat_context import CombatContext

class TestRetreatAggression(unittest.TestCase):
    def test_no_retreat_twice(self):
        """Verify that a fleet cannot retreat twice in the same turn."""
        
        # 1. Setup Mock Context
        mock_context = MagicMock()
        mock_context.logger = MagicMock()
        mock_context.game_config = {"combat": {"use_rust_combat": False}}
        mock_context.get_all_fleets = MagicMock(return_value=[]) # Empty list default
        mock_context.get_all_planets = MagicMock(return_value=[])

        # 2. Setup Fleet
        fleet = Fleet("F1", "FactionA", Mock())
        fleet.units = [Mock()] # Needs units to be alive
        fleet.units[0].is_alive = lambda: True
        
        # 3. Trigger initial retreat via Handler
        handler = RetreatHandler(mock_context)
        
        # Mock active battle data
        mock_battle = MagicMock()
        mock_battle.participating_fleets = ["F1"]
        present_fleets = {"F1": fleet}
        
        # Execute retreat removal (simulating end of first battle)
        handler._execute_retreat_removal(mock_battle, ["F1"], [], present_fleets)
        
        # CHECK: Flag should be set
        self.assertTrue(fleet.has_retreated_this_turn, "Fleet should be marked as retreated")
        
        # 4. Simulate Second Battle (Pursuit) via BattleManager logic
        bm = BattleManager(mock_context)
        
        # Setup location properties
        location = Mock()
        location.name = "TestSystem"
        location.owner = "FactionA"
        location.type = "System" # Explicitly Space
        # Ensure it doesn't trigger ground logic
        del location.parent_planet 
        del location.is_province
        
        # Mock context.get_faction to return evasion rating
        mock_faction = Mock()
        mock_faction.evasion_rating = 1.0 # 100% Evasion chance (normally would retreat)
        mock_context.get_faction.return_value = mock_faction
        
        # Setup BM internals
        bm._fleets_by_location = {location: [fleet]}
        bm._location_factions = {location: {"FactionA", "FactionB"}}
        bm.get_factions_at = MagicMock(return_value={"FactionA", "FactionB"})
        
        # Mock Power Property on Fleets
        # fleet.power = 100 
        # attacker.power = 1000
        # Since power is a property, we can't set it on real Fleet object easily without dirty hacks or mocks
        # Better: Mock the fleet objects entirely or use side_effect
        fleet = MagicMock(spec=Fleet)
        fleet.id = "F1"
        fleet.faction = "FactionA"
        fleet.power = 100
        fleet.has_retreated_this_turn = True # The critical flag
        fleet.is_engaged = False
        fleet.destination = None
        
        attacker = MagicMock(spec=Fleet)
        attacker.id = "F2"
        attacker.faction = "FactionB"
        attacker.power = 1000
        attacker.is_engaged = False
        attacker.destination = None

        bm._fleets_by_location = {location: [fleet, attacker]}
        
        # Mock Diplomacy (War)
        mock_dm = Mock()
        mock_dm.get_enemies.return_value = ["FactionB"] # FactionA hates FactionB
        mock_dm.get_treaty.return_value = "War"
        mock_context.diplomacy = mock_dm

        # Mock _initialize_new_battle to catch the trigger
        bm._initialize_new_battle = MagicMock()
        
        # EXECUTE
        print("DEBUG: Calling resolve_battles_at...")
        bm.resolve_battles_at(location, update_indices=False, aggressor_faction="FactionB")
        
        # VERIFY
        # Evasion check is skipped because has_retreated_this_turn is True
        # Therefore, _initialize_new_battle MUST be called.
        if not bm._initialize_new_battle.called:
             print("DEBUG: _initialize_new_battle was NOT called.")
             print(f"DEBUG: Fleets at loc: {bm._fleets_by_location[location]}")
             print(f"DEBUG: Fleet Retreated Flag: {fleet.has_retreated_this_turn}")
             
        bm._initialize_new_battle.assert_called()
        print("Success: Fleet was forced to fight (Initialize Battle called) despite 100% evasion rating.")

if __name__ == '__main__':
    unittest.main()
