
import sys
import os
import shutil
import random

# Fix path
sys.path.append(os.getcwd())

from src.managers.campaign_manager import CampaignEngine
from src.managers.battle_manager import BattleManager
from src.models.fleet import Fleet
from src.core.simulation_topology import GraphNode
from src.models.planet import Planet
from src.managers.economy_manager import EconomyManager
from src.models.faction import Faction

# Dummy Unit for patching
class MockUnit:
    def __init__(self, name, faction):
        self.name = name
        self.faction = faction
        self.is_alive_val = True
        self.strength = 100
        self.transport_capacity = 0
        self.abilities = {}
        self.grid_size = [1,1]
        self.facing = 0
        self.agility = 45
        self.weapon_arcs = {}
        self.armor_front = 10
        self.armor_side = 10
        self.armor_rear = 10
        self.components = []
        self.bs = 50
        self.is_suppressed = False
        self.shield = 0 
        self.shield_max = 0
        self.state = "IDLE"
        self.movement_points = 10
        self.morale = 100
        self.current_morale = 100
        self.is_broken = False
        self.weapons = []
        self.psyker_mastery = 0
        self.toughness = 40
        self.strength = 10 
        self._is_ship = True

    def is_ship(self): return getattr(self, "_is_ship", True)
    def is_alive(self): return self.is_alive_val
    def recover_suppression(self): pass
    def regenerate_shields(self): pass
    def take_damage(self, dmg): return 0, 0, None
    def to_dict(self):
        return {
            "name": self.name,
            "faction": self.faction,
            "is_alive": self.is_alive_val,
            "strength": self.strength
        }

