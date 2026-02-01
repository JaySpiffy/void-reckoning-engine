
import json
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.dna_generator import blend_dna_profiles, UNIT_CLASSES, normalize_dna

# ==========================================
# 1. UNIT TEMPLATES (Base Stats & Config)
# ==========================================

# SPACE UNITS (Tier 4-6)
SPACE_TEMPLATES = {
    "carrier": {
        "tier": 4,
        "base_cost": 25000,
        "stats": {"hp": 5000, "armor": 150, "damage": 200, "speed": 12, "role": "capital_ship"},
        "suggested_abilities": ["Ability_Point_Defense", "Ability_Sensor_Sweep", "Ability_Shield_Regen", "Ability_Regeneration"],
        "suggested_traits": ["Veteran Crew"],
        "dna_keys": {"atom_information": 30, "atom_stability": 25, "atom_energy": 15} # Preset reference
    },
    "dreadnought": {
        "tier": 4,
        "base_cost": 35000,
        "stats": {"hp": 8000, "armor": 250, "damage": 500, "speed": 10, "role": "capital_ship"},
        "suggested_abilities": ["Ability_Fortify_Position", "Ability_Regeneration", "Ability_Plasma_Burst", "Ability_Overcharge"],
        "suggested_traits": ["Veteran Crew", "Regeneration"],
        "dna_keys": {"atom_mass": 35, "atom_cohesion": 30, "atom_energy": 20}
    },
    "titan": {
        "tier": 5,
        "base_cost": 60000,
        "stats": {"hp": 12000, "armor": 350, "damage": 800, "speed": 8, "role": "titan"},
        "suggested_abilities": ["Ability_Overcharge", "Ability_Ion_Cannon", "Ability_Tracking_Lock", "Ability_Plasma_Burst"],
        "suggested_traits": ["Veteran Crew", "Master-Crafted"],
        "dna_keys": {"atom_focus": 35, "atom_energy": 30, "atom_mass": 20}
    },
    "planet_killer": {
        "tier": 5,
        "base_cost": 80000,
        "stats": {"hp": 10000, "armor": 300, "damage": 2000, "speed": 6, "role": "titan"},
        "suggested_abilities": ["Ability_Overcharge", "Ability_Plasma_Burst", "Ability_Torpedo_Salvo", "Ability_Ion_Cannon"],
        "suggested_traits": ["Veteran Crew", "Reckless Pilot"],
        "dna_keys": {"atom_volatility": 40, "atom_focus": 30, "atom_energy": 20}
    },
    "world_devastator": {
        "tier": 5,
        "base_cost": 75000,
        "stats": {"hp": 15000, "armor": 400, "damage": 1000, "speed": 5, "role": "titan"},
        "suggested_abilities": ["Ability_Regeneration", "Ability_Fortify_Position", "Ability_Torpedo_Salvo", "Ability_Shield_Regen"],
        "suggested_traits": ["Veteran Crew", "Cautious Commander"],
        "dna_keys": {"atom_mass": 40, "atom_energy": 30, "atom_cohesion": 20}
    },
    "stellar_accelerator": {
        "tier": 5,
        "base_cost": 90000,
        "stats": {"hp": 8000, "armor": 200, "damage": 1500, "speed": 15, "role": "titan"},
        "suggested_abilities": ["Ability_EMP_Burst", "Ability_Ion_Cannon", "Ability_Sensor_Sweep", "Ability_Overcharge"],
        "suggested_traits": ["Veteran Crew", "Reckless Pilot"],
        "dna_keys": {"atom_aether": 35, "atom_frequency": 30, "atom_energy": 20}
    },
    "mothership": {
        "tier": 6,
        "base_cost": 150000,
        "stats": {"hp": 25000, "armor": 600, "damage": 1200, "speed": 6, "role": "strategic_asset"},
        "suggested_abilities": ["Ability_Regeneration", "Ability_Shield_Regen", "Ability_Fortify_Position", "Ability_Sensor_Sweep", "Ability_Point_Defense"],
        "suggested_traits": ["Veteran Crew", "Regeneration", "Cautious Commander"],
        "dna_keys": {"atom_mass": 40, "atom_will": 35, "atom_cohesion": 15}
    }
}

