import json
import random

# Base Units to derive from
base_units = {
    "zealot_legions_initiate": {
        "name": "Initiate",
        "type": "infantry",
        "cost": 100,
        "base_stats": {"hp": 12, "armor": 20, "damage": 5, "speed": 4},
        "elemental_dna": {"atom_will": 35.0, "atom_aether": 25.0, "atom_mass": 6.7, "atom_energy": 6.6, "atom_cohesion": 9.3}
    },
    "zealot_legions_cherubim": {
        "name": "Cherubim",
        "type": "ship",
        "cost": 150,
        "base_stats": {"hp": 60, "armor": 0, "damage": 11, "speed": 35},
        "elemental_dna": {"atom_will": 35.0, "atom_aether": 25.0, "atom_frequency": 8.4}
    },
    "zealot_legions_templar": {
        "name": "Templar",
        "type": "infantry",
        "cost": 300,
        "base_stats": {"hp": 30, "armor": 60, "damage": 16, "speed": 4},
        "elemental_dna": {"atom_will": 35.0, "atom_aether": 25.0, "atom_focus": 11.5}
    },
    "zealot_legions_chariot": {
        "name": "Chariot",
        "type": "vehicle",
        "cost": 500,
        "base_stats": {"hp": 96, "armor": 50, "damage": 22, "speed": 12},
        "elemental_dna": {"atom_will": 35.0, "atom_aether": 25.0, "atom_mass": 9.1, "atom_cohesion": 14.0}
    },
    "zealot_legions_penitent_engine": {
        "name": "Penitent Engine",
        "type": "vehicle",
        "cost": 900,
        "base_stats": {"hp": 216, "armor": 90, "damage": 49, "speed": 5},
        "elemental_dna": {"atom_will": 35.0, "atom_aether": 25.0, "atom_cohesion": 14.7}
    },
    "zealot_legions_sword_class": {
        "name": "Sword Class",
        "type": "ship",
        "cost": 2000,
        "base_stats": {"hp": 960, "armor": 50, "damage": 110, "speed": 15},
        "elemental_dna": {"atom_will": 35.0, "atom_aether": 25.0, "atom_mass": 10.4, "atom_cohesion": 10.6}
    }
}

new_variants = [
    # Tier 1
    {"base": "zealot_legions_initiate", "suffix": "Breacher", "role": "Melee", "cost_mod": 1.1, "dna_mod": {"atom_mass": 10, "atom_cohesion": 5}, "abilities": ["Ability_Psychic_Barrier"]},
    {"base": "zealot_legions_initiate", "suffix": "Marksman", "role": "Ranged", "cost_mod": 1.2, "dna_mod": {"atom_focus": 10, "atom_information": 5}, "abilities": ["Ability_Frag_Barrage"]},
    {"base": "zealot_legions_initiate", "suffix": "Acolyte", "role": "Hybrid", "cost_mod": 1.15, "dna_mod": {"atom_will": 10, "atom_aether": 5}, "abilities": ["Ability_Psychic_Barrier"]},
    {"base": "zealot_legions_cherubim", "suffix": "Interceptor", "role": "Anti-Air", "cost_mod": 1.1, "dna_mod": {"atom_energy": 10, "atom_frequency": 5}, "abilities": ["Ability_Plasma_Burst"]},
    {"base": "zealot_legions_cherubim", "suffix": "Bomber", "role": "Anti-Ground", "cost_mod": 1.25, "dna_mod": {"atom_mass": 10, "atom_volatility": 5}, "abilities": ["Ability_Melta_Beam"]},
    
    # Tier 2
    {"base": "zealot_legions_templar", "suffix": "Vanguard", "role": "Assault", "cost_mod": 1.15, "dna_mod": {"atom_volatility": 10, "atom_energy": 5}, "abilities": ["Ability_Melta_Beam"]},
    {"base": "zealot_legions_templar", "suffix": "Devastator", "role": "Fire Support", "cost_mod": 1.2, "dna_mod": {"atom_mass": 10, "atom_focus": 5}, "abilities": ["Ability_Frag_Barrage", "Ability_Kinetic_Strike"]},
    {"base": "zealot_legions_templar", "suffix": "Justicar", "role": "Elite", "cost_mod": 1.25, "dna_mod": {"atom_will": 10, "atom_cohesion": 5}, "abilities": ["Ability_Psychic_Barrier"]},
    {"base": "zealot_legions_chariot", "suffix": "Flamer", "role": "Anti-Infantry", "cost_mod": 1.1, "dna_mod": {"atom_volatility": 15}, "abilities": ["Ability_Frag_Barrage"]},
    {"base": "zealot_legions_chariot", "suffix": "Hunter", "role": "Anti-Tank", "cost_mod": 1.15, "dna_mod": {"atom_focus": 15}, "abilities": ["Ability_Melta_Beam"]},
    
    # Tier 2/3 Ships
    {"base": "zealot_legions_sword_class", "suffix": "Escort", "role": "Defensive", "cost_mod": 0.9, "dna_mod": {"atom_cohesion": 15}, "abilities": ["Ability_Kinetic_Strike"]}, # Lower cost valid within 20%
    {"base": "zealot_legions_sword_class", "suffix": "Raider", "role": "Fast Attack", "cost_mod": 1.1, "dna_mod": {"atom_energy": 10, "atom_volatility": 5}, "abilities": ["Ability_Melta_Beam"]},

    # Tier 3
    {"base": "zealot_legions_penitent_engine", "suffix": "Mortifier", "role": "Melee Blender", "cost_mod": 1.1, "dna_mod": {"atom_volatility": 15, "atom_mass": 5}, "abilities": ["Ability_Frag_Barrage"]},
    {"base": "zealot_legions_penitent_engine", "suffix": "Anchorite", "role": "Defensive", "cost_mod": 1.15, "dna_mod": {"atom_stability": 15, "atom_cohesion": 5}, "abilities": ["Ability_Psychic_Barrier", "Ability_Kinetic_Strike"]},
    
    # Extra T1/T2 to hit 15-20 count
    {"base": "zealot_legions_initiate", "suffix": "Scout", "role": "Light", "cost_mod": 0.9, "dna_mod": {"atom_frequency": 10, "atom_information": 10}, "abilities": ["Ability_Kinetic_Strike"]},
    {"base": "zealot_legions_chariot", "suffix": "Transport", "role": "Transport", "cost_mod": 0.95, "dna_mod": {"atom_mass": 5, "atom_cohesion": 5}, "abilities": ["Ability_Kinetic_Strike"]}
]

