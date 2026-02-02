import unittest
from unittest.mock import MagicMock, patch
from src.managers.turn_processor import TurnProcessor
from src.reporting.telemetry import EventCategory

class TestSequentialTurns(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()
        self.engine.turn_counter = 1
        self.engine.telemetry = MagicMock()
        # Mock factions
        f1 = MagicMock()
        f1.name = "Faction_A"
        f1.is_alive = True
        f2 = MagicMock()
        f2.name = "Faction_B"
        f2.is_alive = True
        
        self.engine.get_all_factions.return_value = [f1, f2]
        self.engine.get_faction.side_effect = lambda name: f1 if name == "Faction_A" else f2
        self.engine.factions = {"Faction_A": f1, "Faction_B": f2}
        
        # Mock economy and strategic AI
        self.engine.economy_manager = MagicMock()
        self.engine.strategic_ai = MagicMock()
        
        self.processor = TurnProcessor(self.engine)

    def test_turn_window_telemetry(self):
        """Verify that faction_turn_start/end events are logged in the correct order."""
        with patch.object(self.processor, 'process_faction_turn'):
            self.processor.process_faction_turns()
            
            # Check telemetry calls
            calls = self.engine.telemetry.log_event.call_args_list
            
            # Expecting: 
            # 1. faction_turn_start (A)
            # 2. faction_turn_end (A)
            # 3. faction_turn_start (B)
            # 4. faction_turn_end (B)
            
            self.assertEqual(calls[0][0][1], 'faction_turn_start')
            self.assertEqual(calls[0][0][2]['faction'], "Faction_A")
            
            self.assertEqual(calls[1][0][1], 'faction_turn_end')
            self.assertEqual(calls[1][0][2]['faction'], "Faction_A")
            
            self.assertEqual(calls[2][0][1], 'faction_turn_start')
            self.assertEqual(calls[2][0][2]['faction'], "Faction_B")
            
            self.assertEqual(calls[3][0][1], 'faction_turn_end')
            self.assertEqual(calls[3][0][2]['faction'], "Faction_B")

    def test_ai_cache_refresh(self):
        """Verify that strategic AI cache is rebuilt for each faction window."""
        with patch.object(self.processor, 'process_faction_turn'):
            self.processor.process_faction_turns()
            
            # build_turn_cache should be called twice (once per faction)
            self.assertEqual(self.engine.strategic_ai.build_turn_cache.call_count, 2)

if __name__ == '__main__':
    unittest.main()
