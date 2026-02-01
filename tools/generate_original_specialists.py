import os
import json
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.dna_generator import generate_dna_from_stats

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

# Specialist Templates
# These fill Rock-Paper-Scissors gaps
SPECIALIST_TEMPLATES = {
    "Anti_Air_Tank": { 
        "role": "anti_air", "tier": 2, "hp": 120, "armor": 40, "damage": 30, "cost": 600, 
        "keywords": "vehicle specialist aa", "desc": "Specialized anti-aircraft vehicle."
    },
    "Tank_Hunter": { 
        "role": "anti_tank", "tier": 3, "hp": 100, "armor": 30, "damage": 120, "cost": 800, 
        "keywords": "infantry specialist heavy_weapon", "desc": "Heavy infantry armed with anti-armor weapons."
    },
    "Infiltrator": { 
        "role": "stealth", "tier": 2, "hp": 60, "armor": 10, "damage": 50, "cost": 700, 
        "keywords": "infantry specialist stealth", "desc": "Stealth operative for behind-lines sabotage."
    },
    "Destroyer": {
        "role": "anti_capital", "tier": 3, "hp": 1500, "armor": 80, "damage": 600, "cost": 5000,
        "keywords": "ship specialist glass_cannon", "desc": "Escort ship designed to hunt Capital ships."
    }
}

NAMING = {
    "Zealot_Legions": { "Anti_Air_Tank": "Exorcist", "Tank_Hunter": "Retributor", "Infiltrator": "Seeker", "Destroyer": "Purge-Ship" },
    "Ascended_Order": { "Anti_Air_Tank": "Sky-Lance", "Tank_Hunter": "Warp-Breaker", "Infiltrator": "Ghost", "Destroyer": "Fate-Ender" },
    "Iron_Vanguard": { "Anti_Air_Tank": "Flak-Track", "Tank_Hunter": "Sapper", "Infiltrator": "Scout", "Destroyer": "Munitions-Barge" },
    "Hive_Swarm": { "Anti_Air_Tank": "Spitter Beast", "Tank_Hunter": "Acid-Spitter", "Infiltrator": "Lictor-Strain", "Destroyer": "Acid-Ship" },
    "Cyber_Synod": { "Anti_Air_Tank": "pylon-Array", "Tank_Hunter": "Deconstructor", "Infiltrator": "Wraith-Frame", "Destroyer": "Deletion-Vessel" },
    "Void_Corsairs": { "Anti_Air_Tank": "Razor-Flock", "Tank_Hunter": "Dark-Lance", "Infiltrator": "Shadow", "Destroyer": "Void-Stinger" },
    "Solar_Hegemony": { "Anti_Air_Tank": "Missile-Boat", "Tank_Hunter": "Rail-Suit", "Infiltrator": "Stealth-Suit", "Destroyer": "Ion-Frigate" },
    "Rift_Daemons": { "Anti_Air_Tank": "Sky-Screamer", "Tank_Hunter": "Blood-Letter", "Infiltrator": "Changeling", "Destroyer": "Hell-Drake" },
    "Scavenger_Clans": { "Anti_Air_Tank": "Flakka-Wagon", "Tank_Hunter": "Tank-Busta", "Infiltrator": "Sneaky-Git", "Destroyer": "Boom-Ship" },
    "Ancient_Guardians": { "Anti_Air_Tank": "Star-Weaver", "Tank_Hunter": "Fire-Dragon", "Infiltrator": "Ranger", "Destroyer": "Void-Hunter" }
}

def generate_specialists():
    if not os.path.exists(UNITS_DIR): os.makedirs(UNITS_DIR)

    for faction, archetype in FACTIONS.items():
        print(f"Generating Specialists for {faction}...")
        
        roster_file = os.path.join(UNITS_DIR, f"{faction.lower()}_specialists.json")
        specialist_data = []

        for key, tmpl in SPECIALIST_TEMPLATES.items():
            name = NAMING[faction].get(key, f"{faction} {key}")
            
            # Morph Stats based on Archetype
            stats = tmpl.copy()
            
            if archetype == "speed": # Corsairs/Speed need speed
                stats["speed"] = 10 if "vehicle" in tmpl["keywords"] else 6
                stats["armor"] = int(stats["armor"] * 0.7)
            elif archetype == "sio": # Hive
                stats["cost"] = int(stats["cost"] * 0.8)
            elif archetype == "elite": # Guardians
                stats["damage"] = int(stats["damage"] * 1.3)
                stats["cost"] = int(stats["cost"] * 1.5)

            # Generate DNA
            dna_stats = {
                "hp": stats["hp"], "armor": stats["armor"], "damage": stats["damage"],
                "speed": 8, "cost": stats["cost"], "name": name,
                "keywords": f"{tmpl['keywords']} {archetype}".lower(),
                "role": tmpl["role"]
            }
            
            dna = generate_dna_from_stats(dna_stats)
            
            unit_entry = {
                "name": name,
                "blueprint_id": f"{faction.lower()}_{name.lower().replace(' ', '_')}",
                "type": "ship" if "ship" in tmpl["keywords"] else ("vehicle" if "vehicle" in tmpl["keywords"] else "infantry"),
                "faction": faction,
                "tier": tmpl["tier"],
                "cost": stats["cost"],
                "base_stats": stats,
                "elemental_dna": dna,
                "source_universe": "eternal_crusade",
                "description": tmpl["desc"],
                "specialist": True
            }
            specialist_data.append(unit_entry)
            
        with open(roster_file, 'w') as f:
            json.dump(specialist_data, f, indent=2)

if __name__ == "__main__":
    generate_specialists()
