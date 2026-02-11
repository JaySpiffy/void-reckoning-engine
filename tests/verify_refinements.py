
import sys
import os
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Add source path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.ai.tactical_ai import TacticalAI
from src.managers.economy_manager import EconomyManager

# --- Mock Classes ---

@dataclass
class MockUnit:
    faction: str
    id: str
    name: str = "TestUnit"
    grid_x: int = 0
    grid_y: int = 0
    components: List[Any] = field(default_factory=list)
    current_hp: float = 100.0
    max_hp: float = 100.0

@dataclass
class MockComponent:
    type: str = "Weapon"
    weapon_stats: Dict = field(default_factory=lambda: {"Range": 10})

@dataclass
class MockFaction:
    name: str
    requisition: float = 1000.0
    poor_performance_streak: int = 0
    enemies: List[str] = field(default_factory=list)
    unlocked_techs: List[str] = field(default_factory=list)

@dataclass
class MockGrid:
    width: int = 100
    height: int = 100
    units: List[MockUnit] = field(default_factory=list)
    
    def get_unit_at(self, x, y):
        for u in self.units:
            if u.grid_x == x and u.grid_y == y:
                return u
        return None
        
    def get_distance(self, u1, u2):
        return math.sqrt((u1.grid_x - u2.grid_x)**2 + (u1.grid_y - u2.grid_y)**2)

class MockEngine:
    def __init__(self):
        self.game_config = {"simulation": {"random_seed": 12345}}
        self.logger = None
        self.telemetry = None
        self.factions = {}
        self.fleets_by_faction = {}
        self.planets_by_faction = {}
        self.cache_manager = None
        self.turn_counter = 1
    
    def get_faction(self, name):
        return self.factions.get(name)
    
    def get_all_factions(self):
        return list(self.factions.values())

# --- Tests ---

def test_guerrilla_movement():
    print("\n--- Testing GUERRILLA Movement ---")
    
    ai = TacticalAI()
    grid = MockGrid()
    
    # Setup Unit at (10, 10) with Range 10
    unit = MockUnit("F1", "U1", components=[MockComponent(type="Weapon", weapon_stats={"Range": 10})])
    unit.grid_x = 10
    unit.grid_y = 10
    
    # Enemy at (20, 10) -> Distance 10 (Max Range)
    enemy = MockUnit("F2", "E1")
    enemy.grid_x = 20
    enemy.grid_y = 10
    
    grid.units = [unit, enemy]
    
    # 1. Test Standard CHARGE (Optimal Range 1)
    # Should move TOWARDS enemy (11, 10) -> Dist 9
    context = {"doctrine": "CHARGE", "war_goal": "NONE"}
    move = ai.decide_movement(unit, grid, [enemy], context)
    print(f"CHARGE Move: {move} (Expected (1, 0) or similar to close distance)")
    
    # 2. Test GUERRILLA (Kite at Max Range)
    # Current Dist is 10. Max Range is 10.
    # Moving closer (1, 0) -> Dist 9. Ratio 0.9. Good?
    # Moving away (-1, 0) -> Dist 11. Ratio 1.1. Good?
    # Stay (0, 0) -> Dist 10. Ratio 1.0. Sweet spot. 
    # But decide_movement iterates neighbors.
    
    context = {"doctrine": "KITE", "war_goal": "GUERRILLA"}
    move = ai.decide_movement(unit, grid, [enemy], context)
    print(f"GUERRILLA Move (at Max Range): {move}")
    
    # 3. Test GUERRILLA (Too Close)
    # Unit at (15, 10) -> Dist 5. Ratio 0.5.
    unit.grid_x = 15
    context = {"doctrine": "KITE", "war_goal": "GUERRILLA"}
    move = ai.decide_movement(unit, grid, [enemy], context)
    print(f"GUERRILLA Move (Too Close, Dist 5): {move} (Expected (-1, 0) to retreat)")
    
    if move == (-1, 0):
        print("✅ GUERRILLA correctly retreated.")
    else:
        print(f"❌ GUERRILLA failed to retreat. Move: {move}")


def test_economic_adaptation():
    print("\n--- Testing Economic Adaptation ---")
    
    engine = MockEngine()
    econ_mgr = EconomyManager(engine)
    
    # 1. Normal State
    f1 = MockFaction("Faction1")
    f1.poor_performance_streak = 0
    engine.factions["Faction1"] = f1
    
    # Mock cached econ
    econ_cache = {
        "income": 1000,
        "total_upkeep": 500,
        "income_by_category": {},
        "military_upkeep": 100
    }
    
    data = econ_mgr._hydrate_cached_econ("Faction1", econ_cache, f1)
    print(f"Normal Mode: {data['active_mode']['name']}")
    if data['active_mode']['name'] in ["EXPANSION", "CONSOLIDATION"]: 
         print("✅ Normal mode selected.")
    else:
         print("❌ Unexpected mode.")

    # 2. Poor Performance Streak -> CONSOLIDATION
    f1.poor_performance_streak = 6
    data = econ_mgr._hydrate_cached_econ("Faction1", econ_cache, f1)
    print(f"Poor Streak (Peace): {data['active_mode']['name']}")
    
    if data['active_mode']['name'] == "CONSOLIDATION":
        print("✅ Correctly forced CONSOLIDATION.")
    else:
         print(f"❌ Failed to force CONSOLIDATION. Got: {data['active_mode']['name']}")

    # 3. Poor Performance + War -> DESPERATE_DEFENSE
    f1.enemies = ["Faction2"]
    data = econ_mgr._hydrate_cached_econ("Faction1", econ_cache, f1)
    print(f"Poor Streak (War): {data['active_mode']['name']}")
    
    if data['active_mode']['name'] == "DESPERATE_DEFENSE":
        print("✅ Correctly forced DESPERATE_DEFENSE.")
    else:
         print(f"❌ Failed to force DESPERATE_DEFENSE. Got: {data['active_mode']['name']}")
         
    # 4. Bankruptcy Override (Should beat Streak)
    f1.requisition = -500
    data = econ_mgr._hydrate_cached_econ("Faction1", econ_cache, f1)
    print(f"Bankruptcy (Req -500): {data['active_mode']['name']}")
    
    if data['active_mode']['name'] == "RECOVERY":
        print("✅ Bankruptcy correctly overrode Streak.")
    else:
         print(f"❌ Bankruptcy failed to override. Got: {data['active_mode']['name']}")

if __name__ == "__main__":
    test_guerrilla_movement()
    test_economic_adaptation()