# GROUND UNITS (Tier 4-6)
GROUND_TEMPLATES = {
    "command_vehicle": {
        "tier": 4,
        "base_cost": 20000,
        "stats": {"hp": 2500, "armor": 100, "damage": 150, "speed": 10, "role": "command"},
        "suggested_abilities": ["Ability_Sensor_Sweep", "Ability_Tracking_Lock", "Ability_Shield_Regen"],
        "suggested_traits": ["Veteran Crew", "Cautious Commander"],
        "dna_keys": {"atom_information": 30, "atom_will": 25, "atom_stability": 20}
    },
    "titan_walker": {
        "tier": 5,
        "base_cost": 50000,
        "stats": {"hp": 8000, "armor": 300, "damage": 600, "speed": 6, "role": "titan"},
        "suggested_abilities": ["Ability_Overcharge", "Ability_Plasma_Burst", "Ability_Fortify_Position", "Ability_Shield_Regen"],
        "suggested_traits": ["Veteran Crew", "Master-Crafted"],
        "dna_keys": {"atom_focus": 35, "atom_energy": 30, "atom_mass": 20}
    },
    "siege_engine": {
        "tier": 5,
        "base_cost": 55000,
        "stats": {"hp": 7000, "armor": 250, "damage": 900, "speed": 5, "role": "titan"},
        "suggested_abilities": ["Ability_Torpedo_Salvo", "Ability_Fortify_Position", "Ability_Tracking_Lock"],
        "suggested_traits": ["Veteran Crew", "Reckless Pilot"],
        "dna_keys": {"atom_volatility": 40, "atom_focus": 25, "atom_mass": 20}
    },
    "mobile_fortress": {
        "tier": 6,
        "base_cost": 120000,
        "stats": {"hp": 20000, "armor": 500, "damage": 1000, "speed": 4, "role": "strategic_asset"},
        "suggested_abilities": ["Ability_Fortify_Position", "Ability_Regeneration", "Ability_Shield_Regen", "Ability_Point_Defense", "Ability_Flak_Barrage"],
        "suggested_traits": ["Veteran Crew", "Regeneration", "Cautious Commander"],
        "dna_keys": {"atom_mass": 40, "atom_will": 30, "atom_cohesion": 20}
    }
}

# ==========================================
# 2. FACTION CONFIGURATION
# ==========================================

