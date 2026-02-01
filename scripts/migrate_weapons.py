
import os
import json
import sys

# Constants matching src/core/elemental_signature.py
ATOM_MASS = "atom_mass"
ATOM_ENERGY = "atom_energy"
ATOM_COHESION = "atom_cohesion"
ATOM_VOLATILITY = "atom_volatility"
ATOM_STABILITY = "atom_stability"
ATOM_FOCUS = "atom_focus"
ATOM_FREQUENCY = "atom_frequency"
ATOM_AETHER = "atom_aether"
ATOM_WILL = "atom_will"

def synthesize_weapon_stats(elemental_dna):
    """
    Replication of src.core.weapon_synthesizer.synthesize_weapon_stats
    We duplicate it here to avoid import issues or dependency complexities during migration script run.
    """
    # 1. Calculate Raw Potency Scores
    raw_strength = (elemental_dna.get(ATOM_ENERGY, 0) * 0.8) + \
                   (elemental_dna.get(ATOM_MASS, 0) * 0.4) + \
                   (elemental_dna.get(ATOM_AETHER, 0) * 0.5)
                   
    raw_ap = (elemental_dna.get(ATOM_FOCUS, 0) * 0.6) + \
             (elemental_dna.get(ATOM_COHESION, 0) * 0.4) + \
             (elemental_dna.get(ATOM_FREQUENCY, 0) * 0.3)
             
    raw_damage = (elemental_dna.get(ATOM_VOLATILITY, 0) * 0.5) + \
                 (elemental_dna.get(ATOM_MASS, 0) * 0.3) + \
                 (elemental_dna.get(ATOM_WILL, 0) * 0.2)
                 
    raw_range = (elemental_dna.get(ATOM_STABILITY, 0) * 1.5) + \
                (elemental_dna.get(ATOM_ENERGY, 0) * 0.5) + \
                (elemental_dna.get(ATOM_FREQUENCY, 0) * 0.5)
                
    raw_attacks = (elemental_dna.get(ATOM_FREQUENCY, 0) * 0.4) + \
                  (elemental_dna.get(ATOM_ENERGY, 0) * 0.2) + \
                  (elemental_dna.get(ATOM_VOLATILITY, 0) * 0.2)

    # 2. Scale to Game Stats (Warhammer 40k style baseline)
    
    # Strength
    final_s = int(raw_strength * 0.25)
    if final_s < 1: final_s = 1
    
    # AP
    ap_val = int(raw_ap / 8.0)
    final_ap = -ap_val if ap_val > 0 else 0 
    
    # Damage
    final_d = int(raw_damage * 6.0) 
    if final_d < 20: final_d = 20
    
    # Range
    final_range = int(raw_range * 1.2)
    if final_range < 24: final_range = 24
    
    # Attacks
    final_a = max(1, int(raw_attacks / 4.0))
    
    return {
        "S": final_s,
        "AP": final_ap,
        "D": final_d,
        "Range": final_range,
        "Attacks": final_a
    }

def migrate_registry(filepath):
    print(f"Migrating {filepath}...")
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    count = 0
    
    for key, entry in data.items():
        # Get DNA stats
        # The structure in weapon_registry.json is usually:
        # "Key": { "stats": { "atom_...": val }, ... }
        # OR sometimes flattened? Let's assume standard registry format from inspection.
        
        dna = entry.get("stats", {})
        if not dna and "elemental_dna" in entry:
            dna = entry.get("elemental_dna")
            
        if not dna:
            # Skip if no DNA found
            # print(f"Skipping {key}: No atom stats found.")
            continue
            
        # Check if already migrated?
        # Actually, user wants us to ENFORCE manual stats. So we overwrite.
        
        manual_stats = synthesize_weapon_stats(dna)
        
        # Inject manual stats into the entry
        # We put them at the top level of the entry, or inside 'stats'?
        # The parser I wrote checks `elemental_dna` (the blueprint) for keys "S", "AP", etc.
        # Wait, get_weapon_dna_stats receives the BLUEPRINT.
        # In weapon_registry.json, the blueprint IS the value associated with the key.
        
        # So we update `entry` directly.
        # BUT `weapon_data.py` logic was:
        # if "S" in elemental_dna ...
        # and elemental_dna was passed as the blueprint.
        
        # So yes, we merge into `entry`.
        # However, `load_weapon_database` checks `entry["stats"]` for DNA.
        # But `get_weapon_stats` logic for manual priority...
        
        # Let's verify `load_weapon_dna_db` again.
        # It updates WEAPON_DNA_DB with the JSON content.
        # `get_weapon_stats` looks up `WEAPON_DNA_DB[key]`.
        # Then it does `dna_source = blueprint.get("elemental_signature", blueprint)`.
        # Then calls `get_weapon_dna_stats(..., dna_source)`.
        
        # So I should inject S/AP/D into `elemental_signature` if it exists, or the blueprint root if not?
        # In `weapon_registry.json`, I see:
        # "Zealot...": { "stats": { atoms... }, ... }
        
        # So I should inject into `"stats"`.
        
        entry["stats"].update(manual_stats)
        
        # Also inject into root to be safe/visible?
        # Dictionary merge
        for k, v in manual_stats.items():
            entry[k] = v
            
        count += 1

    if count > 0:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully migrated {count} weapons.")
    else:
        print("No weapons found to migrate.")

def main():
    target_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\factions\weapon_registry.json"
    if os.path.exists(target_path):
        migrate_registry(target_path)
    else:
        print("Target registry not found.")
        
    # Also check weapon_dna.json
    dna_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\factions\weapon_dna.json"
    if os.path.exists(dna_path):
        migrate_registry(dna_path)

if __name__ == "__main__":
    main()
