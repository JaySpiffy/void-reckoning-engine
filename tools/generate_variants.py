import os
import json
import sys
import copy

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")

# Variant Archetypes define how stats morph
VARIANT_TYPES = {
    "Plasma": {
        "suffix": "Plasma",
        "desc_suffix": "armed with high-energy plasma weaponry.",
        "stats_mod": { "damage": 1.4, "cost": 1.2, "volatility": 15.0 }, # High Damage, Volatility
        "role_req": ["vehicle", "ship", "elite_infantry"]
    },
    "Melta": {
        "suffix": "Melta",
        "desc_suffix": "armed with short-range anti-armor thermal beams.",
        "stats_mod": { "damage": 1.3, "range_mod": 0.5, "cost": 1.1, "energy": 10.0 }, # Anti-Armor
        "role_req": ["infantry", "vehicle"]
    },
    "Missile": {
        "suffix": "Missile",
        "desc_suffix": "equipped with long-range missile pods.",
        "stats_mod": { "range_mod": 2.0, "damage": 0.9, "accuracy_mod": 0.8, "mass": 10.0 }, # Long Range
        "role_req": ["vehicle", "ship"]
    },
    "Assault": {
        "suffix": "Assault",
        "desc_suffix": "configured for close-quarters combat.",
        "stats_mod": { "range_mod": 0.2, "damage": 1.2, "speed": 1.2, "cohesion": 10.0 }, # Melee/Speed
        "role_req": ["infantry", "walker"]
    },
    "Shield": {
        "suffix": "Shield",
        "desc_suffix": "fitted with experimental shield generators.",
        "stats_mod": { "hp": 0.8, "armor": 0.5, "cost": 1.3, "shield": 50, "focus": 20.0 }, # Defensive
        "role_req": ["vehicle", "ship", "titan"]
    }
}

def generate_variants():
    files = [f for f in os.listdir(UNITS_DIR) if f.endswith(".json") and "variants" not in f]
    
    count = 0
    
    for filename in files:
        filepath = os.path.join(UNITS_DIR, filename)
        with open(filepath, 'r') as f:
            units = json.load(f)
            
        new_variants = []
        
        for unit in units:
            # Check if unit is suitable for variants
            # Skip heroes, they are unique
            if unit.get("unique") or unit.get("hero"):
                continue
            
            unit_type = unit.get("type", "unknown")
            keywords = str(unit.get("base_stats", {}).get("keywords", "")).lower()
            
            # Determine applicable variants
            for v_name, v_data in VARIANT_TYPES.items():
                suitable = False
                for req in v_data["role_req"]:
                    if req in keywords or req in unit_type:
                        suitable = True
                        break
                
                if suitable:
                    # Create Variant
                    variant = copy.deepcopy(unit)
                    variant["name"] = f"{unit['name']} ({v_data['suffix']})"
                    variant["blueprint_id"] = f"{unit['blueprint_id']}_{v_data['suffix'].lower()}"
                    variant["description"] = f"{unit.get('description', '')} {v_data['desc_suffix']}"
                    variant["variant"] = True
                    
                    # Morph Stats
                    stats = variant.get("base_stats", {})
                    mods = v_data["stats_mod"]
                    
                    if "damage" in mods: stats["damage"] = int(stats.get("damage", 10) * mods["damage"])
                    if "cost" in mods: stats["cost"] = int(stats.get("cost", 100) * mods["cost"])
                    if "hp" in mods: stats["hp"] = int(stats.get("hp", 100) * mods["hp"])
                    if "armor" in mods: stats["armor"] = int(stats.get("armor", 0) * mods["armor"])
                    if "speed" in mods: stats["speed"] = int(stats.get("speed", 10) * mods["speed"])
                    
                    variant["base_stats"] = stats
                    
                    # Morph DNA (Add atoms from mod)
                    dna = variant.get("elemental_dna", {})
                    for key, val in mods.items():
                        if key in ["volatility", "energy", "mass", "cohesion", "focus"]:
                            # Map key to atom name if needed, but generator uses these keys usually
                            # DNA keys are usually atom_mass etc.
                            atom_key = f"atom_{key}"
                            if atom_key not in dna: dna[atom_key] = 0.0
                            dna[atom_key] += val
                            
                    # Normalize DNA? Maybe not strictly necessary if engine handles overflow, 
                    # but good practice.
                    total = sum(dna.values())
                    if total > 0:
                        for k in dna:
                            dna[k] = (dna[k] / total) * 100.0
                            
                    variant["elemental_dna"] = dna
                    new_variants.append(variant)
                    count += 1
        
        # Save variants to a separate file or append?
        # Let's save to a specific variants file to keep original clean
        if new_variants:
            base_name = filename.replace(".json", "")
            variant_file = os.path.join(UNITS_DIR, f"{base_name}_variants.json")
            with open(variant_file, 'w') as f:
                json.dump(new_variants, f, indent=2)
            print(f"Generated {len(new_variants)} variants for {filename}")

    print(f"Total Variants Generated: {count}")

if __name__ == "__main__":
    generate_variants()
