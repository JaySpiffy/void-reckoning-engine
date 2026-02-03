import sys
import os
import shutil

# Ensure we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.combat.ability_manager import AbilityManager
from src.core.universe_data import UniverseDataManager
from src.models.unit import Unit

def test_unified_abilities():
    print(">>> Verifying Unified Ability System...")
    
    # 1. Initialize Registry
    udm = UniverseDataManager.get_instance()
    # Mocking active universe to force load if needed, but core should load regardless
    # udm.load_universe_data("void_reckoning") 
    
    db = udm.get_ability_database()
    
    # 2. Assert Core Abilities Present
    required_abilities = ["take_cover", "power_to_shields", "micro_warp_jump", "fix_bayonets"]
    missing = [a for a in required_abilities if a not in db]
    
    if missing:
        print(f"FAIL: Missing required abilities in registry: {missing}")
        print(f"Registry keys: {list(db.keys())}")
        return False
        
    print(f"PASS: Registry contains {len(db)} abilities.")
    
    # 3. Test Ground Ability: Take Cover
    print("\n--- Testing Ground Ability: Take Cover ---")
    infantry = Unit(name="Guardsman", faction="Empire", unit_class="Regiment", hp=100)
    
    # Ensure apply_temporary_modifiers exists (Mocking if Unit doesn't have it fully impl in test env)
    if not hasattr(infantry, 'apply_temporary_modifiers'):
        def apply_mods(mods):
            print(f"   [Unit] Applying modifiers: {mods}")
            setattr(infantry, 'temp_mods', mods)
        infantry.apply_temporary_modifiers = apply_mods
        
    am = AbilityManager(db)
    
    # Execute Take Cover
    # Target is self for buff
    ctx = {"faction": "Empire"}
    result = am.execute_ability(infantry, infantry, "take_cover", ctx)
    
    if result["success"]:
        print(f"PASS: Ability execution success: {result.get('description')}")
        # Verify effect
        # result['description'] should verify 'Applied buffs'
        if "Applied buffs" in result["description"]:
            print("PASS: Buffs applied verified.")
        else:
            print("WARN: Description did not explicitly state buffs applied.")
    else:
        print(f"FAIL: Ability execution failed: {result}")
        return False
        
    # 4. Test Space Ability: Power to Shields
    print("\n--- Testing Space Ability: Power to Shields ---")
    ship = Unit(name="Cruiser", faction="Empire", unit_class="Ship", hp=1000)
    # Mock apply
    ship.apply_temporary_modifiers = lambda mods: setattr(ship, 'temp_mods', mods)
    
    result = am.execute_ability(ship, ship, "power_to_shields", ctx)
    if result["success"]:
         print(f"PASS: Space ability execution success: {result.get('description')}")
    else:
         print(f"FAIL: Space ability execution failed: {result}")
         return False

    # 5. Verify NO Elemental DNA dependencies
    print("\n--- Verifying Removal of Atomic DNA ---")
    try:
        # Try to access a value that would trigger DNA check if it existed
        # Actually we just want to ensure no errors were thrown above due to missing DNA
        if hasattr(ship, 'elemental_dna'):
            print("FAIL: Unit still has elemental_dna attribute!")
            return False
        else:
            print("PASS: Unit does not have elemental_dna.")
            
    except Exception as e:
         print(f"FAIL: Exception checking DNA: {e}")
         return False
         
    print("\n>>> ALL TESTS PASSED <<<")
    return True

if __name__ == "__main__":
    success = test_unified_abilities()
    sys.exit(0 if success else 1)
