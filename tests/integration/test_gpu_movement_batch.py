import pytest
from unittest.mock import MagicMock

pytestmark = pytest.mark.skip(reason="CuPy compatibility issue")

from src.combat.tactical_grid import TacticalGrid
from src.combat.tactical.gpu_tracker import GPUTracker
from src.combat.combat_phases import MovementPhase
from src.models.unit import Unit
from src.core import gpu_utils

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
        self.base_damage = 10
        self.rank = 0
        self.leadership = 8
        self.tactical_roles = []
        self.active_mods = {}
        self.movement_points = 1
        self.active_universe = "Simulated"
        self.traits = []
        self.abilities = {}
        
    def is_alive(self):
        return self.current_hp > 0
    
class TestGPUMovementBatch:
    
    @pytest.mark.gpu
    @pytest.mark.integration
    def test_batched_movement(self, monkeypatch):
        print(f"\nTesting Batched Movement with Backend: {gpu_utils.get_xp().__name__}")
        
        # Force GPU avail
        monkeypatch.setattr(gpu_utils, "is_available", lambda: True)
        
        # 1. Setup Units
        # U1 (Imperium) at (10, 10)
        # U2 (Orks) at (20, 10). Distance 10.
        # U3 (Orks) at (10, 20). Distance 10.
        u1 = MockUnit("Imperium1", 10, 10, "Imperium")
        u2 = MockUnit("Ork1", 20, 10, "Orks")
        u3 = MockUnit("Ork2", 10, 20, "Orks")
        
        units = [u1, u2, u3]
        
        # 2. Setup Tracker
        tracker = GPUTracker()
        tracker.initialize(units)
        
        # 3. Validation: Check Flow Field manually first
        flow = tracker.compute_flow_field()
        
        # U1 should target U2 or U3 (both dist 10).
        # If U2 (20,10): dx=1, dy=0
        # If U3 (10,20): dx=0, dy=1
        u1_vec = flow.get(id(u1))
        assert u1_vec is not None
        # Either (1,0) or (0,1) is valid approach
        assert u1_vec[0] == 1 or u1_vec[1] == 1, f"U1 vector {u1_vec} invalid"
        
        # U2 should target U1 (10,10). U2 is at (20,10). dx=-1, dy=0
        u2_vec = flow.get(id(u2))
        assert u2_vec[0] == -1
        assert u2_vec[1] == 0
        
        # 4. Integrate into Phase
        grid = TacticalGrid(100, 100)
        grid.place_unit(u1, 10, 10)
        grid.place_unit(u2, 20, 10)
        grid.place_unit(u3, 10, 20)
        
        context = {
            "active_units": [(u1, "Imperium"), (u2, "Orks"), (u3, "Orks")],
            "enemies_by_faction": {
                "Imperium": [u2, u3],
                "Orks": [u1]
            },
            "grid": grid,
            "tracker": tracker,
            "faction_doctrines": {"Imperium": "CHARGE", "Orks": "CHARGE"},
            "round_num": 1,
            "detailed_log_file": None
        }
        
        phase = MovementPhase()
        phase.execute(context)
        
        # 5. Check Positions
        # U1 should have moved +1 x or +1 y
        # U2 (20,10) -> (19, 10)
        assert u2.grid_x == 19
        assert u2.grid_y == 10
        
        print("Batched Movement Verified: Units moved according to flow field.")
