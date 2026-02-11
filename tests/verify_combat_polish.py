
import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.unit import Regiment
from src.combat.realtime.realtime_manager import RealTimeManager
from src.models.fleet import Fleet

class MockGrid:
    def __init__(self):
        self.obstacles = []
        self.spatial_index = None
    def get_modifiers_at(self, x, y):
        return {}
    def query_units_in_range(self, x, y, radius):
        return []
    def update_unit_position(self, u, x, y):
        pass
    def get_distance(self, u1, u2):
        return 10.0

class MockBattleState:
    def __init__(self, units):
        self.total_sim_time = 0.0
        self.last_snapshot_time = 0.0
        self.grid = MockGrid()
        self.armies_dict = {"FactionA": units}
        self.active_factions = ["FactionA"]
        self.victory_points = {"FactionA": 0}
        self.faction_doctrines = {"FactionA": "STANDARD"}
        self.tracker = None
        self.mechanics_engine = None
    def log_event(self, *args):
        pass
    def _take_snapshot(self):
        pass

def test_fatigue():
    print("=== Testing Fatigue Mechanics ===")
    
    # Setup
    u = Regiment("Guardsman", "FactionA", ma=50, md=50, hp=100)
    # Ensure init_combat_state called
    u.init_combat_state()
    # Mock movement points so they can move
    u.base_movement_points = 10
    u.movement_points = 10
    
    # Mock Manager
    rtm = RealTimeManager()
    state = MockBattleState([u])
    
    # 1. Test Idle Recovery (should stay 0)
    print("1. Idle Test...")
    rtm.update(state, 1.0)
    print(f"   Fatigue after 1s idle: {u.fatigue}")
    if u.fatigue != 0:
        print("FAIL: Fatigue should be 0.")
    else:
        print("PASS")

    # 2. Test Movement Fatigue
    print("2. Movement Test...")
    # Force movement in update loop?
    # RTM calculates steering. We need to trick it into moving.
    # We can just manually set u.grid_x change or mock SteeringManager?
    # RTM calls SteeringManager.calculate_combined_steering.
    # Let's mock SteeringManager in the import? Hard.
    
    # Alternative: The update loop checks "is_moving = abs(dx) > 0.01".
    # dx comes from SteeringManager.
    # If we set u.movement_points to 0, dx might still be non-zero but speed 0?
    # Let's mock SteeringManager.calculate_combined_steering on the class?
    
    from src.combat.real_time.steering_manager import SteeringManager
    original_steer = SteeringManager.calculate_combined_steering
    SteeringManager.calculate_combined_steering = lambda *args, **kwargs: (1.0, 0.0) # Move X
    
    # Run for 10 seconds
    for _ in range(10):
        rtm.update(state, 1.0)
        
    print(f"   Fatigue after 10s moving: {u.fatigue}")
    
    # Expected: 1.0 per sec * 10 = 10.0
    if 9.0 <= u.fatigue <= 11.0:
        print("PASS")
    else:
        print(f"FAIL: Expected ~10, got {u.fatigue}")

    # 3. Test Exhaustion Stats
    print("3. Exhaustion Stats Test...")
    u.fatigue = 90.0 # Exhausted
    print(f"   MA (Base 50) at 90 Fatigue: {u.ma}")
    print(f"   MD (Base 50) at 90 Fatigue: {u.md}")
    
    if u.ma == 25 and u.md == 25:
        print("PASS: Stats reduced by 50%")
    else:
        print(f"FAIL: Expected 25/25, got {u.ma}/{u.md}")
        
    # Restore
    SteeringManager.calculate_combined_steering = original_steer

if __name__ == "__main__":
    test_fatigue()
