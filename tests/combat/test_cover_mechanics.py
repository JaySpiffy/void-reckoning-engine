
import pytest
from unittest.mock import MagicMock
from src.models.unit import Unit
from src.combat.combat_state import CombatState
from src.combat.tactical_grid import TacticalGrid
from src.combat.realtime.realtime_manager import RealTimeManager

def test_directional_cover_reduction():
    """Verify that cover reduces damage only from the front."""
    
    # Setup State & Grid
    state = CombatState({}, {}, {})
    state.grid = TacticalGrid(50, 50)
    state.realtime_manager = RealTimeManager()
    
    # Mock get_cover_at to return Heavy Cover for Target (50% reduction)
    state.grid.get_cover_at = MagicMock(return_value="Heavy")
    
    # 1. Frontal Attack
    attacker_front = Unit(name="Attacker", faction="A", ma=50, md=50, hp=100, armor=0, damage=2, abilities={})
    attacker_front.bs = 100
    attacker_front.grid_x, attacker_front.grid_y = 10, 20
    
    target = Unit(name="Defender", faction="D", ma=50, md=50, hp=100, armor=0, damage=10, abilities={})
    target.grid_x, target.grid_y = 10, 10
    target.facing = 0 # Facing North (towards Attacker at 10,20?)
    # Wait, bearing calculation depends on math.
    # Attacker is at (10, 20), Target at (10, 10). Relative bearing?
    # atan2(dy, dx) -> atan2(10, 0) = 90 deg (North).
    # If Target facing is 90 (North), then bearing is 0 relative.
    target.facing = 90.0 
    
    # Calculate bearing manually or trust logic?
    # Logic in CombatState: rel_bearing = grid.get_relative_bearing(target, attacker)
    # If rel_bearing is within [315, 360] U [0, 45], it's FRONT.
    
    # Let's run a simplified check by leveraging the logic snippet or mocking get_relative_bearing
    state.grid.get_relative_bearing = MagicMock(return_value=0.0) # Dead Front
    
    # Execute Damage Logic (Mocking the loop usually found in update)
    # Since we can't easily run the full loop without setup, we'll verify the math logic conceptually
    # by reproducing the snippet or trusting a full integration test.
    # We will use the 'take_damage' logic which we didn't modify for cover (it's in the loop).
    # So we need to test the Loop integration or the State method.
    
    # Actually, the logic is embedded in `real_time_update`.
    # Let's use a mock "take_damage" on the unit to see what it receives.
    target.take_damage = MagicMock(return_value=(0, 0, 0, None))
    
    # Create armies dict
    state.armies_dict = {"A": [attacker_front], "D": [target]}
    state.active_factions = ["A", "D"]
    attacker_front._shooting_cooldown = 0
    attacker_front.weapon_range_default = 100
    
    # Prevent Defender from shooting to avoid confusion (and self-fire via mock)
    target._shooting_cooldown = 999
    
    # Mock TargetSelector
    from unittest.mock import patch
    # ...
    with patch('src.combat.tactical.target_selector.TargetSelector.select_target_by_doctrine') as mock_select:
        mock_select.return_value = (target, None)
        
        # Run ONE update tick
        state.real_time_update(0.1)
    
    # Verify: Target took damage.
    # Base Damage = 20. Heavy Cover = 50% reduction. Expected = 10.
    # Note: suppression also applied (2.0 * damage = 20 suppression)
    
    # Check assertions
    # Since take_damage was mocked, we check the call args
    args, kwargs = target.take_damage.call_args
    damage_taken = args[0]
    
    # Allow for floating point tolerance
    # Updated mechanics use SV system. Heavy cover improves save (-0.5), SV 7.0 -> 6.5. 8.33% mitigation. 20 -> 18.33
    assert abs(damage_taken - 18.33) < 0.1, f"Frontal Damage should be ~18.33, got {damage_taken}"
    
def test_flanking_ignores_cover():
    """Verify that flanking bypasses cover."""
    state = CombatState({}, {}, {})
    state.grid = TacticalGrid(50, 50)
    state.realtime_manager = RealTimeManager()
    state.grid.get_cover_at = MagicMock(return_value="Heavy")
    
    # Flanker is behind/side
    attacker_flank = Unit(name="Flanker", faction="A", ma=50, md=50, hp=100, armor=0, damage=2, abilities={})
    attacker_flank.bs = 100
    attacker_flank.grid_x, attacker_flank.grid_y = 20, 10
    
    target = Unit(name="Defender", faction="D", ma=50, md=50, hp=100, armor=0, damage=10, abilities={})
    target.grid_x, target.grid_y = 10, 10
    target.facing = 90.0 # Facing North
    
    # Attacker is at (20, 10) -> East. Bearing from Target is 0 (East in grid 0 angle?)
    # Grid angle usually 0=East, 90=North.
    # If Target facing is 90, and Attacker is at 0 (East), relative bearing is -90 -> 270.
    # 270 is FLANK/SIDE.
    
    state.grid.get_relative_bearing = MagicMock(return_value=270.0) # Left Flank
    
    target.take_damage = MagicMock(return_value=(0, 0, 0, None))
    
    state.armies_dict = {"A": [attacker_flank], "D": [target]}
    state.active_factions = ["A", "D"]
    attacker_flank._shooting_cooldown = 0
    attacker_flank.weapon_range_default = 100
    target._shooting_cooldown = 999
    
    from unittest.mock import patch
    with patch('src.combat.tactical.target_selector.TargetSelector.select_target_by_doctrine') as mock_select:
        mock_select.return_value = (target, None)
        state.real_time_update(0.1)
    
    args, kwargs = target.take_damage.call_args
    damage_taken = args[0]
    
    # Expected: Full 20.0 damage (Bypassed Cover)
    assert abs(damage_taken - 20.0) < 0.1, f"Flank Damage should be 20.0, got {damage_taken}"

if __name__ == "__main__":
    test_directional_cover_reduction()
    test_flanking_ignores_cover()
    print("Cover Mechanics Verified!")
