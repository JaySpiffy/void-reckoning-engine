import os
import sys
import random

# Add project root to path
sys.path.append(os.getcwd())

from src.models.unit import Regiment, Unit
from src.models.army import ArmyGroup
from src.managers.battle_manager import BattleManager
from src.core.simulation_topology import GraphNode
from src.combat.tactical_grid import TacticalGrid
from src.combat.combat_simulator import execute_battle_round, initialize_battle_state

class MockEngine:
    def __init__(self):
        self.turn_counter = 1
        self.fleets = []
        self.telemetry = MockTelemetry()
        self.all_planets = []
    
    def log_battle_result(self, *args):
        pass

class MockTelemetry:
    def log_event(self, *args, **kwargs):
        pass

def test_regiment_components():
    print("\n--- Test 1: Regiment Components ---")
    r = Regiment("Imperial Guard", 35, 30, 10, 5, 2, {}, faction="Imperium")
    # By default should have Core Org and Standard Armaments
    comp_names = [c.name for c in r.components]
    print(f"Components: {comp_names}")
    assert "Core Organization" in comp_names
    assert "Standard Armaments" in comp_names
    print("SUCCESS: Regiment generated components.")

def test_army_engagement_lock():
    print("\n--- Test 2: Army Engagement Lock ---")
    node = GraphNode("BattleZone", "Province")
    r1 = Regiment("Attacker", 40, 30, 10, 5, 2, {})
    ag = ArmyGroup("Army_A", "Imperium", [r1], node)
    
    print(f"Initial engaged: {ag.is_engaged}")
    assert ag.is_engaged == False
    
    # Simulate engagement
    ag.is_engaged = True
    print(f"Locked engaged: {ag.is_engaged}")
    
    # Try retreat
    ret_node = GraphNode("SafeZone", "Province")
    ag.retreat(ret_node)
    print(f"State after retreat: {ag.state}, Destination: {ag.destination}")
    print(f"Engaged after retreat: {ag.is_engaged}")
    assert ag.is_engaged == False
    assert ag.state == "MOVING"
    print("SUCCESS: Army engagement and retreat logic working.")

def test_tactical_terrain():
    print("\n--- Test 3: Tactical Terrain/Cover ---")
    grid = TacticalGrid(10, 10)
    # Check if terrain was generated
    terrain_count = len(grid.terrain_map)
    print(f"Generated {terrain_count} terrain tiles on 10x10 grid.")
    assert terrain_count > 0
    
    # Check cover query
    cover = grid.get_cover_at(0, 0)
    print(f"Cover at (0,0): {cover}")
    print("SUCCESS: TacticalGrid terrain support verified.")

def test_ground_combat_resolution():
    print("\n--- Test 4: Ground Combat Melee/Shooting ---")
    # Setup 1v1 Regiment Battle - Using 100 MA to guarantee hits for test
    r1 = Regiment("Ultramarine", 100, 40, 50, 3, 10, {"Tags": ["Infantry"]}, faction="Imperium")
    r2 = Regiment("Ork Boy", 100, 30, 60, 6, 8, {"Tags": ["Infantry"]}, faction="Orks")
    
    armies = {
        "Imperium": [r1],
        "Orks": [r2]
    }
    
    state = initialize_battle_state(armies)
    grid = state["grid"]
    
    # Manual Placement for Melee Test (Distance 0)
    grid.remove_unit(r1)
    grid.remove_unit(r2)
    grid.place_unit(r1, 5, 5)
    grid.place_unit(r2, 6, 5) # Dist 1.0 (Adjacent)
    
    dist = grid.get_distance(r1, r2)
    print(f"Units at distance: {dist}")
    
    # Run 1 Round
    execute_battle_round(state)
    
    # Check if damage happened
    print(f"R1 HP: {r1.current_hp}/{r1.max_hp}")
    print(f"R2 HP: {r2.current_hp}/{r2.max_hp}")
    
    # In distance 1, they should have fired pistols or moved/shot? 
    # Wait, Phase 4 Melee triggers for < 1.5 dist.
    # So they should have fought in Melee.
    # Let's check logs if we had them, but HP reduction is proof enough.
    assert r1.current_hp < 50 or r2.current_hp < 60
    print("SUCCESS: Ground combat resolution (Melee/Shooting) verified.")

if __name__ == "__main__":
    try:
        test_regiment_components()
        test_army_engagement_lock()
        test_tactical_terrain()
        test_ground_combat_resolution()
        print("\n=== ALL PHASE 18 TESTS PASSED ===")
    except Exception as e:
        print(f"\n!!! TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
