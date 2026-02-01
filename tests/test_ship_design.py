import os
import json
import sys

sys.path.append(os.getcwd())

from src.utils.registry_builder import generate_procedural_roster, build_weapon_registry

def verify_design():
    universe_path = os.path.join(os.getcwd(), "universes", "void_reckoning")
    print(f"Generating ships for: {universe_path}")
    
    # Ensure Dependencies
    print("Building Dependencies...")
    build_weapon_registry(universe_path, verbose=False) # Ensure weapons exist
    
    # Run Generator
    generate_procedural_roster(universe_path, verbose=True)
    
    # Load Output
    roster_path = os.path.join(universe_path, "units", "procedural_roster.json")
    if not os.path.exists(roster_path):
        print("FAILED: Roster not found.")
        sys.exit(1)
        
    with open(roster_path, 'r') as f:
        roster = json.load(f)
        
    print(f"\nTotal Procedural Ships: {len(roster)}")
    
    # Analyze Zealot Legions
    zealot_ships = [s for s in roster.values() if s["faction"] == "Zealot_Legions"]
    print(f"Zealot Ships: {len(zealot_ships)}")
    
    if len(zealot_ships) < 10:
        print("FAILED: Too few ships generated.")
        sys.exit(1)
        
    # Sample Inspection
    print("\n=== Sample Designs ===")
    import random
    samples = random.sample(zealot_ships, 3)
    for s in samples:
        print(f"\nName: {s['name']}")
        print(f"Class: {s['type']}")
        print(f"Cost: {s['cost']}")
        
        comps = [c['component'] for c in s['components']]
        unique_comps = set(comps)
        print(f"Components ({len(comps)} total, {len(unique_comps)} unique):")
        for c in comps:
            print(f"  - {c}")
            
    # Logic Verification
    cruisers = [s for s in zealot_ships if s["type"] == "cruiser"]
    if cruisers:
        c = cruisers[0] 
        weapon_types = set([x["component"] for x in c["components"] if "weapon" in x["slot"]])
        if len(weapon_types) < 2:
            print(f"\nWARNING: Cruiser {c['name']} has monotonous weapons: {weapon_types}")
        else:
            print(f"\nSUCCESS: Cruiser {c['name']} has mixed arsenal: {weapon_types}")
            
    print("\nSUCCESS: Ship Design System Verified.")

if __name__ == "__main__":
    verify_design()
