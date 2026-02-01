import pytest
from unittest.mock import MagicMock
from src.combat.tactical.gpu_tracker import GPUTracker
from src.combat.combat_phases import ShootingPhase
from src.core import gpu_utils

pytestmark = pytest.mark.skip(reason="CuPy compatibility issue")

class MockUnit:
    def __init__(self, name, x, y, faction):
        self.name = name
        self.grid_x = x
        self.grid_y = y
        self.faction = faction
        self.is_deployed = True
        self.components = []
        self.current_hp = 100
        self.base_hp = 100
        self.bs = 100 # Guarantee hit
        self.armor = 0 # No mitigation
        self.is_suppressed = False
        self.abilities = {}
        
        # Add a mock weapon
        class MockWpn:
             type = "Weapon"
             name = "Bolter"
             is_destroyed = False
             weapon_stats = {"Range": 50, "Str": 1, "AP": 0, "Type": "Kinetic"} # 10 dmg
        self.components.append(MockWpn())
        
    def is_alive(self):
        return self.current_hp > 0
    
    def take_damage(self, amount):
        self.current_hp -= amount
        return amount, 0, None

class TestGPUShootingBatch:
    
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_batched_shooting(self, monkeypatch):
        print(f"\nTesting Batched Shooting with Backend: {gpu_utils.get_xp().__name__}")
        
        monkeypatch.setattr(gpu_utils, "is_available", lambda: True)
        
        # 1. Setup Units
        # U1 (Imp) vs U2 (Ork)
        u1 = MockUnit("Attacker", 10, 10, "Imperium")
        u2 = MockUnit("Target", 20, 10, "Orks") # Dist 10, within 50 range
        
        units = [u1, u2]
        
        # 2. Setup Tracker
        tracker = GPUTracker()
        tracker.initialize(units)
        
        # 3. Setup Context
        context = {
            "active_units": [(u1, "Imperium"), (u2, "Orks")],
            "enemies_by_faction": {
                "Imperium": [u2],
                "Orks": [u1]
            },
            "grid": MagicMock(), # Not used by batch path
            "tracker": tracker,
            "faction_doctrines": {},
            "faction_metadata": {},
            "round_num": 1,
            "detailed_log_file": None,
            "manager": MagicMock()
        }
        context["manager"].armies_dict = {"Imperium": [u1], "Orks": [u2]}
        
        # 4. Execute Shooting Phase
        phase = ShootingPhase()
        phase.execute(context)
        
        # 5. Verify Damage
        # U1 should shoot U2.
        # BS=100 -> Hit.
        # Str=1 (x10) = 10 dmg.
        assert u2.current_hp < 100, f"Target HP {u2.current_hp} should be < 100"
        print(f"Target HP after shot: {u2.current_hp}")
        
        print("Batched Shooting Verified: Damage applied.")