def verify_persistent_warfare():
    print("=== Verifying Phase 17c: Granular Siege Locking ===")
    
    # 1. Setup minimal engine
    engine = CampaignEngine()
    engine.factions = {"Imperium": Faction("Imperium"), "Orks": Faction("Orks")}
    engine.all_planets = []
    
    # Create Planet with Provinces
    p1 = Planet("System_A", None, 1)
    p1.planet_class = "Tundra"
    p1.owner = "Imperium"
    p1.recalc_stats()
    engine.all_planets.append(p1)
    
    # Mock Provinces
    n_city1 = GraphNode("City_1", "Province")
    n_city1.building_slots = 3
    n_city2 = GraphNode("City_2", "Province")
    n_city2.building_slots = 3
    p1.provinces = [n_city1, n_city2]
    
    # Orbit Node
    n_orbit = GraphNode("Orbit_A", "Planet")
    p1.node_reference = n_orbit
    n_orbit.metadata = {"object": p1}

    # 2. Setup Context
    econ = EconomyManager(engine)
    engine.tech_manager = type('obj', (object,), {'faction_tech_trees': {}})
    engine.unit_blueprints = {"Imperium": []}
    engine.game_config = {
        "mechanics": {"ai_economy": {"sustainability_check": False}},
        "combat": {"rounds_per_turn": 1}
    }
    
    print("\n--- Test 1: Orbital Siege (Planet Node) ---")
    # Start space battle at p1
    f1 = Fleet("Fleet_A1", "Imperium", p1)
    f2 = Fleet("Fleet_B1", "Orks", p1)
    engine.fleets = [f1, f2]
    
    engine.battle_manager.resolve_battles_at(p1)
    
    if p1.is_sieged:
        print("PASS: Planet marked as is_sieged (Orbit).")
    else:
        print("FAIL: Planet NOT marked as sieged.")

    # Check Locks
    cost = econ._process_planet_construction(p1, "Imperium", engine.factions["Imperium"], 10000, "EXPANSION")
    # Since all nodes prefer sorted_nodes, and orbital siege halves everything in my current logic for abstract buildings
    # but does it block node buildings?
    # In Faction.construct_building:
    # if getattr(node, 'is_sieged', False): continue
    # If node is NOT sieged, it SHOULD allow building! (requested change)
    if cost > 0:
        print("PASS: Construction ALLOWED on cities while orbit is sieged.")
    else:
        print("FAIL: Global orbit lock blocked node construction.")

    # Check Fleet Commission
    # spent = econ._process_recruitment("Imperium", engine.factions["Imperium"], [p1], 10000)
    # The above is prone to budget errors etc. Let's just check the logic directly.
    # In EconomyManager: if getattr(spawn_point, 'is_sieged', False): continue
    
    # We can try to call it and see if it prints the block message
    print("  > Testing Recruitment Lock...")
    spent = econ._process_recruitment("Imperium", engine.factions["Imperium"], [p1], 10000)
    if spent == 0:
        print("PASS: Fleet recruitment blocked by Orbital Siege.")
    else:
        # Check if it was blocked but spent because of other reasons? 
        # No, if is_sieged it should return 0 for that planet.
        print(f"FAIL: Fleet recruitment allowed ({spent}) despite Orbital Siege flag={p1.is_sieged}")

    # Check Production Queue (Land Units)
    p1.unit_queue = [{"id": "Guard_Squad", "turns_left": 2, "node_reference": n_city1}]
    p1.process_queue(engine)
    if p1.unit_queue[0]["turns_left"] == 1:
        print("PASS: Land unit production CONTINUES despite Orbital Siege.")
    else:
        print("FAIL: Land unit production frozen by Orbital Siege.")

    print("\n--- Test 2: Node Siege (Province Node) ---")
    # End orbital battle
    engine.battle_manager.active_battles.clear()
    p1.is_sieged = False
    
    # Start ground battle at n_city1
    # We need to mock armies at n_city1
    from src.models.army import ArmyGroup
    ag1 = ArmyGroup("Imperium_Garrison", "Imperium", [MockUnit("Guard", "Imperium")], n_city1)
    ag2 = ArmyGroup("Ork_Infiltrators", "Orks", [MockUnit("Boyz", "Orks")], n_city1)
    n_city1.armies = [ag1, ag2]
    
    engine.battle_manager.resolve_battles_at(n_city1)
    
    if n_city1.is_sieged:
        print("PASS: City_1 marked as is_sieged.")
    else:
        print("FAIL: City_1 NOT marked as sieged.")

    # Check Node Lock (City 1)
    # Mock faction try construct. We need to ensure it only tries City 1 if possible.
    # But Faction.construct_building picks best node.
    # If City 1 is sieged, it should pick City 2.
    n_city1.building_slots = 1
    n_city1.buildings = []
    n_city2.building_slots = 1
    n_city2.buildings = []
    
    # Should skip City 1 and build on City 2
    success = engine.factions["Imperium"].construct_building(p1, "PDF Barracks")
    if success:
        # Check where it went
        last_task = p1.construction_queue[-1]
        if last_task.get("node_id") == "City_2":
            print("PASS: Construction diverted to non-sieged City_2.")
        else:
            print(f"FAIL: Construction started on sieged {last_task.get('node_id')}!")
    else:
        print("FAIL: Construction blocked despite City_2 being free.")

    # Check Production Freeze (City 1)
    p1.unit_queue = [{"id": "Guard_Squad", "turns_left": 2, "node_reference": n_city1}]
    p1.process_queue(engine)
    if p1.unit_queue[0]["turns_left"] == 2:
        print("PASS: Land unit production FROZEN at sieged City_1.")
    else:
        print(f"FAIL: Land unit production ticked at sieged node! Turns left: {p1.unit_queue[0]['turns_left']}")

    # Check Production at City 2
    p1.unit_queue.append({"id": "Guard_B", "turns_left": 2, "node_reference": n_city2})
    # process_queue only processes the FIRST item in the serial queue. 
    # Let's move Guard_B to front to test.
    p1.unit_queue = [{"id": "Guard_B", "turns_left": 2, "node_reference": n_city2}]
    p1.process_queue(engine)
    if p1.unit_queue[0]["turns_left"] == 1:
        print("PASS: Land unit production WORKS at non-sieged City_2.")
    else:
        print("FAIL: City_2 production frozen by City_1 siege.")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    verify_persistent_warfare()
