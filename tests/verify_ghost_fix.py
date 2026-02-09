import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet

def test_ghost_engagement_recovery():
    print("Testing Ghost Engagement Recovery...")
    
    # Setup mocks
    engine = MagicMock()
    battle_manager = MagicMock()
    battle_manager.active_battles = {} # No active battles
    engine.battle_manager = battle_manager
    
    location = MagicMock()
    location.name = "TestPlanet"
    
    # Initialize Fleet
    # (self, fleet_id, faction, start_planet)
    fleet = Fleet("Fleet_1", "TestFaction", location)
    
    # Mock speed and route to avoid further attribute errors during update_movement
    # Since speed is a property, we might need to mock _cached_speed and _speed_dirty
    fleet._cached_speed = 1
    fleet._speed_dirty = False
    fleet.route = [MagicMock()]
    
    # 1. Simulate Ghost Engagement
    fleet.is_engaged = True
    print(f"Initially engaged: {fleet.is_engaged}")
    
    # 2. Call update_movement
    # After the fix, it should notice no battle exists, clear the flag, and proceed.
    fleet.update_movement(engine=engine)
    
    print(f"Engaged after update_movement: {fleet.is_engaged}")
    
    if not fleet.is_engaged:
        print("SUCCESS: Ghost engagement was auto-cleared.")
    else:
        print("FAILURE: Fleet remains trapped in ghost engagement.")

if __name__ == "__main__":
    test_ghost_engagement_recovery()
