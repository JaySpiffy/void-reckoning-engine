
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
UNIVERSE_DIR = BASE_DIR / "universes" / "eternal_crusade"
INFRA_DIR = UNIVERSE_DIR / "infrastructure"
FACTIONS_DIR = UNIVERSE_DIR / "factions"

def load_json(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_building_dna():
    print("Generating Building DNA...")
    
    # 1. Load Data
    buildings = load_json(INFRA_DIR / "building_registry.json")
    faction_dna = load_json(FACTIONS_DIR / "faction_dna.json")
    
    # 2. Define DNA Archetypes
    archetypes = {
        "military": {"energy": 40, "information": 25, "focus": 12, "mass": 8, "cohesion": 5, "will": 5, "aether": 3, "stability": 2, "volatility": 0, "frequency": 0},
        "defensive": {"mass": 37, "cohesion": 32, "stability": 16, "energy": 5, "will": 5, "information": 5, "focus": 0, "aether": 0, "volatility": 0, "frequency": 0},
        "research": {"information": 35, "focus": 25, "stability": 15, "energy": 10, "will": 5, "aether": 5, "mass": 5, "cohesion": 0, "volatility": 0, "frequency": 0},
        "economic": {"stability": 30, "energy": 20, "mass": 15, "information": 15, "cohesion": 10, "focus": 5, "will": 5, "aether": 0, "volatility": 0, "frequency": 0},
        # Map specialized logic to closest archetype or mix
        "psyker": {"aether": 40, "will": 26, "volatility": 11, "focus": 10, "energy": 5, "information": 5, "mass": 3, "stability": 0, "cohesion": 0, "frequency": 0},
        "special": {"energy": 20, "will": 20, "mass": 20, "information": 20, "stability": 20, "aether":0, "cohesion":0, "focus":0, "volatility":0, "frequency":0} # Balanced base
    }

    building_dna_registry = {}

    for b_id, b_data in buildings.items():
        faction = b_data.get('faction')
        name = b_data.get('name', '')
        desc = str(b_data.get('effects', '')) + str(b_data.get('description', ''))
        
        # Determine archetype
        atype_key = "special"
        
        # Keywords
        name_lower = name.lower()
        if any(x in name_lower for x in ["barracks", "factory", "foundry", "shop", "assembly", "shrine", "pit", "dock", "shipyard", "training"]):
            atype_key = "military"
        elif any(x in name_lower for x in ["bunker", "wall", "shield", "defense", "bastion", "turret", "fortification"]):
            atype_key = "defensive"
        elif any(x in name_lower for x in ["lab", "research", "archive", "library", "scriptorium", "data", "synodic", "logic"]):
            atype_key = "research"
        elif any(x in name_lower for x in ["generator", "mining", "farm", "processor", "bank", "scavenge", "loot", "market", "trade"]):
            atype_key = "economic"
        elif any(x in name_lower for x in ["warp", "aether", "portal", "psyker", "daemon", "ritual", "altar"]):
            atype_key = "psyker"
            
        archetype_dna = archetypes.get(atype_key, archetypes['special'])
        f_dna = faction_dna.get(faction, {})
        
        # Blending Formula: (Archetype * 0.6) + (Faction * 0.4)
        new_dna = {}
        total = 0
        
        all_keys = set(archetype_dna.keys()) | set(f_dna.keys())
        
        for k in all_keys:
            val_a = archetype_dna.get(k, 0)
            val_f = f_dna.get(k, 0)
            
            val = (val_a * 0.6) + (val_f * 0.4)
            new_dna[k] = val
            total += val
            
        # Normalize to 100
        if total > 0:
            for k in new_dna:
                new_dna[k] = round((new_dna[k] / total) * 100, 2)
                
        # Faction Tweaks
        if faction == "Zealot_Legions":
            new_dna['will'] = new_dna.get('will', 0) + 5
            new_dna['aether'] = new_dna.get('aether', 0) + 3
        elif faction == "Hive_Swarm":
            new_dna['mass'] = new_dna.get('mass', 0) + 4
            new_dna['cohesion'] = new_dna.get('cohesion', 0) + 4
        elif faction == "Cyber_Synod":
            new_dna['information'] = new_dna.get('information', 0) + 5
            new_dna['stability'] = new_dna.get('stability', 0) + 3
        elif faction == "Void_Corsairs":
            new_dna['frequency'] = new_dna.get('frequency', 0) + 6
        elif faction == "Rift_Daemons":
            new_dna['aether'] = new_dna.get('aether', 0) + 6
            new_dna['volatility'] = new_dna.get('volatility', 0) + 4

        # Re-Normalize after tweaks
        total_final = sum(new_dna.values())
        if total_final > 0:
             for k in new_dna:
                new_dna[k] = round((new_dna[k] / total_final) * 100, 2)
                
        building_dna_registry[b_id] = new_dna
        
    save_json(INFRA_DIR / "building_dna.json", building_dna_registry)
    print(f"Generated DNA for {len(building_dna_registry)} buildings.")

if __name__ == "__main__":
    generate_building_dna()
