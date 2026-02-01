import pytest
from unittest.mock import MagicMock
from src.combat.tactical_grid import TacticalGrid
from src.combat.tactical.gpu_tracker import GPUTracker
from src.combat.tactical_engine import initialize_battle_state, execute_battle_round
from src.models.unit import Unit
from src.core import gpu_utils

class MockFaction:
    def __init__(self, name):
        self.name = name

class MockUnit(Unit):
    def __init__(self, name, x, y, faction):
        self.name = name
        self.grid_x = x
        self.grid_y = y
        self.faction = faction
        self.is_deployed = True
        self.components = []
        self.current_hp = 100
        self.base_hp = 100
        self.base_ma = 50
        self.base_md = 50
        self.rank = 0
        self.leadership = 8
        self.tactical_roles = []
        self.active_mods = {}
        self.movement_points = 1
        self.bs = 50
        self.armor = 10
        self.weapon_arcs = {}
        self.is_suppressed = False
        
        # Add a mock weapon
        class MockWpn:
             type = "Weapon"
             name = "Bolter"
             is_destroyed = False
             current_hp = 100
             weapon_stats = {"Range": 24, "Str": 4, "AP": 0, "Type": "Kinetic"}
        self.components.append(MockWpn())
        self.abilities = {}
        
    def is_alive(self):
        return self.current_hp > 0
    
    def take_damage(self, amount):
        self.current_hp -= amount
        return amount, 0, None
    
    def recover_suppression(self):
        pass
        
    def is_ship(self):
        return False
        
    def regenerate_shields(self):
        pass

class TestGPUCombatFlow:
    
    @pytest.mark.skip(reason="CuPy compatibility issue")
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_gpu_tracker_integration(self, monkeypatch):
        """
        Verifies that GPUTracker is initialized and used by TacticalGrid.
        """
        print(f"\nTesting GPU Flow with Backend: {gpu_utils.get_xp().__name__}")
        
        # Force is_available to True so TacticalEngine initializes the tracker even on CPU
        monkeypatch.setattr(gpu_utils, "is_available", lambda: True)
        
        # 1. Setup Battle
        u1 = MockUnit("Attacker", 10, 10, "Imperium")
        u2 = MockUnit("Target", 12, 12, "Orks") # Distance sqrt(8) ~ 2.82
        u3 = MockUnit("FarTarget", 90, 90, "Orks")
        
        armies = {
            "Imperium": [u1],
            "Orks": [u2, u3]
        }
        
        # 2. Initialize State (should create GPUTracker)
        state = initialize_battle_state(armies)
        
        # ASSERT: GPUTracker exists
        assert hasattr(state, 'gpu_tracker')
        assert state.gpu_tracker is not None
        assert state.gpu_tracker.active_count == 3
        
        # ASSERT: Grid has reference
        assert hasattr(state.grid, 'gpu_tracker')
        assert state.grid.gpu_tracker is not None
        
        # 3. Test find_nearest_enemy via Grid (should use GPU path)
        nearest = state.grid.find_nearest_enemy(u1)
        assert nearest == u2
        
        # 4. Move Unit & Update
        # Move u2 far away manually
        u2.grid_x = 80
        u2.grid_y = 80
        # Now u3 (90,90) is closer to u2 than u1? No we check from u1 (10,10)
        # u2 (80,80), u3 (90,90). Bot far.
        # Let's move u3 close to u1
        u3.grid_x = 11
        u3.grid_y = 11
        
        # Execute Round (should trigger gpu_tracker.update_positions)
        # Check logs/logic
        execute_battle_round(state)
        
        # Now find nearest again. Should be u3
        nearest_new = state.grid.find_nearest_enemy(u1)
        assert nearest_new == u3
        
        print("GPU Integration Verified: Tracker updates and Grid queries work.")
