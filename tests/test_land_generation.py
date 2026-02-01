import os
import json
import sys

# Setup Path
sys.path.append(os.getcwd())

from src.utils.registry_builder import generate_land_roster
from src.core.config import UNIVERSE_ROOT

def verify_land_roster():
    print("=== Verifying Land Unit Generation ===")
    
    universe_path = os.path.join(UNIVERSE_ROOT, "eternal_crusade")
    
    # 1. Run Generation
    generate_land_roster(universe_path, verbose=True)
    
    # 2. Check Output
    out_path = os.path.join(universe_path, "units", "procedural_land_roster.json")
    if not os.path.exists(out_path):
        print("FAILED: Output file not created.")
        return
        
    with open(out_path, 'r', encoding='utf-8') as f:
        roster = json.load(f)
        
    print(f"Total Designs: {len(roster)}")
    
    if len(roster) < 50:
        print("WARNING: Roster seems small. Expected ~70-100 variants.")
        
    # 3. Spot Checks
    factions = set(u["faction"] for u in roster.values())
    print(f"Factions with armies: {len(factions)}")
    
    # Check for specific types
    tanks = [u for u in roster.values() if "Tank" in u["name"]]
    infantry = [u for u in roster.values() if "Infantry" in u["category"]]
    walkers = [u for u in roster.values() if "Walker" in u["category"]]
    
    print(f"Tanks: {len(tanks)}")
    print(f"Infantry Squads: {len(infantry)}")
    print(f"Walkers: {len(walkers)}")
    
    if not tanks or not infantry:
        print("FAILED: Missing major unit categories.")
        return
        
    # 4. Detail Inspection (Composition)
    print("\n--- Detail Inspection ---")
    sample_inf = infantry[0]
    print(f"Sample Infantry: {sample_inf['name']}")
    print(f"  Squad Comp: {sample_inf.get('composition')}")
    print(f"  Stats: {sample_inf['base_stats']}")
    
    sample_tank = tanks[0]
    print(f"Sample Tank: {sample_tank['name']}")
    print(f"  Components: {[c['component'] for c in sample_tank['components']]}")
    print(f"  Hard Attack: {sample_tank['base_stats'].get('hard_attack')}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_land_roster()
