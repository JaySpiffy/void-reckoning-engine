import os
import json
import sys
from pprint import pprint

# Setup path
sys.path.append(os.getcwd())

from src.utils.registry_builder import build_weapon_registry

def verify_arsenal():
    universe_path = os.path.join(os.getcwd(), "universes", "eternal_crusade")
    print(f"Build registry for: {universe_path}")
    
    # Run the builder
    build_weapon_registry(universe_path, verbose=True)
    
    # Load Result
    reg_path = os.path.join(universe_path, "factions", "weapon_registry.json")
    if not os.path.exists(reg_path):
        print("FAILED: Registry not found at", reg_path)
        sys.exit(1)
        
    with open(reg_path, 'r') as f:
        registry = json.load(f)
        
    print(f"\nTotal Weapons Generated: {len(registry)}")
    
    # Check Coverage
    factions_found = set()
    for wid, data in registry.items():
        if "_" in wid:
             faction = wid.split("_")[0]
             factions_found.add(faction)
             
    print(f"Factions with weapons: {len(factions_found)}")
    print(f"Factions: {sorted(list(factions_found))}")
    
    # Sample Output
    print("\n=== Sample Weapons ===")
    import random
    samples = random.sample(list(registry.values()), 5)
    for s in samples:
        print(f"\nName: {s['name']}")
        print(f"ID: {s['id']}")
        print(f"Stats: {s['stats']}")
        
    # Validation
    if len(registry) < 50:
         print("\nFAILED: Too few weapons generated.")
         sys.exit(1)
         
    print("\nSUCCESS: Arsenal Generation Verified.")

if __name__ == "__main__":
    verify_arsenal()
