import os
import json
import sys
import random

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.dna_generator import generate_dna_from_stats, normalize_dna

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")

FACTIONS = {
    "Zealot_Legions": "crusader",
    "Ascended_Order": "psyker",
    "Iron_Vanguard": "industrial",
    "Hive_Swarm": "bio",
    "Cyber_Synod": "cyber",
    "Void_Corsairs": "speed",
    "Solar_Hegemony": "tech",
    "Rift_Daemons": "aether",
    "Scavenger_Clans": "scavenger",
    "Ancient_Guardians": "elite"
}

HERO_TEMPLATES = {
    "Field_Commander": { "role": "commander", "tier": 4, "hp": 100, "armor": 80, "damage": 50, "cost": 2000, "keywords": "hero infantry character" },
    "Legendary_Hero": { "role": "hero", "tier": 5, "hp": 300, "armor": 120, "damage": 150, "cost": 5000, "keywords": "hero infantry unique" },
    "Super_Heavy_Walker": { "role": "titan", "tier": 5, "hp": 5000, "armor": 400, "damage": 800, "cost": 15000, "keywords": "titan vehicle massive" },
    "Flagship": { "role": "capital", "tier": 5, "hp": 40000, "armor": 800, "damage": 3000, "cost": 60000, "keywords": "ship flagship unique" }
}

NAMING = {
    "Zealot_Legions": { "Field_Commander": "Canoness", "Legendary_Hero": "High Lord Solar", "Super_Heavy_Walker": "God-Engine", "Flagship": "Eternal Light" },
    "Ascended_Order": { "Field_Commander": "Warp seer", "Legendary_Hero": "Grand Archon", "Super_Heavy_Walker": "Psi-Titan", "Flagship": "Eye of Terror" },
    "Iron_Vanguard": { "Field_Commander": "Marshall", "Legendary_Hero": "Lord General", "Super_Heavy_Walker": "Siege Colossus", "Flagship": "Iron Duke" },
    "Hive_Swarm": { "Field_Commander": "Broodlord", "Legendary_Hero": "Swarm Lord", "Super_Heavy_Walker": "Bio-Titan", "Flagship": "Leviathan" },
    "Cyber_Synod": { "Field_Commander": "Overlord", "Legendary_Hero": "Silent King", "Super_Heavy_Walker": "Doomsday Monolith", "Flagship": "Tomb World" },
    "Void_Corsairs": { "Field_Commander": "Archon", "Legendary_Hero": "Pirate King", "Super_Heavy_Walker": "Void Wraith", "Flagship": "Shadow Strike" },
    "Solar_Hegemony": { "Field_Commander": "Commander", "Legendary_Hero": "Ethereal Leader", "Super_Heavy_Walker": "Supremacy Suit", "Flagship": "Greater Good" },
    "Rift_Daemons": { "Field_Commander": "Daemon Prince", "Legendary_Hero": "Greater God-Shard", "Super_Heavy_Walker": "Lord of Skulls", "Flagship": "Space Hulk" },
    "Scavenger_Clans": { "Field_Commander": "Warboss", "Legendary_Hero": "The Beast", "Super_Heavy_Walker": "Gargant", "Flagship": "Scrap Moon" },
    "Ancient_Guardians": { "Field_Commander": "Autarch", "Legendary_Hero": "Phoenix Lord", "Super_Heavy_Walker": "Phantom Titan", "Flagship": "Craftworld" }
}

def generate_heroes():
    if not os.path.exists(UNITS_DIR): os.makedirs(UNITS_DIR)

    for faction, archetype in FACTIONS.items():
        print(f"Generating Heroes for {faction}...")
        
        roster_file = os.path.join(UNITS_DIR, f"{faction.lower()}_heroes.json")
        hero_data = []

        for key, tmpl in HERO_TEMPLATES.items():
            name = NAMING[faction].get(key, f"{faction} {key}")
            
            # Morph Stats
            stats = tmpl.copy()
            # Spiky Stat Logic
            
            if archetype == "crusader": 
                stats["hp"] = int(stats["hp"] * 1.5) 
            elif archetype == "psyker":
                stats["damage"] = int(stats["damage"] * 2.0) 
                stats["armor"] = int(stats["armor"] * 0.8)
            elif archetype == "bio":
                stats["hp"] = int(stats["hp"] * 2.0) 
                stats["armor"] = int(stats["armor"] * 0.5)
            elif archetype == "speed":
                stats["damage"] = int(stats["damage"] * 1.5)
                stats["hp"] = int(stats["hp"] * 0.7)
            
            # Prepare for DNA
            # Correction: use tmpl['keywords'] not template['keywords']
            dna_stats = {
                "hp": stats["hp"], "armor": stats["armor"], "damage": stats["damage"],
                "speed": 10, "cost": stats["cost"], "name": name,
                "keywords": f"{tmpl['keywords']} {archetype}".lower(),
                "role": tmpl["role"]
            }
            
            # Generate Standard DNA
            dna = generate_dna_from_stats(dna_stats)
            
            # Apply "Hero Spike"
            sorted_atoms = sorted(dna.items(), key=lambda x: x[1], reverse=True)
            top_atom = sorted_atoms[0][0]
            sec_atom = sorted_atoms[1][0]
            
            # Redistribute 20 points from bottom atoms to top atoms
            dna[top_atom] += 15.0
            dna[sec_atom] += 5.0
            dna = normalize_dna(dna)
            
            unit_entry = {
                "name": name,
                "blueprint_id": f"{faction.lower()}_{name.lower().replace(' ', '_')}",
                "type": "hero" if "ship" not in tmpl["keywords"] else "ship",
                "faction": faction,
                "tier": tmpl["tier"],
                "cost": stats["cost"],
                "base_stats": stats,
                "elemental_dna": dna,
                "source_universe": "eternal_crusade",
                "description": f"Legendary {key} of the {faction}",
                "hero": True,
                "unique": True
            }
            hero_data.append(unit_entry)
            
        with open(roster_file, 'w') as f:
            json.dump(hero_data, f, indent=2)

if __name__ == "__main__":
    generate_heroes()
