import os
import json
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Ensure we can import utils if needed, though simple math works here.

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")
roster_path = os.path.join(UNITS_DIR, "zealot_legions_roster.json")

def rebalance_dna():
    if not os.path.exists(roster_path):
        print(f"Error: {roster_path} not found.")
        return

    with open(roster_path, 'r') as f:
        units = json.load(f)

    modified_count = 0
    
    for unit in units:
        dna = unit.get("elemental_dna", {})
        
        # Target allocation for Zealot feel: High Will (Faith), High Aether (Holy Magic/Warp)
        # Current generator might have spread it too thin.
        
        # We want roughly: Will ~35, Aether ~25 => 60% of budget.
        # Remaining 40% split among others.
        
        current_will = dna.get("atom_will", 0)
        current_aether = dna.get("atom_aether", 0)
        
        # If already high, skip
        if current_will > 30 and current_aether > 20:
            continue
            
        print(f"Rebalancing {unit['name']} DNA...")
        
        # New Target Values (with some variance so not identical)
        new_will = 35.0
        new_aether = 25.0
        
        remaining_budget = 100.0 - new_will - new_aether
        
        # Calculate current sum of OTHER atoms
        other_atoms = {k: v for k, v in dna.items() if k not in ["atom_will", "atom_aether"]}
        current_other_sum = sum(other_atoms.values())
        
        if current_other_sum == 0:
            # Edge case, distribute evenly
            val = remaining_budget / len(other_atoms) if other_atoms else 0
            for k in other_atoms:
                other_atoms[k] = val
        else:
            # Scale down others
            scale_factor = remaining_budget / current_other_sum
            for k in other_atoms:
                other_atoms[k] *= scale_factor
                
        # Reconstruct DNA
        new_dna = other_atoms
        new_dna["atom_will"] = new_will
        new_dna["atom_aether"] = new_aether
        
        # Update unit
        unit["elemental_dna"] = new_dna
        modified_count += 1

    if modified_count > 0:
        with open(roster_path, 'w') as f:
            json.dump(units, f, indent=2)
        print(f"Successfully rebalanced DNA for {modified_count} Zealot units.")
    else:
        print("No units needed rebalancing.")

if __name__ == "__main__":
    rebalance_dna()
