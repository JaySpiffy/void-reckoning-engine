import os
import json
import sys
from typing import Dict, Any

sys.path.append(os.getcwd())

from src.managers.ai_manager import StrategicAI as AI_Manager
from src.factories.design_factory import ShipDesignFactory

# Mock Engine and Faction
class MockFaction:
    def __init__(self, name):
        self.name = name
        self.weapon_registry = {}
        self.requisition = 0
        self.stats = {}
        self.learned_personality = None
        self.intelligence_memory = {}
        self.known_planets = set()

class MockEngine:
    def __init__(self):
        self.factions = {}
        self.unit_registry = {}
        self.turn_counter = 1
        self.diplomacy = None
        self.tech_manager = None # Added for init compatibility

def verify_refit():
    print("=== Verifying AI Ship Refit ===")
    
    # 1. Setup
    engine = MockEngine()
    ai_mgr = AI_Manager(engine)
    
    f_name = "Zealot_Legions"
    faction = MockFaction(f_name)
    engine.factions[f_name] = faction
    
    # 2. Inject DNA and Arsenal
    universe_path = os.path.join(os.getcwd(), "universes", "eternal_crusade")
    dna_path = os.path.join(universe_path, "factions", "faction_dna.json")
    arsenal_path = os.path.join(universe_path, "factions", "weapon_registry.json")
    
    if not os.path.exists(dna_path) or not os.path.exists(arsenal_path):
        print("ERROR: DNA or Arsenal files not found. Run registry builder first.")
        return

    with open(arsenal_path, 'r') as f:
        full_arsenal = json.load(f)
    print(f"Available Factions in Registry: {list(full_arsenal.keys())[:5]}...") # Truncated
        
    # Flat structure: Filter by prefix
    faction.weapon_registry = {k: v for k, v in full_arsenal.items() if k.startswith(f_name)}
        
    print(f"Loaded {len(faction.weapon_registry)} weapons for {f_name}.")
    # Debug print
    if faction.weapon_registry:
        first_k = list(faction.weapon_registry.keys())[0]
        print(f"Sample: {first_k} -> {faction.weapon_registry[first_k]}")

    # 3. Modify Arsenal (Simulate Research)
    print("Simulating Research: Adding 'Infernal Cannon Mk II'...")
    # Find a heavy weapon (high volatility)
    base_id = next((k for k, v in faction.weapon_registry.items() if v.get("stats", {}).get("atom_volatility", 0) > 40), None)
    if not base_id:
        print("No suitable weapon found to upgrade.")
        # Fallback to first
        if faction.weapon_registry:
             base_id = list(faction.weapon_registry.keys())[0]
        else:
             return
             
    base_weapon = faction.weapon_registry[base_id]
    mk2_id = base_id + "_mk2"
    mk2_weapon = base_weapon.copy()
    mk2_weapon["id"] = mk2_id
    mk2_weapon["name"] = base_weapon["name"] + " Mk II"
    mk2_weapon["stats"] = base_weapon["stats"].copy()
    # FORCE Power for ShipDesignFactory (which expects 'power' key)
    mk2_weapon["stats"]["power"] = 9999 
    
    faction.weapon_registry[mk2_id] = mk2_weapon
    
    # 4. Trigger Refit
    print("Triggering update_ship_designs...")
    ai_mgr.update_ship_designs(f_name)
    
    print(f"Registry size after refit: {len(engine.unit_registry)}")
    
    # 5. Verify Results
    # Check if any ship in the registry now uses the Mk II weapon
    found = False
    print(f"Registry keys: {list(engine.unit_registry.keys())[:5]}...")
    for ship_id, ship in engine.unit_registry.items():
        if f_name.lower() in ship_id.lower():
            comps = [c["component"] for c in ship["components"]]
            if "cruiser" in ship_id.lower() or "dreadnought" in ship_id.lower():
                 print(f"Checking {ship_id}: {comps}")
                 
            if mk2_id in comps:
                print(f"SUCCESS: {ship_id} is equipped with {mk2_id}!")
                found = True
                break
                
    if not found:
        print("FAILED: New weapon not found on any ship.")
        
    print("=== Verification Complete ===")

if __name__ == "__main__":
    verify_refit()
