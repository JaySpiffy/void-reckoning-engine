import os
import json
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
BUILDINGS_DIR = os.path.join(UNIVERSE_PATH, "infrastructure")
TECH_DIR = os.path.join(UNIVERSE_PATH, "technology")

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

# Building Templates with atomic flavor biases
BUILDING_TEMPLATES = {
    "barracks": {"tier": 1, "cost": 500, "cat": "military", "name": "Barracks", "effect": "Unlocks infantry"},
    "factory": {"tier": 2, "cost": 1200, "cat": "industry", "name": "Factory", "effect": "Unlocks vehicles"},
    "lab": {"tier": 1, "cost": 800, "cat": "technology", "name": "Research Lab", "effect": "Generates Research"},
    "mine": {"tier": 1, "cost": 600, "cat": "economy", "name": "Mine", "effect": "Generates Resources"},
    "defense": {"tier": 1, "cost": 400, "cat": "defense", "name": "Turret", "effect": "Planetary Defense"},
    "shipyard": {"tier": 3, "cost": 3000, "cat": "navy", "name": "Shipyard", "effect": "Unlocks Ships"}
}

# Technology Templates
TECH_TEMPLATES = {
    "tier1_military": {"tier": 1, "cost": 1000, "cat": "military", "name": "Basic Doctrine"},
    "tier2_vehicles": {"tier": 2, "cost": 2500, "cat": "engineering", "name": "Heavy Armor"},
    "tier3_battleships": {"tier": 3, "cost": 5000, "cat": "navy", "name": "Capital Ships"},
    "adv_economy": {"tier": 1, "cost": 1500, "cat": "economy", "name": "Logistics"},
    "super_weapon": {"tier": 3, "cost": 10000, "cat": "super", "name": "Ultimate Weapon"}
}

# Flavor Text / Naming Dictionaries
FLAVOR = {
    "crusader": {
        "barracks": "Chapel-Barracks", "factory": "Manufactorum", "lab": "Scriptorium", 
        "mine": "Tithe Hall", "defense": "Bastion", "shipyard": "Orbital Cathedral",
        "tech_mil": "Holy Bolter Drills", "tech_veh": "Sacred Hull Plating"
    },
    "psyker": {
        "barracks": "Meditation Spire", "factory": "Crystal Loom", "lab": "Psionic Archive", 
        "mine": "Aether Siphon", "defense": "Warp Shield", "shipyard": "Gateway Node",
        "tech_mil": "Mental Conditioning", "tech_veh": "Warp Geometry"
    },
    "industrial": {
        "barracks": "Training Camp", "factory": "Mega-Foundry", "lab": "Design Bureau", 
        "mine": "Deep Core Drill", "defense": "Flak Tower", "shipyard": "Star Dock",
        "tech_mil": "Mass Production", "tech_veh": "Composite Alloys"
    },
    "bio": {
        "barracks": "Spawning Pool", "factory": "Birthing Sac", "lab": "Evolution Pit", 
        "mine": "Digestion Pool", "defense": "Spore Colony", "shipyard": "Orbital Hive",
        "tech_mil": "Adrenal Glands", "tech_veh": "Chitin Hardening"
    },
    "cyber": {
        "barracks": "Assembly Line", "factory": "Reanimation Crypt", "lab": "Logic Core", 
        "mine": "Matter Converter", "defense": "Gauss Pylon", "shipyard": "Tomb Shipyard",
        "tech_mil": "Targeting Algorithms", "tech_veh": "Living Metal"
    },
    "speed": {
        "barracks": "Raider Den", "factory": "Chop Shop", "lab": "Drug Den", 
        "mine": "Slave Pit", "defense": "Holofield Emitter", "shipyard": "Hidden Dock",
        "tech_mil": "Stimulants", "tech_veh": "Anti-Grav Motors"
    },
    "tech": {
        "barracks": "Academy", "factory": "Drone Port", "lab": "Science Nexus", 
        "mine": "Plasma Extractor", "defense": "Shield Grid", "shipyard": "Gravity Anchor",
        "tech_mil": "Pulse Rifles", "tech_veh": "Hover Tech"
    },
    "aether": {
        "barracks": "Portal", "factory": "Warp Forge", "lab": "Library of Madness", 
        "mine": "Soul Siphon", "defense": "Reality Tear", "shipyard": "Rift Anchor",
        "tech_mil": "Daemon Binding", "tech_veh": "Possessed Metal"
    },
    "scavenger": {
        "barracks": "Fight Pit", "factory": "Mek Shop", "lab": "Oddboy Hut", 
        "mine": "Scrap Pile", "defense": "Big Gunz", "shipyard": "Space Hulk Dock",
        "tech_mil": "More Dakka", "tech_veh": "Red Paint"
    },
    "elite": {
        "barracks": "Aspect Shrine", "factory": "Wraithbone Singer", "lab": "Path Seer", 
        "mine": "Starlight Catcher", "defense": "Webway Gate", "shipyard": "Void Span",
        "tech_mil": "Ancient Discipline", "tech_veh": "Ghost Tech"
    }
}

