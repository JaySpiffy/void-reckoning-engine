
import sys
import os
import math

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.unit import Regiment, Ship
from src.combat.components.health_component import HealthComponent
from src.combat.real_time.steering_manager import SteeringManager

def test_mass():
    print("=== Testing Unit Mass ===")
    
    # Setup: Heavy unit at 0,0. Light unit at 1,0.
    heavy = Regiment("Tank", "FactionA", mass=10.0)
    heavy.grid_x, heavy.grid_y = 0, 0
    
    light = Regiment("Infantry", "FactionA", mass=1.0)
    light.grid_x, light.grid_y = 1, 0 # Distance 1.0
    
    # Calculate Steering for Light (Should be pushed hard)
    # dx = 1-0 = 1.0, dy = 0
    # dist = 1.0
    # mass_ratio = 10 / 1 = 10.0
    # sep force = (1/1) * 10 = 10.0
    dx_l, dy_l = SteeringManager.calculate_combined_steering(light, [heavy], doctrine="CHARGE")
    print(f"   Light Unit Steering (vs Heavy): ({dx_l:.2f}, {dy_l:.2f})")
    
    # Calculate Steering for Heavy (Should ignore light)
    # dx = 0-1 = -1.0
    # mass_ratio = 1 / 10 = 0.1
    # sep force = (-1/1) * 0.1 = -0.1
    dx_h, dy_h = SteeringManager.calculate_combined_steering(heavy, [light], doctrine="CHARGE")
    print(f"   Heavy Unit Steering (vs Light): ({dx_h:.2f}, {dy_h:.2f})")
    
    if dx_l > 5.0 and abs(dx_h) < 0.5:
        print("PASS: Light unit pushed, Heavy unit holds.")
    else:
        print("FAIL: Mass displacement logic incorrect.")

def test_shield_flare():
    print("\n=== Testing Shield Flare ===")
    
    # Setup Unit with 100 Shield, 100 HP
    u = Ship("Cruiser", "FactionA", hp=100, shield=100)
    # Note: Ship init adds HealthComponent via kwargs parsing
    
    print(f"   Initial: Shield={u.health_comp.current_shield}, HP={u.health_comp.current_hp}")
    
    # 1. Pure Shield Hit (Ion Cannon: 10 dmg * 3 = 30 shield breakdown)
    # 30 shield dmg < 100 shield. Full absorb. 0 Hull.
    s, h, destroyed, _ = u.take_damage(10.0, shield_mult=3.0, hull_mult=0.1)
    
    print(f"   Hit 1 (10 dmg, x3 shield): ShieldDmg={s:.1f}, HullDmg={h:.1f}")
    if s == 30.0 and h == 0.0:
        print("PASS: Shield took full amplified damage.")
    else:
        print(f"FAIL: Expected 30.0/0.0, got {s}/{h}")
        
    print(f"   State 1: Shield={u.health_comp.current_shield}, HP={u.health_comp.current_hp}")

    # 2. Bleed Through Hit
    # Current Shield: 70.
    # Damage: 100.
    # Shield Potential: 300.
    # Absorbed: 70.
    # Remainder Ratio: (300 - 70) / 300 = 230/300 = 0.766
    # Remaining Base: 100 * 0.766 = 76.66
    # Hull Potential: 76.66 * 0.1 = 7.66
    
    s, h, destroyed, _ = u.take_damage(100.0, shield_mult=3.0, hull_mult=0.1)
    print(f"   Hit 2 (100 dmg, x3 shield, x0.1 hull): ShieldDmg={s:.1f}, HullDmg={h:.1f}")
    
    if s == 70.0 and 7.0 < h < 8.0:
         print("PASS: Shield depleted, hull took reduced damage.")
    else:
         print(f"FAIL: Expected s=70, h~7.6. Got {s}/{h}")

if __name__ == "__main__":
    test_mass()
    test_shield_flare()
