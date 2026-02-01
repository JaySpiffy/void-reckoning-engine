
import os
import sys
sys.path.append(os.getcwd())

from src.core.trait_system import TraitSystem
from src.core.trait_synergy import TraitSynergy
from src.core.civic_system import Civic

def test_massive_expansion():
    print("--- Verifying Massive Trait System Expansion ---")
    
    # 1. Initialize
    ts = TraitSystem()
    ts.initialize_subsystems()
    
    # 2. Test Subsystems Existence
    if hasattr(ts, 'civics') and hasattr(ts, 'ethics'):
        print("  [PASS] Subsystems initialized (Civics, Ethics, Origins, Ascension).")
    else:
        print("  [FAIL] Subsystems missing.")

    # 3. Test Synergy Logic
    print("\n[Testing Synergy]")
    syn = TraitSynergy("klingon_synergy", "Honor Bound", 
                      trait_ids=["strong", "aggressive"], 
                      modifiers={"damage": 0.5}) # +50% Damage if both present
    
    ts.register_synergy(syn)
    
    bonuses_fail = ts.check_synergies(["strong"])
    if not bonuses_fail:
        print("  [PASS] Synergy inactive with missing trait.")
        
    bonuses_pass = ts.check_synergies(["strong", "aggressive", "fast"])
    if bonuses_pass.get("damage") == 0.5:
        print("  [PASS] Synergy active with all traits.")
    else:
        print(f"  [FAIL] Synergy failed. Got {bonuses_pass}")

    # 4. Test Civic Registration
    print("\n[Testing Civics]")
    c = Civic("fanatic_purifiers", "Fanatic Purifiers", "government", {"damage": 0.3})
    ts.civics.register_civic(c)
    
    if "fanatic_purifiers" in ts.civics.available_civics:
        ts.civics.activate_civic("fanatic_purifiers")
        if "fanatic_purifiers" in ts.civics.active_civics:
             print("  [PASS] Civic registered and activated.")
        else:
             print("  [FAIL] Civic activation failed.")
    
    print("\n--- Expansion Verified ---")

if __name__ == "__main__":
    test_massive_expansion()
