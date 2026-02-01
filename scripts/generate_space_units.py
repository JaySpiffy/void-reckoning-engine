
import json
import os
import sys
import copy

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.dna_generator import blend_dna_profiles, UNIT_CLASSES, normalize_dna, validate_unit_class

SPACE_UNIT_TEMPLATES = {
    # TIER 1
    "fighter": {
        "tier": 1,
        "cost_range": (150, 250),
        "base_stats": {"hp": 80, "armor": 15, "damage": 18, "speed": 55, "type": "strike_craft"},
        "suggested_abilities": ["Evasive_Maneuvers", "Rapid_Fire"],
        "suggested_traits": ["Veteran_Crew"]
    },
    "bomber": {
        "tier": 1,
        "cost_range": (200, 300),
        "base_stats": {"hp": 100, "armor": 20, "damage": 35, "speed": 40, "type": "strike_craft"},
        "suggested_abilities": ["Plasma_Burst", "Torpedo_Salvo"],
        "suggested_traits": ["Master-Crafted"]
    },
    "interceptor": {
        "tier": 1,
        "cost_range": (180, 280),
        "base_stats": {"hp": 70, "armor": 10, "damage": 20, "speed": 65, "type": "strike_craft"},
        "suggested_abilities": ["Afterburner", "Tracking_Lock"],
        "suggested_traits": ["Reckless_Pilot"]
    },
    # TIER 2
    "corvette": {
        "tier": 2,
        "cost_range": (800, 1200),
        "base_stats": {"hp": 400, "armor": 45, "damage": 40, "speed": 35, "type": "ship"},
        "suggested_abilities": ["Point_Defense", "Flak_Barrage"],
        "suggested_traits": ["Cautious_Commander"]
    },
    "frigate": {
        "tier": 2,
        "cost_range": (1000, 1500),
        "base_stats": {"hp": 500, "armor": 50, "damage": 55, "speed": 30, "type": "ship"},
        "suggested_abilities": ["EMP_Burst", "Sensor_Sweep"],
        "suggested_traits": ["Veteran_Crew"]
    },
    "destroyer": {
        "tier": 2,
        "cost_range": (1200, 2000),
        "base_stats": {"hp": 450, "armor": 40, "damage": 80, "speed": 32, "type": "ship"},
        "suggested_abilities": ["Ion_Cannon", "Overcharge"],
        "suggested_traits": ["Reckless_Pilot"]
    },
    # TIER 3
    "light_cruiser": {
        "tier": 3,
        "cost_range": (4000, 6000),
        "base_stats": {"hp": 1500, "armor": 80, "damage": 120, "speed": 25, "type": "ship"},
        "suggested_abilities": ["Sensor_Sweep", "Hit_and_Run"],
        "suggested_traits": ["Veteran_Crew"]
    },
    "heavy_cruiser": {
        "tier": 3,
        "cost_range": (6000, 10000),
        "base_stats": {"hp": 2500, "armor": 100, "damage": 180, "speed": 20, "type": "ship"},
        "suggested_abilities": ["Shield_Regen", "Fortify_Position"],
        "suggested_traits": ["Cautious_Commander"]
    },
    "battlecruiser": {
        "tier": 3,
        "cost_range": (8000, 12000),
        "base_stats": {"hp": 2200, "armor": 90, "damage": 220, "speed": 22, "type": "ship"},
        "suggested_abilities": ["Plasma_Burst", "Overcharge"],
        "suggested_traits": ["Reckless_Pilot"]
    },
    "battleship": {
        "tier": 3,
        "cost_range": (10000, 15000),
        "base_stats": {"hp": 4000, "armor": 120, "damage": 250, "speed": 15, "type": "ship"},
        "suggested_abilities": ["Fortify_Position", "Regeneration"],
        "suggested_traits": ["Regeneration", "Cautious_Commander"]
    }
}

FACTION_FLAVOR_NAMES = {
    "Zealot_Legions": ["Conviction", "Crusader", "Righteous", "Faithful", "Holy", "Divine", "Redeemer", "Purifier", "Confessor", "Templar"],
    "Ascended_Order": ["Aether", "Mindstrike", "Prescient", "Psionic", "Astral", "Celestial", "Mystic", "Oracle", "Seer", "Prophet"],
    "Iron_Vanguard": ["Bulwark", "Siege", "Fortress", "Bastion", "Iron", "Steel", "Heavy", "Armored", "Shield", "Guardian"],
    "Hive_Swarm": ["Drone", "Spore", "Hive", "Brood", "Swarm", "Chitin", "Biomass", "Living", "Apex", "Predator"],
    "Cyber_Synod": ["Logic", "Reaper", "Protocol", "Digital", "Network", "Binary", "Cyber", "Tech", "Algorithm", "System"],
    "Void_Corsairs": ["Shadow", "Raider", "Phantom", "Pirate", "Corsair", "Void", "Ghost", "Spectre", "Rogue", "Outlaw"],
    "Solar_Hegemony": ["Plasma", "Sunburst", "Hegemony", "Solar", "Radiant", "Imperial", "Stellar", "Nova", "Fusion", "Luminous"],
    "Rift_Daemons": ["Warp", "Chaos", "Daemon", "Abyssal", "Hellfire", "Torment", "Rift", "Vortex", "Entropy", "Infernal"],
    "Scavenger_Clans": ["Scrap", "Salvage", "Junker", "Rust", "Raider", "Trash", "Recycled", "Makeshift", "Patchwork", "Debris"],
    "Ancient_Guardians": ["Sentinel", "Guardian", "Eternal", "Ancient", "Relic", "Warden", "Keeper", "Watcher", "Preserver", "Timeless"]
}

