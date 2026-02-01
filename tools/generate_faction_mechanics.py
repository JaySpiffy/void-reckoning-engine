import os
import json
import sys

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
FACTIONS_DIR = os.path.join(UNIVERSE_PATH, "factions")

# Mechanics are defined as Global Modifiers applied to the faction
mechanics_data = {
    "Zealot_Legions": {
        "id": "Mech_Crusade",
        "name": "Eternal Crusade",
        "description": "Infinite morale and recruitment slots.",
        "modifiers": { "morale_regen": 0.5, "recruitment_slots": 2 }
    },
    "Ascended_Order": {
        "id": "Mech_Psionic_Network",
        "name": "Psionic Network",
        "description": "Instant communication allows perfect coordination.",
        "modifiers": { "accuracy_global": 0.15, "intel_generation": 20 }
    },
    "Iron_Vanguard": {
        "id": "Mech_Industrial_Machine",
        "name": "Industrial Machine",
        "description": "Output is prioritized above all.",
        "modifiers": { "production_speed": 0.25, "building_cost": -0.1 }
    },
    "Hive_Swarm": {
        "id": "Mech_Biomass",
        "name": "Biomass Recycling",
        "description": "The dead feed the living.",
        "modifiers": { "unit_cost": -0.2, "growth_rate": 0.3 }
    },
    "Cyber_Synod": {
        "id": "Mech_Logic_Core",
        "name": "Global Logic Core",
        "description": "Absolute efficiency.",
        "modifiers": { "research_speed": 0.3, "maintenance_cost": -0.1 }
    },
    "Void_Corsairs": {
        "id": "Mech_Raider_Economy",
        "name": "Raider Economy",
        "description": "Profit from violence.",
        "modifiers": { "loot_bonus": 0.5, "speed_strategic": 0.4 }
    },
    "Solar_Hegemony": {
        "id": "Mech_Diplomatic_Corps",
        "name": "Diplomatic Corps",
        "description": "Integration is preferable to destruction.",
        "modifiers": { "diplomacy_bonus": 20, "trade_income": 0.2 }
    },
    "Rift_Daemons": {
        "id": "Mech_Warp_Storm",
        "name": "Aetheric Instability",
        "description": "Reality breaks around them.",
        "modifiers": { "enemy_morale_debuff": -0.1, "volatility_damage_bonus": 0.2 }
    },
    "Scavenger_Clans": {
        "id": "Mech_Waaagh",
        "name": "The Great Waaagh!",
        "description": "Momentum builds with every fight.",
        "modifiers": { "damage_bonus_global": 0.1, "fire_rate": 0.1 }
    },
    "Ancient_Guardians": {
        "id": "Mech_Webway",
        "name": "Webway Network",
        "description": "Masters of travel.",
        "modifiers": { "speed_strategic": 1.0, "defense_global": 0.1 }
    }
}

def generate_mechanics():
    if not os.path.exists(FACTIONS_DIR): os.makedirs(FACTIONS_DIR)
    
    reg_path = os.path.join(FACTIONS_DIR, "mechanics_registry.json")
    
    with open(reg_path, 'w') as f:
        json.dump(mechanics_data, f, indent=2)
    
    print(f"Generated mechanics for {len(mechanics_data)} factions to {reg_path}")

if __name__ == "__main__":
    generate_mechanics()
