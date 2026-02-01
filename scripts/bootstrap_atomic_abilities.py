
import os
import re
import json

# Paths for the Atomic Universes
TARGET_DIRS = [
    r"universes/warhammer40k_atomic",
    r"universes/star_wars_atomic",
    r"universes/star_trek_atomic"
]

OUTPUT_REGISTRY = "universes/base/abilities/atomic_ability_registry.json"

# Abilities that have been manually tuned and should not be overwritten
CORE_ABILITIES = [
    "tractor_beam", "cloaking_device", "transporter", "borg_adaptation",
    "psychic_barrier", "ion_cannon", "feel_no_pain", "force_choke"
]

def harvest_abilities():
    """Scans all atomic markdown files for unique ability names."""
    unique_abilities = {}
    for dir_path in TARGET_DIRS:
        if not os.path.exists(dir_path): continue
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith(".md"): continue
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Support both standard Markdown and Star Trek JSON blocks
                parser_match = re.search(r"<!-- PARSER_DATA(.*?)-->", content, re.DOTALL)
                if not parser_match:
                     parser_match = re.search(r"## Parser Data.*?```json(.*?)```", content, re.DOTALL)
                
                if not parser_match: continue
                block = parser_match.group(1)
                
                # Scoped to abilities: section to avoid noise
                ab_section_match = re.search(r"abilities:\s*(.*?)(\n\s*\w+:|$)", block, re.DOTALL)
                if not ab_section_match: continue
                ab_section = ab_section_match.group(1)
                
                for line in ab_section.split('\n'):
                    line = line.strip()
                    if line.startswith("-"):
                        item = line.lstrip("- ").strip()
                        if item.startswith("name:"): item = item.replace("name:", "").strip()
                        
                        # Handle potential JSON array strings
                        if "[" in item:
                             json_matches = re.findall(r"['\"]([^'\"]+)['\"]", item)
                             for jm in json_matches: add_to_harvest(jm, unique_abilities)
                        else:
                            add_to_harvest(item, unique_abilities)
    return unique_abilities

def add_to_harvest(name, registry):
    name = name.strip(",'\" ")
    if not name or name.isdigit() or len(name) < 3: return
    # Exclude categories/tags
    if name.lower() in ["infantry", "vehicle", "monster", "tags", "core", "battleline", "keywords"]: return
    registry[name] = registry.get(name, 0) + 1

def generate_ability_profile(name):
    """Derives Elemental DNA and Effect Categories from Ability names."""
    dna = {
        "atom_mass": 0, "atom_energy": 0, "atom_cohesion": 0,
        "atom_stability": 0, "atom_volatility": 0, "atom_frequency": 0,
        "atom_will": 0, "atom_focus": 0, "atom_aether": 0, "atom_information": 0
    }
    n = name.lower()
    effect = "generic_combat_modifier"
    # Logic for Attack Buffs
    if any(k in n for k in ["aim", "attack", "damage", "strike", "hit", "lethal", "crit", "storm", "burst", "shuriken", "bolt", "precision"]):
        dna["atom_focus"] += 40; dna["atom_stability"] += 20; dna["atom_energy"] += 20
        effect = "attack_buff"
    
    # Logic for Defense / Resilience
    elif any(k in n for k in ["shield", "armor", "durab", "resil", "pain", "defend", "guard", "wall", "cohesion", "hard", "plate", "resilience"]):
        dna["atom_cohesion"] += 50; dna["atom_mass"] += 30
        effect = "defense_buff"
        
    # Logic for Mobility / Stealth
    elif any(k in n for k in ["speed", "swift", "move", "jump", "fly", "teleport", "cloak", "stealth", "frequency", "jet"]):
        dna["atom_frequency"] += 60; dna["atom_information"] += 20
        effect = "mobility_buff"
        
    # Logic for Warp / Psychic / Force
    elif any(k in n for k in ["psyk", "warp", "aether", "will", "mind", "fate", "force", "power", "guide", "sense", "precog", "rune"]):
        dna["atom_aether"] += 50; dna["atom_will"] += 30; dna["atom_focus"] += 20
        effect = "warp_interaction"

    total = sum(dna.values())
    if total == 0: total = 1.0; dna["atom_focus"] = 1.0
    for k in dna: dna[k] = round((dna[k] / total) * 100.0, 2)
    dna["atom_stability"] = round(dna["atom_stability"] + (100.0 - sum(dna.values())), 2)
    
    return dna, effect

def bootstrap():
    print("Refreshing Atomic Ability Registry (Cross-Universe)...")
    abilities = harvest_abilities()
    print(f"Harvested {len(abilities)} unique abilities from unit files.")
    
    # Load existing to preserve manual overrides
    registry = {}
    if os.path.exists(OUTPUT_REGISTRY):
        with open(OUTPUT_REGISTRY, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            for k in CORE_ABILITIES:
                if k in old_data: registry[k] = old_data[k]
            
    added_count = 0
    for ab_name in sorted(abilities.keys()):
        key = ab_name.lower().replace(" ", "_").replace("-", "_")
        if key not in registry:
            dna, effect = generate_ability_profile(ab_name)
            registry[key] = {
                "display_name": ab_name,
                "description": f"Atomic DNA profile for {ab_name}.",
                "elemental_dna": dna,
                "effect_type": effect
            }
            added_count += 1
            
    with open(OUTPUT_REGISTRY, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=4)
        
    print(f"Update complete. Registry now contains {len(registry)} atomic-encoded abilities.")

if __name__ == "__main__":
    bootstrap()
