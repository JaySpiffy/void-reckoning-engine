
import json
import os

def migrate_dna():
    input_path = r"universes/eternal_crusade/factions/faction_dna.json"
    output_path = r"universes/eternal_crusade/factions/faction_traits.json"
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, 'r') as f:
        dna_data = json.load(f)
        
    trait_data = {}
    
    print(f"Migrating {len(dna_data)} factions...")
    
    for faction, atoms in dna_data.items():
        traits = []
        
        # Analyze Atoms
        mass = atoms.get("atom_mass", 0)
        volatility = atoms.get("atom_volatility", 0)
        cohesion = atoms.get("atom_cohesion", 0)
        frequency = atoms.get("atom_frequency", 0)
        aether = atoms.get("atom_aether", 0)
        focus = atoms.get("atom_focus", 0)
        
        print(f"  Processing {faction}...")
        
        # Physical / Defensive
        if mass > 18:
            if cohesion > 18:
                traits.append("resilient") # Mass + Cohesion
                traits.append("defensive")
            else:
                traits.append("strong")
        elif cohesion > 20:
             traits.append("defensive")
        
        # Combat / Speed
        if volatility > 18:
            traits.append("aggressive")
        
        if frequency > 20:
            traits.append("fast")
            
        # Special
        if aether > 10:
            if aether > 20:
                traits.append("ethereal")
            else:
                traits.append("psionic")
                
        # Tactical
        if focus > 15:
            traits.append("tactical")
            
        # Fallback
        if not traits:
             traits.append("thrifty") # Default to economic
             
        trait_data[faction] = {
            "name": faction.replace("_", " "),
            "id": faction,
            "traits": traits,
            "description": f"Imported from DNA. Notable atoms: Mass {int(mass)}, Vol {int(volatility)}."
        }
        
        print(f"    -> Assigned: {traits}")

    with open(output_path, 'w') as f:
        json.dump(trait_data, f, indent=2)
        
    print(f"\nMigration complete. Saved to {output_path}")

if __name__ == "__main__":
    migrate_dna()