FACTION_CONFIGS = {
    "Zealot_Legions": {
        "naming_theme": ["Eternal Wrath", "Divine Retribution", "Saint's Fury", "Holy Ark", "Penitent Titan"],
        "dna_boost": {"atom_will": 10, "atom_aether": 10},
        "cost_mod": 1.0,
        "stat_mod": {"hp": 1.15}, # Durability from Will
        "abil_pref": ["Ability_Overcharge", "Ability_Plasma_Burst"],
        "trait_pref": ["Master-Crafted"],
        "mechanics": {
            "morale_aura": {
                "range": 500,
                "bonus": 0.5,
                "description": "Inspired by the Eternal Crusade."
            }
        }
    },
    "Ascended_Order": {
        "naming_theme": ["Mindbreaker", "Thought Weaver", "Aether Sovereign", "Psionic Nexus", "Void Citadel"],
        "dna_boost": {"atom_aether": 15, "atom_focus": 10},
        "cost_mod": 1.0,
        "stat_mod": {"hp": 1.15},
        "abil_pref": ["Ability_EMP_Burst", "Ability_Ion_Cannon"],
        "trait_pref": [],
        "mechanics": {
            "psionic_network_boost": {
                "range_multiplier": 2.0,
                "accuracy_bonus": 0.25,
                "description": "Amplifies the Psionic Network."
            }
        }
    },
    "Hive_Swarm": {
        "naming_theme": ["Hive Leviathan", "Brood Colossus", "Apex Devourer", "Swarm Mothership", "Biomass Titan"],
        "dna_boost": {"atom_mass": 10, "atom_volatility": 5},
        "cost_mod": 0.8, # Biomass recycling
        "stat_mod": {},
        "abil_pref": ["Ability_Regeneration", "Ability_Torpedo_Salvo"],
        "trait_pref": [],
        "mechanics": {
            "biomass_spawning": {
                "units_per_turn": 1,
                "unit_tier": 1,
                "description": "Spawns units from consumed biomass."
            }
        }
    },
    "Cyber_Synod": {
        "naming_theme": ["Logic Engine", "Reanimation Ark", "Eternal Construct", "Protocol Titan", "Core Processor"],
        "dna_boost": {"atom_stability": 15, "atom_information": 10},
        "cost_mod": 1.0,
        "stat_mod": {"hp": 1.2, "armor": 1.2}, # High Cohesion/Stability
        "abil_pref": ["Ability_Sensor_Sweep", "Ability_Tracking_Lock"],
        "trait_pref": [],
        "mechanics": {
            "research_optimization": {
                "speed_bonus": 0.20,
                "description": "Optimizes logic core processing."
            }
        }
    },
    "Void_Corsairs": {
        "naming_theme": ["Shadow Reaver", "Void Marauder", "Eclipse Raider", "Plunder Ark", "Ghost Titan"],
        "dna_boost": {"atom_frequency": 10, "atom_energy": 5},
        "cost_mod": 1.1,
        "stat_mod": {},
        "abil_pref": ["Ability_Hit_and_Run", "Ability_Afterburner"],
        "trait_pref": ["Veteran Crew"], # Already in base but reinforcing
        "mechanics": {
            "raider_loot_boost": {
                "loot_bonus": 1.0,
                "description": "Increases plunder from raids."
            }
        }
    },
    "Rift_Daemons": {
        "naming_theme": ["Warp Titan", "Reality Breaker", "Chaos Harbinger", "Hellfire Ark", "Daemon Lord"],
        "dna_boost": {"atom_aether": 20, "atom_volatility": 10},
        "cost_mod": 1.0,
        "stat_mod": {"hp": 0.9, "armor": 0.9, "damage": 1.3},
        "abil_pref": ["Ability_EMP_Burst", "Ability_Overcharge"],
        "trait_pref": [],
        "mechanics": {
            "reality_tear": {
                "damage": 500,
                "radius": 100,
                "chance": 0.1,
                "description": "Causes random reality tears."
            }
        }
    },
    "Scavenger_Clans": {
        "naming_theme": ["Scrap Titan", "Loot Hauler", "Junk Colossus", "Rust Ark", "Debris Lord"],
        "dna_boost": {"atom_volatility": 15, "atom_mass": 5},
        "cost_mod": 1.0,
        "stat_mod": {"hp": 0.9, "armor": 0.9, "damage": 1.3}, 
        "abil_pref": ["Ability_Rapid_Fire", "Ability_Flak_Barrage"],
        "trait_pref": [],
        "mechanics": {
            "waaagh_aura": {
                "damage_stack": 0.05,
                "radius": 300,
                "description": "Increases damage per nearby friendly."
            }
        }
    },
    "Iron_Vanguard": {
        "naming_theme": ["Forge Dreadnought", "Industrial Titan", "War Foundry", "Iron Citadel", "Siege Breaker"],
        "dna_boost": {"atom_mass": 15, "atom_cohesion": 10},
        "cost_mod": 0.9,
        "stat_mod": {"hp": 1.2, "armor": 1.2},
        "abil_pref": ["Ability_Fortify_Position", "Ability_Regeneration"],
        "trait_pref": [],
        "mechanics": {
            "industrial_efficiency": {
                "building_cost_reduction": 0.20,
                "description": "Reduces local construction costs."
            }
        }
    },
    "Solar_Hegemony": {
        "naming_theme": ["Harmony Carrier", "Unity Dreadnought", "Accord Titan", "Solar Ark", "Radiant Lord"],
        "dna_boost": {"atom_energy": 15, "atom_information": 10},
        "cost_mod": 1.0,
        "stat_mod": {},
        "abil_pref": ["Ability_Shield_Regen", "Ability_Ion_Cannon"],
        "trait_pref": ["Master-Crafted"],
        "mechanics": {
            "diplomatic_envoy": {
                "bonus": 30,
                "description": "Acts as a mobile diplomatic hub."
            }
        }
    },
    "Ancient_Guardians": {
        "naming_theme": ["Webway Ark", "Eternal Guardian", "Aspect Titan", "Spirit Construct", "Wraith Lord"],
        "dna_boost": {"atom_focus": 15, "atom_stability": 10},
        "cost_mod": 1.15,
        "stat_mod": {},
        "abil_pref": ["Ability_Sensor_Sweep", "Ability_Tracking_Lock"],
        "trait_pref": ["Master-Crafted"],
        "mechanics": {
            "webway_teleport": {
                "range": "infinite",
                "cooldown": 5,
                "description": "Can traverse the Webway instantly."
            }
        }
    }
}

# ==========================================
# 3. GENERATION LOGIC
# ==========================================

def get_min_cost(tier):
    if tier == 4: return 20000
    if tier == 5: return 50000
    if tier == 6: return 100000
    return 0