def normalize_dna(dna):
    total = sum(dna.values())
    if total == 0: return dna
    return {k: (v / total) * 100.0 for k, v in dna.items()}

generated = []

for var in new_variants:
    base_def = base_units[var["base"]]
    
    new_u = {}
    new_u["name"] = f"{base_def['name']} {var['suffix']}"
    new_u["blueprint_id"] = f"{var['base']}_{var['suffix'].lower().replace(' ', '_')}"
    new_u["type"] = base_def["type"]
    new_u["faction"] = "Zealot_Legions"
    new_u["cost"] = int(base_def["cost"] * var["cost_mod"])
    
    # Stats
    stats = base_def["base_stats"].copy()
    stats["cost"] = new_u["cost"]
    
    # Mod stats slightly based on role logic (simplified)
    if "Melee" in var["role"]: stats["damage"] = int(stats["damage"] * 1.1)
    if "Tank" in var["role"] or "Defensive" in var["role"]: stats["hp"] = int(stats["hp"] * 1.1)
    if "Ranged" in var["role"]: stats["damage"] = int(stats["damage"] * 1.05)
    
    new_u["base_stats"] = stats
    
    # DNA
    dna = base_def.get("elemental_dna", {}).copy()
    # Fill missing defaults
    for k in ["atom_mass", "atom_energy", "atom_cohesion", "atom_volatility", "atom_stability", 
              "atom_focus", "atom_frequency", "atom_information", "atom_will", "atom_aether"]:
        if k not in dna: dna[k] = 0.0
        
    # Apply mods
    for k, v in var["dna_mod"].items():
        dna[k] += v
        if dna[k] < 0: dna[k] = 0
        
    new_u["elemental_dna"] = normalize_dna(dna)
    new_u["source_universe"] = "eternal_crusade"
    new_u["description"] = f"Variant of {base_def['name']} specialized for {var['role']}."
    new_u["traits"] = ["Trait_Fearless"] # Inherit basic trait
    new_u["abilities"] = var["abilities"]
    
    generated.append(new_u)

# Output / Merge
import os
target_file = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units\zealot_legions_roster.json"

if os.path.exists(target_file):
    with open(target_file, 'r', encoding='utf-8') as f:
        existing = json.load(f)
else:
    existing = []

# Deduplicate by blueprint_id just in case
existing_ids = {u["blueprint_id"] for u in existing}
for new_u in generated:
    if new_u["blueprint_id"] not in existing_ids:
        existing.append(new_u)

with open(target_file, 'w', encoding='utf-8') as f:
    json.dump(existing, f, indent=2)

print(f"Successfully added {len(generated)} variants to {target_file}")
