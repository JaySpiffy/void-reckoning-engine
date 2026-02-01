
import os
import sys
import json
sys.path.append(os.getcwd())

from src.core.trait_system import TraitSystem, Trait

def test_trait_system():
    print("--- Verifying Trait System ---")
    
    # 1. Initialize
    ts = TraitSystem()
    ts.load_traits_from_directory("data/traits")
    # ts.load_traits_from_file("data/traits/core_traits.json") # Old way
    
    print(f"  Loaded {len(ts.all_traits)} traits total.")
    
    # 2. Check Specific Traits (Verify Phase 2 Content)
    check_traits = ["giant", "berserker", "industrialist", "genius", "psionic"]
    for tid in check_traits:
        if ts.get_trait(tid):
            print(f"  [PASS] Found trait: {tid}")
        else:
            print(f"  [FAIL] Missing trait: {tid}")
    
    # Verify Load (for 'strong' trait, which should still be loaded if core_traits.json is in data/traits)
    strong = ts.get_trait("strong")
    if strong:
        print(f"  [PASS] Loaded trait 'strong': {strong.name} ({strong.category})")
    else:
        print("  [FAIL] Could not load 'strong' trait.")
        return

    # 3. Test Pool Logic
    phys_pool = ts.pools["physical"]
    print(f"Physical Pool Size: {len(phys_pool.traits)}")
    if "strong" in phys_pool.traits and "weak" in phys_pool.traits:
         print("  [PASS] Physical pool contains expected traits.")
    else:
         print("  [FAIL] Physical pool missing traits.")

    # 4. Test Calculation
    print("\n--- Testing Stat Modifiers ---")
    base_stats = {"hp": 100.0, "damage": 10.0, "armor": 0.0}
    traits = [ts.get_trait("strong"), ts.get_trait("resilient")] 
    # Strong: +20% HP, +10% Dmg
    # Resilient: +10% HP, +10 Flat Armor
    # Exp HP: 100 * (1 + 0.20 + 0.10) = 130
    # Exp Dmg: 10 * (1 + 0.10) = 11
    # Exp Armor: 0 + 10 = 10
    
    final_stats = ts.apply_traits_to_stats(base_stats, traits)
    print(f"Base: {base_stats}")
    print(f"Traits: Strong (+20% HP), Resilient (+10% HP, +10 Armor)")
    print(f"Final: {final_stats}")
    
    if final_stats["hp"] == 130 and final_stats["armor"] == 10:
        print("  [PASS] Stat calculation correct.")
    else:
        print("  [FAIL] Stat calculation incorrect!")
        print(f"Expected HP 130, Armor 10. Got HP {final_stats['hp']}, Armor {final_stats['armor']}")

if __name__ == "__main__":
    test_trait_system()
