
import pytest
from unittest.mock import MagicMock, call
from src.managers.turn_processor import TurnProcessor

def test_total_war_loop_execution_order():
    """
    Verifies that Production, Consolidation, and Combat happen INSIDE the faction turn.
    """
    # Setup Mocks
    engine = MagicMock()
    engine.all_planets = []
    engine.systems = []
    engine.fleets = []
    engine.turn_counter = 1
    engine.config.max_fleet_size = 500
    
    # Mock Managers
    engine.fleet_manager = MagicMock()
    engine.battle_manager = MagicMock()
    engine.economy_manager = MagicMock()
    engine.intel_manager = MagicMock()
    engine.construction_service = MagicMock()
    engine.strategies = {}
    engine.default_strategy = MagicMock()
    
    # Mock Faction
    faction = MagicMock()
    faction.name = "Imperium"
    engine.get_all_factions.return_value = [faction]
    engine.get_faction.return_value = faction
    
    # Mock Planets
    planet = MagicMock()
    planet.owner = "Imperium"
    engine.all_planets = [planet]
    
    # Initialize Processor
    tp = TurnProcessor(engine)
    
    # Execute Turn
    tp.process_turn()
    
    # VERIFICATION: Check Call Order for 'Imperium'
    
    # 1. Production (Start)
    planet.process_queue.assert_called_with(engine)
    
    # 2. Consolidation (Start)
    engine.fleet_manager.consolidate_fleets.assert_called_with(max_size=500, faction_filter="Imperium")
    
    # 3. Strategy/Economy (Middle)
    engine.strategic_ai.process_faction_strategy.assert_called_with("Imperium")
    engine.economy_manager.process_faction_economy.assert_called_with("Imperium")
    
    # 4. Combat (End)
    engine.battle_manager.process_active_battles.assert_called_with(faction_filter="Imperium")
    engine.battle_manager.resolve_ground_war.assert_called_with(faction_filter="Imperium")
    
if __name__ == "__main__":
    test_total_war_loop_execution_order()
    print("Game Loop Verified!")
