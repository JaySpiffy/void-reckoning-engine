from src.factories.tech_factory import ProceduralTechGenerator
from src.managers.tech_manager import TechManager
import copy
import json

def test_tech_evolution():
    print("--- Testing Procedural Tech Evolution ---")
    
    # Mock Physics Profile
    class PhysicsProfile:
        def __init__(self, aether=1.0, mass=1.0):
            self.atom_multipliers = {"atom_aether": aether, "atom_mass": mass}
            
    # Mock Tech Tree
    base_tree = {
        "techs": {
            "Psychic_Awakening": 1000,
            "Plasteel_Armor": 1000,
            "Warp_Drive": 2000
        },
        "units": {
            "Battle_Psyker": "Psychic_Awakening",
            "Super_Tank": "Plasteel_Armor",
            "Void_Ship": "Warp_Drive"
        }
    }
    
    # 1. Test Universe A
    print("\n[Universe A]")
    gen_a = ProceduralTechGenerator("universe_a")
    res_a = gen_a.evolve_tree(copy.deepcopy(base_tree))
    
    print(f"Psychic Cost (Base 1000): {res_a['techs']['Psychic_Awakening']}")
    print(f"Armor Cost (Base 1000): {res_a['techs']['Plasteel_Armor']}")
    
    # 2. Test Universe B
    print("\n[Universe B]")
    gen_b = ProceduralTechGenerator("universe_b")
    res_b = gen_b.evolve_tree(copy.deepcopy(base_tree))
    
    print(f"Psychic Cost (Base 1000): {res_b['techs']['Psychic_Awakening']}")
    print(f"Armor Cost (Base 1000): {res_b['techs']['Plasteel_Armor']}")
    
    # 3. Verify Determinism
    print("\n[Verification]")
    gen_a_2 = ProceduralTechGenerator("universe_a")
    res_a_2 = gen_a_2.evolve_tree(copy.deepcopy(base_tree))
    
    if res_a["techs"] == res_a_2["techs"]:
        print("SUCCESS: Evolution is deterministic.")
    else:
        print("FAILURE: Non-deterministic results.")

if __name__ == "__main__":
    test_tech_evolution()
