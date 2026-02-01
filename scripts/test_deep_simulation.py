
import os
import sys
import json
sys.path.append(os.getcwd())

from src.core.trait_system import TraitSystem
from src.generators.trait_based_generator import TraitBasedGenerator

def test_deep_sim():
    print("--- Verifying Deep Simulation (Stellaris/Total War) ---")
    
    # 1. Setup
    ts = TraitSystem()
    ts.initialize_subsystems()
    ts.load_traits_from_directory(r"data/traits")
    
    # Init generator (auto-loads deep data)
    gen = TraitBasedGenerator(ts)
    
    if not gen.hulls: 
        print("[FAIL] No hulls loaded. Check data/ships/hulls.json")
        return
        
    print(f"  Loaded {len(gen.hulls)} Hulls and {len(gen.ground_classes)} Ground Classes.")
    
    # 2. Generate Ship (Corvette)
    print("\n[Test 1] Generating Corvette...")
    dummy_traits = ["industrialist", "strong"] # +Production, +HP?
    ship = gen.generate_unit(dummy_traits, "corvette")
    
    if ship["type"] == "ship":
        print(f"  [PASS] Generated Ship: {ship['name']}")
        print(f"  Components: {json.dumps(ship['components'], indent=2)}")
        print(f"  Stats: {ship['stats']}")
        if "laser_s_1" in str(ship['components']):
            print("  [PASS] Ship has weapons fitted.")
    else:
        print(f"  [FAIL] Expected ship type, got {ship.get('type')}")

    # 3. Generate Regiment (Line Infantry)
    print("\n[Test 2] Generating Line Infantry...")
    regiment = gen.generate_unit(["aggressive", "weak"], "line_infantry")
    
    if regiment["type"] == "regiment":
         print(f"  [PASS] Generated Regiment: {regiment['name']}")
         print(f"  Stats: {regiment['stats']}")
         # Aggressive (+20% Dmg usually) -> Check Damage? 
         # Note: Core traits modify 'damage', but regiment has 'melee_attack' / 'weapon_strength'.
         # If 'aggressive' trait only targets "damage", it might NOT affect "melee_attack" unless mapped.
         # This highlights a data sync need.
    else:
         print(f"  [FAIL] Expected regiment type, got {regiment.get('type')}")

    # 4. Generate 'Cavalry' (User Request Check)
    print("\n[Test 3] Generating 'Cavalry' (Legacy/Fallback)...")
    cav = gen.generate_unit([], "cavalry")
    print(f"  Result Type: {cav['type']}")
    if cav['type'] == 'legacy':
        print("  [INFO] 'Cavalry' used legacy fallback (acceptable until new class added).")

if __name__ == "__main__":
    test_deep_sim()
