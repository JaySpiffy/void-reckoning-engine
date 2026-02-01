
import os
import json
import random
import sys
sys.path.append(os.getcwd())

from src.core.trait_system import TraitSystem
from src.generators.trait_based_generator import TraitBasedGenerator

def create_cosmic_ascendancy():
    universe_path = r"universes/cosmic_ascendancy"
    factions_path = os.path.join(universe_path, "factions")
    
    # Ensure dirs
    os.makedirs(factions_path, exist_ok=True)
    
    # Init Systems
    ts = TraitSystem()
    ts.initialize_subsystems()
    ts.load_traits_from_directory(r"data/traits")
    
    # Register Core Civics/Ethics (if not loaded from files yet, creating basic ones here for flavor)
    from src.core.civic_system import Civic
    ts.civics.register_civic(Civic("parliamentary_system", "Parliamentary System", "government", {"diplomacy": 0.2}))
    ts.civics.register_civic(Civic("fanatic_purifiers", "Fanatic Purifiers", "government", {"damage": 0.3}, conflicts=["pacifist"]))
    ts.civics.register_civic(Civic("technocracy", "Technocracy", "government", {"research": 0.2}))
    ts.civics.register_civic(Civic("warrior_culture", "Warrior Culture", "government", {"morale": 0.2}))
    
    gen = TraitBasedGenerator(ts)
    
    # Define Archetypes we want
    archetypes = [
        {
            "name": "United Systems Alliance",
            "flavor": "federation", 
            "fixed_traits": ["charismatic", "merchants"],
            "ethics": ["xenophile", "egalitarian"],
            "civics": ["parliamentary_system"]
        },
        {
            "name": "Covenant of the Void",
            "flavor": "theocracy",
            "fixed_traits": ["psionic", "strong"],
            "ethics": ["spiritualist", "authoritarian"],
            "civics": ["imperial_cult"] # Assume exists or ignored
        },
        {
            "name": "Terran Command",
            "flavor": "military",
            "fixed_traits": ["resilient", "adaptive", "industrialist"],
            "ethics": ["militarist", "materialist"],
            "civics": ["warrior_culture"]
        },
        {
            "name": "The Assimilators",
            "flavor": "hive",
            "fixed_traits": ["cybernetic", "aggressive"],
            "ethics": ["gestalt_consciousness"],
            "civics": ["fanatic_purifiers"]
        },
        {
            "name": "Ancient Custodians",
            "flavor": "fallen",
            "fixed_traits": ["genius", "long_lived", "technologist"], # using genius as proxy
            "ethics": ["materialist", "pacifist"],
            "civics": ["technocracy"]
        }
    ]
    
    generated_factions = {}
    
    print(f"Generating 'Cosmic Ascendancy' in {universe_path}...")
    
    for arch in archetypes:
        print(f"  Creating {arch['name']}...")
        
        # 1. Base Generation (to get biases)
        # We manually inject traits for specific flavor
        traits = arch["fixed_traits"]
        
        # 2. Fill gaps if needed
        # (Simplification: Just using what we defined)
        
        # 3. Construct Profile manually to ensure flavor matches user request
        profile = {
            "name": arch["name"],
            "id": arch["name"].replace(" ", "_"),
            "traits": traits,
            "ethics": arch["ethics"],
            "civics": arch["civics"],
            "description": f"A {arch['flavor']} faction. Traits: {', '.join(traits)}."
        }
        
        generated_factions[profile["id"]] = profile
        
    # Save
    traits_file = os.path.join(factions_path, "faction_traits.json")
    with open(traits_file, 'w') as f:
        json.dump(generated_factions, f, indent=2)
        
    # Create Layout (galaxy? config?)
    config = {
        "universe_name": "Cosmic Ascendancy",
        "description": "A diverse galaxy containing Federation, Theocratic, and Cybernetic factions.",
        "factions": list(generated_factions.keys())
    }
    
    with open(os.path.join(universe_path, "config.json"), 'w') as f:
        json.dump(config, f, indent=2)
        
    print("Universe generated successfully.")

if __name__ == "__main__":
    create_cosmic_ascendancy()