def generate_strategic_units():
    base_path = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\units"
    factions_dir = r"c:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\eternal_crusade\factions"
    
    # Load faction DNA
    with open(os.path.join(factions_dir, "faction_dna.json"), "r") as f:
        faction_dna_data = json.load(f)
        
    registry_path = os.path.join(factions_dir, "faction_registry.json")
    with open(registry_path, "r", encoding='utf-8') as f:
        registry = json.load(f)

    for faction_key, config in FACTION_CONFIGS.items():
        print(f"Generating Strategic Assets for {faction_key}...")
        
        f_dna = faction_dna_data.get(faction_key, {})
        
        # ---------------------------
        # SPACE UNITS (Capital Ships)
        # ---------------------------
        capital_ships = []
        for cls_name, template in SPACE_TEMPLATES.items():
            unit = create_unit_entry(faction_key, cls_name, template, "space", config, f_dna)
            capital_ships.append(unit)
            
        space_outfile = os.path.join(base_path, f"{faction_key.lower()}_capital_ships.json")
        with open(space_outfile, "w", encoding='utf-8') as f:
            json.dump(capital_ships, f, indent=2)
        print(f"  Saved {space_outfile}")
        
        # Register Space
        register_file(registry, faction_key, f"units/{os.path.basename(space_outfile)}")

        # ---------------------------
        # GROUND UNITS (Strategic)
        # ---------------------------
        strategic_ground = []
        for cls_name, template in GROUND_TEMPLATES.items():
            unit = create_unit_entry(faction_key, cls_name, template, "ground", config, f_dna)
            strategic_ground.append(unit)
            
        ground_outfile = os.path.join(base_path, f"{faction_key.lower()}_strategic_ground.json")
        with open(ground_outfile, "w", encoding='utf-8') as f:
            json.dump(strategic_ground, f, indent=2)
        print(f"  Saved {ground_outfile}")
        
        # Register Ground
        register_file(registry, faction_key, f"units/{os.path.basename(ground_outfile)}")
        
    # Save Registry
    with open(registry_path, "w", encoding='utf-8') as f:
        json.dump(registry, f, indent=2)


def create_unit_entry(faction, cls_name, template, domain, config, faction_dna):
    # 1. Base Class DNA
    c_dna = UNIT_CLASSES.get(cls_name)
    if not c_dna:
        print(f"CRITICAL WARNING: No preset for {cls_name}")
        c_dna = {}

    # 2. Blend DNA (70% Class, 30% Faction)
    blended = blend_dna_profiles(c_dna, faction_dna, class_weight=0.7)
    
    # 3. Apply Manual Faction Boosts
    for atom, boost in config["dna_boost"].items():
        if atom in blended:
            blended[atom] += boost
            
    final_dna = normalize_dna(blended)
    
    # 4. Generate Name
    import random
    base_name = random.choice(config["naming_theme"])
    # Append class part if not in name already to ensure uniqueness/clarity
    displayName = f"{faction} {base_name}"
    if cls_name.replace("_", " ").title() not in displayName:
         displayName += f" {cls_name.replace('_', ' ').title()}"

    # 5. Calculate Cost
    min_cost = get_min_cost(template["tier"])
    cost = int(template["base_cost"] * config.get("cost_mod", 1.0))
    if cost < min_cost: cost = min_cost
    upkeep = cost // 10
    
    # 6. Adjust Stats
    stats = template["stats"].copy()
    stats_mod = config.get("stat_mod", {})
    if "hp" in stats_mod: stats["hp"] = int(stats["hp"] * stats_mod["hp"])
    if "armor" in stats_mod: stats["armor"] = int(stats["armor"] * stats_mod["armor"])
    if "damage" in stats_mod: stats["damage"] = int(stats["damage"] * stats_mod["damage"])
    stats["cost"] = cost
    
    # 7. Merge Abilities/Traits
    abilities = list(set(template["suggested_abilities"] + config.get("abil_pref", [])))
    # Ensure reasonable limit (max 6)
    abilities = abilities[:6]
    
    traits = list(set(template["suggested_traits"] + config.get("trait_pref", [])))
    
    # 8. Build Object
    unit = {
        "name": displayName,
        "blueprint_id": f"{faction.lower()}_{cls_name}",
        "type": stats["role"], # capital_ship, titan, strategic_asset
        "faction": faction,
        "tier": template["tier"],
        "cost": cost,
        "upkeep": upkeep,
        "base_stats": stats,
        "elemental_dna": final_dna,
        "source_universe": "eternal_crusade",
        "description": f"{faction} {cls_name} ({domain}). Tier {template['tier']} Strategic Asset.",
        "abilities": abilities,
        "traits": traits,
        "unit_class": cls_name,
        "domain": domain
    }
    
    # Special Mechanic Hooks
    if "mechanics" in config:
        unit["special_mechanics"] = config["mechanics"]
        
    return unit

def register_file(registry, faction, rel_path):
    if "unit_files" not in registry[faction]:
        registry[faction]["unit_files"] = []
    
    if rel_path not in registry[faction]["unit_files"]:
        registry[faction]["unit_files"].append(rel_path)

if __name__ == "__main__":
    generate_strategic_units()
