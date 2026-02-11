
import math
from unittest.mock import MagicMock
from src.combat.realtime.realtime_manager import RealTimeManager
from src.combat.components.weapon_component import WeaponComponent

def test_firing_arcs():
    print("Testing Firing Arcs...")
    
    # Setup
    manager = RealTimeManager()
    manager.projectile_manager = MagicMock()
    
    # Mock Unit
    u = MagicMock()
    u.name = "TestShip"
    u.grid_x = 0
    u.grid_y = 0
    u.facing = 0.0 # Facing East (X+)
    u.is_alive.return_value = True
    u.is_ship.return_value = True
    u.morale_state = "Steady"
    u.tactical_directive = "HOLD" # Don't move
    u.current_suppression = 0
    u.time_since_last_damage = 0.0
    u.recent_damage_taken = 0.0
    u.morale_current = 100
    u.morale_max = 100
    u.morale_max = 100
    u.bs = 100 # Perfect accuracy to ensure firing
    u.damage = 1
    u.domain = "space"
    u.movement_comp = MagicMock()
    u.movement_comp.turn_rate = 10.0
    u.movement_comp.acceleration = 1.0
    u.movement_comp.base_movement_points = 10.0
    u.movement_comp.base_movement_points = 10.0
    u.movement_comp.facing = 0.0
    u.movement_comp.current_speed = 0.0
    u.detection_range = 800
    
    # Weapons
    # Mocking as actual objects partially to pass isinstance checks if any? No, loose typing.
    # But RealTimeManager uses getattr(wpn, 'arc', "Front")
    
    def create_weapon(name, arc):
        w = MagicMock(spec=WeaponComponent)
        w.name = name
        w.arc = arc
        w.weapon_stats = {"Range": 100, "S": 10, "ap": 0, "D": 1, "attacks": 10.0, "category": "KINETIC"}
        w.cooldown = 0
        w.is_destroyed = False
        w.type = "Weapon"
        return w

    w_front = create_weapon("FrontGun", "Front")
    w_left = create_weapon("LeftGun", "Left")
    w_right = create_weapon("RightGun", "Right")
    w_rear = create_weapon("RearGun", "Rear")
    
    u.weapon_comps = [w_front, w_left, w_right, w_rear]
    u.components = u.weapon_comps
    
    # BattleState
    bs = MagicMock()
    bs.grid = MagicMock()
    bs.grid.get_distance.side_effect = lambda a, b: math.sqrt((a.grid_x - b.grid_x)**2 + (a.grid_y - b.grid_y)**2)
    bs.grid.get_modifiers_at.return_value = {}
    bs.armies_dict = {"FactionA": [u]}
    bs.active_factions = ["FactionA", "FactionB"]
    bs.faction_doctrines = {"FactionA": "HOLD"}
    bs.total_sim_time = 0.0
    bs.last_snapshot_time = 0.0
    bs.mechanics_engine = MagicMock()
    bs.mechanics_engine.config.throttle_snapshots = False
    bs._orbital_cooldown = 0
    
    # Targets
    target_front = MagicMock()
    target_front.name = "TargetFront"
    target_front.grid_x = 10 # East (Rel Angle 0)
    target_front.grid_y = 0
    target_front.is_alive.return_value = True
    target_front.components = []
    
    target_left = MagicMock()
    target_left.name = "TargetLeft"
    target_left.grid_x = 0
    target_left.grid_y = 10 # North (Rel Angle 90) -> Left
    target_left.is_alive.return_value = True
    target_left.components = []

    target_right = MagicMock()
    target_right.name = "TargetRight"
    target_right.grid_x = 0
    target_right.grid_y = -10 # South (Rel Angle -90) -> Right
    target_right.is_alive.return_value = True
    target_right.components = []

    for t in [target_front, target_left, target_right]:
        t.current_suppression = 0
        t.time_since_last_damage = 0.0
        t.recent_damage_taken = 0.0
        t.morale_current = 100
        t.morale_max = 100
        t.bs = 50
        t.damage = 1
        t.detection_range = 800
        t.domain = "space"
        t.is_ship.return_value = True
        t.weapon_range_default = 24
        t.facing = 0.0

    # Mock TargetSelector and MovementCalculator
    from src.combat.tactical.target_selector import TargetSelector
    from src.combat.tactical.movement_calculator import MovementCalculator
    
    original_selector = TargetSelector.select_target_by_doctrine
    TargetSelector.select_target_by_doctrine = MagicMock()
    
    original_mocalc = MovementCalculator.calculate_movement_vector
    MovementCalculator.calculate_movement_vector = MagicMock(return_value=(0.0, 0.0))
    
    try:
        # Case 1: Target Front
        print("\n--- Scenario 1: Target Front ---")
        TargetSelector.select_target_by_doctrine.return_value = (target_front, None)
        bs.armies_dict["FactionB"] = [target_front]
        
        manager.update(bs, 0.1)
        
        fired = check_fired(bs)
        assert_fired(fired, ["FrontGun"], "Front Target")

        # Case 2: Target Left
        print("\n--- Scenario 2: Target Left ---")
        reset_weapons([w_front, w_left, w_right, w_rear])
        bs.log_event.reset_mock()
        TargetSelector.select_target_by_doctrine.return_value = (target_left, None)
        bs.armies_dict["FactionB"] = [target_left]
        
        manager.update(bs, 0.1)
        
        fired = check_fired(bs)
        assert_fired(fired, ["LeftGun"], "Left Target")

        # Case 3: Target Right
        print("\n--- Scenario 3: Target Right ---")
        reset_weapons([w_front, w_left, w_right, w_rear])
        bs.log_event.reset_mock()
        TargetSelector.select_target_by_doctrine.return_value = (target_right, None)
        bs.armies_dict["FactionB"] = [target_right]
        
        manager.update(bs, 0.1)
        
        fired = check_fired(bs)
        assert_fired(fired, ["RightGun"], "Right Target")

    finally:
        TargetSelector.select_target_by_doctrine = original_selector
        MovementCalculator.calculate_movement_vector = original_mocalc

def reset_weapons(weapons):
    for w in weapons:
        w.cooldown = 0

def check_fired(bs):
    fired_names = []
    for c in bs.log_event.call_args_list:
        args = c[0]
        if args[0] == "shooting_fire":
             desc = args[3]
             if "FrontGun" in desc: fired_names.append("FrontGun")
             if "LeftGun" in desc: fired_names.append("LeftGun")
             if "RightGun" in desc: fired_names.append("RightGun")
             if "RearGun" in desc: fired_names.append("RearGun")
    return fired_names

def assert_fired(actual, expected, scenario):
    actual.sort()
    expected.sort()
    if actual == expected:
        print(f"SUCCESS {scenario}: Fired {actual}")
    else:
        print(f"FAIL {scenario}: Expected {expected}, got {actual}")

if __name__ == "__main__":
    test_firing_arcs()