def generate_units():
    base_path = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade"
    factions_dir = os.path.join(base_path, "factions")
    units_dir = os.path.join(base_path, "units")
    
    # Load DNA
    with open(os.path.join(factions_dir, "faction_dna.json"), "r") as f:
        faction_dna_data = json.load(f)
        
    for faction, flavor_names in FACTION_FLAVOR_NAMES.items():
        print(f"Generating space units for {faction}...")
        faction_dna = faction_dna_data.get(faction)
        if not faction_dna:
            print(f"Skipping {faction}, no DNA found.")
            continue
            
        units = []
        name_idx = 0
        
        for class_name, template in SPACE_UNIT_TEMPLATES.items():
            # Blend DNA
            class_dna = UNIT_CLASSES.get(class_name)
            if not class_dna:
                print(f"Warning: No DNA preset for {class_name}")
                continue
                
            blended_dna = blend_dna_profiles(class_dna, faction_dna, class_weight=0.5)
            
            # Name
            flavor = flavor_names[name_idx % len(flavor_names)]
            display_name = f"{flavor} {class_name.replace('_', ' ').title()}"
            name_idx += 1
            
            # Cost
            cost = int(sum(template["cost_range"]) / 2)
            upkeep = cost // 10
            
            # Abilities/Traits
            abilities = list(template["suggested_abilities"]) # Copy
            traits = list(template["suggested_traits"]) # Copy
            
            # Adjust Traits based on DNA (Simple Logic)
            if blended_dna.get("atom_cohesion", 0) > 15:
                if "Regeneration" not in traits: traits.append("Regeneration")
            if blended_dna.get("atom_frequency", 0) > 20:
                if "Reckless Pilot" not in traits: traits.append("Reckless Pilot")
                
            # Formatting traits/abilities IDs
            final_traits = []
            for t in traits:
                # [VERIFY COMMENT 2] Use Registry Keys directly (no Trait_ prefix)
                # Ensure spacing matches registry (e.g. "Veteran_Crew" -> "Veteran Crew")
                t_clean = t.replace("_", " ")
                final_traits.append(t_clean)
            
            final_abilities = []
            for a in abilities:
                if not a.startswith("Ability_"): a = f"Ability_{a}"
                final_abilities.append(a)

            unit = {
                "name": display_name,
                "blueprint_id": f"{faction.lower()}_{class_name}",
                "type": template["base_stats"]["type"],
                "faction": faction,
                "cost": cost,
                "upkeep": upkeep,
                "base_stats": dict(template["base_stats"]), # Copy
                "elemental_dna": blended_dna,
                "source_universe": "eternal_crusade",
                "description": f"{faction} {class_name}-class unit. Auto-generated via Taxonomy.",
                "abilities": final_abilities,
                "traits": final_traits,
                "unit_class": class_name,
                "domain": "space"
            }
            # Fix base stats cost
            unit["base_stats"]["cost"] = cost
            
            units.append(unit)
            
        # Write to file
        filename = f"{faction.lower()}_space_units.json"
        outfile = os.path.join(units_dir, filename)
        with open(outfile, "w", encoding='utf-8') as f:
            json.dump(units, f, indent=2)
        print(f"Created {outfile}")
        
        # [VERIFY COMMENT 4] Update Faction Registry
        # Load registry
        registry_path = os.path.join(factions_dir, "faction_registry.json")
        try:
            with open(registry_path, "r", encoding='utf-8') as f:
                mod_registry = json.load(f)
            
            if faction in mod_registry:
                # Ensure unit_files list exists
                if "unit_files" not in mod_registry[faction]:
                     mod_registry[faction]["unit_files"] = []
                
                # Add file if missing
                rel_path = f"units/{filename}"
                if rel_path not in mod_registry[faction]["unit_files"]:
                    mod_registry[faction]["unit_files"].append(rel_path)
                    print(f"Registered {rel_path} for {faction}")
            
            # Write back
            with open(registry_path, "w", encoding='utf-8') as f:
                json.dump(mod_registry, f, indent=2)
                
        except Exception as e:
            print(f"Failed to update registry for {faction}: {e}")

if __name__ == "__main__":
    generate_units()
