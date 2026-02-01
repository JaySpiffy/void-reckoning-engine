
import os
import json
import sys
sys.path.append(os.getcwd())

from src.core.trait_system import TraitSystem
from src.generators.trait_based_generator import TraitBasedGenerator

def generate_assets():
    universe_path = r"universes/cosmic_ascendancy"
    factions_file = os.path.join(universe_path, "factions", "faction_traits.json")
    units_path = os.path.join(universe_path, "units")
    
    os.makedirs(units_path, exist_ok=True)
    
    # Init Systems
    ts = TraitSystem()
    ts.initialize_subsystems()
    ts.load_traits_from_directory(r"data/traits")
    
    gen = TraitBasedGenerator(ts)
    
    # Load Factions
    if not os.path.exists(factions_file):
        print("Factions file not found!")
        return
        
    with open(factions_file, 'r') as f:
        factions = json.load(f)
        
    print(f"Generating assets for {len(factions)} factions...")
    
    # Define Roster Templates
    roster_templates = [
        "infantry", "tank", "titan", 
        "corvette", "destroyer", "cruiser", "battleship"
    ]
    
    # Patch Generator to support ships if not already (it only had infantry/tank/titan in previous view)
    # Monkey-patching for now or relying on defaults?
    # Let's add ships to the generator's template logic dynamically or just subclass/extend here?
    # I'll extend the generator instance's method for this script.
    
    original_get_template = gen._get_base_template
    
    def extended_get_template(role):
        if role == "corvette":
            return {"hp": 100, "damage": 10, "armor": 2, "speed": 20, "cost": 500}
        elif role == "destroyer":
            return {"hp": 200, "damage": 25, "armor": 5, "speed": 15, "cost": 1000}
        elif role == "cruiser":
            return {"hp": 500, "damage": 60, "armor": 15, "speed": 10, "cost": 2500}
        elif role == "battleship":
            return {"hp": 1200, "damage": 150, "armor": 40, "speed": 5, "cost": 5000}
        return original_get_template(role)
        
    gen._get_base_template = extended_get_template
    
    for f_id, f_data in factions.items():
        print(f"  Processing {f_data['name']}...")
        traits = f_data["traits"]
        
        faction_roster = {}
        
        for role in roster_templates:
            # Generate Unit
            unit_data = gen.generate_unit(traits, role)
            
            # Flavor Name (e.g. "Terran Infantry" or "Covenant Cruiser")
            # Simple prefixing for now
            flavor_name = f"{f_data['name'].split()[0]} {unit_data['name']}"
            unit_data["name"] = flavor_name
            
            # Save to roster dict
            faction_roster[role] = unit_data
            
        # Save Roster File
        # Format: universes/cosmic_ascendancy/units/{faction_id}_roster.json
        roster_file = os.path.join(units_path, f"{f_id}_roster.json")
        with open(roster_file, 'w') as f:
            json.dump(faction_roster, f, indent=2)
            
    print("Asset generation complete.")

if __name__ == "__main__":
    generate_assets()
