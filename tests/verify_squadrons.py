
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.unit import Ship
from src.combat.realtime.realtime_manager import RealTimeManager

class MockGrid:
    def __init__(self):
        self.obstacles = []
        self.spatial_index = None
    def get_modifiers_at(self, x, y):
        return {}
    def query_units_in_range(self, x, y, radius, faction_filter=None):
        return []
    def update_unit_position(self, u, x, y):
        pass
    def get_distance(self, u1, u2):
        return 10.0 # Always in range

class MockBattleState:
    def __init__(self, units):
        self.total_sim_time = 0.0
        self.last_snapshot_time = 0.0
        self.grid = MockGrid()
        self.armies_dict = {"FactionA": units, "FactionB": []} # Enemies handled differently in RTM
        self.active_factions = ["FactionA", "FactionB"]
        self.victory_points = {"FactionA": 0}
        self.faction_doctrines = {"FactionA": "STANDARD"}
        self.tracker = None
        self.mechanics_engine = None
        self.projectiles_spawned = 0
    def log_event(self, *args):
        pass
    def _take_snapshot(self):
        pass
    def track_unit_destruction(self, *args):
        pass

class MockProjectileManager:
    def __init__(self, grid):
        self.spawn_count = 0
    def spawn_projectile(self, owner, *args, **kwargs):
        self.spawn_count += 1
        # print(f"DEBUG: Shot by {owner.name} at {kwargs.get('lifetime', '?')}")
    def update(self, *args):
        pass

def test_squadrons():
    print("=== Testing Squadron Logic ===")
    
    # Setup: Tie Fighter Squadron (10 HP, 10 Members -> 1 HP per member)
    u = Ship("TIE Fighter", "FactionA", hp=10, max_members=10)
    # Give weapon
    from src.combat.components.weapon_component import WeaponComponent
    stats = {"Range": 100, "S": 1, "attacks": 1.0, "category": "LASER", "AP": 0}
    wpn = WeaponComponent("Laser", stats)
    u.add_component(wpn)
    u.init_combat_state()
    
    # Mock Enemy
    target = Ship("X-Wing", "FactionB", hp=10)
    target.grid_x, target.grid_y = 10, 0
    # Silence Target (Give it a text component to block Dummy, or just 0 damage weapon)
    # If we add a weapon, RealTimeManager uses it. Range 0 prevents firing.
    target.add_component(WeaponComponent("Silencer", {"Range": 0}))
    target.init_combat_state()
    
    # Mock State/Manager
    # RTM needs enemies_by_faction populated
    rtm = RealTimeManager()
    rtm.projectile_manager = MockProjectileManager(MockGrid())
    
    # We need to monkey patch RTM to use our mock projectile manager 
    # OR just use the one we set if update checks for it.
    # Update checks if self.projectile_manager is None. We set it, so it keeps it.
    
    state = MockBattleState([u])
    state.armies_dict["FactionB"] = [target]
    
    # 1. Full Strength Test
    print(f"1. Full Strength (10/10 Members)...")
    print(f"   Member Count: {u.member_count}")
    if u.member_count != 10:
        print(f"FAIL: Expected 10, got {u.member_count}")
        return

    # Run for 1.0 second. Attacks = 1.0 * 10 = 10 shots/sec.
    # Cooldown = 0.1s.
    # Update loop needs dt small enough to catch multiple shots?
    # RTM loop: if cooldown > 0: cooldown -= dt.
    # So we can run 1.0s in one go? No, we need to iterate.
    # If dt=0.05 (20Hz).
    
    rtm.projectile_manager.spawn_count = 0
    for _ in range(20): # 1 second total
        rtm.update(state, 0.05)
        
    print(f"   Shots fired in 1s: {rtm.projectile_manager.spawn_count}")
    
    # Expected: ~10 shots. Maybe 9 or 11 depending on phase alignment.
    if 9 <= rtm.projectile_manager.spawn_count <= 11:
        print("PASS: Fire rate scaled correctly.")
    else:
        print(f"FAIL: Expected ~10, got {rtm.projectile_manager.spawn_count}")

    # 2. Damage Test (50% HP)
    print("\n2. Taking 5 Damage (50% HP)...")
    u.take_damage(5.0) # Down to 5 HP
    print(f"   Member Count: {u.member_count}")
    
    if u.member_count != 5:
        print(f"FAIL: Expected 5, got {u.member_count}")
    else:
        print("PASS: Member count reduced.")
        
    rtm.projectile_manager.spawn_count = 0 
    for _ in range(20): # 1 second total
        rtm.update(state, 0.05)
        
    print(f"   Shots fired in 1s: {rtm.projectile_manager.spawn_count}")
    
    # Expected: ~5 shots.
    if 4 <= rtm.projectile_manager.spawn_count <= 6:
        print("PASS: Fire rate reduced correctly.")
    else:
        print(f"FAIL: Expected ~5, got {rtm.projectile_manager.spawn_count}")

if __name__ == "__main__":
    test_squadrons()
