
import pytest
import math
from unittest.mock import MagicMock
from src.combat.combat_state import CombatState
from src.combat.real_time.steering_manager import SteeringManager
from src.models.unit import Unit

class MockComponent:
    def __init__(self):
        self.current_movement_points = 10
        self.base_movement_points = 10
        self.current_hp = 100
        self.max_hp = 100
        self.base_hp = 100
        self.regen = 0
        self.current_morale = 100
        self.max_morale = 100
        self.suppression = 0
        self.leadership = 7
        self.base_armor = 0
        self.traits = []
        self.abilities = {}
        
    def regenerate_shields(self):
        return 0

class MockUnit(Unit):
    def __init__(self, name, faction, x, y):
        self.comp = MockComponent()
        self.movement_comp = self.comp
        self.health_comp = self.comp
        self.stats_comp = self.comp
        self.morale_comp = self.comp
        self.trait_comp = self.comp
        self.armor_comp = self.comp
        
        self.name = name
        self.faction = faction
        self.grid_x = x
        self.grid_y = y
        self.movement_points = 10
        self.is_alive = lambda: True
        self.current_hp = 100
        self.base_hp = 100
        self.shield_current = 0
        self.shield_max = 0
        self.morale_state = "Steady"
        self.morale_current = 100
        self.morale_max = 100
        self.time_since_last_damage = 0.0
        self.recent_damage_taken = 0.0
        self.tactical_directive = "STANDARD" # Default
        self.facing = 0
        self.formations = []
        self.components = []
        # self.abilities will use trait_comp
        self.domain = "ground"
        self.rank = 0
        self.current_suppression = 0
        self.is_pinned = False
        
    def take_damage(self, amount, target_component=None, impact_angle=0):
        self.current_hp -= amount
        return 0, amount, 0, None
        
def test_doctrine_steering_behavior():
    """Calculates steering vectors for different doctrines and asserts behavior."""
    
    attacker = MockUnit("Attacker", "FactionA", 50, 50)
    target = MockUnit("Target", "FactionB", 60, 50) # 10 units away (Close)
    target_pos = (target.grid_x, target.grid_y)
    
    # 1. Test CHARGE (Should seek aggressively)
    dx, dy = SteeringManager.calculate_combined_steering(
        attacker, 
        neighbors=[], 
        target_pos=target_pos, 
        obstacles=[], 
        doctrine="CHARGE"
    )
    
    # Expect strong positive X movement (towards target at 60)
    assert dx > 0.5, f"CHARGE should aggressively seek target. Got dx={dx}"
    
    # 2. Test KITE (Should flee if too close)
    # Distance is 10. Kite optimal is 25. Should back off.
    dx_kite, dy_kite = SteeringManager.calculate_combined_steering(
        attacker, 
        neighbors=[], 
        target_pos=target_pos, 
        obstacles=[], 
        doctrine="KITE"
    )
    
    assert dx_kite < 0, f"KITE should retreat when too close (Dist 10 < 25). Got dx={dx_kite}"
    
    # 3. Test KITE at Range (Should hold or slow approach)
    attacker.grid_x = 20 # Distance 40. > 35. Should approach slowly.
    dx_kite_far, _ = SteeringManager.calculate_combined_steering(
        attacker, 
        neighbors=[], 
        target_pos=target_pos, 
        obstacles=[], 
        doctrine="KITE"
    )
    
    assert dx_kite_far > 0, "KITE should approach when very far away."
    assert dx_kite_far < dx, "KITE approach should be more cautious than CHARGE."

def test_combat_state_integration():
    """Verifies CombatState correctly propagates faction doctrines."""
    
    # Setup
    units = [
        MockUnit("UnitA", "FactionA", 10, 10),
        MockUnit("UnitB", "FactionB", 90, 90)
    ]
    
    armies = {"FactionA": [units[0]], "FactionB": [units[1]]}
    
    # Inject Doctrine: FactionA = KITE
    doctrines = {"FactionA": "KITE", "FactionB": "CHARGE"}
    
    state = CombatState(armies, doctrines, {}, None)
    state.initialize_battle() # Setup grid
    
    # Mock Grid/Steering internal calls if needed, but we can check state change
    # Run one update tick
    state.real_time_update(0.1)
    
    # Check UnitA (KITE) behavior
    # UnitA is at 10,10. UnitB is at 90,90. Dist ~ 113. 
    # KITE at 113 dist should APPROACH (seek) because it's > 35.
    
    # Let's force them close to test KITE retreat in update
    units[0].grid_x = 85
    units[0].grid_y = 85
    # Dist ~ 7. KITE should flee.
    
    # Reset positions for clarity in new tick
    state.real_time_update(0.1)
    
    # UnitA was at 85. Target at 90. vector is +5.
    # If CHARGE, it would move +X. 
    # If KITE, it should move -X (away).
    
    new_x = units[0].grid_x
    # We expect new_x < 85 if it retreated.
    
    assert new_x < 85, f"UnitA with KITE doctrine should retreat from close enemy. New X: {new_x}"
    
if __name__ == "__main__":
    test_doctrine_steering_behavior()
    test_combat_state_integration()
    print("AI Doctrines Tests Passed!")
