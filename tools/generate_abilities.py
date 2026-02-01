import os
import json
import sys

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
FACTIONS_DIR = os.path.join(UNIVERSE_PATH, "factions")

# Atomic Logic Payloads define what happens when an ability triggers
# Based on the White Paper's definition of "Atomic DNA as Gameplay Logic"

# Extended Ability Templates
ABILITY_TEMPLATES = {
    # --- CORE (Generic) ---
    "Aether_Blast": { "logic": { "target": "AOE", "damage_type": "magical", "scaling": "volatility_atom", "effect": "deal_damage" }, "base_cost": 50, "cooldown": 30 },
    "Iron_Will": { "logic": { "target": "Friendly_AOE", "scaling": "will_atom", "effect": "restore_morale_and_shield" }, "base_cost": 30, "cooldown": 60 },
    "Nano_Repair": { "logic": { "target": "Self", "scaling": "mass_atom", "effect": "regenerate_hp" }, "base_cost": 40, "cooldown": 45 },
    "Time_Warp": { "logic": { "target": "Global", "scaling": "frequency_atom", "effect": "increase_fleet_speed" }, "base_cost": 100, "cooldown": 120 },
    "Orbital_Bombardment": { "logic": { "target": "Target_Area", "scaling": "energy_atom", "effect": "massive_kinetic_damage" }, "base_cost": 200, "cooldown": 300 },

    # --- UNIQUE (Faction Specific) ---
    
    # ZEALOT
    "Divine_Intervention": { "logic": { "target": "Friendly_Hero", "effect": "invulnerability_short", "scaling": "will_atom" }, "base_cost": 150, "cooldown": 200 },
    "Crusade_Charge": { "logic": { "target": "Global", "effect": "melee_damage_bonus", "scaling": "will_atom" }, "base_cost": 80, "cooldown": 90 },
    
    # PSYKER
    "Psionic_Domination": { "logic": { "target": "Single_Enemy", "effect": "mind_control_temp", "scaling": "aether_atom" }, "base_cost": 120, "cooldown": 180 },
    "Foresight": { "logic": { "target": "Global", "effect": "dodge_bonus", "scaling": "focus_atom" }, "base_cost": 60, "cooldown": 60 },
    
    # INDUSTRIAL
    "Artillery_Barrage": { "logic": { "target": "AOE", "effect": "kinetic_damage", "scaling": "mass_atom" }, "base_cost": 75, "cooldown": 20 },
    "Fortify_Position": { "logic": { "target": "Friendly_AOE", "effect": "defense_bonus", "scaling": "stability_atom" }, "base_cost": 50, "cooldown": 60 },
    
    # HIVE
    "Biomass_Conversion": { "logic": { "target": "Dead_Unit", "effect": "spawn_units", "scaling": "mass_atom" }, "base_cost": 100, "cooldown": 60 },
    "Spore_Cloud": { "logic": { "target": "AOE", "effect": "poison_dot", "scaling": "volatility_atom" }, "base_cost": 40, "cooldown": 30 },
    
    # CYBER
    "Logic_Override": { "logic": { "target": "Enemy_Vehicle", "effect": "stun", "scaling": "information_atom" }, "base_cost": 60, "cooldown": 45 },
    "Reconstruction_Beam": { "logic": { "target": "Friendly_Titan", "effect": "massive_heal", "scaling": "energy_atom" }, "base_cost": 150, "cooldown": 120 },
    
    # SPEED/CORSAIR
    "Hit_and_Run": { "logic": { "target": "Self", "effect": "teleport_short", "scaling": "frequency_atom" }, "base_cost": 40, "cooldown": 15 },
    "Slave_Raid": { "logic": { "target": "Enemy_City", "effect": "steal_resources", "scaling": "volatility_atom" }, "base_cost": 80, "cooldown": 100 },
    
    # TECH
    "Drone_Swarm": { "logic": { "target": "Target_Area", "effect": "spawn_temp_drones", "scaling": "information_atom" }, "base_cost": 100, "cooldown": 90 },
    "Marker_Light": { "logic": { "target": "Single_Enemy", "effect": "accuracy_debuff_target", "scaling": "focus_atom" }, "base_cost": 20, "cooldown": 10 },
    
    # AETHER/DAEMON
    "Reality_Tear": { "logic": { "target": "Target_Area", "effect": "summon_daemons", "scaling": "aether_atom" }, "base_cost": 200, "cooldown": 240 },
    "Corruption": { "logic": { "target": "Single_Enemy", "effect": "convert_take_damage", "scaling": "will_atom" }, "base_cost": 90, "cooldown": 60 },
    
    # SCAVENGER
    "Big_Red_Button": { "logic": { "target": "Self", "effect": "random_explode_or_buff", "scaling": "volatility_atom" }, "base_cost": 10, "cooldown": 10 },
    "More_Dakka": { "logic": { "target": "Friendly_AOE", "effect": "fire_rate_bonus", "scaling": "volatility_atom" }, "base_cost": 50, "cooldown": 40 },
    
    # ELITE/GUARDIAN
    "Webway_Strike": { "logic": { "target": "Global", "effect": "strategic_teleport", "scaling": "focus_atom" }, "base_cost": 300, "cooldown": 300 },
    "Prescience": { "logic": { "target": "Self", "effect": "guaranteed_crit", "scaling": "focus_atom" }, "base_cost": 80, "cooldown": 60 }
}