def generate_infrastructure():
    if not os.path.exists(BUILDINGS_DIR): os.makedirs(BUILDINGS_DIR)
    if not os.path.exists(TECH_DIR): os.makedirs(TECH_DIR)

    buildings_registry = {}
    tech_registry = {}

    for faction, archetype in FACTIONS.items():
        print(f"Generating infrastructure for {faction}...")
        flavor = FLAVOR.get(archetype, FLAVOR["industrial"])
        
        # 1. Generate Buildings
        for b_key, tmpl in BUILDING_TEMPLATES.items():
            b_name = flavor.get(b_key, tmpl["name"])
            b_id = f"{faction}_{b_key}".replace(" ", "_")
            
            # Write Markdowns (Simulating manual content creation)
            md_path = os.path.join(BUILDINGS_DIR, f"{faction}_buildings.md")
            with open(md_path, 'a') as f:
                f.write(f"\n## {b_name}\n")
                f.write(f"* **Tier {tmpl['tier']}: {b_name}**\n")
                f.write(f"* Cost: {tmpl['cost']}\n")
                f.write(f"* Effect: {tmpl['effect']}\n")
            
            # Add to registry dict for later dump
            buildings_registry[b_id] = {
                "id": b_id,
                "name": b_name,
                "tier": tmpl["tier"],
                "cost": tmpl["cost"],
                "faction": faction,
                "category": tmpl["cat"],
                "source_file": "generated"
            }
            
            # 2. Links to Technology
            # We create a technology required to build this if it's tier > 1
            if tmpl["tier"] > 1:
               t_key = f"tech_tier{tmpl['tier']}"
               t_name = f"Unlock {b_name}"
               t_id = f"Tech_{faction}_{t_key}"
               
               tech_registry[t_id] = {
                   "id": t_id,
                   "name": t_name,
                   "tier": tmpl["tier"],
                   "cost": tmpl["cost"] * 2,
                   "faction": faction,
                   "unlocks_buildings": [b_id],
                   "prerequisites": [],
                   "category": ["infrastructure"]
               }

        # 3. Generate Pure Technologies
        for t_key, tmpl in TECH_TEMPLATES.items():
            t_name = flavor.get(t_key, tmpl["name"])
            if t_key.startswith("tech"): # Use flavor name if mapped
                base_key = t_key.split("_")[1] # mil or veh
                flavor_key = f"tech_{base_key}"
                if flavor_key in flavor:
                    t_name = flavor[flavor_key]
            
            t_id = f"Tech_{faction}_{t_key}"
            
            md_path = os.path.join(TECH_DIR, f"{faction}_tech.md")
            with open(md_path, 'a') as f:
                 f.write(f"\n## {t_name}\n")
                 f.write(f"* **Tier {tmpl['tier']}: {t_name}**\n")
                 f.write(f"* Cost: {tmpl['cost']}\n")
            
            tech_registry[t_id] = {
                "id": t_id,
                "name": t_name,
                "tier": tmpl["tier"],
                "cost": tmpl["cost"],
                "faction": faction,
                "category": [tmpl["cat"]],
                "source_file": "generated"
            }

    # Save Intermediate Registries (The Builder script will standardize them later)
    # Actually, we can just rely on the builder parsing the MD files we just wrote?
    # Or just dump these JSONs directly. Let's dump JSONs to be safe and comprehensive.
    
    with open(os.path.join(BUILDINGS_DIR, "building_registry.json"), 'w') as f:
        json.dump(buildings_registry, f, indent=2)

    with open(os.path.join(TECH_DIR, "technology_registry.json"), 'w') as f:
        json.dump(tech_registry, f, indent=2)

if __name__ == "__main__":
    generate_infrastructure()
