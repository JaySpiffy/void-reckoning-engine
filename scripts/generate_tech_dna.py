
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
UNIVERSE_DIR = BASE_DIR / "universes" / "eternal_crusade"
TECH_DIR = UNIVERSE_DIR / "technology"
FACTIONS_DIR = UNIVERSE_DIR / "factions"

def load_json(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_tech_dna():
    print("Generating Technology DNA...")
    
    # Loads
    techs = load_json(TECH_DIR / "technology_registry.json")
    faction_dna = load_json(FACTIONS_DIR / "faction_dna.json")
    
    # Archetypes (Category based)
    archetypes = {
        "military": {"mass": 30, "energy": 30, "cohesion": 20, "will": 10, "stability": 10},
        "psychic": {"aether": 40, "will": 30, "volatility": 20, "focus": 10},
        "industry": {"mass": 20, "stability": 40, "information": 20, "cohesion": 20},
        "economy": {"energy": 20, "information": 40, "focus": 20, "frequency": 20},
        "default": {"stability": 20, "focus": 20, "mass": 20, "energy": 20, "information": 20}
    }

    # Blending Ratios
    # Military: 60% Faction / 40% Archetype
    # Psychic: 70% Faction / 30% Archetype
    # Industry: 50% Faction / 50% Archetype
    # Economy: 40% Faction / 60% Archetype
    
    ratios = {
        "military": 0.4,
        "psychic": 0.3,
        "industry": 0.5,
        "economy": 0.6
    }
    
    tech_dna_registry = {}
    
    for t_id, t_data in techs.items():
        faction = t_data.get('faction')
        cats = t_data.get('category', ['military'])
        cat = cats[0] if cats else 'military'
        
        # Get baselines
        f_dna = faction_dna.get(faction, {})
        a_dna = archetypes.get(cat, archetypes['default'])
        ratio = ratios.get(cat, 0.5)
        
        new_dna = {}
        all_keys = set(f_dna.keys()) | set(a_dna.keys())
        total = 0
        
        for k in all_keys:
            val_f = f_dna.get(k, 0)
            val_a = a_dna.get(k, 0)
            
            # Formula: (Archetype * Ratio) + (Faction * (1-Ratio))
            val = (val_a * ratio) + (val_f * (1.0 - ratio))
            new_dna[k] = val
            total += val
            
        # Tweaks
        if faction == "Zealot_Legions":
            new_dna['will'] = new_dna.get('will', 0) + 5
            new_dna['aether'] = new_dna.get('aether', 0) + 3
        elif faction == "Hive_Swarm" and cat == "psychic": # Bio-techs
             new_dna['mass'] = new_dna.get('mass', 0) + 4
             new_dna['frequency'] = new_dna.get('frequency', 0) + 4
        elif faction == "Cyber_Synod":
             new_dna['information'] = new_dna.get('information', 0) + 6
             new_dna['stability'] = new_dna.get('stability', 0) + 4
        elif faction == "Rift_Daemons" and cat == "psychic":
             new_dna['aether'] = new_dna.get('aether', 0) + 8
             new_dna['volatility'] = new_dna.get('volatility', 0) + 5
             
        # Normalize
        final_total = sum(new_dna.values())
        if final_total > 0:
            for k in new_dna:
                new_dna[k] = round((new_dna[k] / final_total) * 100, 2)
                
        tech_dna_registry[t_id] = new_dna
        
    save_json(TECH_DIR / "tech_dna.json", tech_dna_registry)
    print(f"Generated DNA for {len(tech_dna_registry)} technologies.")

if __name__ == "__main__":
    generate_tech_dna()
