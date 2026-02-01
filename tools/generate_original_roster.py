import os
import json
import sys

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

BASE_TEMPLATES = {
    "Infantry": {"hp": 10, "armor": 20, "damage": 5, "speed": 4, "type": "infantry", "cost": 100},
    "Elite_Infantry": {"hp": 25, "armor": 60, "damage": 15, "speed": 4, "type": "infantry", "cost": 300},
    "Light_Vehicle": {"hp": 80, "armor": 50, "damage": 20, "speed": 12, "type": "vehicle", "cost": 500},
    "Heavy_Tank": {"hp": 250, "armor": 150, "damage": 60, "speed": 6, "type": "vehicle", "cost": 1200},
    "Walker": {"hp": 180, "armor": 90, "damage": 45, "speed": 5, "type": "vehicle", "cost": 900},
    "Fighter": {"hp": 50, "armor": 0, "damage": 10, "speed": 35, "type": "ship", "cost": 150},
    "Frigate": {"hp": 800, "armor": 50, "damage": 100, "speed": 15, "type": "ship", "cost": 2000},
    "Cruiser": {"hp": 3000, "armor": 150, "damage": 400, "speed": 8, "type": "ship", "cost": 8000},
    "Battleship": {"hp": 12000, "armor": 400, "damage": 1500, "speed": 4, "type": "ship", "cost": 25000}
}

NAMING_SCHEMES = {
    "Zealot_Legions": {
        "Infantry": "Initiate", "Elite_Infantry": "Templar", "Light_Vehicle": "Chariot",
        "Heavy_Tank": "Purifier", "Walker": "Penitent Engine", "Fighter": "Cherubim",
        "Frigate": "Sword Class", "Cruiser": "Cathedral Class", "Battleship": "Basilica Class"
    },
    "Ascended_Order": {
        "Infantry": "Acolyte", "Elite_Infantry": "Magus", "Light_Vehicle": "Warp Skiff",
        "Heavy_Tank": "Prism Tank", "Walker": "Construct", "Fighter": "Wisp",
        "Frigate": "Lantern Class", "Cruiser": "Beacon Class", "Battleship": "Nexus Class"
    },
    "Iron_Vanguard": {
        "Infantry": "Conscript", "Elite_Infantry": "Grenadier", "Light_Vehicle": "Rover",
        "Heavy_Tank": "Sledgehammer", "Walker": "Iron Strider", "Fighter": "Hawk",
        "Frigate": "Hammer Class", "Cruiser": "Anvil Class", "Battleship": "Foundry Class"
    },
    "Hive_Swarm": {
        "Infantry": "Drone", "Elite_Infantry": "Warrior", "Light_Vehicle": "Skitterer",
        "Heavy_Tank": "Crusher Beast", "Walker": "Stalking Horror", "Fighter": "Spore",
        "Frigate": "Bio-Ship", "Cruiser": "Hive Ship", "Battleship": "World Eater"
    },
    "Cyber_Synod": {
        "Infantry": "Thrall", "Elite_Infantry": "Immortal", "Light_Vehicle": "Skimmer",
        "Heavy_Tank": "Monolith", "Walker": "Strider", "Fighter": "Doom Scythe",
        "Frigate": "Dirge Class", "Cruiser": "Requiem Class", "Battleship": "Silicon God"
    },
    "Void_Corsairs": {
        "Infantry": "Raider", "Elite_Infantry": "Incubus", "Light_Vehicle": "Jetbike",
        "Heavy_Tank": "Ravager", "Walker": "Wraith", "Fighter": "Razorwing",
        "Frigate": "Corsair Class", "Cruiser": "Eclipse Class", "Battleship": "Void Stalker"
    },
    "Solar_Hegemony": {
        "Infantry": "Cadre", "Elite_Infantry": "Battlesuit", "Light_Vehicle": "Pathfinder",
        "Heavy_Tank": "Hammerhead", "Walker": "Riptide", "Fighter": "Barracuda",
        "Frigate": "Protector Class", "Cruiser": "Diplomat Class", "Battleship": "Custodian Class"
    },
    "Rift_Daemons": {
        "Infantry": "Lesser Horror", "Elite_Infantry": "Herald", "Light_Vehicle": "Seeker Chariot",
        "Heavy_Tank": "Soul Grinder", "Walker": "Greater Daemon", "Fighter": "Screamer",
        "Frigate": "Hellfire Class", "Cruiser": "Torment Class", "Battleship": "Abyssal Class"
    },
    "Scavenger_Clans": {
        "Infantry": "Boyz", "Elite_Infantry": "Nobz", "Light_Vehicle": "Buggy",
        "Heavy_Tank": "Battle Wagon", "Walker": "Stompa", "Fighter": "Dakka Jet",
        "Frigate": "Scrap Ship", "Cruiser": "Kill Kroozer", "Battleship": "Space Hulk"
    },
    "Ancient_Guardians": {
        "Infantry": "Guardian", "Elite_Infantry": "Warden", "Light_Vehicle": "Grav-Sled",
        "Heavy_Tank": "Prism", "Walker": "Wraith Lord", "Fighter": "Interceptor",
        "Frigate": "Watcher Class", "Cruiser": "Shield Class", "Battleship": "Glory Class"
    }
}