# Mapping Specific Abilities to Factions (Beyond the specific ones named above)
FACTION_ABILITIES = {
    "Zealot_Legions": ["Iron_Will", "Orbital_Bombardment", "Divine_Intervention", "Crusade_Charge"],
    "Ascended_Order": ["Aether_Blast", "Time_Warp", "Psionic_Domination", "Foresight"],
    "Iron_Vanguard": ["Orbital_Bombardment", "Nano_Repair", "Artillery_Barrage", "Fortify_Position"],
    "Hive_Swarm": ["Nano_Repair", "Biomass_Conversion", "Spore_Cloud"],
    "Cyber_Synod": ["Nano_Repair", "Logic_Override", "Reconstruction_Beam", "Orbital_Bombardment"],
    "Void_Corsairs": ["Time_Warp", "Hit_and_Run", "Slave_Raid"],
    "Solar_Hegemony": ["Orbital_Bombardment", "Drone_Swarm", "Marker_Light"],
    "Rift_Daemons": ["Aether_Blast", "Reality_Tear", "Corruption", "Time_Warp"],
    "Scavenger_Clans": ["Orbital_Bombardment", "Big_Red_Button", "More_Dakka"],
    "Ancient_Guardians": ["Time_Warp", "Webway_Strike", "Prescience", "Aether_Blast"]
}

def generate_abilities():
    registry = {}
    
    for faction, ability_keys in FACTION_ABILITIES.items():
        for key in ability_keys:
            if key not in ABILITY_TEMPLATES:
                print(f"Warning: Ability {key} not found in templates.")
                continue
                
            tmpl = ABILITY_TEMPLATES[key]
            
            # Flavor Naming roughly based on key + faction if needed, or just use Key Name if it's unique enough
            name = key.replace("_", " ")
            
            # Zealot Flavoring
            if faction == "Zealot_Legions" and key == "Iron_Will": name = "Litany of Hate"
            if faction == "Zealot_Legions" and key == "Orbital_Bombardment": name = "Exterminatus"
            
            # Scavenger Flavor
            if faction == "Scavenger_Clans" and key == "Orbital_Bombardment": name = "Rok Drop"
            
            ability_id = f"Ability_{faction}_{key}"
            
            registry[ability_id] = {
                "id": ability_id,
                "name": name,
                "faction": faction,
                "description": f"{name}: {tmpl['logic'].get('effect', 'Unknown effect')}",
                "manacost": tmpl["base_cost"],
                "cooldown": tmpl["cooldown"],
                "payload": tmpl["logic"],
                "source": "generated"
            }
            
    # Write Registry
    path = os.path.join(FACTIONS_DIR, "ability_registry.json")
    with open(path, 'w') as f:
        json.dump(registry, f, indent=2)
    print(f"Generated {len(registry)} abilities to {path}")


if __name__ == "__main__":
    generate_abilities()
