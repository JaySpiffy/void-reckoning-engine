import os
import json
import sys

UNIVERSE_PATH = os.path.join("universes", "eternal_crusade")
UNITS_DIR = os.path.join(UNIVERSE_PATH, "units")
FACTIONS_DIR = os.path.join(UNIVERSE_PATH, "factions")

TRAIT_DEFINITIONS = {
    "Fearless": {"effect": "immune_morale", "desc": "Unit never flees from combat."},
    "Regeneration": {"effect": "heal_turn", "value": 0.1, "desc": "Unit regenerates 10% HP per turn."},
    "Shielded": {"effect": "shield_layer", "value": 50, "desc": "Unit has a rechargeable energy shield."},
    "Stealth": {"effect": "visibility_reduce", "desc": "Unit is invisible at long range."},
    "Entrenched": {"effect": "defense_bonus_static", "value": 0.2, "desc": "+20% Defense when not moving."},
    "Reanimation": {"effect": "resurrect_chance", "value": 0.3, "desc": "30% chance to stand back up after death."},
    "Fleet_Footed": {"effect": "move_bonus", "value": 2, "desc": "Unit moves faster than standard."},
    "Sniper": {"effect": "range_bonus", "value": 0.5, "desc": "+50% Weapon Range."},
    "Hatred": {"effect": "damage_bonus_conditional", "desc": "+Damage vs hated enemies."}
}

FACTION_TRAITS = {
    "Zealot_Legions": ["Fearless", "Hatred"],
    "Ascended_Order": ["Shielded"],
    "Iron_Vanguard": ["Entrenched"],
    "Hive_Swarm": ["Regeneration", "Fearless"],
    "Cyber_Synod": ["Reanimation", "Fearless"],
    "Void_Corsairs": ["Fleet_Footed", "Stealth"],
    "Solar_Hegemony": ["Sniper"],
    "Rift_Daemons": ["Shielded", "Fearless"],
    "Scavenger_Clans": [], # They rely on numbers, maybe "Unpredictable"?
    "Ancient_Guardians": ["Shielded", "Sniper"]
}

ROLE_TRAITS = {
    "stealth": ["Stealth"],
    "boss": ["Fearless"],
    "titan": ["Fearless", "Shielded"]
}

def apply_traits():
    # 1. Write Trait Registry
    reg_path = os.path.join(FACTIONS_DIR, "traits_registry.json")
    registry_out = {}
    for key, data in TRAIT_DEFINITIONS.items():
        registry_out[f"Trait_{key}"] = {
            "id": f"Trait_{key}",
            "name": key,
            "effect": data
        }
    
    with open(reg_path, 'w') as f:
        json.dump(registry_out, f, indent=2)
    print("Traits Registry updated.")

    # 2. Update Units
    count = 0
    for filename in os.listdir(UNITS_DIR):
        if not filename.endswith(".json"): continue
        
        filepath = os.path.join(UNITS_DIR, filename)
        with open(filepath, 'r') as f:
            units = json.load(f)
            
        modified = False
        for unit in units:
            faction = unit.get("faction")
            traits = unit.get("traits", [])
            
            # Apply Faction Traits
            if faction == "Zealot_Legions":
                # Zealot Specific Logic per comment
                # Infantry -> Fearless
                # Tank -> Shielded (Holy Armor)
                # Specialist (AA/Sniper) -> Sniper (Guided by Faith)
                
                name_lower = unit.get("name", "").lower()
                kw_lower = str(unit.get("base_stats", {}).get("keywords", "")).lower()
                
                if "infantry" in kw_lower:
                    if "Trait_Fearless" not in traits: traits.append("Trait_Fearless")
                
                if "tank" in name_lower or "vehicle" in kw_lower:
                    if "Trait_Shielded" not in traits: traits.append("Trait_Shielded")
                    
                if "anti_air" in unit.get("role", "") or "specialist" in kw_lower:
                    if "Trait_Sniper" not in traits: traits.append("Trait_Sniper")
                
                # Apply base 'Hatred' to everyone as fallback
                if "Trait_Hatred" not in traits: traits.append("Trait_Hatred")

            elif faction in FACTION_TRAITS:
                for t in FACTION_TRAITS[faction]:
                    trait_id = f"Trait_{t}"
                    if trait_id not in traits:
                        traits.append(trait_id)
                        modified = True
            
            # Apply Role Traits (based on keywords/role)
            # Check description or name since 'role' isn't always consistent in roster files
            keywords = str(unit.get("base_stats", {}).get("keywords", "")).lower()
            name = unit.get("name", "").lower()
            
            if "stealth" in keywords or "infiltrator" in name:
                if "Trait_Stealth" not in traits:
                    traits.append("Trait_Stealth")
                    modified = True
            
            if "titan" in keywords or "god-engine" in name:
                if "Trait_Fearless" not in traits:
                    traits.append("Trait_Fearless")
                    modified = True

            unit["traits"] = traits
            
        if modified:
            with open(filepath, 'w') as f:
                json.dump(units, f, indent=2)
            count += len(units)
            print(f"Updated {filename}")

    print(f"Applied traits to {count} units.")

if __name__ == "__main__":
    apply_traits()
