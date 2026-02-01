
import os
import sys
import json
sys.path.append(os.getcwd())

from src.core.trait_system import TraitSystem
from src.generators.trait_based_generator import TraitBasedGenerator

def test_generator():
    print("--- Verifying Trait Generator ---")
    
    # 1. Setup
    ts = TraitSystem()
    ts.initialize_subsystems()
    ts.load_traits_from_directory(r"data/traits")
    # Also register dummy civics to prevent crash
    from src.core.civic_system import Civic
    ts.civics.register_civic(Civic("dummy_civic", "Test Civic", "government", {}))
    from src.core.ethics_system import Ethics
    ts.ethics.register_ethics(Ethics("dummy_ethic", "Test Ethic", "militarist", {}))
    
    gen = TraitBasedGenerator(ts)
    
    # 2. Generate Faction
    print("\n[Step 1] Generating Random Faction...")
    faction = gen.generate_faction("Test Empire")
    print(f"  Name: {faction['name']}")
    print(f"  Traits: {faction['traits']}")
    print(f"  Desc: {faction['description']}")
    
    # 3. Generate Unit
    print("\n[Step 2] Generating Infantry Unit...")
    unit_profile = gen.generate_unit(faction["traits"], "infantry")
    stats = unit_profile["stats"]
    
    print(f"  Unit: {unit_profile['name']}")
    print(f"  Final Stats: HP={stats['hp']}, Armor={stats['armor']}, Dmg={stats['damage']}")
    
    # Basic Validation
    # Base Infantry: HP 10
    # If Strong (+20%), HP = 12. If Weak (-15%), HP = 8.
    
    if stats["hp"] != 10:
         print("  [PASS] Traits modified the base HP (10) ->", stats["hp"])
    else:
         print("  [WARN] HP matches base (10). Did we pick neutral traits or fail to apply?")
         
    # 4. Generate Titan
    print("\n[Step 3] Generating Titan...")
    titan = gen.generate_unit(faction["traits"], "titan")
    t_stats = titan["stats"]
    print(f"  Titan Stats: HP={t_stats['hp']}, Armor={t_stats['armor']}, Dmg={t_stats['damage']}")
    
    if t_stats["hp"] > 400:
        print("  [PASS] Titan generation scaled correctly.")
    else:
        print("  [FAIL] Titan stats seem too low.")

    # 5. Integration Test (Unit Class)
    print("\n[Step 4] Instantiating Real Unit Class...")
    from src.models.unit import Unit
    
    # The generator returns a dict with "stats" key being a dict representation of ExpandedStats
    # Unit.__init__ expects expanded_stats to be passed.
    
    u = Unit(
        name=unit_profile["name"],
        ma=50, md=50, hp=1, armor=0, damage=1, abilities={}, # Dummies, will be overridden
        expanded_stats=unit_profile["stats"]
    )
    
    print(f"  Created Unit: {u.name}")
    print(f"  Unit HP: {u.current_hp} (Base: {u.base_hp})")
    print(f"  Unit Armor: {u.base_armor}")
    
    if u.base_hp == stats["hp"]:
        print("  [PASS] Unit class accepted ExpandedStats correctly.")
    else:
        print(f"  [FAIL] Unit HP {u.base_hp} does not match generated stats {stats['hp']}")

if __name__ == "__main__":
    test_generator()
