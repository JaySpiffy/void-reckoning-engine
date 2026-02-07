
import math
from unittest.mock import MagicMock
from src.combat.realtime.projectile_manager import ProjectileManager
from src.models.projectile import Projectile

class MockUnit:
    def __init__(self, x, y, name="Target"):
        self.grid_x = x
        self.grid_y = y
        self.name = name
        self.faction = "TargetFaction"
        self.is_alive = lambda: True
        self.take_damage = MagicMock(return_value=(10, 0, False, "hit"))

def test_tunneling():
    print("Testing Projectile Tunneling...")
    grid = MagicMock()
    pm = ProjectileManager(grid)
    
    # Setup: 
    # Target at (100, 0)
    # Shooter at (0, 0)
    # Projectile speed 120 (Kinetic), dt=0.1 -> step 12.0
    # Steps: 0, 12, 24, 36, 48, 60, 72, 84, 96, 108...
    # At 108, dist to 100 is 8.
    # At 96, dist is 4.
    # It misses the 2.0 threshold!
    
    target = MockUnit(100, 0)
    shooter = MockUnit(0, 0, "Shooter")
    
    # Spawn projectile manually to control parameters
    # Projectile(owner, target, damage, ap, speed, pos, projectile_type=projectile_type, **kwargs)
    proj = Projectile(shooter, target, 10, 0, 120.0, (0, 0), projectile_type="KINETIC")
    pm.projectiles.append(proj)
    
    battle_state = MagicMock()
    battle_state.tracker = MagicMock()
    battle_state.battle_stats = {}
    
    # Simulate ticks
    dt = 0.1
    hit = False
    
    print(f"Start: Proj at ({proj.x}, {proj.y}), Target at ({target.grid_x}, {target.grid_y})")
    
    for i in range(20):
        pm.update(dt, battle_state)
        print(f"Tick {i+1}: Proj at ({proj.x:.2f}, {proj.y:.2f})")
        
        if proj.is_destroyed:
            print("Projectile destroyed (Hit!)")
            hit = True
            break
            
    if not hit:
        print("FAIL: Projectile tunneled through target!")
    else:
        print("SUCCESS: Projectile hit target.")

if __name__ == "__main__":
    test_tunneling()