def generate_rosters():
    if not os.path.exists(UNITS_DIR):
        os.makedirs(UNITS_DIR)

    for faction, archetype in FACTIONS.items():
        print(f"Generating roster for {faction} ({archetype})...")
        roster_file = os.path.join(UNITS_DIR, f"{faction.lower()}_roster.json")
        roster_data = []

        for role, template in BASE_TEMPLATES.items():
            name = NAMING_SCHEMES[faction].get(role, f"{faction} {role}")
            
            # 1. Morph Stats based on Archetype
            stats = template.copy()
            keywords = [role.lower(), archetype]

            # --- ORIGINAL 3 ---
            if archetype == "crusader":
                stats["hp"] = int(stats["hp"] * 1.2)
                stats["damage"] = int(stats["damage"] * 1.1)
                keywords.append("zealot")
            elif archetype == "psyker":
                stats["armor"] = int(stats["armor"] * 0.5)
                stats["damage"] = int(stats["damage"] * 1.5)
                keywords.append("psyker")
            elif archetype == "industrial":
                stats["armor"] = int(stats["armor"] * 1.5)
                stats["speed"] = int(stats["speed"] * 0.8)
                keywords.append("heavy")
            
            # --- NEW 7 ---
            elif archetype == "bio":
                stats["armor"] = int(stats["armor"] * 0.4) # Flesh is weak
                stats["hp"] = int(stats["hp"] * 1.3) # Biomass is cheap
                stats["speed"] = int(stats["speed"] * 1.4) # Fast
                stats["cost"] = int(stats["cost"] * 0.7) # Cheap
                keywords.append("organic")
            elif archetype == "cyber":
                stats["hp"] = int(stats["hp"] * 1.5) # Reanimation protocols
                stats["speed"] = int(stats["speed"] * 0.5) # Slow
                stats["damage"] = int(stats["damage"] * 1.2)
                keywords.append("robot")
            elif archetype == "speed":
                stats["armor"] = int(stats["armor"] * 0.2) # Paper planes
                stats["speed"] = int(stats["speed"] * 2.0) # Insanely fast
                stats["damage"] = int(stats["damage"] * 1.5) # Glass cannon
                keywords.append("agile")
            elif archetype == "tech":
                stats["damage"] = int(stats["damage"] * 1.2) # Better guns
                stats["range"] = 1.2 # Conceptual range boost
                keywords.append("ranged")
            elif archetype == "aether":
                stats["armor"] = 0 # No armor, only ward save (Focus/Will)
                stats["hp"] = int(stats["hp"] * 0.8)
                stats["damage"] = int(stats["damage"] * 1.5)
                keywords.append("daemon")
            elif archetype == "scavenger":
                stats["cost"] = int(stats["cost"] * 0.5) # Dirt cheap
                stats["damage"] = int(stats["damage"] * 0.8) # Bad guns
                stats["hp"] = int(stats["hp"] * 1.2) # Tough
                keywords.append("junk")
            elif archetype == "elite":
                stats["cost"] = int(stats["cost"] * 2.5) # Very expensive
                stats["hp"] = int(stats["hp"] * 1.5)
                stats["damage"] = int(stats["damage"] * 1.5)
                stats["armor"] = int(stats["armor"] * 1.5)
                keywords.append("ancient")

            # 2. Generate DNA
            # Prepare stats dict for generator
            dna_input_stats = {
                "hp": stats["hp"],
                "armor": stats["armor"],
                "damage": stats["damage"],
                "speed": stats["speed"],
                "cost": stats["cost"],
                "name": name,
                "keywords": " ".join(keywords),
                "role": role.lower()
            }
            
            try:
                dna = generate_dna_from_stats(dna_input_stats)
                
                # 3. Create Unit JSON
                unit_entry = {
                    "name": name,
                    "blueprint_id": f"{faction.lower()}_{name.lower().replace(' ', '_')}",
                    "type": stats["type"],
                    "faction": faction,
                    "cost": stats["cost"],
                    "base_stats": stats,
                    "elemental_dna": dna,
                    "source_universe": "eternal_crusade",
                    "description": f"{faction} {role} unit. Auto-generated."
                }
                roster_data.append(unit_entry)
                
            except Exception as e:
                print(f"Failed to generate {name}: {e}")

        # Save Faction Roster
        with open(roster_file, "w") as f:
            json.dump(roster_data, f, indent=2)
        print(f"Saved {len(roster_data)} units to {roster_file}")

if __name__ == "__main__":
    generate_rosters()
